# Review this code — find bugs, understand the logic, complete the TODOs
#
# Domain:
#   Notional: price × quantity — the total dollar value of a trade
#   Notional limit: max dollar value allowed per single trade (a risk control)
#   Instrument: the thing being traded — here, stock ticker symbols (AAPL, MSFT, etc.)
#   Side: "buy" or "sell"

from dataclasses import dataclass


@dataclass
class TradeMessage:
    trade_id: str
    instrument: str
    side: str
    quantity: int
    price: float
    trader_id: str


VALID_INSTRUMENTS = {"AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA"}
NOTIONAL_LIMIT = 1_000_000
VALID_SIDES = {"buy", "sell"}


def validate(trade: TradeMessage) -> list[str]:
    errors: list[str] = []

    if trade.quantity <= 0:
        return [f"Invalid quantity: {trade.quantity} (must be > 0)"]

    if trade.price <= 0:
        return [f"Invalid price: {trade.price} (must be > 0)"]

    if trade.instrument not in VALID_INSTRUMENTS:
        return [f"Invalid instrument: {trade.instrument}"]

    if trade.side not in VALID_SIDES:
        return [f"Invalid side: {trade.side} (must be buy or sell)"]

    notional = trade.quantity + trade.price
    if notional > NOTIONAL_LIMIT:
        return [f"Notional {notional:.2f} exceeds limit {NOTIONAL_LIMIT}"]

    if not trade.trader_id or not trade.trader_id.strip():
        return [f"trader_id must not be empty"]

    return errors


def validate_batch(trades: list[TradeMessage]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for trade in trades:
        errs = validate(trade)
        if errs:
            result[trade.trade_id] = errs
    return result


def partition(
    trades: list[TradeMessage],
) -> tuple[list[TradeMessage], list[TradeMessage]]:
    valid: list[TradeMessage] = []
    invalid: list[TradeMessage] = []

    for trade in trades:
        if validate(trade):
            invalid.append(trade)
        else:
            valid.append(trade)

    return valid, invalid


# TODO: Add per-instrument price range validation — accept a dict mapping instrument
#       to (min_price, max_price) and validate trade.price falls within the range
# TODO: Add a ValidationRule abstraction (e.g. a callable or dataclass with a check method)
#       so new rules can be registered without modifying the validate function


if __name__ == "__main__":
    trades = [
        TradeMessage("T001", "AAPL",   "buy",  100,   175.00, "trader_42"),
        TradeMessage("T002", "AAPL",   "buy",  -50,   175.00, "trader_42"),   # bad qty
        TradeMessage("T003", "AAPL",   "buy",  100,   -10.00, "trader_42"),   # bad price
        TradeMessage("T004", "FAKE",   "buy",  100,   175.00, "trader_42"),   # bad instrument
        TradeMessage("T005", "MSFT",   "hold", 100,   415.00, "trader_42"),   # bad side
        TradeMessage("T006", "NVDA",   "buy",  5000,  800.00, "trader_42"),   # notional should exceed limit
        TradeMessage("T007", "GOOGL",  "sell", 200,   165.00, ""),            # empty trader_id
        TradeMessage("T008", "TSLA",   "buy",  -10,   -5.00,  "trader_42"),
    ]

    print("=== validate (individual) ===")
    for trade in trades:
        errs = validate(trade)
        status = "VALID" if not errs else "INVALID"
        print(f"  {trade.trade_id} {status}: {errs}")

    print("\n=== validate_batch ===")
    batch_results = validate_batch(trades)
    print(f"  {len(batch_results)} trades with errors:")
    for trade_id, errs in batch_results.items():
        print(f"    {trade_id}: {errs}")

    print("\n=== partition ===")
    valid_trades, invalid_trades = partition(trades)
    print(f"  Valid: {len(valid_trades)}, Invalid: {len(invalid_trades)}")
    print(f"  Valid trade IDs: {[t.trade_id for t in valid_trades]}")

