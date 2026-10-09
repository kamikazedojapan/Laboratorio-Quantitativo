"""Ledger de barras: sinais de t-1 são executados na abertura t."""
import math
import pandas as pd
from .strategies import signals


def backtest(data, c, strategy, signal_override=None):
    d = data.reset_index(drop=True)
    sig, indicators = signals(d, strategy)
    if signal_override is not None:
        sig = signal_override.reset_index(drop=True)
    cash, qty, basis, realized = float(c["initial_cash"]), 0, 0., 0.
    fees_total = slip_total = traded = 0.
    ledger, orders, trades = [], [], []
    entry_time = None
    for j, row in d.iterrows():
        same = j > 0 and d.session.iloc[j-1] == row.session
        clock = row.timestamp.strftime("%H:%M")
        liquidate = clock >= c["liquidation_time"]
        sell = qty > 0 and (liquidate or (same and bool(sig.sell.iloc[j-1])))
        buy = qty == 0 and not liquidate and ((strategy == "session_hold" and not same) or (same and bool(sig.buy.iloc[j-1])))
        if sell:
            price = row.Open * (1 - c["slippage_bps"] / 10000)
            notional = qty * price
            fee = notional * c["fee_bps"] / 10000 + c["fixed_fee"]
            slip = qty * (row.Open - price)
            pnl = notional - fee - basis
            cash += notional - fee
            realized += pnl
            orders.append(dict(timestamp=row.timestamp, side="SELL", quantity=qty, price=price, fee=fee, slippage=slip, reason="session" if liquidate else "signal"))
            trades.append(dict(entry=entry_time, exit=row.timestamp, quantity=qty, pnl=pnl))
            fees_total += fee
            slip_total += slip
            traded += notional
            qty, basis = 0, 0.
        elif buy:
            price = row.Open * (1 + c["slippage_bps"] / 10000)
            budget = cash * c["allocation"]
            lot = c["lot_size"]
            quantity = max(0, math.floor((budget-c["fixed_fee"]) / (price*(1+c["fee_bps"]/10000)*lot)) * lot)
            if quantity:
                notional = quantity * price
                fee = notional*c["fee_bps"]/10000 + c["fixed_fee"]
                slip = quantity*(price-row.Open)
                qty, basis, entry_time = quantity, notional+fee, row.timestamp
                cash -= basis
                fees_total += fee
                slip_total += slip
                traded += notional
                orders.append(dict(timestamp=row.timestamp, side="BUY", quantity=qty, price=price, fee=fee, slippage=slip, reason="baseline" if strategy == "session_hold" else "signal"))
        market = qty * row.Close
        equity = cash + market
        if cash < -1e-7 or qty < 0:
            raise AssertionError("Violação de capital/posição")
        ledger.append(dict(timestamp=row.timestamp, cash=cash, quantity=qty, market_value=market, equity=equity, realized_pnl=realized, unrealized_pnl=market-basis, exposure=market/equity if equity else 0, fees=fees_total, slippage=slip_total, turnover_notional=traded))
    l = pd.DataFrame(ledger)
    l["drawdown"] = l.equity / l.equity.cummax().clip(lower=c["initial_cash"]) - 1
    return {"ledger": l, "orders": pd.DataFrame(orders, columns=["timestamp", "side", "quantity", "price", "fee", "slippage", "reason"]), "trades": pd.DataFrame(trades, columns=["entry", "exit", "quantity", "pnl"]), "signals": sig, "indicators": indicators}
