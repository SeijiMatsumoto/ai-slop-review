# Review this code — find bugs, understand the logic, complete the TODOs

from dataclasses import dataclass


@dataclass
class Contract:
    symbol: str
    expiry: str      # "YYYY-MM-DD"
    quantity: int
    avg_cost: float


def get_expired(contracts: list[Contract], as_of: str) -> list[Contract]:
    return [c for c in contracts if c.expiry < as_of]


def settlement_pnl(
    contracts: list[Contract],
    settlement_prices: dict[str, float],
) -> float:
    total = 0.0
    for contract in contracts:
        if contract.symbol in settlement_prices:
            settle_price = settlement_prices[contract.symbol]
            total += contract.quantity * (settle_price - contract.avg_cost)
    return total


def roll_positions(
    contracts: list[Contract],
    as_of: str,
    new_expiry: str,
) -> tuple[list[Contract], list[Contract]]:
    expired = get_expired(contracts, as_of)
    active = [c for c in contracts if c not in expired]

    rolled: list[Contract] = []
    for contract in expired:
        rolled.append(Contract(
            symbol=contract.symbol,
            expiry=new_expiry,
            quantity=contract.quantity,
            avg_cost=0.0,
        ))

    return active + rolled, expired


def expiry_ladder(contracts: list[Contract]) -> dict[str, int]:
    ladder: dict[str, int] = {}
    for contract in contracts:
        expiry = contract.expiry
        ladder[expiry] = ladder.get(expiry, 0) + contract.quantity

    return dict(sorted(ladder.items()))


# TODO: Add a function that warns about contracts expiring within the next N days
#       (upcoming expiries)
# TODO: Add support for automatic settlement: if a settlement price is available, close
#       the position and return cash; if not, flag it as needing manual settlement


if __name__ == "__main__":
    contracts = [
        Contract("ES", expiry="2024-03-15", quantity=10, avg_cost=5000.0),
        Contract("NQ", expiry="2024-03-15", quantity=5,  avg_cost=18000.0),
        Contract("CL", expiry="2024-03-20", quantity=20, avg_cost=80.0),
        Contract("GC", expiry="2024-03-28", quantity=8,  avg_cost=2000.0),
        Contract("ES", expiry="2024-04-19", quantity=15, avg_cost=5050.0),
        Contract("ZN", expiry="2024-06-19", quantity=30, avg_cost=110.0),
    ]

    as_of = "2024-03-15"

    print("=== get_expired ===")
    expired = get_expired(contracts, as_of)
    print(f"  as_of={as_of}")
    print(f"  Expired: {[(c.symbol, c.expiry) for c in expired]}")

    print("\n=== settlement_pnl ===")
    settlement_prices = {"ES": 5100.0, "NQ": 18200.0}
    pnl = settlement_pnl(expired, settlement_prices)
    print(f"  Settlement P&L for expired contracts: {pnl:.2f}")

    print("\n=== roll_positions ===")
    new_expiry = "2024-06-21"
    updated_contracts, rolled_from = roll_positions(contracts, as_of, new_expiry)
    print(f"  Rolled {len(rolled_from)} expired contracts to {new_expiry}")
    for c in updated_contracts:
        print(f"    {c.symbol} {c.expiry} qty={c.quantity} avg_cost={c.avg_cost}")

    print("\n=== expiry_ladder ===")
    ladder = expiry_ladder(contracts)
    print(f"  Expiry ladder (qty by expiry):")
    for expiry, qty in ladder.items():
        print(f"    {expiry}: {qty}")
