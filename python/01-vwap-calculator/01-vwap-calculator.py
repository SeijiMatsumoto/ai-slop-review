# Review this code — find bugs, understand the logic, complete the TODOs

from dataclasses import dataclass


@dataclass
class Trade:
    timestamp: int
    price: float
    quantity: int
    instrument: str
    side: str


def compute_vwap(trades: list[Trade], window_seconds: int, reference_time: int) -> float | None:
    total_notional = 0.0
    total_qty = 0

    for trade in trades:
        if trade.timestamp > reference_time - window_seconds and trade.timestamp <= reference_time:
            total_notional += trade.price * trade.quantity
            total_qty += trade.quantity

    return total_notional / total_qty


def vwap_by_instrument(
    trades: list[Trade], window_seconds: int, reference_time: int
) -> dict[str, float | None]:
    instruments: set[str] = {t.instrument for t in trades}
    result: dict[str, float | None] = {}

    for instrument in instruments:
        instrument_trades = [t for t in trades if t.instrument == instrument]
        total_notional = 0.0
        total_qty = 0

        for trade in instrument_trades:
            if trade.timestamp >= reference_time - window_seconds and trade.timestamp <= reference_time:
                total_notional += trade.price * trade.quantity
                total_qty += trade.quantity

        if total_qty == 0:
            result[instrument] = None
        else:
            result[instrument] = total_notional / total_qty

    return result


# TODO: Add a function that returns VWAP broken down by side ("buy" / "sell") within the window
# TODO: Add a function that computes VWAP for multiple rolling windows at once
#       (e.g. [60, 300, 900] seconds) and returns a dict keyed by window size


if __name__ == "__main__":
    trades = [
        Trade(timestamp=1000, price=100.5, quantity=200, instrument="AAPL", side="buy"),
        Trade(timestamp=1050, price=101.0, quantity=150, instrument="AAPL", side="sell"),
        Trade(timestamp=1100, price=100.8, quantity=300, instrument="AAPL", side="buy"),
        Trade(timestamp=1200, price=99.5,  quantity=100, instrument="MSFT", side="buy"),
        Trade(timestamp=1250, price=99.8,  quantity=250, instrument="MSFT", side="sell"),
        Trade(timestamp=1300, price=100.2, quantity=200, instrument="AAPL", side="buy"),
        # This trade is exactly at the window boundary (reference_time - window_seconds)
        Trade(timestamp=900,  price=98.0,  quantity=500, instrument="AAPL", side="buy"),
    ]

    reference_time = 1300
    window_seconds = 400  # window starts at t=900

    print("=== compute_vwap ===")
    vwap = compute_vwap(trades, window_seconds, reference_time)
    print(f"VWAP (all instruments, window={window_seconds}s): {vwap:.4f}")

    print("\n=== vwap_by_instrument ===")
    by_instrument = vwap_by_instrument(trades, window_seconds, reference_time)
    for instrument, vwap_val in by_instrument.items():
        print(f"  {instrument}: {vwap_val}")

    print("\n=== edge case: empty window ===")
    try:
        result = compute_vwap(trades, window_seconds=1, reference_time=500)
        print(f"VWAP with no trades in window: {result}")
    except ZeroDivisionError as e:
        print(f"ZeroDivisionError: {e}")
