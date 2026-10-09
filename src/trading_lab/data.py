import json
import csv
import io
import re
from copy import deepcopy
from numbers import Real
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd

REQUIRED = ["timestamp", "asset", "Open", "High", "Low", "Close", "Volume"]


def load_config(path):
    c = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    validate_config(c)
    return c


def validate_config(c):
    for k in ("initial_cash", "allocation", "fee_bps", "fixed_fee", "slippage_bps"):
        if isinstance(c[k], (bool, np.bool_)) or not isinstance(c[k], Real) or not np.isfinite(c[k]) or c[k] < 0:
            raise ValueError(f"Número finito não negativo obrigatório: {k}")
    ZoneInfo(c["timezone"])
    if c["data_kind"] not in ("synthetic", "real") or not c["provenance"].strip() or not c["session_provenance"].strip():
        raise ValueError("Informe tipo e procedência dos dados/sessões")
    f = c["frequency_minutes"]
    if isinstance(f, bool) or not isinstance(f, int) or not 0 < f < 1440:
        raise ValueError("Esta versão aceita apenas frequência intraday em minutos")
    for k in ("session_start", "session_end", "liquidation_time"):
        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", c[k]):
            raise ValueError("Horários devem usar HH:MM com dois dígitos")
    start, end, close = [pd.Timestamp("2000-01-01 " + c[k]) for k in ("session_start", "session_end", "liquidation_time")]
    if not start < close < end or any((t-start).total_seconds() % (f*60) for t in (close, end)):
        raise ValueError("Sessão/liquidação precisam estar alinhadas à frequência; liquidação antes do fim")
    if not 0 < c["allocation"] <= 1 or c["initial_cash"] <= 0:
        raise ValueError("Capital/alocação inválidos")
    if isinstance(c["lot_size"], bool) or not isinstance(c["lot_size"], int) or c["lot_size"] < 1:
        raise ValueError("Lote inválido")
    if c["fee_bps"] >= 10000 or c["slippage_bps"] >= 10000:
        raise ValueError("Taxas devem ser inferiores a 10000 bps")
    dates = c["session_dates"]
    if not dates or dates != sorted(set(dates)):
        raise ValueError("Calendário vazio, duplicado ou fora de ordem")
    for d in dates:
        if pd.Timestamp(d).strftime("%Y-%m-%d") != d:
            raise ValueError("Data inválida")
    a, b = c["split"]["development_end"], c["split"]["validation_end"]
    if not dates[0] <= a < b < dates[-1]:
        raise ValueError("Fronteiras não formam três partições cronológicas")


def grid(date, c):
    return pd.date_range(f"{date} {c['session_start']}", f"{date} {c['session_end']}", freq=f"{c['frequency_minutes']}min", tz=c["timezone"], inclusive="left")


def read_data(source, c, suffix=None):
    suffix = suffix or Path(source).suffix
    if suffix.lower() == ".csv":
        # Validate original names before pandas silently renames duplicates.
        text = source.read() if hasattr(source, 'read') else Path(source).read_text(encoding='utf-8-sig')
        if isinstance(text, bytes):
            text = text.decode('utf-8-sig')
        text = text.lstrip('\ufeff')
        header = next((row for row in csv.reader(io.StringIO(text))
                       if any(field.strip() for field in row)), [])
        if len(header) != len(set(header)):
            raise ValueError("Colunas duplicadas não são permitidas no CSV")
        raw = pd.read_csv(io.StringIO(text))
    elif suffix.lower() == ".parquet":
        raw = pd.read_parquet(source)
    else:
        raise ValueError("Use CSV ou Parquet")
    return validate_data(raw, c)


def validate_data(raw, c):
    validate_config(c)
    if raw.columns.duplicated().any():
        raise ValueError("Colunas duplicadas não são permitidas")
    missing = set(REQUIRED) - set(raw.columns)
    if missing or raw.empty:
        raise ValueError(f"Dados vazios ou colunas ausentes: {sorted(missing)}")
    d = raw[REQUIRED].copy()
    if d.asset.isna().any() or d.asset.nunique() != 1 or not str(d.asset.iloc[0]).strip():
        raise ValueError("Cada execução exige exatamente um ativo")
    try:
        stamps = [pd.Timestamp(x) for x in d.timestamp]
        if any(pd.isna(t) or t.tzinfo is None for t in stamps):
            raise ValueError("Timestamp deve incluir timezone/offset explícito")
        d["timestamp"] = pd.to_datetime(stamps, utc=True).tz_convert(c["timezone"])
    except (TypeError, ValueError) as e:
        raise ValueError(f"Timestamp/timezone inválido: {e}") from e
    if d.timestamp.duplicated().any() or not d.timestamp.is_monotonic_increasing:
        raise ValueError("Timestamps duplicados ou fora de ordem; não ordenamos silenciosamente")
    for k in REQUIRED[2:]:
        if d[k].map(lambda x: isinstance(x, (bool, np.bool_))).any():
            raise ValueError(f"Booleano não é preço ou volume: {k}")
        d[k] = pd.to_numeric(d[k], errors="raise")
        if not np.isfinite(d[k]).all() or (d[k] < 0).any() or (k != "Volume" and (d[k] == 0).any()):
            raise ValueError(f"Valores inválidos em {k}")
    if ((d.High < d[["Open", "Close", "Low"]].max(axis=1)) | (d.Low > d[["Open", "Close", "High"]].min(axis=1))).any():
        raise ValueError("OHLC inconsistente")
    d["session"] = d.timestamp.dt.strftime("%Y-%m-%d")
    if list(d.session.unique()) != c["session_dates"]:
        raise ValueError("Sessões divergem do calendário explícito (incluindo dias ausentes)")
    for date, part in d.groupby("session", sort=False):
        if list(part.timestamp) != list(grid(date, c)):
            raise ValueError(f"Frequência, lacunas ou sessão incompleta: {date}")
    return d.reset_index(drop=True)


def synthetic_config(c, sessions=60):
    """Artificial weekdays, with chronological 8:4:3 splits (whole sessions)."""
    if isinstance(sessions, bool) or not isinstance(sessions, int) or sessions < 3:
        raise ValueError("Número de sessões sintéticas deve ser inteiro, no mínimo 3")
    validate_config(c)
    if c['data_kind'] != 'synthetic':
        raise ValueError("Calendário artificial exige dados sintéticos")
    result = deepcopy(c)
    dates = pd.bdate_range(c['session_dates'][0], periods=sessions).strftime('%Y-%m-%d').tolist()
    development = max(1, sessions * 8 // 15)
    validation = max(1, sessions * 4 // 15)
    result['session_dates'] = dates
    result['split'] = {'development_end': dates[development-1],
                       'validation_end': dates[development+validation-1]}
    result['synthetic_sessions'] = sessions
    result['synthetic_calendar_policy'] = 'weekdays; no exchange holidays'
    result['synthetic_split_policy'] = 'development=max(1,floor(8N/15)); validation=max(1,floor(4N/15)); test=remainder'
    validate_config(result)
    return result


def synthetic(c):
    rng = np.random.default_rng(c["seed"])
    times = pd.DatetimeIndex([t for date in c["session_dates"] for t in grid(date, c)])
    x = np.arange(len(times))
    close = 100 + 4 * np.sin(x / 11) + .8 * np.sin(x / 3) + rng.normal(0, .12, len(x))
    opening = np.r_[close[0], close[:-1]] + rng.normal(0, .06, len(x))
    d = pd.DataFrame({"timestamp": times, "asset": "SINTETICO", "Open": opening, "High": np.maximum(opening, close) + .15, "Low": np.minimum(opening, close) - .15, "Close": close, "Volume": rng.integers(1000, 10000, len(x))})
    return validate_data(d, c)
