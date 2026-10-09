"""Boundary contracts and independent audit checks, seed 20261007."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from trading_lab.data import load_config, synthetic, validate_config, validate_data
from trading_lab.indicators import sma, ema, rsi, bollinger, macd
from trading_lab.research import run_research, partitions
from trading_lab.backtest import backtest


@pytest.fixture
def c():
    return load_config('configs/demo.json')


@pytest.mark.parametrize('key', ['initial_cash', 'allocation', 'fee_bps', 'fixed_fee', 'slippage_bps'])
def test_boolean_money_rejected(c, key):
    c[key] = True
    with pytest.raises(ValueError):
        validate_config(c)


@pytest.mark.parametrize('column', ['Open', 'High', 'Low', 'Close', 'Volume'])
def test_boolean_market_data_rejected(c, column):
    d = synthetic(c)
    # All-one OHLC keeps internal consistency and exposes silent bool conversion.
    d[['Open', 'High', 'Low', 'Close', 'Volume']] = 1.
    d[column] = True
    with pytest.raises(ValueError):
        validate_data(d, c)


def test_duplicate_columns_rejected(c):
    d = synthetic(c)
    d = pd.concat([d, d[['Close']]], axis=1)
    with pytest.raises(ValueError, match='duplicad'):
        validate_data(d, c)


@pytest.mark.parametrize('n', [1, 2, 9, 21])
def test_indicators_against_independent_window_and_weights(n):
    xs = np.random.default_rng(20261007).normal(20, 2, 70)
    s = pd.Series(xs, index=pd.date_range('2020-01-01', periods=len(xs)))
    expected_sma = [np.mean(xs[t-n+1:t+1]) for t in range(n-1, len(xs))]
    np.testing.assert_allclose(sma(s,n).iloc[n-1:], expected_sma, atol=1e-10, rtol=1e-10)
    a = 2/(n+1)
    weights = [np.mean(xs[:n])*(1-a)**(t-n+1) +
               sum(a*(1-a)**(t-j)*xs[j] for j in range(n,t+1))
               for t in range(n-1,len(xs))]
    np.testing.assert_allclose(ema(s,n).iloc[n-1:], weights, atol=1e-10, rtol=1e-10)
    # Population variance via pairwise squared distances, independent of rolling.std.
    widths = [np.sqrt(sum((x-y)**2 for x in w for y in w)/(2*n*n))
              for w in (xs[t-n+1:t+1] for t in range(n-1,len(xs)))]
    bb = bollinger(s,n,2)
    np.testing.assert_allclose((bb.bb_upper-bb.bb_lower).iloc[n-1:], np.array(widths)*4, atol=1e-10)


@pytest.mark.parametrize('fn',[sma,ema,rsi,bollinger,macd])
def test_future_price_perturbation_does_not_change_indicator_prefix(fn):
    a = pd.Series(np.random.default_rng(20261007).normal(100,2,100))
    b = a.copy(); b.iloc[60:] *= 20
    np.testing.assert_allclose(fn(a).iloc[:60],fn(b).iloc[:60],atol=1e-10,equal_nan=True)


def test_partition_reset_and_future_independence(c):
    d = synthetic(c)
    changed = d.copy()
    changed.loc[changed.session > c['split']['validation_end'], ['Open','High','Low','Close']] *= 2
    before, after = partitions(d,c), partitions(changed,c)
    for name in ('desenvolvimento','validacao'):
        for strategy in ('ema','rsi'):
            a,b = backtest(before[name],c,strategy),backtest(after[name],c,strategy)
            for key in a:
                pd.testing.assert_frame_equal(a[key],b[key])
    for part in before.values():
        r = backtest(part,c,'ema')
        assert r['indicators'].ema21.iloc[:20].isna().all()
        assert r['ledger'].equity.iloc[0] == c['initial_cash']


def test_snapshot_and_artifact_hashes_match_bytes(c,tmp_path):
    out,_,_ = run_research(synthetic(c),c,tmp_path)
    m = json.loads((out/'manifest.json').read_text(encoding='utf-8'))
    assert m['status'] == 'complete'
    for relative,digest in m['source_sha256'].items():
        assert hashlib.sha256((out/'source'/relative).read_bytes()).hexdigest()==digest
    for relative,digest in m['artifact_sha256'].items():
        assert hashlib.sha256((out/relative).read_bytes()).hexdigest()==digest
    assert m['spec_sha256']['strategies/ema/SPEC.md'] == hashlib.sha256(Path('strategies/ema/SPEC.md').read_bytes()).hexdigest()


def test_real_run_does_not_claim_untouched_holdout(c,tmp_path):
    d=synthetic(c)
    c['data_kind']='real'
    c['provenance']='TEST ONLY: deliberately relabelled fixture; not actual market data'
    out,_,_=run_research(d,c,tmp_path)
    m=json.loads((out/'manifest.json').read_text(encoding='utf-8'))
    assert m['test_sample_status']=='not_attested_by_software'
