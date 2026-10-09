import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
import pandas as pd
from .data import validate_data
from .backtest import backtest
from .metrics import metrics, cash_metrics


def partitions(d, c):
    a, b = c["split"]["development_end"], c["split"]["validation_end"]
    return {"desenvolvimento": d[d.session <= a], "validacao": d[(d.session > a) & (d.session <= b)], "teste_final": d[d.session > b]}


def run_research(data, c, root="runs"):
    d = validate_data(data, c)
    parts = partitions(d, c)
    if any(len(p) < 35 for p in parts.values()):
        raise ValueError("Evidência insuficiente: cada partição precisa de pelo menos 35 barras para o warm-up")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    out = Path(root) / stamp
    out.mkdir(parents=True, exist_ok=False)
    payload = d.to_csv(index=False).encode("utf-8")
    (out / "data.csv").write_bytes(payload)
    code_hash = hashlib.sha256()
    for p in sorted(Path(__file__).parent.glob("*.py")):
        code_hash.update(p.name.encode()+p.read_bytes())
    manifest = {"id": stamp, "config": c, "data_sha256": hashlib.sha256(payload).hexdigest(), "code_sha256": code_hash.hexdigest(), "versions": {p: importlib.metadata.version(p) for p in ["laboratorio-trading", "numpy", "pandas", "streamlit", "plotly", "pyarrow"]}, "partitions": {k: {"start": str(v.timestamp.iloc[0]), "end": str(v.timestamp.iloc[-1]), "bars": len(v), "sessions": v.session.nunique()} for k,v in parts.items()}, "status": "fronteiras registradas antes dos resultados"}
    # A digest identifies bytes but cannot recover them. Preserve the exact
    # executable package and specifications before producing any results.
    project = Path(__file__).resolve().parents[2]
    source_hashes, spec_hashes = {}, {}
    files = [(p, Path('trading_lab')/p.name) for p in sorted(Path(__file__).parent.glob('*.py'))]
    files += [(p, p.relative_to(project)) for p in sorted((project/'strategies').glob('*/SPEC.md'))]
    files += [(project/name, Path(name)) for name in ('pyproject.toml', 'requirements-lock.txt') if (project/name).is_file()]
    for p, relative in files:
        payload_source = p.read_bytes()
        target = out/'source'/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload_source)
        source_hashes[relative.as_posix()] = hashlib.sha256(payload_source).hexdigest()
        if p.name == 'SPEC.md':
            spec_hashes[relative.as_posix()] = source_hashes[relative.as_posix()]
    manifest.update(schema_version=2, source_sha256=source_hashes,
        spec_sha256=spec_hashes, python_version=sys.version,
        test_sample_status=('synthetic_previously_observed' if c['data_kind']=='synthetic'
                            else 'not_attested_by_software'),
        status='in_progress',
        split_policy='fixed_config; capital and indicators reset per partition')
    manifest['execution_costs'] = {
        'fee_bps': c['fee_bps'], 'fixed_fee': c['fixed_fee'],
        'slippage_bps': c['slippage_bps'],
        'application': 'each buy/sell; fixed_fee in price currency; adverse slippage included once in fill price',
        'realized_costs': 'summary.csv: taxas, slippage, custo_total per strategy and partition',
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    rows, results = [], {}
    for name, p in parts.items():
        for strategy in ("ema", "rsi", "session_hold"):
            result = backtest(p, c, strategy)
            results[(name, strategy)] = result
            rows.append({"particao": name, "estrategia": strategy, **metrics(result, c)})
            for artifact, frame in result.items():
                if artifact in ("signals", "indicators"):
                    frame = frame.copy()
                    frame.insert(0, "timestamp", p.timestamp.reset_index(drop=True))
                frame.to_csv(out / f"{name}_{strategy}_{artifact}.csv", index=False)
        rows.append({"particao": name, "estrategia": "caixa", **cash_metrics()})
    summary = pd.DataFrame(rows)
    for column in set(summary.columns) - {"particao", "estrategia", "evidencia"}:
        summary[column] = pd.to_numeric(summary[column], errors="raise")
    summary.to_csv(out / "summary.csv", index=False)
    (out / "report.md").write_text("# Execução exploratória\n\n" + f"ID: {stamp}\n\nTipo: {c['data_kind']}. Procedência: {c['provenance']}\n\n" + "Evidência insuficiente. Sem seleção de vencedor ou otimização. Dados sintéticos verificam funcionamento, não eficácia.\n\nFronteiras, configuração e hashes: manifest.json. Resultados: summary.csv; ordens, patrimônio, sinais e indicadores: CSVs por partição/estratégia. Campos ausentes significam não estimável.\n\nCada partição começa com capital inicial e warm-up próprios. Custos são taxas mais slippage adverso; slippage já está nos preços e não é debitado duas vezes. Caixa sem remuneração e posição por sessão são os baselines. Sem execução real, impostos, spread variável, impacto, leilões ou limites de liquidez. Calendário deve ser fornecido pelo usuário para dados reais. Resultados não anualizados.\n", encoding="utf-8")
    manifest['status'] = 'complete'
    manifest['artifact_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in sorted(out.iterdir()) if p.is_file() and p.name != 'manifest.json'}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    return out, summary, results
