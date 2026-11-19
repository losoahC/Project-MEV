"""ABI-compatible event decoding; protocol identity requires deployment/factory proof."""
from web3 import Web3
from src.decoding.events import swap,signed_word,integer
sig=lambda x:'0x'+Web3.keccak(text=x).hex().removeprefix('0x')
PANCAKE=sig('Swap(address,address,int256,int256,uint160,uint128,int24,uint128,uint128)')
V4=sig('Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)')
FILL=sig('Fill(bytes32,address,address,uint256)')
ORDER=sig('OrderFilled(bytes32,uint256)')

def extended_swap(log):
    old=swap(log)
    if old:return {**old,'pool_key':old['pool'],'amount_sign_convention':'V2/V3 pool delta'}
    topics=log.get('topics',[])
    if not topics:return None
    topic=topics[0].lower();words=[log['data'][i:i+64] for i in range(2,len(log['data']),64)]
    if topic==PANCAKE and len(words)==7 and len(topics)==3:
        return {'pool':log['address'].lower(),'pool_key':log['address'].lower(),'protocol':'Pancake-V3-compatible (event only)','amount0_raw':str(signed_word(words[0])),'amount1_raw':str(signed_word(words[1])),'log_index':integer(log['logIndex']),'amount_sign_convention':'pool delta','sqrt_price_x96_after':str(int(words[2],16))}
    if topic==V4 and len(words)==6 and len(topics)==3:
        return {'pool':log['address'].lower(),'pool_key':log['address'].lower()+':'+topics[1].lower(),'pool_id':topics[1].lower(),'protocol':'V4-compatible (event only)','amount0_raw':str(signed_word(words[0])),'amount1_raw':str(signed_word(words[1])),'log_index':integer(log['logIndex']),'amount_sign_convention':'raw V4 event delta; do not combine with pool-transfer PnL without settlement reconstruction','sqrt_price_x96_after':str(int(words[2],16))}
    return None

def order_event(log):
    ts=log.get('topics',[])
    if not ts:return None
    if ts[0].lower()==FILL and len(ts)==4 and len(log['data'])==66:
        return {'protocol':'UniswapX-compatible Fill (deployment not yet checked)','emitter':log['address'].lower(),'order_hash':ts[1].lower(),'filler':'0x'+ts[2][-40:].lower(),'swapper':'0x'+ts[3][-40:].lower(),'nonce':str(integer(log['data'])),'log_index':integer(log['logIndex'])}
    if ts[0].lower()==ORDER and len(ts)>=1:
        return {'protocol':'1inch-compatible OrderFilled (event only)','emitter':log['address'].lower(),'topics':ts,'data':log['data'],'log_index':integer(log['logIndex'])}
    return None
