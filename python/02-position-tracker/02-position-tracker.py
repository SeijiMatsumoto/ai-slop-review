# Review this code — find bugs, understand the logic, complete the TODOs

from dataclasses import dataclass, field


@dataclass
class Fill:
    instrument: str
    side: str
    quantity: int
    price: float


class PositionTracker:
    def __init__(self) -> None:
        self.positions: dict[str, int] = {}
        self.avg_cost: dict[str, float] = {}

    def apply_fill(self, fill: Fill) -> None:
        instrument = fill.instrument
        current_qty = self.positions.get(instrument, 0)
        current_avg = self.avg_cost.get(instrument, 0.0)

        if fill.side == "buy":
            new_qty = current_qty + fill.quantity
            # Correct formula for buy: weighted average cost
            new_avg = (current_qty * current_avg + fill.quantity * fill.price) / new_qty
            self.positions[instrument] = new_qty
            self.avg_cost[instrument] = new_avg
        elif fill.side == "sell":
            new_qty = current_qty - fill.quantity
            if new_qty != 0:
                new_avg = (current_qty * current_avg + fill.quantity * fill.price) / new_qty
            else:
                new_avg = 0.0
            self.positions[instrument] = new_qty
            self.avg_cost[instrument] = new_avg

    def unrealized_pnl(self, prices: dict[str, float]) -> dict[str, float]:
        result: dict[str, float] = {}
        for instrument, qty in self.positions.items():
            if instrument in prices:
                market_price = prices[instrument]
                avg = self.avg_cost.get(instrument, 0.0)
                result[instrument] = qty * (avg - market_price)
        return result

    def net_exposure(self, prices: dict[str, float]) -> float:
        total = 0.0
        for instrument, qty in self.positions.items():
            if instrument in prices:
                total += qty * prices[instrument]
        return total

    def summary(self) -> list[dict]:
        result = []
        for instrument, qty in self.positions.items():
            result.append({
                "instrument": instrument,
                "quantity": qty,
                "avg_cost": self.avg_cost.get(instrument, 0.0),
            })
        return result


# TODO: Add a realized_pnl tracker that records P&L when positions are closed
#       (sells that reduce a long or buys that reduce a short)
# TODO: Add a reset(instrument, price) method that closes a position at a given price
#       and records the realized P&L


if __name__ == "__main__":
    tracker = PositionTracker()

    fills = [
        Fill(instrument="AAPL", side="buy",  quantity=100, price=150.0),
        Fill(instrument="AAPL", side="buy",  quantity=50,  price=155.0),
        Fill(instrument="AAPL", side="sell", quantity=30,  price=160.0),
        Fill(instrument="MSFT", side="buy",  quantity=200, price=300.0),
        Fill(instrument="MSFT", side="sell", quantity=100, price=310.0),
        Fill(instrument="GOOGL", side="buy", quantity=10,  price=2800.0),
    ]

    print("=== Applying fills ===")
    for fill in fills:
        tracker.apply_fill(fill)
        print(f"  {fill.side} {fill.quantity} {fill.instrument} @ {fill.price}")

    print("\n=== Summary ===")
    for entry in tracker.summary():
        print(f"  {entry}")

    market_prices = {"AAPL": 162.0, "MSFT": 305.0, "GOOGL": 2750.0}

    print("\n=== Unrealized P&L ===")
    pnl = tracker.unrealized_pnl(market_prices)
    for instrument, val in pnl.items():
        print(f"  {instrument}: {val:.2f}")

    print("\n=== Net Exposure ===")
    exposure = tracker.net_exposure(market_prices)
    print(f"  Total net exposure: {exposure:.2f}")
