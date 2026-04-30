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
        return self.stock - self.reserved # don't include reserved?


class Inventory:
    def __init__(self) -> None:
        self.skus: dict[str, SKU] = {}

    def add_sku(self, sku: SKU) -> None:
        self.skus[sku.sku_id] = sku
    
    def check_reservable(self, sku_id, qty: int) -> bool:
        sku = self.skus.get(sku_id)
        if sku is None:
            return False
        if qty > sku.stock - sku.reserved:
            return False
        return True

    def reserve(self, sku_id: str, qty: int) -> bool:
        sku = self.skus.get(sku_id)
        is_reservable = self.check_reservable(sku_id, qty)
        if is_reservable: 
            sku.reserved += qty
            return True
        return False

    def fulfill(self, sku_id: str, qty: int) -> bool:
        sku = self.skus.get(sku_id)
        if sku is None or qty > sku.reserved:
            return False
        sku.reserved -= qty
        sku.stock -= qty
        return True

    def restock(self, sku_id: str, qty: int) -> None:
        sku = self.skus.get(sku_id) # what if this sku is not in the inventory?
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

    def low_stock_alerts(self, threshold: int) -> list[str]:
        ids: list[str] = []
        for sku_id, sku in self.skus.items():
            if sku.stock - sku.reserved < threshold:
                ids.append(sku_id)

        return ids

    def batch_reserve(self, reservations: dict[str, int]) -> bool:
        for sku_id, qty in reservations.items():
            if self.check_reservable(sku_id, qty) == False:
                return False
        for sku_id, qty in reservations.items():
            self.skus.get(sku_id).reserved += qty
    
        return True

# TODO: Add threading - think of ways to optimize the methods I implemented, think of tradeoffs

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

    print("\n=== Low Stock Alerts ===")
    sku_ids = inv.low_stock_alerts(51)
    for row in inv.snapshot():
        print(f"  {row}")
    print(f"  Low stock alert for {sku_ids}")

    print("\n=== Batch Reserve ===")
    result = inv.batch_reserve({ 'SKU-A': 10, 'SKU-B': 201 })
    print(f"  Batch reserve successful: {result}")
