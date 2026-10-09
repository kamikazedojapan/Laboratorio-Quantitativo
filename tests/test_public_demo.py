import hashlib
import json
from pathlib import Path
import shutil

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from trading_lab import dashboard
from trading_lab.data import load_config, synthetic
from trading_lab.research import run_research


@pytest.mark.parametrize('value,expected', [(None, False), ('1', True), ('0', False),
    ('', False), ('true', False), ('01', False), (' 1', False), ('1 ', False)])
def test_public_flag_exact_environment_value(monkeypatch, value, expected):
    monkeypatch.delenv('LAB_PUBLIC_DEMO', raising=False)
    if value is not None:
        monkeypatch.setenv('LAB_PUBLIC_DEMO', value)
    assert dashboard.public_demo_enabled() is expected


@pytest.mark.parametrize('manifest,expected', [
    ({'config': {'data_kind': 'synthetic'}}, True),
    ({'config': {'data_kind': 'real'}}, False),
    ({'config': {'data_kind': 'historical'}}, False),
    ({'config': {'data_kind': 'imported'}}, False),
    ({'config': {'data_kind': 'Synthetic'}}, False),
    ({'config': {'data_kind': None}}, False),
    ({'config': {}}, False), ({}, False),
    ({'data_kind': 'synthetic'}, False),
    ({'config': None}, False), ({'config': []}, False), ([], False),
])
def test_history_requires_explicit_synthetic_manifest(tmp_path, manifest, expected):
    path = tmp_path / 'manifest.json'
    path.write_text(json.dumps(manifest), encoding='utf-8')
    assert dashboard.is_synthetic_record(path) is expected


def test_unreadable_and_invalid_manifests_are_hidden(tmp_path):
    path = tmp_path / 'manifest.json'
    assert not dashboard.is_synthetic_record(path)
    path.write_text('{invalid', encoding='utf-8')
    assert not dashboard.is_synthetic_record(path)
    path.write_bytes(b'\xff')
    assert not dashboard.is_synthetic_record(path)


@pytest.fixture
def project(tmp_path, monkeypatch):
    for folder in ['configs', 'strategies']:
        shutil.copytree(folder, tmp_path / folder)
    monkeypatch.setattr(dashboard, 'ROOT', tmp_path)
    return tmp_path


def app():
    return AppTest.from_file(str(Path('app.py').resolve()), default_timeout=90).run()


def test_public_ui_execution_and_filtered_history(project, monkeypatch):
    monkeypatch.setenv('LAB_PUBLIC_DEMO', '1')
    def forbidden(*args, **kwargs):
        pytest.fail('Public mode must never read visitor data')
    monkeypatch.setattr(dashboard, 'read_data', forbidden)
    c = load_config('configs/demo.json')
    saved, _, _ = run_research(synthetic(c), c, project / 'runs')
    excluded = []
    for i, manifest in enumerate([
        {'config': {'data_kind': 'real'}}, {'config': {'data_kind': 'historical'}},
        {'config': {'data_kind': 'imported'}}, {'config': {}}, {},
    ]):
        folder = project / 'runs' / f'zz-excluded-{i}'
        folder.mkdir()
        (folder / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        excluded.append(folder)
    broken = project / 'runs' / 'zz-broken'
    broken.mkdir()
    (broken / 'manifest.json').write_text('{', encoding='utf-8')
    hashes = {p: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (project / 'runs').rglob('*') if p.is_file()}
    at = app()
    assert not at.exception and not at.error
    assert not at.sidebar.radio and not at.get('file_uploader')
    assert not at.get('text_input') and not at.get('text_area')
    assert any('Versão pública' in x.value and 'sintéticos' in x.value for x in at.caption)
    control = at.sidebar.number_input[0]
    assert (control.min, control.max, control.value) == (3, 260, 60)
    assert at.selectbox[0].options == [str(saved)]
    assert len(at.get('plotly_chart')) == 6
    assert len(at.get('download_button')) == 1
    at.button[0].click().run()
    assert not at.exception and not at.error
    new = next(p for p in (project / 'runs').iterdir()
               if p != saved and p not in excluded and p != broken)
    manifest = json.loads((new / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest['config']['data_kind'] == 'synthetic'
    assert len(manifest['config']['session_dates']) == 60
    assert manifest['status'] == 'complete'
    at.selectbox[0].select(str(new)).run()
    assert not at.exception and not at.error
    summary = pd.read_csv(new / 'summary.csv')
    assert len(summary) == 12
    assert set(summary.estrategia) == {'ema', 'rsi', 'session_hold', 'caixa'}
    pd.testing.assert_frame_equal(at.dataframe[1].value, summary)
    indicators = pd.read_csv(new / 'desenvolvimento_ema_indicators.csv')
    assert {'ema9', 'ema21', 'rsi14', 'macd'} <= set(indicators.columns)
    assert indicators.ema21.notna().any()
    assert len(at.get('plotly_chart')) == 6
    assert at.get('download_button')[0].proto.label == 'Baixar comparação CSV'
    assert set(at.selectbox[0].options) == {str(saved), str(new)}
    for count in (3, 260):
        at.sidebar.number_input[0].set_value(count).run()
        assert not at.exception and not at.error
        assert len(json.loads(at.json[0].value)['session_dates']) == count
    assert all(hashlib.sha256(p.read_bytes()).hexdigest() == h for p, h in hashes.items())


@pytest.mark.parametrize('value', [None, '0', 'true', ' 1'])
def test_local_controls_and_history_unchanged(project, monkeypatch, value):
    monkeypatch.delenv('LAB_PUBLIC_DEMO', raising=False)
    if value is not None:
        monkeypatch.setenv('LAB_PUBLIC_DEMO', value)
    c = load_config('configs/demo.json')
    saved, _, _ = run_research(synthetic(c), c, project / 'runs')
    # An imported record is still offered locally. This fixture never touches real history.
    path = saved / 'manifest.json'
    manifest = json.loads(path.read_text(encoding='utf-8'))
    manifest['config']['data_kind'] = 'real'
    path.write_text(json.dumps(manifest), encoding='utf-8')
    at = app()
    assert not at.exception and not at.error
    assert at.sidebar.radio[0].options == ['Demonstração sintética', 'Importar CSV/Parquet']
    assert len(at.get('file_uploader')) == 2
    assert at.selectbox[0].options == [str(saved)]
    assert not any('Versão pública' in x.value for x in at.caption)
    assert at.sidebar.number_input[0].value == 60
    at.sidebar.number_input[0].set_value(261).run()
    assert not at.exception and not at.error
    at.sidebar.radio[0].set_value('Importar CSV/Parquet').run()
    assert not at.exception and not at.error
    assert len(at.get('file_uploader')) == 2
    assert any('Envie dados e configuração' in x.value for x in at.info)
