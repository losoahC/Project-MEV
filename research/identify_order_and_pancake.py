import json,gzip
from pathlib import Path
from collections import defaultdict,Counter
from Crypto.Hash import keccak
R=Path(__file__).resolve().parent
hashsig=lambda s:'0x'+keccak.new(digest_bits=256,data=s.encode()).hexdigest()
FILL=hashsig('Fill(bytes32,address,address,uint256)');ORDER=hashsig('OrderFilled(bytes32,uint256)');PAN=hashsig('Swap(address,address,int256,int256,uint160,uint128,int24,uint128,uint128)')
REACTORS={'0x00000011f84b9aa48e5f8aa8b9897600006289be','0x6000da47483062a0d734ba3dc7576ce6a0b645c4'}
def main():
 old=json.loads((R/'unified_target_valuation.json').read_text())['rows'];leads={r['address'].lower() for r in json.loads((R/'address_leads.json').read_text())['wallets']};cache={};orders=[];pancakes=[]
 for r in old:
  n=r['block']
  if n not in cache:
   folder='window_raw' if n<=26301940 else 'extension_raw';cache[n]={x['transactionHash']:x for x in json.loads(gzip.decompress((R/folder/f'{n}.json.gz').read_bytes()))}
  rec=cache[n][r['hash']]
  for l in rec['logs']:
   ts=l['topics']
   if not ts:continue
   if ts[0]==FILL and l['address'] in REACTORS and len(ts)==4:
    swapper='0x'+ts[3][-40:]
    if swapper in leads:orders.append({'hash':r['hash'],'block':n,'protocol':'UniswapX','reactor':l['address'],'order_hash':ts[1],'filler':'0x'+ts[2][-40:],'swapper':swapper,'nonce':str(int(l['data'],16)),'root_from':rec['from'],'root_to':rec['to']})
   elif ts[0]==ORDER:orders.append({'hash':r['hash'],'block':n,'protocol':'1inch-compatible OrderFilled','emitter':l['address'],'root_from':rec['from'],'root_to':rec['to'],'data':l['data']})
   elif ts[0]==PAN:pancakes.append({'hash':r['hash'],'block':n,'pool':l['address'],'log_index':int(l['logIndex'],16),'topics':ts,'data':l['data']})
 out={'sources':['https://developers.uniswap.org/docs/liquidity/uniswapx/deployments','https://raw.githubusercontent.com/Uniswap/UniswapX/main/src/base/ReactorEvents.sol','https://raw.githubusercontent.com/1inch/limit-order-protocol/master/contracts/interfaces/IOrderMixin.sol','https://raw.githubusercontent.com/pancakeswap/pancake-v3-contracts/main/projects/v3-core/contracts/interfaces/pool/IPancakeV3PoolEvents.sol'],'signatures':{'Fill':FILL,'OrderFilled':ORDER,'PancakeSwap':PAN},'orders':orders,'pancake_events':pancakes}
 (R/'order_protocol_identification.json').write_text(json.dumps(out,indent=2));print('orders',dict(Counter(x['protocol'] for x in orders)),'pancake',len(pancakes),len({x['pool'] for x in pancakes}),len({x['hash'] for x in pancakes}));print('fillers',dict(Counter(x.get('filler',x['root_to']) for x in orders)))
if __name__=='__main__':main()
