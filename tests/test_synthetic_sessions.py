import copy
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
import pandas as pd
import pytest
from trading_lab.data import load_config, synthetic, synthetic_config
from trading_lab.research import partitions, run_research
from trading_lab.presentation import load_record_chart


@pytest.mark.parametrize('count,expected', [(3,[1,1,1]),(15,[8,4,3]),(16,[8,4,4]),(60,[32,16,12]),(61,[32,16,13])])
def test_calendar_and_partition_contract(count,expected):
    base=load_config('configs/demo.json'); before=copy.deepcopy(base)
    c=synthetic_config(base,count); d=synthetic(c)
    assert base==before
    for key in ['frequency_minutes','session_start','session_end','liquidation_time','seed','initial_cash','allocation','lot_size','fee_bps','fixed_fee','slippage_bps']:
        assert c[key]==base[key]
    assert len(d)==count*36
    assert d.groupby('session').size().eq(36).all()
    assert d.timestamp.dt.dayofweek.lt(5).all()
    assert not d.timestamp.duplicated().any()
    for _,day in d.groupby('session'):
        assert day.timestamp.iloc[0].strftime('%H:%M')=='09:00'
        assert day.timestamp.iloc[-1].strftime('%H:%M')=='11:55'
        assert (np.diff(day.timestamp.astype('int64').to_numpy()) == 300_000_000_000).all()  # Five minutes in ns.
    parts=list(partitions(d,c).values())
    assert [p.session.nunique() for p in parts]==expected
    pd.testing.assert_frame_equal(pd.concat(parts),d)
    assert parts[0].timestamp.iloc[-1]<parts[1].timestamp.iloc[0]<parts[2].timestamp.iloc[0]
    pd.testing.assert_frame_equal(synthetic(c),d)
    if count==15:
        pd.testing.assert_frame_equal(d,synthetic(base))
        assert c['split']==base['split']
    if count==60:
        assert c['split']=={'development_end':'2026-10-14','validation_end':'2026-11-05'}
        assert c['session_dates'][-1]=='2026-11-23'


@pytest.mark.parametrize('bad',[True,2,0,-1,60.5,'60'])
def test_reject_invalid_session_counts(bad):
    with pytest.raises(ValueError):synthetic_config(load_config('configs/demo.json'),bad)


def test_reject_artificial_calendar_for_real_data():
    c=load_config('configs/demo.json');c['data_kind']='real'
    with pytest.raises(ValueError):synthetic_config(c,60)


def test_dashboard_session_control_keeps_saved_record_graphs(tmp_path,monkeypatch):
    from streamlit.testing.v1 import AppTest
    import trading_lab.dashboard as dashboard
    root=tmp_path/'project';root.mkdir()
    for folder in ['configs','strategies']:shutil.copytree(folder,root/folder)
    base=load_config('configs/demo.json')
    old,_,_=run_research(synthetic(base),base,root/'runs')
    old_hashes={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in old.rglob('*') if p.is_file()}
    monkeypatch.setattr(dashboard,'ROOT',root)
    observed=[];original=dashboard.record_figure
    def observe(prices,orders):
        observed.append((prices.copy(),orders.copy()))
        return original(prices,orders)
    monkeypatch.setattr(dashboard,'record_figure',observe)
    app=AppTest.from_file(str(Path('app.py').resolve()),default_timeout=60).run()
    assert not app.exception and not app.error
    assert app.sidebar.number_input[0].label=='Número de sessões sintéticas'
    assert app.sidebar.number_input[0].value==60
    app.button[0].click().run()
    assert not app.exception and not app.error
    new=next(p for p in (root/'runs').iterdir() if p!=old)
    m=json.loads((new/'manifest.json').read_text(encoding='utf-8'))
    assert [m['partitions'][p]['sessions'] for p in ['desenvolvimento','validacao','teste_final']]==[32,16,12]
    assert len(pd.read_csv(new/'data.csv'))==2160
    for key in ['fee_bps','fixed_fee','slippage_bps']:
        assert m['execution_costs'][key]==m['config'][key]==base[key]
    summary=pd.read_csv(new/'summary.csv')
    for row in summary.itertuples():
        if row.estrategia=='caixa':continue
        orders=pd.read_csv(new/f'{row.particao}_{row.estrategia}_orders.csv')
        assert row.taxas==pytest.approx(orders.fee.sum())
        assert row.slippage==pytest.approx(orders.slippage.sum())
        assert row.custo_total==pytest.approx(orders.fee.sum()+orders.slippage.sum())
    app.selectbox[0].select(str(new)).run()
    app.selectbox[1].select('teste_final').run()
    app.sidebar.number_input[0].set_value(30).run()
    assert not app.exception and not app.error
    assert len(list((root/'runs').iterdir()))==2  # Display change is not a new experiment.
    for record in [new,old]:
        app.selectbox[0].select(str(record)).run()
        expected=load_record_chart(record,'teste_final','ema')
        pd.testing.assert_frame_equal(observed[-1][0],expected[0])
        pd.testing.assert_frame_equal(observed[-1][1],expected[1])
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==h for p,h in old_hashes.items())
