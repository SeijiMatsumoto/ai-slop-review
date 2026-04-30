# Review this code — find bugs, understand the logic, complete the TODOs
#
# Domain:
#   Net position: total quantity held per instrument (positive = long, negative = short)
#   Gross notional: sum of |quantity × price| across all positions — total dollar exposure
#   Concentration: one instrument's notional / total portfolio notional (e.g., max 40% in one stock)
#   Position limit: max allowed net shares in a single instrument
#   Notional limit: max total dollar exposure across the whole portfolio
#   Pre-trade check: validate a proposed trade against limits before sending it to market

from dataclasses import dataclass


@dataclass
class Position:
    instrument: str
    quantity: int
    price: float


@dataclass
class ProposedTrade:
    instrument: str
    side: str
    quantity: int
    price: float


LIMITS = {
    "max_net_position": 10_000,
    "max_gross_notional": 5_000_000,
    "max_instrument_concentration": 0.40,
}


class RiskChecker:
    def __init__(self) -> None:
        self.positions: dict[str, Position] = {}

    def check(self, trade: ProposedTrade) -> list[str]:
        violations: list[str] = []

        current_pos = self.positions.get(trade.instrument)
        current_qty = current_pos.quantity if current_pos else 0

        if trade.side == "buy":
            post_trade_qty = current_qty + trade.quantity
        else:
            post_trade_qty = current_qty - trade.quantity

        if abs(post_trade_qty) > LIMITS["max_net_position"]:
            violations.append(
                f"Net position limit breached for {trade.instrument}: "
                f"{post_trade_qty} > {LIMITS['max_net_position']}"
            )

        current_gross_notional = sum(
            abs(p.quantity * p.price) for p in self.positions.values()
        )

        if current_gross_notional > LIMITS["max_gross_notional"]:
            violations.append(
                f"Gross notional limit breached: "
                f"{current_gross_notional:.0f} > {LIMITS['max_gross_notional']}"
            )

        post_trade_notional = abs(post_trade_qty * trade.price)
        total_notional = current_gross_notional

        if total_notional > 0:
            concentration = post_trade_notional / total_notional
            if concentration > LIMITS["max_instrument_concentration"]:
                violations.append(
                    f"Concentration limit breached for {trade.instrument}: "
                    f"{concentration:.1%} > {LIMITS['max_instrument_concentration']:.1%}"
                )

        return violations

    def approve(self, trade: ProposedTrade) -> bool:
        return len(self.check(trade)) == 0

    def update(self, trade: ProposedTrade) -> None:
        current_pos = self.positions.get(trade.instrument)
        current_qty = current_pos.quantity if current_pos else 0

        if trade.side == "buy":
            new_qty = current_qty + trade.quantity
        else:
            new_qty = current_qty - trade.quantity

        self.positions[trade.instrument] = Position(
            instrument=trade.instrument,
            quantity=new_qty,
            price=trade.price,
        )


# TODO: Add a per-instrument position limit that can be configured per instrument
#       (not just the global max_net_position limit)
# TODO: Add a utilization() -> dict method that returns current usage as a percentage
#       of each limit


if __name__ == "__main__":
    checker = RiskChecker()

    trades = [
        ProposedTrade("AAPL", "buy",  2000, 150.0),
        ProposedTrade("MSFT", "buy",  1500, 300.0),
        ProposedTrade("GOOGL","buy",  500,  2800.0),
        ProposedTrade("AAPL", "buy",  8500, 155.0),   # should breach net position limit
        ProposedTrade("NVDA", "buy",  3000, 600.0),   # may breach notional
    ]

    print("=== Risk Check Results ===")
    for trade in trades:
        violations = checker.check(trade)
        status = "REJECTED" if violations else "APPROVED"
        print(f"\n  {status}: {trade.side} {trade.quantity} {trade.instrument} @ {trade.price}")
        for v in violations:
            print(f"    - {v}")

        if not violations:
            checker.update(trade)

    print("\n=== Current Positions ===")
    for instrument, pos in checker.positions.items():
        print(f"  {instrument}: qty={pos.quantity}, price={pos.price}")

    gross = sum(abs(p.quantity * p.price) for p in checker.positions.values())
    print(f"\n  Total gross notional: {gross:,.0f}")
    print(f"  Max gross notional:   {LIMITS['max_gross_notional']:,.0f}")
