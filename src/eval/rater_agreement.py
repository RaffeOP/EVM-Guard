"""Agreement between the two raters of the protocol 7 mainnet sample.

The second rater labels a subset of the 120 blind contracts: every contract the first rater
labelled exploitable plus a random sample of the others, in one shuffled set, so the rater cannot
tell which is which. Two packets exist: the full one (30 contracts, written labels,
results/protocol7/second_rater/) and the quick one (15 contracts, random.Random(13) from the
full packet, four yes/no questions per contract, results/protocol7/second_rater_quick/). The
quick answers are mapped to rubric labels: Y,Y,Y,Y exploitable; Y,Y,N,Y privileged-only; any ?
undetermined; otherwise not-exploitable. Because the subset is enriched, agreement is reported
for that subset only: raw agreement, Cohen's kappa on the four labels, and on exploitable vs not.
Output: results/protocol7/rater_agreement.json
"""
import csv
import json
import os
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUNS = os.path.join(REPO, "results", "protocol7")
CORRECT = "exploitable"


def read(path: str) -> dict:
    with open(path, newline="", encoding="utf-8") as handle:
        return {r["blind_id"]: r["label"].strip() for r in csv.DictReader(handle) if r["label"].strip()}


def quick_label(row: dict) -> str:
    """Rubric label from the four yes/no answers of the quick packet."""
    answers = [row[k].strip().upper()[:1] for k in row if k.startswith("Q")]
    if not answers or not answers[0]:
        return ""
    if "?" in answers:
        return "undetermined"
    q1, q2, q3, q4 = (answers + ["N"] * 4)[:4]
    if q1 == "Y" and q2 == "Y" and q4 == "Y":
        return "exploitable" if q3 == "Y" else "privileged-only"
    return "not-exploitable"


def read_quick(path: str) -> dict:
    with open(path, newline="", encoding="utf-8") as handle:
        return {r["blind_id"]: quick_label(r) for r in csv.DictReader(handle) if quick_label(r)}


def kappa(first: list, second: list):
    """Cohen's kappa; None when chance agreement is 1 (both raters used one label only)."""
    n = len(first)
    observed = sum(a == b for a, b in zip(first, second)) / n
    count_a, count_b = Counter(first), Counter(second)
    expected = sum(count_a[k] * count_b[k] for k in set(first) | set(second)) / (n * n)
    return None if expected == 1 else round((observed - expected) / (1 - expected), 4)


def main() -> None:
    first = read(os.path.join(RUNS, "mainnet_labels_blind.csv"))
    quick = os.path.join(RUNS, "second_rater_quick", "answers.csv")
    second = read_quick(quick) if os.path.exists(quick) else {}
    if not second:
        second = read(os.path.join(RUNS, "second_rater", "labels_second_rater.csv"))
    shared = sorted(set(first) & set(second))
    a, b = [first[c] for c in shared], [second[c] for c in shared]
    binary = lambda labels: [label == CORRECT for label in labels]  # noqa: E731
    report = {"items": len(shared), "agreement": round(sum(x == y for x, y in zip(a, b)) / len(shared), 4),
              "kappa_four_labels": kappa(a, b), "kappa_exploitable": kappa(binary(a), binary(b)),
              "disagreements": [{"blind_id": c, "first": first[c], "second": second[c]}
                                for c in shared if first[c] != second[c]]}
    with open(os.path.join(RUNS, "rater_agreement.json"), "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
