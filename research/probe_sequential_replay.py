"""Read-only historical RPC capability probes. Retain exact requests/errors."""
import json, time, subprocess
from pathlib import Path
R = Path(__file__).resolve().parent
def main():
    call = {'to':'0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2','data':'0x18160ddd','gas':'0x186a0'}
    block = hex(26301608)
    probes = [
      ('eth_simulateV1',[{'blockStateCalls':[{'calls':[call,call]}],'validation':False},block]),
      ('trace_callMany',[[[call,['trace','stateDiff']],[call,['trace','stateDiff']]],block]),
    ]
    rows=[]
    for method,params in probes:
        request={'jsonrpc':'2.0','id':1,'method':method,'params':params}
        row={'endpoint':'https://eth.drpc.org','request':request,'retrieved_unix':time.time()}
        try:
            p=subprocess.run(['curl','--silent','--show-error','--max-time','55','-H','Content-Type: application/json','--data',json.dumps(request),row['endpoint']],capture_output=True,text=True,check=True)
            row['response']=json.loads(p.stdout)
        except Exception as e: row['transport_error']=str(e)
        rows.append(row)
        print(method,json.dumps(row.get('response',row.get('transport_error')))[:1600],flush=True)
    (R/'sequential_replay_capabilities.json').write_text(json.dumps(rows,indent=2))
if __name__=='__main__': main()
