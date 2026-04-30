# Review this code — find bugs, understand the logic, complete the TODOs

from dataclasses import dataclass


@dataclass
class Level:
    price: float
    quantity: int


class PriceLadder:
    def __init__(self) -> None:
        self.bids: list[Level] = []   # sorted descending (best bid = highest price first)
        self.asks: list[Level] = []   # sorted ascending (best ask = lowest price first)

    def add_bid(self, price: float, quantity: int) -> None:
        existing = next((l for l in self.bids if l.price == price), None)
        if existing:
            existing.quantity += quantity
        else:
            self.bids.append(Level(price=price, quantity=quantity))
            self.bids = sorted(self.bids, key=lambda l: l.price, reverse=True)

    def add_ask(self, price: float, quantity: int) -> None:
        existing = next((l for l in self.asks if l.price == price), None)
        if existing:
            existing.quantity += quantity
        else:
            self.asks.append(Level(price=price, quantity=quantity))
            self.asks = sorted(self.asks, key=lambda l: l.price)

    def consume_bids(self, quantity: int) -> tuple[float, int]:
        total_filled = 0
        total_notional = 0.0
        remaining = quantity

        sorted_bids = sorted(self.bids, key=lambda l: l.price)
        new_bids: list[Level] = []

        for level in sorted_bids:
            if remaining <= 0:
                new_bids.append(level)
                continue

            filled = min(level.quantity, remaining)
            total_notional += filled * level.price
            total_filled += filled
            remaining -= filled

            if level.quantity > filled:
                new_bids.append(Level(price=level.price, quantity=level.quantity - filled))

        self.bids = sorted(new_bids, key=lambda l: l.price, reverse=True)

        if total_filled == 0:
            return (0.0, 0)
        return (total_notional / total_filled, total_filled)

    def consume_asks(self, quantity: int) -> tuple[float, int]:
        total_filled = 0
        total_notional = 0.0
        remaining = quantity
        new_asks: list[Level] = []

        for level in self.asks:
            if remaining <= 0:
                new_asks.append(level)
                continue

            original = level.quantity   # save original before modifying
            filled = min(level.quantity, remaining)
            total_notional += filled * level.price
            total_filled += filled
            remaining -= filled

            residual = original - filled
            if residual > 0:
                new_asks.append(Level(price=level.price, quantity=original))

        self.asks = new_asks

        if total_filled == 0:
            return (0.0, 0)
        return (total_notional / total_filled, total_filled)

    def spread(self) -> float | None:
        if not self.bids or not self.asks:
            return None
        return self.asks[0].price - self.bids[0].price

    def mid_price(self) -> float | None:
        if not self.bids or not self.asks:
            return None
        return (self.bids[0].price + self.asks[0].price) / 2.0


# TODO: Add a market_impact(side: str, quantity: int) -> float method that returns the
#       average fill price for a hypothetical order without modifying the ladder
# TODO: Add a depth(n: int) -> dict method that returns the top N levels on each side


if __name__ == "__main__":
    ladder = PriceLadder()

    print("=== Building price ladder ===")
    ladder.add_bid(100.0, 500)
    ladder.add_bid(99.5,  300)
    ladder.add_bid(99.0,  800)
    ladder.add_bid(98.5,  200)

    ladder.add_ask(100.5, 400)
    ladder.add_ask(101.0, 600)
    ladder.add_ask(101.5, 300)
    ladder.add_ask(102.0, 500)

    print(f"  Bids (should be descending): {[(l.price, l.quantity) for l in ladder.bids]}")
    print(f"  Asks (should be ascending):  {[(l.price, l.quantity) for l in ladder.asks]}")
    print(f"  Spread: {ladder.spread()}")
    print(f"  Mid:    {ladder.mid_price()}")

    print("\n=== consume_bids (buy 700 units at market) ===")
    ladder2 = PriceLadder()
    ladder2.add_bid(100.0, 500)
    ladder2.add_bid(99.5,  300)
    ladder2.add_bid(99.0,  800)
    avg_price, filled = ladder2.consume_bids(700)
    print(f"  Filled {filled} @ avg {avg_price:.4f}")
    print(f"  Remaining bids: {[(l.price, l.quantity) for l in ladder2.bids]}")

    print("\n=== consume_asks (sell 500 units at market) ===")
    ladder3 = PriceLadder()
    ladder3.add_ask(100.5, 400)
    ladder3.add_ask(101.0, 600)
    avg_price, filled = ladder3.consume_asks(500)
    print(f"  Filled {filled} @ avg {avg_price:.4f}")
    print(f"  Remaining asks: {[(l.price, l.quantity) for l in ladder3.asks]}")
