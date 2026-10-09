from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from trading_lab.data import load_config, synthetic, validate_data, read_data
from trading_lab.indicators import sma, ema, rsi, bollinger, macd
from trading_lab.backtest import backtest
from trading_lab.research import run_research


@pytest.fixture
def c():
    return load_config("configs/demo.json")


def test_manual_indicators():
    s = pd.Series([1., 2., 3., 4., 5.])
    assert sma(s, 3).iloc[2:].tolist() == [2, 3, 4]
    assert ema(s, 3).iloc[2:].tolist() == [2, 3, 4]
    assert rsi(s, 3).iloc[3:].tolist() == [100, 100]
    assert rsi(-s, 3).iloc[3:].tolist() == [0, 0]
    assert rsi(s*0+5, 3).iloc[3:].tolist() == [50, 50]
    bb = bollinger(s, 3)
    assert bb.bb_upper.iloc[2] == pytest.approx(2+2*np.sqrt(2/3))
    assert bb.bb_lower.iloc[2] == pytest.approx(2-2*np.sqrt(2/3))
    m = macd(s, 2, 3, 2)
    assert m.macd.iloc[2] == pytest.approx(.5)
    assert m.macd_signal.iloc[3] == pytest.approx(.5)
    assert m.macd_histogram.iloc[3] == pytest.approx(0)
    # Gains [2,0,3], losses [0,1,0]; next change -2.
    known = rsi(pd.Series([10., 12., 11., 14., 12.]), 3)
    assert known.iloc[3] == pytest.approx(100*5/6)
    assert known.iloc[4] == pytest.approx(100*10/18)


def test_warmup_missing():
    s = pd.Series([1., 2., np.nan, 4., 5., 6.])
    assert ema(s, 2).isna().tolist() == [True, False, True, True, False, False]
    assert rsi(pd.Series(range(15), dtype=float)).notna().sum() == 1
    assert macd(pd.Series(range(34), dtype=float)).macd_signal.notna().sum() == 1
    with pytest.raises(ValueError):
        ema(s, 0)


@pytest.mark.parametrize("fault", ["order", "duplicate", "negative", "timezone", "gap", "ohlc", "session", "volume", "daily"])
def test_reject_data(c, fault):
    d = synthetic(c)
    if fault == "order": d = d.iloc[::-1]
    if fault == "duplicate": d.loc[1, "timestamp"] = d.loc[0, "timestamp"]
    if fault == "negative": d.loc[0, "Close"] = -1
    if fault == "timezone": d.timestamp = d.timestamp.dt.tz_localize(None)
    if fault == "gap": d = d.drop(10)
    if fault == "ohlc": d.loc[0, "High"] = 1
    if fault == "session": d = d[d.session != c["session_dates"][0]]
    if fault == "volume": d.loc[0, "Volume"] = np.nan
    if fault == "daily": d = d.groupby("session").head(1)
    with pytest.raises(ValueError): validate_data(d, c)


def test_roundtrip(c, tmp_path):
    d = synthetic(c)
    for suffix in ("csv", "parquet"):
        path = tmp_path / f"data.{suffix}"
        getattr(d, "to_"+suffix)(path, index=False)
        pd.testing.assert_frame_equal(read_data(path, c), d, check_exact=False)


def test_accounting_next_open_costs(c):
    d = synthetic(c).iloc[:4].copy()
    d["Open"] = [9., 10., 11., 12.]
    d["Close"] = [9., 11., 12., 12.]
    c.update(initial_cash=100., allocation=1., fixed_fee=1., fee_bps=100., slippage_bps=100.)
    sig = pd.DataFrame({"buy": [True, False, False, False], "sell": [False, False, True, False]})
    result = backtest(d, c, "ema", sig)
    l = result["ledger"]
    assert l.quantity.tolist() == [0, 9, 9, 0]
    buy = 9*10.1
    cost_basis = buy*1.01+1
    proceeds = 9*11.88*.99-1
    assert l.cash.iloc[1] == pytest.approx(100-cost_basis)
    assert l.unrealized_pnl.iloc[1] == pytest.approx(99-cost_basis)
    assert l.equity.iloc[-1] == pytest.approx(100-cost_basis+proceeds)
    assert result["trades"].pnl.iloc[0] == pytest.approx(proceeds-cost_basis)
    assert l.realized_pnl.iloc[1] == 0


def test_session_and_affordability(c):
    d = synthetic(c)
    r = backtest(d, c, "session_hold")
    assert len(r["trades"]) == len(c["session_dates"])
    assert set(r["orders"].query("side == 'SELL'").timestamp.dt.strftime("%H:%M")) == {c["liquidation_time"]}
    assert (r["ledger"].cash >= 0).all()
    assert (r["ledger"].quantity.groupby(d.session).last() == 0).all()
    assert r["orders"].fee.gt(0).all()
    c["initial_cash"] = .1
    assert backtest(d, c, "session_hold")["orders"].empty


@pytest.mark.parametrize("strategy", ["ema", "rsi", "session_hold"])
def test_no_lookahead(c, strategy):
    d = synthetic(c)
    future = d.copy()
    future.loc[201:, ["Open", "High", "Low", "Close"]] *= 1.4
    a, b = backtest(d, c, strategy), backtest(future, c, strategy)
    for k in ("signals", "indicators", "ledger"):
        pd.testing.assert_frame_equal(a[k].iloc[:201], b[k].iloc[:201])
    # Removing future bars cannot change earlier states either.
    prefix = backtest(d.iloc[:201], c, strategy)
    pd.testing.assert_frame_equal(a["ledger"].iloc[:201], prefix["ledger"])


def test_research(c, tmp_path):
    out, summary, results = run_research(synthetic(c), c, tmp_path)
    assert len(summary) == 12
    assert (out / "manifest.json").exists()
    for r in results.values():
        assert r["ledger"].quantity.iloc[-1] == 0
        assert r["ledger"].equity.iloc[-1]-c["initial_cash"] == pytest.approx(r["trades"].pnl.sum())


def test_dashboard():
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(Path("app.py").resolve()), default_timeout=30).run()
    assert not app.exception
    assert app.title[0].value == "Laboratório de Trading com ChatGPT"
    app.button[0].click().run()
    assert not app.exception
    assert len(app.dataframe) >= 3


def test_crossing_rules(monkeypatch):
    import trading_lab.strategies as strategies
    values = pd.DataFrame({"ema9": [0, 0, 2, 2, 0, 2], "ema21": [1]*6, "rsi14": [29, 30, 31, 69, 70, 71]})
    monkeypatch.setattr(strategies, "all_indicators", lambda s: values)
    d = pd.DataFrame({"Close": [100.]*6})
    a, _ = strategies.signals(d, "ema")
    b, _ = strategies.signals(d, "rsi")
    assert a.buy.tolist() == [False, False, True, False, False, True]
    assert a.sell.tolist() == [False, False, False, False, True, False]
    assert b.buy.tolist() == [False, False, True, False, False, False]
    assert b.sell.tolist() == [False, False, False, False, False, True]


def test_no_overnight_signal_and_forced_exit(c):
    d = synthetic(c)
    sig = pd.DataFrame({"buy": False, "sell": False}, index=d.index)
    sig.loc[35, "buy"] = True  # última barra da primeira sessão
    assert backtest(d, c, "ema", sig)["orders"].empty
    sig.loc[0, "buy"] = True
    r = backtest(d, c, "ema", sig)
    assert len(r["orders"]) == 2
    assert r["orders"].iloc[-1].reason == "session"
    assert r["orders"].iloc[-1].fee > 0
    assert r["ledger"].equity.iloc[-1]-c["initial_cash"] == pytest.approx(r["trades"].pnl.sum())


def test_metrics_known(c):
    from trading_lab.metrics import metrics
    r = backtest(synthetic(c), c, "ema")
    r["trades"] = pd.DataFrame({"pnl": [20., -10., 0.]})
    m = metrics(r, c)
    assert m["win_rate"] == pytest.approx(1/3)
    assert m["expectancy"] == pytest.approx(10/3)
    assert m["profit_factor"] == 2
    assert m["ganho_medio"] == 20
    assert m["perda_media"] == -10
    r["trades"] = pd.DataFrame({"pnl": []})
    m = metrics(r, c)
    assert m["profit_factor"] is None and m["win_rate"] is None


def test_reject_ambiguous_clock(c):
    from trading_lab.data import validate_config
    c["liquidation_time"] = "9:50"
    with pytest.raises(ValueError, match="HH:MM"):
        validate_config(c)
