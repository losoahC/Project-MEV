"""Additional Binance spot marks only for already contract-matched currency IDs."""
import json
from collections import defaultdict
from src.arbitrage.discover import ROOT
from src.arbitrage.value_candidates import book_from_archive
from src.arbitrage.full_valuations import FullWindowBook
from src.arbitrage.reconstruct import Reconstruction

def run():
    p=ROOT/'data/processed/mev_full_window';book=book_from_archive();book.__class__=FullWindowBook;book.engine=Reconstruction(ROOT.parent/'research',True);needed=defaultdict(set)
    for r in json.loads((p/'terminal_cycle_profits.json').read_text()):
        for a in r['missing_price_assets']:
            if a in book.registry:needed[a].add(r['reference_exit_timestamp'])
    rows=[]
    for a,timestamps in needed.items():
        meta=book.registry[a];book.binance_spot(meta['symbol'],('2026-10-29','2026-10-30'))
        for ts in sorted(timestamps):
            quote=book.price(meta['symbol'],ts,venue='Binance');rows.append({'address':a,'timestamp':ts,'metadata':meta,'accepted':quote is not None,'USD_price':str(quote[0]) if quote else None,'evidence':quote[1] if quote else None,'method':'Already verified exact Ethereum contract to currency ID; independent Binance spot prior completed minute, converted with observed USDTUSD. No ticker-only new contract mapping.'})
    (ROOT/'data/processed/completion_binance_prices.json').write_text(json.dumps({'rows':rows},indent=2));print(json.dumps(rows,indent=2))
if __name__=='__main__':run()
