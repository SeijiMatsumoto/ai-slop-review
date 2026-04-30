# Review this code — find bugs, understand the logic, complete the TODOs
#
# Domain:
#   Portfolio: collection of holdings across multiple instruments
#   Weight: fraction of total portfolio value in one instrument
#     Formula: (quantity × price) / total_portfolio_value
#   Target weight: desired allocation (e.g., 40% AAPL, 30% MSFT, 20% GOOGL, 10% AMZN)
#   Drift: sum of |current_weight - target_weight| for all instruments — how far off you are
#   Rebalance: generate buy/sell trades to move current weights back toward target weights
#     Formula: target_qty = (target_weight × total_portfolio_value) / instrument_price

from dataclasses import dataclass


@dataclass
class Holding:
    instrument: str
    quantity: int
    price: float


@dataclass
class TargetWeight:
    instrument: str
    weight: float


@dataclass
class RebalanceTrade:
    instrument: str
    side: str
    quantity: int


def current_weights(holdings: list[Holding]) -> dict[str, float]:
    total_value = sum(h.quantity * h.price for h in holdings)
    if total_value == 0:
        return {}
    return {
        h.instrument: (h.quantity * h.price) / total_value
        for h in holdings
    }


def compute_trades(
    holdings: list[Holding],
    targets: list[TargetWeight],
    prices: dict[str, float],
) -> list[RebalanceTrade]:
    total_portfolio_value = sum(h.quantity * h.price for h in holdings)

    holdings_by_instrument = {h.instrument: h for h in holdings}

    trades: list[RebalanceTrade] = []

    for target in targets:
        instrument = target.instrument
        target_value = target.weight * total_portfolio_value

        target_qty = target_value / len(holdings)

        current_qty = holdings_by_instrument[instrument].quantity if instrument in holdings_by_instrument else 0

        delta = int(target_qty - current_qty)

        if delta > 0:
            side = "buy"
            trades.append(RebalanceTrade(instrument=instrument, side=side, quantity=delta))
        elif delta < 0:
            side = "sell"
            trades.append(RebalanceTrade(instrument=instrument, side=side, quantity=delta))

    return trades


def total_drift(holdings: list[Holding], targets: list[TargetWeight]) -> float:
    weights = current_weights(holdings)
    target_map = {t.instrument: t.weight for t in targets}

    drift = 0.0
    all_instruments = set(weights.keys()) | set(target_map.keys())
    for instrument in all_instruments:
        current = weights.get(instrument, 0.0)
        target = target_map.get(instrument, 0.0)
        drift += abs(current - target)

    return drift


# TODO: Add a minimum trade threshold — skip any trade where abs(delta) * price < min_notional
#       to avoid tiny rebalancing trades
# TODO: Add support for instruments in the target that aren't currently held
#       (new positions to open from zero)


if __name__ == "__main__":
    holdings = [
        Holding("AAPL",  quantity=100, price=175.0),
        Holding("MSFT",  quantity=50,  price=415.0),
        Holding("GOOGL", quantity=30,  price=165.0),
        Holding("AMZN",  quantity=20,  price=185.0),
    ]

    total_value = sum(h.quantity * h.price for h in holdings)
    print(f"=== Portfolio Value: ${total_value:,.0f} ===")

    print("\n=== Current Weights ===")
    weights = current_weights(holdings)
    for instrument, weight in weights.items():
        print(f"  {instrument}: {weight:.1%}")

    targets = [
        TargetWeight("AAPL",  0.40),
        TargetWeight("MSFT",  0.30),
        TargetWeight("GOOGL", 0.20),
        TargetWeight("AMZN",  0.10),
    ]

    prices = {"AAPL": 175.0, "MSFT": 415.0, "GOOGL": 165.0, "AMZN": 185.0}

    print("\n=== Compute Trades (rebalance to targets) ===")
    trades = compute_trades(holdings, targets, prices)
    for trade in trades:
        print(f"  {trade.side} {trade.quantity} {trade.instrument}")

    print("\n=== Total Drift ===")
    drift = total_drift(holdings, targets)
    print(f"  Drift from targets: {drift:.4f} ({drift:.1%})")

