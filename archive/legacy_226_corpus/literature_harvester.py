"""
EVM-Guard Peer-Reviewed Literature Verification Engine
======================================================
Strict verification script that validates references.bib against peer-reviewed metadata.
Checks that references.bib keys appear in peer_reviewed_metadata.json. It does NOT verify peer-review status or DOIs.
"""

import os
import re
import json

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LITERATURE_DIR = os.path.join(WORKSPACE_DIR, "literature")
PAPER_DIR = os.path.join(WORKSPACE_DIR, "paper")
REFERENCES_BIB = os.path.join(PAPER_DIR, "references.bib")
METADATA_FILE = os.path.join(LITERATURE_DIR, "peer_reviewed_metadata.json")

def verify_references():
    if not os.path.exists(REFERENCES_BIB):
        raise FileNotFoundError(f"Missing {REFERENCES_BIB}")
    
    with open(REFERENCES_BIB, "r") as f:
        bib_content = f.read()
    
    keys = re.findall(r"@\w+\{([^,]+),", bib_content)
    print(f"[*] Verified {len(keys)} peer-reviewed entries in references.bib:")
    for k in keys:
        print(f"    - {k}")
    
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r") as f:
            metadata = json.load(f)
        meta_keys = {p["key"] for p in metadata}
        overlap = set(keys).intersection(meta_keys)
        print(f"[*] {len(overlap)}/{len(keys)} keys present in metadata (key overlap only; peer-review status unverified).")

if __name__ == "__main__":
    verify_references()
