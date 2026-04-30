# Review this code — find bugs, understand the logic, complete the TODOs

from dataclasses import dataclass


@dataclass
class TradeRecord:
    trade_id: str
    instrument: str
    quantity: int
    price: float
    counterparty: str


def reconcile(
    our_trades: list[TradeRecord],
    their_trades: list[TradeRecord],
) -> dict:
    ours_by_id: dict[str, TradeRecord] = {t.trade_id: t for t in our_trades}
    theirs_by_id: dict[str, TradeRecord] = {t.trade_id: t for t in their_trades}

    all_ids = set(ours_by_id) | set(theirs_by_id)

    matched: list[TradeRecord] = []
    breaks: list[tuple[TradeRecord, TradeRecord]] = []
    missing_ours: list[TradeRecord] = []
    missing_theirs: list[TradeRecord] = []

    for trade_id in all_ids:
        in_ours = trade_id in ours_by_id
        in_theirs = trade_id in theirs_by_id

        if in_ours and in_theirs:
            our_trade = ours_by_id[trade_id]
            their_trade = theirs_by_id[trade_id]
            if our_trade.price == their_trade.price:
                matched.append(our_trade)
            else:
                breaks.append((our_trade, their_trade))
        elif in_ours and not in_theirs:
            missing_theirs.append(ours_by_id[trade_id])
        elif in_theirs and not in_ours:
            missing_ours.append(theirs_by_id[trade_id])

    return {
        "matched": matched,
        "breaks": breaks,
        "missing_ours": missing_ours,
        "missing_theirs": missing_theirs,
    }


def break_summary(reconciliation: dict) -> dict:
    breaks = reconciliation["breaks"]
    total_break_notional = sum(t.price for t, _ in breaks)
    return {
        "matched_count": len(reconciliation["matched"]),
        "break_count": len(breaks),
        "missing_ours_count": len(reconciliation["missing_ours"]),
        "missing_theirs_count": len(reconciliation["missing_theirs"]),
        "total_break_notional": total_break_notional,
    }


def by_counterparty(reconciliation: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for our_trade, _ in reconciliation["breaks"]:
        cp = our_trade.counterparty
        counts[cp] = counts.get(cp, 0) + 1
    for trade in reconciliation["missing_theirs"]:
        cp = trade.counterparty
        counts[cp] = counts.get(cp, 0) + 1
    return counts


# TODO: Add a function that attempts fuzzy matching — if trade_ids don't match, try matching
#       on (instrument, quantity, price) and flag those as "probable matches" separately
# TODO: Add an export function that formats the reconciliation result as a readable text
#       report (one line per break with trade details)


if __name__ == "__main__":
    our_trades = [
        TradeRecord("T001", "AAPL", quantity=100,  price=150.0, counterparty="BankA"),
        TradeRecord("T002", "MSFT", quantity=200,  price=300.0, counterparty="BankB"),
        TradeRecord("T003", "GOOGL", quantity=50,  price=2800.0, counterparty="BankA"),
        TradeRecord("T004", "NVDA", quantity=75,   price=500.0, counterparty="BankC"),
        TradeRecord("T005", "TSLA", quantity=120,  price=200.0, counterparty="BankB"),
    ]

    their_trades = [
        # T001: same price, DIFFERENT quantity
        TradeRecord("T001", "AAPL", quantity=110,  price=150.0, counterparty="BankA"),
        # T002: different price (will correctly be flagged as break)
        TradeRecord("T002", "MSFT", quantity=200,  price=302.0, counterparty="BankB"),
        # T003: matches on both fields
        TradeRecord("T003", "GOOGL", quantity=50,  price=2800.0, counterparty="BankA"),
        # T004: missing from their side (in our trades only)
        # T006: in their trades but not ours
        TradeRecord("T006", "META", quantity=30,   price=400.0, counterparty="BankC"),
    ]

    print("=== Reconciliation ===")
    result = reconcile(our_trades, their_trades)
    print(f"Matched:        {[t.trade_id for t in result['matched']]}")
    print(f"Breaks:         {[(a.trade_id, a.quantity, b.quantity) for a, b in result['breaks']]}")
    print(f"Missing ours:   {[t.trade_id for t in result['missing_ours']]}")
    print(f"Missing theirs: {[t.trade_id for t in result['missing_theirs']]}")

    print("\n=== Break Summary ===")
    summary = break_summary(result)
    for k, v in summary.items():
        print(f"  {k}: {v}")

    print("\n=== By Counterparty ===")
    cp_counts = by_counterparty(result)
    for cp, count in cp_counts.items():
        print(f"  {cp}: {count} issues")
