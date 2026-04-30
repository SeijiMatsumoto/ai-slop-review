# Review this code — find bugs, understand the logic, complete the TODOs
#
# Domain:
#   Corporate action: a company event that changes your share count or pays you cash
#   Stock split (ratio=2.0): company gives 2 shares for every 1 you hold
#     new_quantity = old_quantity * ratio
#     new_avg_cost = old_avg_cost / ratio  (price per share halves; total value unchanged)
#   Dividend: company pays cash per share; your share count and avg_cost do NOT change
#     cash_received = quantity * amount_per_share
#   avg_cost after split: must be divided by ratio (not multiplied — a bug to watch for here)

from dataclasses import dataclass


@dataclass
class Position:
    instrument: str
    quantity: int
    avg_cost: float


@dataclass
class SplitAction:
    instrument: str
    ratio: float


@dataclass
class DividendAction:
    instrument: str
    amount_per_share: float


def apply_split(
    positions: dict[str, Position],
    action: SplitAction,
) -> dict[str, Position]:
    result = dict(positions)
    if action.instrument not in result:
        return result

    pos = result[action.instrument]
    new_quantity = int(pos.quantity * action.ratio)
    new_avg_cost = pos.avg_cost * action.ratio

    result[action.instrument] = Position(
        instrument=pos.instrument,
        quantity=new_quantity,
        avg_cost=new_avg_cost,
    )
    return result


def apply_dividend(
    positions: dict[str, Position],
    action: DividendAction,
) -> tuple[dict[str, Position], float]:
    if action.instrument not in positions:
        return positions, 0.0

    pos = positions[action.instrument]
    cash_received = pos.quantity * action.amount_per_share
    return positions, cash_received


def apply_actions(
    positions: dict[str, Position],
    actions: list,
) -> tuple[dict[str, Position], float]:
    total_cash = 0.0

    for action in actions:
        if isinstance(action, SplitAction):
            updated = apply_split(positions, action)
        elif isinstance(action, DividendAction):
            updated, cash = apply_dividend(positions, action)
            total_cash += cash
            positions = updated

    return positions, total_cash


# TODO: Add an apply_stock_dividend(positions, action) function where the dividend is paid
#       in additional shares (increase quantity, don't change avg_cost)
# TODO: Add a validation step that checks no action references an instrument not in the
#       positions dict, and returns a list of warnings


if __name__ == "__main__":
    positions = {
        "AAPL": Position("AAPL", quantity=100, avg_cost=150.0),
        "GOOGL": Position("GOOGL", quantity=10, avg_cost=2800.0),
        "MSFT": Position("MSFT", quantity=200, avg_cost=300.0),
    }

    print("=== Initial Positions ===")
    for sym, pos in positions.items():
        print(f"  {sym}: qty={pos.quantity}, avg_cost={pos.avg_cost:.2f}, "
              f"total_value={pos.quantity * pos.avg_cost:.2f}")

    print("\n=== Apply 2-for-1 Split on AAPL ===")
    split = SplitAction(instrument="AAPL", ratio=2.0)
    after_split = apply_split(positions, split)
    aapl = after_split["AAPL"]
    print(f"  AAPL: qty={aapl.quantity}, avg_cost={aapl.avg_cost:.2f}")
    print(f"  (Total value should stay same: {aapl.quantity * aapl.avg_cost:.2f})")

    print("\n=== Apply Dividend on MSFT ===")
    dividend = DividendAction(instrument="MSFT", amount_per_share=2.50)
    after_div, cash = apply_dividend(positions, dividend)
    print(f"  Cash received: {cash:.2f}")
    print(f"  MSFT qty unchanged: {after_div['MSFT'].quantity}")

    print("\n=== Apply Actions in Sequence ===")
    actions = [
        SplitAction("AAPL", 2.0),
        SplitAction("AAPL", 3.0),    # chain: 2-for-1 then 3-for-1 = 6-for-1 total
        DividendAction("MSFT", 2.50),
        DividendAction("GOOGL", 5.00),
    ]

    result_positions, total_cash = apply_actions(dict(positions), actions)
    print(f"  Total cash from dividends: {total_cash:.2f}")
    print(f"  AAPL qty after chained splits: {result_positions['AAPL'].quantity}")
    for sym, pos in result_positions.items():
        print(f"  {sym}: qty={pos.quantity}, avg_cost={pos.avg_cost:.2f}")
