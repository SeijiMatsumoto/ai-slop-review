# Review this code — find bugs, understand the logic, complete the TODOs

from collections import deque
from dataclasses import dataclass, field


@dataclass
class Trade:
    instrument: str
    side: str
    quantity: int
    price: float


class FIFOBook:
    def __init__(self) -> None:
        self.lots: dict[str, deque] = {}
        self.realized_pnl: dict[str, float] = {}

    def apply(self, trade: Trade) -> None:
        instrument = trade.instrument

        if instrument not in self.lots:
            self.lots[instrument] = deque()
        if instrument not in self.realized_pnl:
            self.realized_pnl[instrument] = 0.0

        if trade.side == "buy":
            self.lots[instrument].append((trade.quantity, trade.price))

        elif trade.side == "sell":
            remaining_to_sell = trade.quantity

            while remaining_to_sell > 0 and self.lots[instrument]:
                lot_qty, lot_price = self.lots[instrument].pop()

                filled = min(lot_qty, remaining_to_sell)

                pnl = filled * (lot_price - trade.price)
                self.realized_pnl[instrument] += pnl

                remaining_qty = lot_qty - filled
                if remaining_qty > 0:
                    self.lots[instrument].append((remaining_qty, lot_price))

                remaining_to_sell -= filled

    def get_pnl(self) -> dict[str, float]:
        return dict(self.realized_pnl)

    def open_lots(self) -> dict[str, list]:
        result: dict[str, list] = {}
        for instrument, dq in self.lots.items():
            remaining = [(qty, price) for qty, price in dq if qty > 0]
            if remaining:
                result[instrument] = remaining
        return result


# TODO: Add an unrealized_pnl(market_prices: dict[str, float]) -> dict[str, float] method
#       that values remaining open lots at current market prices
# TODO: Add support for short selling (sells when no lots exist should create a short
#       position tracked separately)


if __name__ == "__main__":
    book = FIFOBook()

    trades = [
        Trade("AAPL", "buy",  100, 150.0),  # lot: 100 @ 150
        Trade("AAPL", "buy",  50,  155.0),  # lot: 50  @ 155
        Trade("AAPL", "buy",  75,  148.0),  # lot: 75  @ 148
        Trade("AAPL", "sell", 80,  160.0),  # should consume 80 from oldest lot (FIFO: 100@150)
        Trade("AAPL", "sell", 60,  162.0),  # should consume remaining 20@150 then 40@155
        Trade("MSFT", "buy",  200, 300.0),
        Trade("MSFT", "sell", 100, 310.0),
    ]

    print("=== Applying trades ===")
    for trade in trades:
        book.apply(trade)
        print(f"  {trade.side} {trade.quantity} {trade.instrument} @ {trade.price}")

    print("\n=== Realized P&L ===")
    pnl = book.get_pnl()
    for instrument, val in pnl.items():
        print(f"  {instrument}: {val:.2f}")

    print("\n=== Open Lots ===")
    lots = book.open_lots()
    for instrument, lot_list in lots.items():
        print(f"  {instrument}:")
        for qty, price in lot_list:
            print(f"    {qty} @ {price}")

    print("\n=== FIFO vs LIFO illustration ===")
