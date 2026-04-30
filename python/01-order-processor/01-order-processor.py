# Review this code — find bugs, understand the logic, complete the TODOs
#
# Domain:
#   Line item: a single product in an order (product, unit price, quantity, per-item discount)
#   Subtotal: sum of (unit_price * quantity * (1 - discount_pct)) for all line items
#   Order discount: a percentage off the entire subtotal (e.g. 10% off the whole order)
#   Tax: a percentage added on top of the discounted subtotal
#   Total = discounted_subtotal + tax

from dataclasses import dataclass


@dataclass
class LineItem:
    product_id: str
    name: str
    unit_price: float
    quantity: int
    discount_pct: float  # 0.0 to 1.0 (e.g. 0.10 = 10% off this item)


def calculate_subtotal(items: list[LineItem]) -> float:
    return sum(item.unit_price * (1 - item.discount_pct) for item in items)


def apply_order_discount(subtotal: float, discount_pct: float) -> float:
    return subtotal * (1 - discount_pct)


def calculate_tax(amount: float, tax_rate: float) -> float:
    return amount * tax_rate


def calculate_total(
    items: list[LineItem],
    order_discount_pct: float = 0.0,
    tax_rate: float = 0.0,
) -> dict:
    subtotal = calculate_subtotal(items)
    after_discount = apply_order_discount(subtotal, order_discount_pct)
    tax = calculate_tax(subtotal, tax_rate)
    total = after_discount + tax

    return {
        "subtotal": subtotal,
        "discount_amount": subtotal - after_discount,
        "tax": tax,
        "total": total,
    }


def most_expensive_item(items: list[LineItem]) -> LineItem | None:
    if not items:
        return None
    return max(items, key=lambda i: i.unit_price * i.quantity)


# TODO: Add an apply_coupon(subtotal: float, coupon: dict) -> float function where coupon
#       has "type" ("flat" or "pct") and "value"; flat coupons should be capped at subtotal
# TODO: Add a group_by_discount(items: list[LineItem]) -> dict[float, list[LineItem]]
#       function that groups items by their discount_pct value


if __name__ == "__main__":
    items = [
        LineItem("P001", "Laptop",   unit_price=999.99, quantity=1, discount_pct=0.10),
        LineItem("P002", "Mouse",    unit_price=29.99,  quantity=2, discount_pct=0.0),
        LineItem("P003", "Keyboard", unit_price=79.99,  quantity=1, discount_pct=0.05),
        LineItem("P004", "Monitor",  unit_price=399.99, quantity=2, discount_pct=0.15),
    ]

    print("=== Line Items ===")
    for item in items:
        line_total = item.unit_price * item.quantity * (1 - item.discount_pct)
        print(f"  {item.name}: {item.quantity} x ${item.unit_price:.2f} @ -{item.discount_pct:.0%} = ${line_total:.2f}")

    expected_subtotal = sum(i.unit_price * i.quantity * (1 - i.discount_pct) for i in items)
    print(f"\n  Expected subtotal: ${expected_subtotal:.2f}")

    print("\n=== calculate_total (10% order discount, 8% tax) ===")
    result = calculate_total(items, order_discount_pct=0.10, tax_rate=0.08)
    for k, v in result.items():
        print(f"  {k}: ${v:.2f}")

    print("\n=== edge case: single item ===")
    single = [LineItem("X", "Widget", unit_price=50.0, quantity=3, discount_pct=0.0)]
    result2 = calculate_total(single, order_discount_pct=0.0, tax_rate=0.10)
    print(f"  3x$50, 10% tax — total: ${result2['total']:.2f} (expected: $165.00)")

    print("\n=== most_expensive_item ===")
    best = most_expensive_item(items)
    print(f"  {best.name} (${best.unit_price:.2f} x {best.quantity})")
    print(f"  most_expensive_item([]) -> {most_expensive_item([])}")
