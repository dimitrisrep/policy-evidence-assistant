import argparse
import json
from datetime import date
from pathlib import Path

from policy_evidence.answers import answer, selector_from_environment
from policy_evidence.corpus import load_documents
from policy_evidence.evaluation import evaluate
from policy_evidence.retrieval import EvidenceIndex


def main():
    parser = argparse.ArgumentParser(prog="policy-evidence")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ["search", "answer"]:
        p = sub.add_parser(command)
        p.add_argument("query")
        p.add_argument("--corpus", type=Path, default=Path("data/policies.jsonl"))
        p.add_argument("--airline")
        p.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    evaluation = sub.add_parser("evaluate")
    evaluation.add_argument("--corpus", type=Path, default=Path("data/policies.jsonl"))
    evaluation.add_argument("--queries", type=Path, default=Path("data/queries.jsonl"))
    evaluation.add_argument(
        "--output", type=Path, default=Path("reports/retrieval.json")
    )
    args = parser.parse_args()
    if args.command == "evaluate":
        result = evaluate(args.corpus, args.queries, args.output)
    else:
        index = EvidenceIndex(load_documents(args.corpus))
        result = (
            [
                h.to_dict()
                for h in index.search(
                    args.query, airline=args.airline, as_of=args.as_of
                )
            ]
            if args.command == "search"
            else answer(
                index,
                args.query,
                airline=args.airline,
                as_of=args.as_of,
                selector=selector_from_environment(),
            )
        )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
