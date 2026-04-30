# Review this code — find bugs, understand the logic, complete the TODOs
#
# Domain:
#   Plan: a subscription tier with a fixed monthly price
#   Billing period: one month, modelled as 30 days (day 1 through day 30)
#   Proration: when a user changes plans mid-period, charge/credit proportionally
#     Formulas (given):
#       days_remaining = 30 - current_day
#       prorated_new   = (days_remaining / 30) * new_plan_price
#       prorated_old   = (days_remaining / 30) * old_plan_price
#       net_charge     = prorated_new - prorated_old
#         positive net_charge = user owes money (upgrade)
#         negative net_charge = user gets a credit (downgrade)

from dataclasses import dataclass


PLANS: dict[str, float] = {
    "free":       0.00,
    "basic":      9.99,
    "pro":        29.99,
    "enterprise": 99.99,
}


@dataclass
class Subscription:
    user_id: str
    plan: str
    price: float
    start_day: int
    status: str = "active"   # "active" | "cancelled"


class SubscriptionManager:
    def __init__(self) -> None:
        self.subscriptions: dict[str, Subscription] = {}

    def subscribe(self, user_id: str, plan: str, start_day: int = 1) -> Subscription:
        if plan not in PLANS:
            raise ValueError(f"Unknown plan: {plan}")
        sub = Subscription(
            user_id=user_id,
            plan=plan,
            price=PLANS[plan],
            start_day=start_day,
        )
        self.subscriptions[user_id] = sub
        return sub

    def change_plan(self, user_id: str, new_plan: str, current_day: int) -> float:
        sub = self.subscriptions.get(user_id)
        if sub is None or sub.status != "active":
            raise ValueError("No active subscription")
        if new_plan not in PLANS:
            raise ValueError(f"Unknown plan: {new_plan}")

        days_remaining = 30 - current_day
        net_charge = (days_remaining / 30) * PLANS[new_plan] - (days_remaining / 30) * sub.price

        sub.plan = new_plan
        return net_charge

    def cancel(self, user_id: str) -> bool:
        sub = self.subscriptions.get(user_id)
        if sub is None:
            return False
        sub.status = "cancelled"
        return True

    def monthly_revenue(self) -> float:
        return sum(
            s.price for s in self.subscriptions.values()
            if s.status == "active"
        )

    def active_count(self) -> int:
        return sum(1 for s in self.subscriptions.values() if s.status == "active")


# TODO: Add a trial_subscribe(user_id, plan, trial_days) method that sets status="trial"
#       and stores a trial_ends_on_day: int; trial subscriptions are excluded from
#       monthly_revenue() until converted
# TODO: Add a bulk_discount(user_ids: list[str], discount_pct: float) method that
#       reduces the price field by discount_pct for all listed active subscriptions


if __name__ == "__main__":
    mgr = SubscriptionManager()

    print("=== subscribe ===")
    mgr.subscribe("alice", "basic", start_day=1)
    mgr.subscribe("bob", "pro", start_day=5)
    mgr.subscribe("charlie", "free", start_day=10)
    for uid, sub in mgr.subscriptions.items():
        print(f"  {uid}: {sub.plan} @ ${sub.price:.2f}/mo")

    print(f"\n  Monthly revenue: ${mgr.monthly_revenue():.2f}")

    print("\n=== change_plan: alice basic→pro on day 10 ===")
    # days_remaining = 20; net = (20/30)*(29.99 - 9.99) = (20/30)*20.00 = $13.33
    charge = mgr.change_plan("alice", "pro", current_day=10)
    print(f"  Net charge: ${charge:.2f} (expected: $13.33)")
    alice = mgr.subscriptions["alice"]
    print(f"  Alice plan={alice.plan}, price=${alice.price:.2f} (price should be $29.99 now)")

    print("\n=== change_plan: bob pro→basic on day 20 ===")
    # days_remaining = 10; net = (10/30)*(9.99 - 29.99) = (10/30)*(-20.00) = -$6.67 (credit)
    charge2 = mgr.change_plan("bob", "basic", current_day=20)
    print(f"  Net charge: ${charge2:.2f} (expected: -$6.67)")

    print("\n=== cancel ===")
    mgr.cancel("charlie")
    print(f"  charlie status: {mgr.subscriptions['charlie'].status}")
    print(f"  Revenue after cancel: ${mgr.monthly_revenue():.2f}")
    print(f"  Active count: {mgr.active_count()}")
