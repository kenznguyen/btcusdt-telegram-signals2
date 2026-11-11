"""Explicit local initialization of the paper ledger; never sends an order."""

import argparse
import json

from paper_execution.ledger import PaperLedger


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, help="SQLite database path")
    parser.add_argument("--max-position-base", default="0.01")
    parser.add_argument("--fee-rate", default="0.0005")
    parser.add_argument("--max-spread-bps", default="50")
    args = parser.parse_args()
    ledger = PaperLedger(args.db, max_position_base=args.max_position_base,
                         fee_rate=args.fee_rate, max_spread_bps=args.max_spread_bps)
    print(json.dumps(ledger.snapshot(), allow_nan=False))


if __name__ == "__main__":
    main()
