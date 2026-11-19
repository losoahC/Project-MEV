"""Current token display metadata; symbols never become price identity keys."""
import json
from eth_abi import decode
from src.arbitrage.discover import ROOT
from src.arbitrage.tron_pool_metadata import batch,selector
from src.arbitrage.tron_collect import encode_addr

def run():
    p=ROOT/'data/processed/mev_tron';pools=json.loads((p/'pool_metadata_current.json').read_text());keys=json.loads((p/'sun_v4_pool_keys.json').read_text());tokens={r['fields'][k] for r in pools for k in ['token0','token1'] if k in r['fields']}|{r[k] for r in keys for k in ['currency0_hex','currency1_hex'] if k in r};tokens.discard('41'+'0'*40);jobs=[(t,f,t,'0x'+selector(f+'()').hex()) for t in sorted(tokens) for f in ['symbol','decimals']];rows={t:{'token_hex':t,'token_address':encode_addr(t),'metadata_state':'latest, not historical','price_identity_inferred_from_symbol':False,'evidence':{},'failures':{}} for t in tokens}
    for (t,field),doc in batch(jobs).items():
        rows[t]['evidence'][field]=doc;raw=doc['response'].get('result')
        try:
            assert isinstance(raw,str)
            if field=='decimals':assert len(raw)==66;v=int(raw,16);assert 0<=v<=255
            else:
                b=bytes.fromhex(raw[2:]);v=decode(['string'],b)[0] if len(b)!=32 else b.rstrip(b'\0').decode();assert len(v)<256
            rows[t][field]=v
        except Exception as ex:rows[t]['failures'][field]=str(ex)
    (p/'token_metadata_current.json').write_text(json.dumps(list(rows.values()),indent=2));print('Current TRON token metadata',len(rows))
if __name__=='__main__':run()
