"""SunSwap V4 key lookup, authenticated by hashing all five ABI words to PoolId."""
import json
from web3 import Web3
from src.arbitrage.discover import ROOT
from src.arbitrage.tron_collect import encode_addr,decode_addr
from src.arbitrage.tron_more import fetch
TOPIC='04206ad2b7c0f463bff3dd4f33c5735b0f2957a351e4f79763a4fa9e775dd237'

def run():
    p=ROOT/'data/processed/mev_tron';receipts=json.loads((p/'named_bot_receipts.json').read_text());receipts += [r for path in p.glob('*/receipts.json') for r in json.loads(path.read_text())];needed={(l['address'],l['topics'][1]) for r in receipts for l in r['receipt'].get('log',[]) if l.get('topics') and l['topics'][0]==TOPIC};rows=[]
    for manager,pid in sorted(needed):
        body={'owner_address':decode_addr('TUAAqYySyBJDLJDxnQKqtcPBW1JXJuqrSS'),'contract_address':'41'+manager[-40:],'function_selector':'poolIdToPoolKey(bytes32)','parameter':pid,'visible':False};doc,path=fetch('https://api.trongrid.io/wallet/triggerconstantcontract',body);j=doc.get('response',{});r={'manager':encode_addr(manager),'manager_hex':'41'+manager[-40:],'pool_id':pid,'evidence':path,'verified_pool_key':False}
        try:
            key=j['constant_result'][0];assert len(key)==320
            actual=Web3.keccak(bytes.fromhex(key)).hex().removeprefix('0x');assert actual==pid
            w=[key[i:i+64] for i in range(0,len(key),64)];r.update(verified_pool_key=True,encoded_key=key,currency0_hex='41'+w[0][-40:],currency1_hex='41'+w[1][-40:],hooks_hex='41'+w[2][-40:],fee=int(w[3],16),parameters=w[4],official_manager=r['manager']=='TVjuTE3V5bMVdpfNhid8kD2v35T2k1u1Br')
        except Exception as ex:r['error']=repr(ex);r['response']=j
        r['limit']='Getter is current state; exact key preimage hashes to historical event PoolId. This authenticates token identities/key values, not historical reserves or subsequent price path.';rows.append(r)
    (p/'sun_v4_pool_keys.json').write_text(json.dumps(rows,indent=2));print([(r['pool_id'][:12],r['verified_pool_key'],r.get('currency0_hex'),r.get('currency1_hex')) for r in rows])
if __name__=='__main__':run()
