import json
import logging
from pathlib import Path
import shutil
import numpy as np
import pandas as pd
import pyarrow as pa
import pytest
from trading_lab.data import load_config, synthetic
from trading_lab.research import run_research
from trading_lab.metrics import metrics
from trading_lab.presentation import load_record_chart, record_figure, style_summary


@pytest.fixture(scope="module")
def record(tmp_path_factory):
    c = load_config("configs/demo.json")
    d = synthetic(c)
    out, summary, results = run_research(d, c, tmp_path_factory.mktemp("review"))
    return out, summary, results, d, c


def test_cash_complete_and_numeric_roundtrip(record):
    out, summary, results, _, _ = record
    saved = pd.read_csv(out / "summary.csv")
    zero = ["retorno_liquido", "drawdown_maximo", "operacoes_fechadas", "exposicao_media", "tempo_posicionado", "turnover", "taxas", "slippage", "custo_total", "pnl_realizado", "pnl_nao_realizado", "quantidade_aberta", "valor_posicao_aberta"]
    undefined = ["win_rate", "ganho_medio", "perda_media", "expectancy", "profit_factor", "sharpe_anualizado", "retorno_anualizado"]
    for frame in (summary, saved):
        cash = frame[frame.estrategia == "caixa"]
        assert len(cash) == 3
        assert cash[zero].eq(0).all().all()
        assert cash[undefined].isna().all().all()
        for col in zero + undefined:
            assert pd.api.types.is_numeric_dtype(frame[col]), col
    assert set(summary.columns) - {"particao", "estrategia"} == set(metrics(results[("desenvolvimento", "ema")], record[4]))


def test_style_preserves_numbers_and_formats_only_display(record):
    summary = record[1]
    before = summary.copy(deep=True)
    styled = style_summary(summary)
    pa.Table.from_pandas(styled.data)  # Falha se houver mistura de números e texto.
    pd.testing.assert_frame_equal(styled.data, before)
    html = styled.to_html()
    assert "não estimável" in html
    assert "0,00%" in html
    # O retorno permanece fração e valores monetários permanecem float.
    pd.testing.assert_frame_equal(summary, before)


@pytest.mark.parametrize("part", ["desenvolvimento", "validacao", "teste_final"])
@pytest.mark.parametrize("strategy", ["ema", "rsi", "session_hold"])
def test_record_prices_signals_and_fills(record, part, strategy):
    out, _, results, _, _ = record
    prices, orders = load_record_chart(out, part, strategy)
    result = results[(part, strategy)]
    np.testing.assert_allclose(prices.ema9, result["indicators"].ema9, equal_nan=True)
    assert prices.buy.tolist() == result["signals"].buy.tolist()
    assert prices.sell.tolist() == result["signals"].sell.tolist()
    assert orders.timestamp.tolist() == result["orders"].timestamp.tolist()
    fig = record_figure(prices, orders)
    traces = {t.name: t for t in fig.data}
    for side, name in (("BUY", "Compra executada"), ("SELL", "Venda executada")):
        actual = orders[orders.side == side]
        assert [pd.Timestamp(t) for t in traces[name].x] == actual.timestamp.tolist()
        np.testing.assert_allclose(traces[name].y, actual.price)
        assert list(traces[name].customdata[:, 1]) == actual.reason.tolist()
    assert [pd.Timestamp(t) for t in traces["Sinal de compra"].x] == prices.loc[prices.buy, "timestamp"].tolist()


def test_saved_values_are_not_recomputed_and_legacy_supported(record, tmp_path, monkeypatch):
    out = tmp_path / "legacy"
    shutil.copytree(record[0], out)
    for kind in ("signals", "indicators"):
        path = out / f"validacao_ema_{kind}.csv"
        frame = pd.read_csv(path).drop(columns="timestamp")
        if kind == "indicators":
            frame["ema9"] = 1234.5  # Sentinel prova leitura, não recálculo.
        else:
            frame["buy"] = False
            frame.loc[0, "buy"] = True
        frame.to_csv(path, index=False)
    import trading_lab.indicators as indicators
    monkeypatch.setattr(indicators, "all_indicators", lambda *args: pytest.fail("Não deve recalcular"))
    prices, orders = load_record_chart(out, "validacao", "ema")
    assert prices.ema9.eq(1234.5).all()
    assert prices.buy.sum() == 1 and prices.buy.iloc[0]
    assert len(orders) == len(record[2][("validacao", "ema")]["orders"])


def test_record_rejects_misaligned_timestamp(record, tmp_path):
    out = tmp_path / "misaligned"
    shutil.copytree(record[0], out)
    path = out / "validacao_ema_signals.csv"
    frame = pd.read_csv(path)
    frame.loc[0, "timestamp"] = frame.loc[1, "timestamp"]
    frame.to_csv(path, index=False)
    with pytest.raises(ValueError, match="Timestamps"):
        load_record_chart(out, "validacao", "ema")


def test_record_no_orders(record, tmp_path):
    out = tmp_path / "no_orders"
    shutil.copytree(record[0], out)
    path = out / "teste_final_ema_orders.csv"
    pd.read_csv(path).iloc[:0].to_csv(path, index=False)
    prices, orders = load_record_chart(out, "teste_final", "ema")
    fig = record_figure(prices, orders)
    assert all(len(t.x) == 0 for t in fig.data if t.name in ("Compra executada", "Venda executada"))


def test_dashboard_record_independent_of_current_data_and_no_arrow_warning(record, tmp_path, monkeypatch, caplog):
    from streamlit.testing.v1 import AppTest
    import trading_lab.dashboard as dashboard
    root = tmp_path / "project"
    root.mkdir()
    shutil.copytree("configs", root / "configs")
    shutil.copytree("strategies", root / "strategies")
    saved = root / "runs" / record[0].name
    shutil.copytree(record[0], saved)
    monkeypatch.setattr(dashboard, "ROOT", root)
    different = record[3].copy()
    different[["Open", "High", "Low", "Close"]] *= 10
    monkeypatch.setattr(dashboard, "synthetic", lambda config: different)
    observed = []
    original = dashboard.record_figure

    def observe(prices, orders):
        observed.append((prices.copy(), orders.copy()))
        return original(prices, orders)

    monkeypatch.setattr(dashboard, "record_figure", observe)
    logger = logging.getLogger("streamlit.dataframe_util")
    monkeypatch.setattr(logger, "propagate", True)
    with caplog.at_level(logging.DEBUG, logger="streamlit.dataframe_util"):
        app = AppTest.from_file(str(Path("app.py").resolve()), default_timeout=30).run()
        assert not app.exception and not app.error
        app.selectbox[1].select("validacao").run()
        app.selectbox[2].select("rsi").run()
        assert not app.exception and not app.error
    expected, orders = load_record_chart(saved, "validacao", "rsi")
    pd.testing.assert_frame_equal(observed[-1][0], expected)
    pd.testing.assert_frame_equal(observed[-1][1], orders)
    assert observed[-1][0].Close.max() < different.Close.min()
    assert "ArrowInvalid" not in caplog.text
    assert "Applying automatic fixes" not in caplog.text
    # Dados numéricos também permanecem numéricos dentro do componente Streamlit.
    summary_table = app.dataframe[1].value
    assert pd.api.types.is_numeric_dtype(summary_table.win_rate)
    assert pd.api.types.is_numeric_dtype(summary_table.retorno_liquido)
