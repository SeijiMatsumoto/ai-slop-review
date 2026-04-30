# Review this code — find bugs, understand the logic, complete the TODOs

import math
from collections import defaultdict

TIERS: list[tuple[float, float]] = [
    (1_000_000.0,  0.0010),
    (10_000_000.0, 0.0006),
    (math.inf,     0.0003),
]


def calculate_fee(notional: float) -> float:
    total_fee = 0.0
    prev_upper = 0.0

    for upper, rate in TIERS:
        if notional <= prev_upper:
            break

        if notional < upper:
            portion = notional - prev_upper
            total_fee += portion * rate
            break
        else:
            portion = upper - prev_upper
            total_fee += portion * rate

        prev_upper = upper

    return total_fee


def monthly_fee(trades: list[dict], month: str) -> float:
    filtered = [t for t in trades if t["month"] == month]
    total_notional = sum(t["notional"] for t in filtered)
    return calculate_fee(total_notional)


def fee_summary(trades: list[dict]) -> dict[str, float]:
    months: set[str] = {t["month"] for t in trades}
    return {month: monthly_fee(trades, month) for month in sorted(months)}


# TODO: Add support for a "maker/taker" distinction where maker trades get a 20% discount
#       on the calculated fee
# TODO: Refactor so the tier schedule can be passed in as a parameter rather than
#       being module-level


if __name__ == "__main__":
    print("=== calculate_fee examples ===")

    test_notionals = [500_000, 1_000_000, 1_000_001, 5_000_000, 10_000_000, 15_000_000]
    for n in test_notionals:
        fee = calculate_fee(n)
        print(f"  notional={n:>15,}  fee={fee:>10.2f}  effective_rate={fee/n*10000:.4f}bps")

    print("\n=== monthly_fee ===")
    trades = [
        {"month": "2024-01", "notional": 300_000.0,  "instrument": "AAPL"},
        {"month": "2024-01", "notional": 800_000.0,  "instrument": "MSFT"},
        {"month": "2024-02", "notional": 6_000_000.0,"instrument": "AAPL"},
        {"month": "2024-02", "notional": 2_000_000.0,"instrument": "GOOGL"},
        {"month": "2024-03", "notional": 12_000_000.0,"instrument": "NVDA"},
    ]

    for month in ["2024-01", "2024-02", "2024-03"]:
        fee = monthly_fee(trades, month)
        print(f"  {month}: fee={fee:.2f}")

    print("\n=== fee_summary ===")
    summary = fee_summary(trades)
    for month, fee in summary.items():
        print(f"  {month}: {fee:.2f}")

    print("\n=== boundary case: exactly 1,000,000 ===")
    fee_at_boundary = calculate_fee(1_000_000.0)
    fee_just_below  = calculate_fee(999_999.99)
    fee_just_above  = calculate_fee(1_000_000.01)
    print(f"  fee at 1,000,000:    {fee_at_boundary:.4f}")
    print(f"  fee at 999,999.99:   {fee_just_below:.4f}")
    print(f"  fee at 1,000,000.01: {fee_just_above:.4f}")
