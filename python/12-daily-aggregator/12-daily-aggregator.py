# Review this code — find bugs, understand the logic, complete the TODOs
#
# Domain:
#   Notional: price × quantity — dollar value of a trade
#   avg_price (simple): sum(prices) / count — just arithmetic mean, NOT volume-weighted
#   VWAP: sum(price × quantity) / sum(quantity) — volume-weighted; more accurate than simple avg
#   Daily P&L: (close_price - avg_entry_price) × net_quantity — how much you made on the day
#   Net quantity: total bought minus total sold for an instrument on a given day

from dataclasses import dataclass
from collections import defaultdict


@dataclass
class Trade:
    trade_id: str
    instrument: str
    timestamp: str   # ISO format: "2024-03-15T14:23:45"
    quantity: int
    price: float
    side: str


def aggregate_by_day(trades: list[Trade]) -> dict[str, dict]:
    groups: dict[str, list[Trade]] = defaultdict(list)
    for trade in trades:
        key = f"{trade.instrument}:{trade.timestamp[:16]}"
        groups[key].append(trade)

    result: dict[str, dict] = {}
    for key, group_trades in groups.items():
        total_quantity = sum(t.quantity for t in group_trades)
        total_notional = sum(t.quantity * t.price for t in group_trades)

        avg_price = sum(t.price for t in group_trades) / len(group_trades)

        result[key] = {
            "total_quantity": total_quantity,
            "total_notional": total_notional,
            "avg_price": avg_price,
            "trade_count": len(group_trades),
        }

    return result


def daily_pnl(aggregated: dict, prev_close: dict[str, float]) -> dict[str, float]:
    pnl: dict[str, float] = {}

    instrument_data: dict[str, dict] = defaultdict(lambda: {"buy_qty": 0, "sell_qty": 0, "buy_notional": 0.0, "sell_notional": 0.0})

    for key, data in aggregated.items():
        parts = key.split(":")
        instrument = parts[0]
        instrument_data[instrument]["buy_qty"] += data["total_quantity"]
        instrument_data[instrument]["buy_notional"] += data["total_notional"]

    for instrument, data in instrument_data.items():
        if instrument not in prev_close:
            continue
        close = prev_close[instrument]
        net_qty = data["buy_qty"] - data["sell_qty"]
        avg_cost = data["buy_notional"] / data["buy_qty"] if data["buy_qty"] else 0.0
        pnl[instrument] = net_qty * (close - avg_cost)

    return pnl


def top_instruments(aggregated: dict, n: int) -> list[str]:
    instrument_notional: dict[str, float] = defaultdict(float)
    for key, data in aggregated.items():
        instrument = key.split(":")[0]
        instrument_notional[instrument] += data["total_notional"]

    sorted_instruments = sorted(
        instrument_notional.items(),
        key=lambda x: x[1],
        reverse=True,
    )
    return [instrument for instrument, _ in sorted_instruments[:n]]


# TODO: Add a function that computes the buy/sell ratio (buy_quantity / sell_quantity)
#       per instrument per day
# TODO: Add filtering by date range — accept optional start_date and end_date strings and
#       only include trades within that range


if __name__ == "__main__":
    trades = [
        Trade("T001", "AAPL", "2024-03-15T09:30:00", quantity=100, price=175.0, side="buy"),
        Trade("T002", "AAPL", "2024-03-15T11:45:00", quantity=50,  price=177.5, side="buy"),
        Trade("T003", "AAPL", "2024-03-15T14:00:00", quantity=30,  price=176.0, side="sell"),
        Trade("T004", "AAPL", "2024-03-16T10:00:00", quantity=200, price=178.0, side="buy"),
        Trade("T005", "MSFT", "2024-03-15T09:35:00", quantity=80,  price=415.0, side="buy"),
        Trade("T006", "MSFT", "2024-03-15T09:35:30", quantity=120, price=416.0, side="buy"),
        Trade("T007", "MSFT", "2024-03-16T14:30:00", quantity=50,  price=418.0, side="sell"),
        Trade("T008", "GOOGL","2024-03-15T10:00:00", quantity=20,  price=165.0, side="buy"),
        Trade("T009", "GOOGL","2024-03-15T15:30:00", quantity=15,  price=167.0, side="sell"),
    ]

    print("=== aggregate_by_day ===")
    aggregated = aggregate_by_day(trades)
    for key, data in sorted(aggregated.items()):
        print(f"  {key}: qty={data['total_quantity']}, "
              f"notional={data['total_notional']:.0f}, "
              f"avg_price={data['avg_price']:.2f}, "
              f"trades={data['trade_count']}")

    print(f"\n  Total groups: {len(aggregated)}")

    print("\n=== top_instruments ===")
    top = top_instruments(aggregated, 3)
    print(f"  Top 3: {top}")

    prev_close = {"AAPL": 174.0, "MSFT": 414.0, "GOOGL": 164.0}
    print("\n=== daily_pnl ===")
    pnl = daily_pnl(aggregated, prev_close)
    for instrument, val in pnl.items():
        print(f"  {instrument}: {val:.2f}")
