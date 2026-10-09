"""Apresentação de registros persistidos, independente dos dados em edição."""
import json
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

PERCENT_COLUMNS = {
    "retorno_liquido", "drawdown_maximo", "win_rate", "exposicao_media",
    "tempo_posicionado", "retorno_anualizado",
}
MONEY_COLUMNS = {
    "ganho_medio", "perda_media", "expectancy", "taxas", "slippage",
    "custo_total", "pnl_realizado", "pnl_nao_realizado", "valor_posicao_aberta",
}


def style_summary(summary):
    """Styler preserva os dtypes e muda somente a apresentação."""
    formats = {k: "{:.2%}" for k in PERCENT_COLUMNS & set(summary.columns)}
    formats.update({k: "{:,.2f}" for k in MONEY_COLUMNS & set(summary.columns)})
    formats.update({k: "{:.2f}" for k in {"turnover", "profit_factor", "sharpe_anualizado"} & set(summary.columns)})
    formats.update({k: "{:.0f}" for k in {"operacoes_fechadas", "quantidade_aberta"} & set(summary.columns)})
    return summary.style.format(formats, na_rep="não estimável", decimal=",", thousands=".")


def load_record_chart(folder, partition, strategy):
    """Novos CSVs têm timestamp. Legados alinham por barra após conferir ledger."""
    folder = Path(folder)
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    boundary = manifest["partitions"][partition]
    prices = pd.read_csv(folder / "data.csv")
    zone = manifest["config"]["timezone"]
    prices["timestamp"] = pd.to_datetime(prices.timestamp, utc=True).dt.tz_convert(zone)
    start, end = pd.Timestamp(boundary["start"]), pd.Timestamp(boundary["end"])
    prices = prices[prices.timestamp.between(start, end)].reset_index(drop=True)
    if len(prices) != boundary["bars"] or prices.timestamp.duplicated().any() or not prices.timestamp.is_monotonic_increasing:
        raise ValueError("Snapshot não corresponde à partição do manifesto")
    prefix = folder / f"{partition}_{strategy}"
    ledger = pd.read_csv(str(prefix) + "_ledger.csv")

    def check_times(frame):
        times = pd.to_datetime(frame.timestamp, utc=True).dt.tz_convert(zone)
        if not times.reset_index(drop=True).equals(prices.timestamp):
            raise ValueError("Timestamps persistidos não correspondem ao snapshot")

    check_times(ledger)
    for kind in ("indicators", "signals"):
        frame = pd.read_csv(str(prefix) + f"_{kind}.csv")
        if len(frame) != len(prices):
            raise ValueError("Quantidade de indicadores/sinais diverge do snapshot")
        if "timestamp" in frame:
            check_times(frame)
            frame = frame.drop(columns="timestamp")
        if kind == "signals":
            for col in ("buy", "sell"):
                if frame[col].isna().any() or not frame[col].isin([True, False]).all():
                    raise ValueError("Sinais persistidos inválidos")
                frame[col] = frame[col].astype(bool)
        prices = pd.concat([prices, frame], axis=1)
    orders = pd.read_csv(str(prefix) + "_orders.csv")
    orders["timestamp"] = pd.to_datetime(orders.timestamp, utc=True).dt.tz_convert(zone)
    if not orders.timestamp.isin(prices.timestamp).all():
        raise ValueError("Ordens fora da partição persistida")
    return prices, orders


def record_figure(prices, orders):
    def times(frame):
        # ISO explícito evita perda de timezone na conversão Pandas/Plotly.
        return [t.isoformat() for t in frame.timestamp]

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[.6, .2, .2], vertical_spacing=.05)
    for col in ("Close", "sma20", "ema9", "ema21", "bb_middle", "bb_upper", "bb_lower"):
        fig.add_trace(go.Scatter(x=times(prices), y=prices[col], name=col, mode="lines"), row=1, col=1)
    for col, label, color in (("buy", "Sinal de compra", "#3b82f6"), ("sell", "Sinal de venda", "#f59e0b")):
        points = prices[prices[col]]
        fig.add_trace(go.Scatter(x=times(points), y=points.Close, name=label, mode="markers", marker=dict(symbol="circle-open", size=10, color=color)), row=1, col=1)
    for side, label, symbol, color in (("BUY", "Compra executada", "triangle-up", "#15803d"), ("SELL", "Venda executada", "triangle-down", "#dc2626")):
        points = orders[orders.side == side]
        fig.add_trace(go.Scatter(x=times(points), y=points.price, name=label, mode="markers", marker=dict(symbol=symbol, size=13, color=color), customdata=points[["quantity", "reason", "fee"]].to_numpy(), hovertemplate="%{x}<br>Preço executado: %{y:.4f}<br>Quantidade: %{customdata[0]}<br>Motivo: %{customdata[1]}<br>Taxa: %{customdata[2]:.2f}<extra>%{fullData.name}</extra>"), row=1, col=1)
    fig.add_trace(go.Scatter(x=times(prices), y=prices.rsi14, name="RSI14"), row=2, col=1)
    for level in (30, 70):
        fig.add_hline(y=level, line_dash="dot", row=2, col=1)
    for col in ("macd", "macd_signal"):
        fig.add_trace(go.Scatter(x=times(prices), y=prices[col], name=col), row=3, col=1)
    fig.add_trace(go.Bar(x=times(prices), y=prices.macd_histogram, name="macd_histogram"), row=3, col=1)
    fig.update_layout(height=850, title="Registro selecionado — preços, indicadores, sinais e execuções", hovermode="x unified")
    fig.update_yaxes(title_text="Preço (u.m.)", row=1, col=1)
    fig.update_yaxes(title_text="RSI", row=2, col=1)
    fig.update_yaxes(title_text="MACD", row=3, col=1)
    return fig
