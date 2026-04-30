# Review this code — find bugs, understand the logic, complete the TODOs

from dataclasses import dataclass


@dataclass
class Allocation:
    account: str
    quantity: int


def allocate(parent_qty: int, weights: dict[str, float]) -> list[Allocation]:
    result: list[Allocation] = []
    for account, weight in weights.items():
        qty = round(weight * parent_qty)
        result.append(Allocation(account=account, quantity=qty))
    return result


def reallocate(allocations: list[Allocation], new_total: int) -> list[Allocation]:
    total_current = sum(a.quantity for a in allocations)
    if total_current == 0:
        return allocations

    weights = {a.account: a.quantity / total_current for a in allocations}
    return allocate(new_total, weights)


def validate_allocations(allocations: list[Allocation], expected_total: int) -> list[str]:
    errors: list[str] = []
    actual_total = sum(a.quantity for a in allocations)

    if actual_total != expected_total:
        errors.append(
            f"Allocation sum {actual_total} does not match expected {expected_total}"
        )

    for alloc in allocations:
        if alloc.quantity < 0:
            errors.append(f"Account {alloc.account} has negative quantity {alloc.quantity}")
        elif alloc.quantity == 0:
            errors.append(f"Account {alloc.account} has zero quantity")

    return errors


# TODO: Implement the largest-remainder rounding method so allocations always sum exactly
#       to parent_qty
# TODO: Add a minimum lot size parameter — any account whose raw allocation falls below the
#       minimum should have its quantity set to 0 (or the minimum, depending on a flag),
#       with the remainder redistributed to other accounts


if __name__ == "__main__":
    weights = {
        "AccountA": 0.40,
        "AccountB": 0.35,
        "AccountC": 0.25,
    }

    print("=== allocate ===")
    for parent_qty in [100, 333, 1000, 7]:
        allocs = allocate(parent_qty, weights)
        total = sum(a.quantity for a in allocs)
        print(f"  parent_qty={parent_qty}: {[(a.account, a.quantity) for a in allocs]} -> sum={total}")

    print("\n=== validate_allocations ===")
    allocs_1000 = allocate(1000, weights)
    errors = validate_allocations(allocs_1000, 1000)
    if errors:
        print(f"  Errors: {errors}")
    else:
        print("  Allocations valid")

    allocs_333 = allocate(333, weights)
    errors = validate_allocations(allocs_333, 333)
    if errors:
        for e in errors:
            print(f"  Error: {e}")

    print("\n=== reallocate ===")
    initial = [
        Allocation("AccountA", 400),
        Allocation("AccountB", 350),
        Allocation("AccountC", 250),
    ]
    realloc_result = reallocate(initial, 500)
    realloc_total = sum(a.quantity for a in realloc_result)
    print(f"  Reallocated to 500: {[(a.account, a.quantity) for a in realloc_result]} -> sum={realloc_total}")

    print("\n=== weights don't sum to 1.0 ===")
    bad_weights = {"AccountA": 0.50, "AccountB": 0.30}  # sums to 0.80
    bad_allocs = allocate(1000, bad_weights)
    bad_total = sum(a.quantity for a in bad_allocs)
    print(f"  Weights sum to 0.80, got total allocation: {bad_total}")
