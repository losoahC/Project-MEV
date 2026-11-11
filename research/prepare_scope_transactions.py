import json
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parent
load=lambda n:json.loads((R/n).read_text())
def main():
 data=load('expanded_scope_logs.json');leads={x['address'].lower() for x in load('address_leads.json')['wallets']};tokens={x['address'].lower():x for x in load('coingecko_eth_tokenlist.json')['tokens'] if x['chainId']==1};net=defaultdict(lambda:defaultdict(int));blocks={};invalid=[]
 for l in data['rows']:
  if len(l['topics'])!=3 or len(l['data'])!=66:invalid.append(l);continue
  h=l['transactionHash'];blocks[h]=int(l['blockNumber'],16);src='0x'+l['topics'][1][-40:];dst='0x'+l['topics'][2][-40:];v=int(l['data'],16)
  if src in leads:net[h][l['address']]-=v
  if dst in leads:net[h][l['address']]+=v
 rows=[{'hash':h,'block':blocks[h],'net_token_raw':{t:str(v) for t,v in ns.items() if v},'verified_token_net_out':{t:str(v) for t,v in ns.items() if v<0 and t in tokens}} for h,ns in net.items()]
 (R/'expanded_scope_transactions.json').write_text(json.dumps({'scope_cutoff':data['cutoff_timestamp'],'rows':rows,'invalid_or_non_erc20_logs':invalid},indent=2));print('known outflows',sum(bool(r['verified_token_net_out']) for r in rows),'valid logs transactions',len(rows),'pre-window',sum(r['block']<26300640 for r in rows),'invalid',len(invalid))
if __name__=='__main__':main()
