"""Inspect ABI-compatible router limits. Decoding alone does not authenticate deployed code."""
from eth_abi import decode


def inspect_router(calldata):
    selector=calldata[:10].lower()
    if selector not in ('0x3593564c','0x24856bc3'):
        return {'status':'unsupported_selector','selector':selector,'limits':[]}
    try:
        types=['bytes','bytes[]','uint256'] if selector=='0x3593564c' else ['bytes','bytes[]']
        decoded=decode(types,bytes.fromhex(calldata[10:]))
        commands,inputs=decoded[:2]
        limits=[];unknown=[]
        def visit(commands,inputs,prefix='',depth=0):
            if depth>8 or len(commands)!=len(inputs):
                raise ValueError('Invalid command plan')
            for i,(command,payload) in enumerate(zip(commands,inputs)):
                code=command&0x7f;location=f'{prefix}{i}'
                if code in (0,1,8,9):
                    path_type='bytes' if code in (0,1) else 'address[]'
                    recipient,amount,bound,path,payer=decode(['address','uint256','uint256',path_type,'bool'],payload)
                    limits.append({'command_location':location,'command_type':code,'allow_revert':bool(command&0x80),'recipient':recipient.lower(),'amount_raw':str(amount),'bound_raw':str(bound),'bound_kind':'minimum_output' if code in (0,8) else 'maximum_input','path':'0x'+path.hex() if isinstance(path,bytes) else list(path),'payer_is_user':payer})
                elif code==0x21:
                    nested_commands,nested_inputs=decode(['bytes','bytes[]'],payload)
                    visit(nested_commands,nested_inputs,location+'.',depth+1)
                elif code in (0x0b,0x0c):
                    recipient,bound=decode(['address','uint256'],payload)
                    limits.append({'command_location':location,'command_type':code,'allow_revert':bool(command&0x80),'recipient':recipient.lower(),'bound_raw':str(bound),'bound_kind':'wrap_minimum' if code==0x0b else 'unwrap_minimum'})
                elif code==4:
                    token,recipient,bound=decode(['address','address','uint256'],payload)
                    limits.append({'command_location':location,'command_type':code,'allow_revert':bool(command&0x80),'token':token.lower(),'recipient':recipient.lower(),'bound_raw':str(bound),'bound_kind':'sweep_minimum'})
                else:
                    unknown.append({'command_location':location,'command_type':code,'payload_bytes':len(payload)})
        visit(commands,inputs)
        return {'status':'ABI_compatible_fields_decoded','selector':selector,'deadline':str(decoded[2]) if len(decoded)>2 else None,'limits':limits,'undecoded_commands':unknown,'meaning_limit':'Numeric ABI-compatible fields only. Contract implementation, recipient aliases, V4 actions and per-hop limits need separate validation. A low/zero bound is not evidence of deliberate self-loss.'}
    except Exception as exc:
        return {'status':'decode_error','selector':selector,'error':str(exc),'limits':[]}
