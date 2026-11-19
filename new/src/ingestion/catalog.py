"""Regenerate DuckDB's query layer from the processed and figure-support Parquet tables."""
import hashlib
import json

import duckdb

from src.visualization.common import ROOT


def build():
    rows=[]
    with duckdb.connect(str(ROOT/'data/processed/research.duckdb')) as db:
        for directory in ('data/processed','reports/tables'):
            for path in sorted((ROOT/directory).glob('*.parquet')):
                name=path.stem
                identifier='"'+name.replace('"','""')+'"'
                filename=str(path).replace("'","''")
                db.execute(f"CREATE OR REPLACE TABLE {identifier} AS SELECT * FROM read_parquet('{filename}')")
                count=db.execute(f'SELECT COUNT(*) FROM {identifier}').fetchone()[0]
                rows.append({'table':name,'source':str(path.relative_to(ROOT)),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rows':count})
    (ROOT/'data/processed/catalog.json').write_text(json.dumps(rows,indent=2))
    print(f'Rebuilt {len(rows)} query tables from Parquet; evidence remains in immutable raw objects')


if __name__=='__main__':
    build()
