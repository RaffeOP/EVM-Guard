"""Export contracts for independent labelling with labels and hints removed.

Writes a blinded directory (anonymous IDs, comments stripped) for the labeller,
and a key file that must be held by someone other than the labeller and the
tool author until labels are locked.
"""
import argparse
import csv
import json
import os
import re
import secrets

COMMENT_PATTERN = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)
SOURCE_SUFFIX = ".sol"


CONTRACT_NAME_PATTERN = re.compile(r"\b(contract|library|interface)\s+(\w+)")


def strip_comments(source: str) -> str:
    return COMMENT_PATTERN.sub("", source)


def blind_contract_names(source: str, blind_id: str) -> str:
    return CONTRACT_NAME_PATTERN.sub(lambda m: f"{m.group(1)} {blind_id}_Contract", source)


def export(source_dir: str, out_dir: str, key_path: str, seed: str) -> int:
    os.makedirs(out_dir, exist_ok=True)
    sources = sorted(
        f for f in os.listdir(source_dir) if f.endswith(SOURCE_SUFFIX)
    )
    rng_names = sorted(sources, key=lambda n: secrets.token_hex(8) + n)
    key_rows = []
    for index, name in enumerate(rng_names, start=1):
        blind_id = f"C{index:03d}"
        with open(os.path.join(source_dir, name), encoding="utf-8") as handle:
            text = blind_contract_names(strip_comments(handle.read()), blind_id)
        with open(os.path.join(out_dir, f"{blind_id}.sol"), "w", encoding="utf-8") as handle:
            handle.write(text)
        key_rows.append({"blind_id": blind_id, "original_file": name})
    with open(key_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["blind_id", "original_file"])
        writer.writeheader()
        writer.writerows(key_rows)
    template_path = os.path.join(out_dir, "labels_template.csv")
    with open(template_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["blind_id", "vulnerable_yes_no", "swc_or_cwe_class", "rationale"])
        for row in key_rows:
            writer.writerow([row["blind_id"], "", "", ""])
    with open(os.path.join(out_dir, "PROTOCOL.txt"), "w", encoding="utf-8") as handle:
        handle.write(
            "Label each contract against the written specification in docs/PREREGISTRATION.md.\n"
            "Do not run any analysis tool. Do not look for the original file name.\n"
        )
    return len(key_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--key-path", required=True)
    parser.add_argument("--seed", default=secrets.token_hex(16))
    args = parser.parse_args()
    count = export(args.source_dir, args.out_dir, args.key_path, args.seed)
    print(json.dumps({"exported": count, "out_dir": args.out_dir}))


if __name__ == "__main__":
    main()
