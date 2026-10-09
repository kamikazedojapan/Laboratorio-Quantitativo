def cash_metrics():
    """Caixa sem remuneração: ausência de exposição, custos e operações."""
    return {
        "retorno_liquido": 0., "drawdown_maximo": 0., "operacoes_fechadas": 0,
        "win_rate": None, "ganho_medio": None, "perda_media": None,
        "expectancy": None, "profit_factor": None,
        "exposicao_media": 0., "tempo_posicionado": 0., "turnover": 0.,
        "taxas": 0., "slippage": 0., "custo_total": 0.,
        "pnl_realizado": 0., "pnl_nao_realizado": 0.,
        "quantidade_aberta": 0, "valor_posicao_aberta": 0.,
        "sharpe_anualizado": None, "retorno_anualizado": None,
        "evidencia": "evidência insuficiente",
    }


def metrics(result, c):
    l, trades = result["ledger"], result["trades"]
    pnl = trades.pnl
    wins, losses = pnl[pnl > 0], pnl[pnl < 0]
    last = l.iloc[-1]
    return {
        "retorno_liquido": float(last.equity/c["initial_cash"]-1),
        "drawdown_maximo": float(l.drawdown.min()),
        "operacoes_fechadas": len(trades),
        "win_rate": float((pnl > 0).mean()) if len(pnl) else None,
        "ganho_medio": float(wins.mean()) if len(wins) else None,
        "perda_media": float(losses.mean()) if len(losses) else None,
        "expectancy": float(pnl.mean()) if len(pnl) else None,
        "profit_factor": float(wins.sum()/-losses.sum()) if len(losses) else None,
        "exposicao_media": float(l.exposure.mean()),
        "tempo_posicionado": float((l.quantity > 0).mean()),
        "turnover": float(last.turnover_notional/c["initial_cash"]),
        "taxas": float(last.fees), "slippage": float(last.slippage),
        "custo_total": float(last.fees+last.slippage),
        "pnl_realizado": float(last.realized_pnl),
        "pnl_nao_realizado": float(last.unrealized_pnl),
        "quantidade_aberta": int(last.quantity),
        "valor_posicao_aberta": float(last.market_value),
        "sharpe_anualizado": None, "retorno_anualizado": None,
        "evidencia": "evidência insuficiente",
    }
