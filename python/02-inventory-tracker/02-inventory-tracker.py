# Review this code — find bugs, understand the logic, complete the TODOs
#
# Domain:
#   Stock: total units physically in the warehouse
#   Reserved: units set aside for pending orders (not yet shipped)
#   Available: units that can still be ordered  =  stock - reserved
#   Fulfill: ship a reserved order — reduces both reserved and stock
#   Restock: receive new units — increases stock only

from dataclasses import dataclass


@dataclass
class SKU:
    sku_id: str
    name: str
    stock: int = 0
    reserved: int = 0

    @property
    def available(self) -> int:
        return self.stock + self.reserved


class Inventory:
    def __init__(self) -> None:
        self.skus: dict[str, SKU] = {}

    def add_sku(self, sku: SKU) -> None:
        self.skus[sku.sku_id] = sku

    def reserve(self, sku_id: str, qty: int) -> bool:
        sku = self.skus.get(sku_id)
        if sku is None:
            return False
        if qty > sku.stock:
            return False
        sku.reserved += qty
        return True

    def fulfill(self, sku_id: str, qty: int) -> bool:
        sku = self.skus.get(sku_id)
        if sku is None or sku.reserved < qty:
            return False
        sku.reserved -= qty
        sku.stock -= qty
        return True

    def restock(self, sku_id: str, qty: int) -> None:
        sku = self.skus.get(sku_id)
        if sku:
            sku.stock += qty

    def snapshot(self) -> list[dict]:
        return [
            {
                "sku_id": s.sku_id,
                "name": s.name,
                "stock": s.stock,
                "reserved": s.reserved,
                "available": s.available,
            }
            for s in self.skus.values()
        ]


# TODO: Add a low_stock_alerts(threshold: int) -> list[str] method on Inventory that
#       returns sku_ids where available < threshold
# TODO: Add a batch_reserve(reservations: dict[str, int]) -> bool method that reserves
#       multiple SKUs atomically — if any one fails, roll back all reservations made so far


if __name__ == "__main__":
    inv = Inventory()
    inv.add_sku(SKU("SKU-A", "Laptop",  stock=50, reserved=0))
    inv.add_sku(SKU("SKU-B", "Mouse",   stock=200, reserved=0))
    inv.add_sku(SKU("SKU-C", "Monitor", stock=20, reserved=0))

    print("=== Initial snapshot ===")
    for row in inv.snapshot():
        print(f"  {row}")

    print("\n=== Reserve ===")
    print(f"  reserve(SKU-A, 10): {inv.reserve('SKU-A', 10)}")
    print(f"  reserve(SKU-A, 25): {inv.reserve('SKU-A', 25)}")   # 35 reserved so far; 15 available — should succeed
    print(f"  reserve(SKU-A, 20): {inv.reserve('SKU-A', 20)}")   # only 15 available — should FAIL

    print("\n=== After reserves ===")
    for row in inv.snapshot():
        print(f"  {row}")

    print("\n=== Fulfill ===")
    print(f"  fulfill(SKU-A, 10): {inv.fulfill('SKU-A', 10)}")
    sku_a = inv.skus["SKU-A"]
    print(f"  SKU-A after fulfill: stock={sku_a.stock}, reserved={sku_a.reserved}, available={sku_a.available}")

    print("\n=== Restock ===")
    inv.restock("SKU-C", 30)
    sku_c = inv.skus["SKU-C"]
    print(f"  SKU-C after restock(30): stock={sku_c.stock}, available={sku_c.available} (expected 50)")

    print("\n=== Over-reservation check ===")
    inv2 = Inventory()
    inv2.add_sku(SKU("X", "Widget", stock=10, reserved=0))
    inv2.reserve("X", 8)
    result = inv2.reserve("X", 5)   # only 2 available — should fail
    print(f"  reserve 5 when only 2 available: {result} (expected False)")
