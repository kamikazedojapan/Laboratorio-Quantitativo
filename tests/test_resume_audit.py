"""Additional input contracts found during the accompanied review."""
import io
import numpy as np
import pandas as pd
import pytest
from trading_lab.indicators import bollinger, macd
from trading_lab.data import load_config, read_data, synthetic


@pytest.mark.parametrize('bad', [True, np.bool_(True), '2', None, [2], complex(2, 0)])
def test_bollinger_multiplier_requires_real_scalar(bad):
    with pytest.raises(ValueError):
        bollinger(pd.Series([1., 2., 3.]), 2, bad)


@pytest.mark.parametrize('kwargs', [{'fast': '2'}, {'slow': None}, {'signal': True}])
def test_macd_invalid_periods_have_explicit_error(kwargs):
    with pytest.raises(ValueError):
        macd(pd.Series([1., 2., 3.]), **kwargs)


@pytest.mark.parametrize('prefix', ['', '\n\n', '\ufeff\n'])
def test_csv_duplicate_header_is_rejected_before_pandas_mangling(prefix):
    c = load_config('configs/demo.json')
    d = synthetic(c).drop(columns='session')
    # A second conflicting Close must not disappear as an ignored Close.1 column.
    d = pd.concat([d, d[['Close']] * 10], axis=1)
    with pytest.raises(ValueError, match='duplicad'):
        read_data(io.StringIO(prefix + d.to_csv(index=False)), c, '.csv')


def test_binary_csv_with_bom_and_quoted_header_roundtrip():
    c = load_config('configs/demo.json')
    d = synthetic(c).drop(columns='session')
    payload = ('\ufeff' + d.to_csv(index=False, quoting=1)).encode('utf-8')
    actual = read_data(io.BytesIO(payload), c, '.csv')
    pd.testing.assert_frame_equal(actual.drop(columns='session'), d, check_exact=False, atol=1e-10)
