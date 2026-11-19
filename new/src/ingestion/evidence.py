import gzip
import hashlib
import json
from pathlib import Path


def read_json(path):
    path = Path(path)
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def unwrap(data):
    return data.get("result", data) if isinstance(data, dict) else data


class EvidenceStore:
    """Copy exact source bytes once; never replace an archived object."""

    def __init__(self, root, legacy):
        self.root, self.legacy = Path(root), Path(legacy)
        manifest = self.root / "data/raw/manifest.json"
        self.records = {r["path"]: r for r in read_json(manifest).get("objects", [])} if manifest.exists() else {}
        (self.root / "data/raw/objects").mkdir(parents=True, exist_ok=True)

    def archive(self, path, provider, method):
        path = Path(path)
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        suffix = ".json.gz" if path.suffix == ".gz" else path.suffix
        rel = "data/raw/objects/" + digest + suffix
        dest = self.root / rel
        if not dest.exists():
            with dest.open("xb") as f:
                f.write(raw)
        elif hashlib.sha256(dest.read_bytes()).hexdigest() != digest:
            raise ValueError(f"Evidence corruption: {rel}")
        origin = str(path.relative_to(self.legacy)) if path.is_relative_to(self.legacy) else str(path.name)
        self.records[rel] = {"path": rel, "sha256": digest, "bytes": len(raw),
                             "legacy_source": origin, "provider": provider, "method": method,
                             "original_fetch_time": None,
                             "time_note": "Legacy cache; original fetch time not reliably recorded. Import time is not acquisition time."}
        return rel

    def save(self):
        path = self.root / "data/raw/manifest.json"
        path.write_text(json.dumps({"version": 1, "objects": sorted(self.records.values(), key=lambda x: x["path"])}, indent=2))


def block_candidates(number, kind):
    names = {
        "header": [f"window_raw/{number}_block.json.gz", f"extension_raw/{number}_block.json.gz",
                   f"wallet_header_raw/{number}.json.gz", f"full_headers_raw/{number}.json.gz",
                   f"chain_raw/{number}_block.json"],
        "receipts": [f"window_raw/{number}.json.gz", f"extension_raw/{number}.json.gz",
                     f"scope_detail_raw/{number}_receipts.json.gz", f"chain_raw/{number}_receipts.json"],
        "traces": [f"drpc_trace_raw/{number}.json.gz", f"scope_detail_raw/{number}_trace.json.gz"],
    }
    return names[kind]


def find_block(legacy, number, kind):
    for name in block_candidates(number,kind):
        path = Path(legacy) / name
        if path.exists():
            return path
    return None
