"""Match ETH receipts, THORNode/Midgard and confirmed BTC outputs. Attribution is flow-only."""
import argparse
from datetime import datetime,timezone
from decimal import Decimal,getcontext
import json
from eth_abi import decode
from web3 import Web3
import pandas as pd
from src.ingestion.public_evidence import PublicEvidence
from src.ingestion.evidence import read_json
from src.visualization.common import ROOT
getcontext().prec=80
BASE='https://gateway.liquify.com/chain/'
ROUTER='0xd37bbe5744d730a1d98d8dc97c42f0ca46ad7146'
DEPOSIT='0x'+Web3.keccak(text='Deposit(address,address,uint256,string)').hex().removeprefix('0x')
HASHES=['0x8136b0834bb7d45761421875688a3a2106051e3d9f3fd23e351ffef3ad384172','0x6c796881f623a50383d112545ff2fbf224b5a8c26d8f824c53c681de0269612e','0x7f8d415a1661815c4150d7b4f313af0a491026bc3908947aa342c22c621adc6b']

def norm(h): return h.lower().removeprefix('0x')
def units(raw): return Decimal(raw)/10**8

def btc_match(transaction,txid,address,amount,inbound):
    assert norm(transaction['txid'])==norm(txid),'BTC hash mismatch'
    assert transaction['status']['confirmed'],'Unconfirmed BTC output'
    outputs=[{'index':i,'value_sats':o['value']} for i,o in enumerate(transaction['vout']) if o.get('scriptpubkey_address')==address]
    assert sum(o['value_sats'] for o in outputs)==int(amount),'BTC recipient/amount mismatch'
    memo=('OUT:'+norm(inbound).upper()).encode().hex()
    assert any(memo in o['scriptpubkey'].lower() for o in transaction['vout'] if o.get('scriptpubkey_type')=='op_return'),'BTC inbound memo mismatch'
    return outputs

def prior_close(bars,timestamp,minutes=1):
    minute=(timestamp//60-minutes)*60
    selected=[b for b in bars if int(b[0])==minute and Decimal(str(b[5]))>0]
    assert len(selected)==1,'Missing or duplicate completed reference candle'
    return Decimal(str(selected[0][4])),minute

def run(online=False):
    public=PublicEvidence(ROOT,online)
    discovery=read_json(ROOT/'data/processed/thorchain_discovery.json')
    registry={w['address']:w for w in read_json(ROOT/'data/processed/wallet_registry.json')}
    def get(url):
        d,path=public.get(url)
        assert d.get('http_status')==200 and d.get('response') is not None,(url,d.get('error'))
        return d['response'],path
    def eth(h):
        t,tp=public.rpc('eth_getTransactionByHash',[h]);r,rp=public.rpc('eth_getTransactionReceipt',[h]);b,bp=public.rpc('eth_getBlockByNumber',[t['blockNumber'],False])
        assert norm(t['hash'])==norm(h)==norm(r['transactionHash'])
        assert r['status']=='0x1' and r['blockHash'].lower()==b['hash'].lower()==t['blockHash'].lower()
        assert b['transactions'][int(t['transactionIndex'],16)].lower()==h.lower()
        return t,r,b,[tp,rp,bp]
    def fund_path(address,before,required,visited=None):
        visited=set() if visited is None else visited
        assert address not in visited and len(visited)<6,'Cyclic/too long funding path'
        visited.add(address)
        if address in registry:return [],address
        candidates=[]
        for link in discovery['addresses'].get(address,{}).get('funding_links',[]):
            t,r,b,refs=eth(link['tx_hash'])
            if int(b['timestamp'],16)<before and int(t['value'],16)>=required:
                candidates.append((int(b['timestamp'],16),t,r,b,refs,link.get('evidence_path')))
        if not candidates:
            d,path=get(f'https://eth.blockscout.com/api/v2/addresses/{address}/transactions?filter=to')
            for item in d['items']:
                if item['to']['hash'].lower()!=address or int(item['value'])<required:continue
                if datetime.fromisoformat(item['timestamp'].replace('Z','+00:00')).timestamp()>=before:continue
                t,r,b,refs=eth(item['hash'])
                if t['input']=='0x' and int(b['timestamp'],16)<before:
                    candidates.append((int(b['timestamp'],16),t,r,b,refs,path))
        assert candidates,('No prior material ordinary funding link',address,before)
        ts,t,r,b,refs,indexsource=max(candidates,key=lambda c:c[0])
        assert t['to'].lower()==address and t['input']=='0x'
        amount=int(t['value'],16);prior,anchor=fund_path(t['from'].lower(),ts,amount,visited)
        link={'sender':t['from'].lower(),'recipient':address,'tx_hash':t['hash'].lower(),'amount_wei':str(amount),'timestamp':ts,'timestamp_utc':datetime.fromtimestamp(ts,timezone.utc).isoformat(),'evidence':refs,'index_evidence':indexsource}
        return prior+[link],anchor
    prices={};price_refs={}
    for symbol in ['ETH','BTC']:
        prices[symbol],price_refs[symbol]=get(f'https://api.exchange.coinbase.com/products/{symbol}-USD/candles?granularity=60&start=2026-11-17T13:00:00Z&end=2026-11-17T15:00:00Z')
    cases=[]
    for i,h in enumerate(HASHES,1):
        t,r,b,refs=eth(h);ts=int(b['timestamp'],16);amount=int(t['value'],16)
        assert t['to'].lower()==ROUTER and t['input'][:10]=='0x44bc937b'
        vault,asset,declared,memo,expiry=decode(['address','address','uint256','string','uint256'],bytes.fromhex(t['input'][10:]))
        assert asset=='0x'+'0'*40 and declared==amount and expiry>=ts
        matching=[l for l in r['logs'] if l['address'].lower()==ROUTER and l['topics'][0].lower()==DEPOSIT]
        assert len(matching)==1
        log=matching[0];logged,logmemo=decode(['uint256','string'],bytes.fromhex(log['data'][2:]))
        assert logged==amount and logmemo==memo and log['topics'][1][-40:].lower()==vault[2:].lower() and int(log['topics'][2],16)==0
        node,np=get(BASE+'thorchain_api/thorchain/tx/details/'+norm(h).upper());inbound=node['tx']['tx']
        assert norm(inbound['id'])==norm(h) and inbound['chain']=='ETH' and inbound['from_address'].lower()==t['from'].lower()
        assert inbound['to_address'].lower()==vault.lower() and inbound['memo']==memo
        assert inbound['coins']==[{'asset':'ETH.ETH','amount':str(amount//10**10)}] and amount%10**10==0
        midurl=BASE+'thorchain_midgard/v2/actions?txid='+norm(h).upper();d,path=public.get(midurl)
        if d.get('http_status')!=200:midurl+='&type=swap&limit=50'
        mid,mp=get(midurl)
        actions=[a for a in mid['actions'] if a['type']=='swap' and any(norm(x['txID'])==norm(h) for x in a['in'])]
        assert len(actions)==1 and actions[0]['status']=='success';action=actions[0]
        assert len(action['in'])==1 and action['in'][0]['coins']==inbound['coins'] and action['in'][0]['address'].lower()==t['from'].lower()
        assert action['metadata']['swap']['memo']==memo
        out=node['out_txs'];assert len(out)==len(action['out'])==1,'Multi-output conversion requires explicit aggregation'
        outbound=out[0];mo=action['out'][0]
        assert norm(outbound['id'])==norm(mo['txID']) and outbound['chain']=='BTC' and outbound['coins']==mo['coins']
        coin=outbound['coins'][0];assert coin['asset']=='BTC.BTC' and outbound['to_address']==mo['address']==memo.split(':')[2]
        btc,btcp=get('https://blockstream.info/api/tx/'+norm(outbound['id']))
        matches=btc_match(btc,outbound['id'],outbound['to_address'],coin['amount'],h)
        funding,anchor=fund_path(t['from'].lower(),ts,amount)
        metadata=action['metadata']['swap'];ethqty=Decimal(amount)/10**18;btcqty=units(coin['amount'])
        ep,minute=prior_close(prices['ETH'],ts);bpUSD,_=prior_close(prices['BTC'],ts)
        inputusd=ethqty*ep;outputusd=btcqty*bpUSD;shortfall=inputusd-outputusd
        gas=Decimal(int(r['gasUsed'],16)*int(r['effectiveGasPrice'],16))/10**18
        network=sum((units(c['amount']) for c in metadata['networkFees'] if c['asset']=='BTC.BTC'),Decimal(0));stream=metadata['streamingSwapMeta']
        assert int(stream['outCoin']['amount'])-int(coin['amount'])==sum(int(c['amount']) for c in metadata['networkFees'] if c['asset']=='BTC.BTC')
        sensitivity={}
        for lookback in [5,15]:
            e,_=prior_close(prices['ETH'],ts,lookback);v,_=prior_close(prices['BTC'],ts,lookback)
            sensitivity[f'prior_{lookback}min_USD']=str(ethqty*e-btcqty*v)
        row={'case_id':f'T{i}','ethereum_deposit':h,'source_address':t['from'].lower(),'source_block':int(t['blockNumber'],16),'deposit_timestamp':ts,'deposit_utc':datetime.fromtimestamp(ts,timezone.utc).isoformat(),'router':ROUTER,'vault':vault.lower(),'memo':memo,'input_ETH':str(ethqty),'output_BTC':str(btcqty),'BTC_per_ETH':str(btcqty/ethqty),'destination_address':outbound['to_address'],'bitcoin_txid':norm(outbound['id']),'bitcoin_outputs':matches,'bitcoin_confirmed_block':btc['status'],'inclusion_delay_seconds':btc['status']['block_time']-ts,'delay_definition':'Ethereum inclusion to Bitcoin block timestamp; coarse cross-chain clocks, not exact service latency','funding_path':funding,'incident_anchor_address':anchor,'common_control_established':False,'exclusive_stolen_unit_provenance_established':False,'funding_scope':'Chronologically prior ordinary transfers, each >= the next transfer. Fund-flow association, not exclusive coin-taint accounting or ownership. Other inputs and intervening spending not exhausted.','reference':{'venue':'Coinbase','method':'prior completed minute close for both assets at deposit time; output valued at same reference time','minute_utc':datetime.fromtimestamp(minute,timezone.utc).isoformat(),'ETH_USD':str(ep),'BTC_USD':str(bpUSD),'evidence':price_refs},'input_reference_USD':str(inputusd),'output_reference_USD':str(outputusd),'estimated_execution_shortfall_USD':str(shortfall),'shortfall_rate':str(shortfall/inputusd),'ethereum_gas_ETH':str(gas),'ethereum_gas_reference_USD':str(gas*ep),'network_fee_BTC':str(network),'network_fee_reference_USD':str(network*bpUSD),'actual_bitcoin_network_fee_sats':btc['fee'],'reported_liquidity_fee_RUNE':str(units(metadata['liquidityFee'])),'reported_swap_slip_bps':metadata['swapSlip'],'streaming_swap':stream,'midgard_price_mark_USD':{'ETH':metadata['inPriceUSD'],'BTC':metadata['outPriceUSD']},'price_impact_USD':None,'price_impact_limit':'No historical THOR pool/counterfactual replay; liquidity fee RUNE-denominated. No invented USD fee/additive decomposition. Shortfall includes market/streaming/timing effects.','sensitivity':sensitivity,'evidence':{'ethereum':refs,'thornode':np,'midgard':mp,'bitcoin':btcp},'classification':'observed conversion; estimated reference shortfall; incident fund-flow association only','ethereum_MEV_link_established':False}
        assert row['inclusion_delay_seconds']>=0
        cases.append(row);(ROOT/f'reports/case_studies/T{i}_thorchain.json').write_text(json.dumps(row,indent=2))
        print(row['case_id'],ethqty,btcqty,'shortfall USD',shortfall,'prior funding links',len(funding),flush=True)
    (ROOT/'data/processed/thorchain_paths.json').write_text(json.dumps(cases,indent=2))
    pd.DataFrame([{k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in cases]).to_parquet(ROOT/'data/processed/thorchain_paths.parquet',index=False)
    public.write_index()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--online',action='store_true');a=p.parse_args();run(a.online)
