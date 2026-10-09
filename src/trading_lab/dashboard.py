import json
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from .data import load_config, read_data, synthetic, synthetic_config, validate_config
from .indicators import all_indicators
from .research import run_research
from .presentation import style_summary, load_record_chart, record_figure

ROOT = Path(__file__).resolve().parents[2]


def main():
    st.set_page_config(page_title="Laboratório de Trading", page_icon="🧪", layout="wide")
    st.title("Laboratório de Trading com ChatGPT")
    st.caption("Pesquisa local • Indicadores determinísticos • Sem envio de ordens")
    st.warning("Comparação exploratória. Evidência insuficiente para eficácia no mercado.")
    mode = st.sidebar.radio("Fonte de dados", ["Demonstração sintética", "Importar CSV/Parquet"])
    config_upload = st.sidebar.file_uploader("Configuração JSON (obrigatória na importação)", type=["json"])
    data_upload = st.sidebar.file_uploader("Barras OHLCV", type=["csv", "parquet"])
    try:
        if mode == "Demonstração sintética":
            sessions = st.sidebar.number_input("Número de sessões sintéticas", min_value=3, value=60, step=1)
            c = synthetic_config(load_config(ROOT / "configs/demo.json"), sessions)
            d = synthetic(c)
            st.info("DEMONSTRAÇÃO SINTÉTICA — ativo, preços, calendário e sessão artificiais.")
            development = c['session_dates'].index(c['split']['development_end']) + 1
            validation_end = c['session_dates'].index(c['split']['validation_end']) + 1
            st.sidebar.caption(f"Sessões: {development} desenvolvimento / {validation_end-development} validação / {sessions-validation_end} teste final. Calendário artificial de segunda a sexta, sem ajuste de feriados.")
            st.sidebar.caption(f"Custos por ordem: {c['fee_bps']:g} bps + {c['fixed_fee']:g} u.m.; slippage adverso: {c['slippage_bps']:g} bps.")
        else:
            if config_upload is None or data_upload is None:
                st.info("Envie dados e configuração com calendário, timezone, procedência e fronteiras cronológicas.")
                return
            c = json.loads(config_upload.getvalue().decode("utf-8-sig"))
            validate_config(c)
            d = read_data(data_upload, c, Path(data_upload.name).suffix)
            st.info(f"Tipo declarado: {c['data_kind']} | {c['provenance']}")
    except (ValueError, KeyError, TypeError) as e:
        st.error(f"Dados/configuração rejeitados: {e}")
        return
    with st.expander("Diagnóstico e configuração", expanded=False):
        st.write(f"{len(d)} barras • {d.session.nunique()} sessões • {d.asset.iloc[0]} • {c['timezone']}")
        st.success("Ordenação, duplicatas, OHLCV, timezone, frequência e calendário verificados.")
        st.json(c)
        st.dataframe(d.head(), hide_index=True)
    with st.expander("Regras, parâmetros fixos e premissas"):
        st.markdown((ROOT / "strategies/ema/SPEC.md").read_text(encoding="utf-8"))
        st.markdown((ROOT / "strategies/rsi/SPEC.md").read_text(encoding="utf-8"))
    st.subheader("Preços e indicadores")
    st.caption("Visualização do arquivo completo. Os indicadores dos backtests reiniciam em cada partição.")
    chart = pd.concat([d[["timestamp", "Close"]], all_indicators(d.Close)], axis=1)
    chosen = st.multiselect("Indicadores de preço (filtro apenas visual)", ["sma20", "ema9", "ema21", "bb_upper", "bb_lower"], default=["ema9", "ema21"])
    st.plotly_chart(px.line(chart, x="timestamp", y=["Close"]+chosen), width="stretch")
    with st.expander("RSI e MACD"):
        st.plotly_chart(px.line(chart, x="timestamp", y="rsi14"), width="stretch")
        st.plotly_chart(px.line(chart, x="timestamp", y=["macd", "macd_signal", "macd_histogram"]), width="stretch")
    if st.button("Executar comparação e registrar", type="primary"):
        try:
            out, summary, _ = run_research(d, c, ROOT / "runs")
            st.session_state["run_path"] = str(out)
            st.success(f"Execução registrada: {out.name}")
        except ValueError as e:
            st.error(str(e))
    folders = sorted((ROOT / "runs").glob("*/manifest.json"), reverse=True)
    if folders:
        st.subheader("Histórico das execuções")
        selected = st.selectbox("Registro salvo — filtros abaixo não recalculam a pesquisa", [str(p.parent) for p in folders])
        out = Path(selected)
        st.caption(f"Resultados do registro {out.name}; podem diferir dos dados/configuração atualmente selecionados acima.")
        st.json(json.loads((out / "manifest.json").read_text(encoding="utf-8")))
        summary_file = out / "summary.csv"
        if not summary_file.exists():
            st.warning("Registro incompleto; resultados indisponíveis.")
            return
        summary = pd.read_csv(summary_file)
        st.subheader("Comparação das hipóteses e benchmarks")
        st.caption("Valores ausentes: não estimável. Percentuais formatados somente na tela; valores monetários em unidades do preço (u.m.). O CSV mantém números e campos ausentes.")
        st.dataframe(style_summary(summary), hide_index=True)
        part = st.selectbox("Partição visualizada", ["desenvolvimento", "validacao", "teste_final"])
        strategy = st.selectbox("Estratégia visualizada", ["ema", "rsi", "session_hold"])
        st.subheader("Preços e operações do registro selecionado")
        st.caption("Fonte exclusiva: snapshot e arquivos persistidos deste registro. Círculos indicam sinais associados à barra (conhecidos no fechamento); triângulos indicam ordens executadas na abertura, ao preço com slippage. O eixo usa o timestamp de abertura da barra no timezone registrado.")
        try:
            saved_prices, saved_orders = load_record_chart(out, part, strategy)
            st.plotly_chart(record_figure(saved_prices, saved_orders), width="stretch", key="record_chart")
        except (ValueError, KeyError, OSError) as e:
            st.error(f"Não foi possível carregar o gráfico persistido: {e}")
        ledger = pd.read_csv(out / f"{part}_{strategy}_ledger.csv")
        st.plotly_chart(px.line(ledger, x="timestamp", y="equity", title="Patrimônio líquido"), width="stretch")
        st.plotly_chart(px.area(ledger, x="timestamp", y="drawdown", title="Drawdown"), width="stretch")
        st.subheader("Operações simuladas e posição")
        st.dataframe(pd.read_csv(out / f"{part}_{strategy}_orders.csv"), hide_index=True)
        st.dataframe(ledger.tail(), hide_index=True)
        st.download_button("Baixar comparação CSV", summary_file.read_bytes(), "comparacao.csv", "text/csv")
    st.subheader("Limitações")
    st.write("Execução aproximada na abertura seguinte com slippage fixo. Sem modelagem de fila, liquidez, leilões, impostos ou eventos corporativos. Sessões e calendários reais exigem fonte externa verificada. Não há otimização, recomendação ou seleção de vencedor. Black-Scholes P01 é um módulo isolado de preços e Greeks, sem integração ao motor intraday. IV, Monte Carlo, hedge, jumps, machine learning e NautilusTrader permanecem pendentes.")
    coverage = ROOT / "reports/acompanhamento/20261007-retomada/method_coverage.csv"
    if coverage.is_file():
        with st.expander("Cobertura da auditoria e pendências"):
            st.caption("Implementação, teste e autorrevisão são estados distintos. Revisão externa pendente. Testes sintéticos não demonstram eficácia financeira.")
            st.dataframe(pd.read_csv(coverage).fillna(""), hide_index=True)
