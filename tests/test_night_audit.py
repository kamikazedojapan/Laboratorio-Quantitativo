import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from trading_lab.indicators import sma, ema, rsi, bollinger, macd
from trading_lab.data import load_config, synthetic, validate_config, validate_data
from trading_lab.backtest import backtest
from trading_lab.metrics import metrics
from trading_lab.research import run_research, partitions

@pytest.fixture
def c(): return load_config('configs/demo.json')

@pytest.mark.parametrize('fn',[sma,ema,rsi,bollinger])
@pytest.mark.parametrize('period',[True,False,0,-1,1.5])
def test_invalid_indicator_period(fn,period):
    with pytest.raises(ValueError): fn(pd.Series([1.,2.,3.]),period)

@pytest.mark.parametrize('key',['lot_size','frequency_minutes'])
def test_boolean_config_is_not_integer(c,key):
    c[key]=True
    with pytest.raises(ValueError): validate_config(c)

@pytest.mark.parametrize('fn',[sma,ema,rsi,bollinger,macd])
def test_indicator_affine_properties(fn):
    s=pd.Series(np.random.default_rng(20261007).normal(100,5,100),index=np.arange(100)*3)
    a,b=fn(s),fn(s*3+11)
    if fn is rsi: expected=a
    elif fn is macd: expected=a*3
    else: expected=a*3+11
    np.testing.assert_allclose(b,expected,rtol=1e-10,atol=1e-10,equal_nan=True)
    assert a.index.equals(s.index)

def test_ema_independent_weighted_sum():
    s=pd.Series([4.,1.,7.,2.,9.,5.,8.,3.]); n=3; alpha=.5
    # Closed form weighted sum, independent of recursive update.
    expected=[np.nan,np.nan]+[(sum(s[:n])/n)*(1-alpha)**(t-n+1)+sum(alpha*(1-alpha)**(t-j)*s[j] for j in range(n,t+1)) for t in range(n-1,len(s))]
    np.testing.assert_allclose(ema(s,n),expected,rtol=1e-10,atol=1e-10,equal_nan=True)

def test_rsi_infinity_restarts_full_warmup():
    s=pd.Series([1.,2.,3.,np.inf,5.,6.,7.,8.])
    expected=rsi(s.replace([np.inf,-np.inf],np.nan),2)
    np.testing.assert_allclose(rsi(s,2),expected,equal_nan=True,atol=1e-10)

@pytest.mark.parametrize('fn',[sma,ema,rsi,bollinger,macd])
def test_constant_and_missing_warmup(fn):
    s=pd.Series([5.]*45+[np.nan]+[5.]*40)
    a=fn(s)
    if fn is rsi: assert a.dropna().eq(50).all()
    elif fn is macd: assert a.dropna().eq(0).all().all()
    elif fn is bollinger: assert a.dropna().eq(5).all().all()
    else: assert a.dropna().eq(5).all()
    assert np.asarray(a.iloc[45]).reshape(-1).tolist()==pytest.approx([np.nan]*np.asarray(a.iloc[45]).size,nan_ok=True)

@pytest.mark.parametrize('pnls,win,pf,expectancy',[([],None,None,None),([2,4],1,None,3),([-2,-4],0,0,-3),([0,0],0,None,0),([6,-2,0],1/3,3,4/3)])
def test_trade_metrics_edges(c,pnls,win,pf,expectancy):
    r=backtest(synthetic(c).iloc[:4],c,'ema'); r['trades']=pd.DataFrame({'pnl':pnls})
    m=metrics(r,c)
    for key,value in [('win_rate',win),('profit_factor',pf),('expectancy',expectancy)]:
        if value is None: assert m[key] is None
        else: assert m[key]==pytest.approx(value)

@pytest.mark.parametrize('strategy',['ema','rsi','session_hold'])
def test_independent_order_reconstruction(c,strategy):
    d=synthetic(c); result=backtest(d,c,strategy)
    cash=c['initial_cash']; qty=0; basis=0; realized=0; fees=0; slip=0; turnover=0; peak=cash
    for j,row in d.iterrows():
        orders=result['orders']; executed=orders[orders.timestamp==row.timestamp]
        assert len(executed)<=1
        for order in executed.itertuples():
            sign=1 if order.side=='BUY' else -1
            expected_price=row.Open*(1+sign*c['slippage_bps']/10000)
            assert order.price==pytest.approx(expected_price)
            fee=order.quantity*order.price*c['fee_bps']/10000+c['fixed_fee']
            cash-=sign*order.quantity*order.price+fee
            if sign==1: basis=order.quantity*order.price+fee
            else: realized+=order.quantity*order.price-fee-basis; basis=0
            qty+=sign*order.quantity
            fees+=fee; slip+=order.quantity*abs(order.price-row.Open); turnover+=order.quantity*order.price
        market=qty*row.Close; equity=cash+market; peak=max(peak,equity)
        expected={'cash':cash,'quantity':qty,'market_value':market,'equity':equity,'realized_pnl':realized,'unrealized_pnl':market-basis,'fees':fees,'slippage':slip,'turnover_notional':turnover,'drawdown':equity/peak-1}
        for k,v in expected.items(): assert result['ledger'].iloc[j][k]==pytest.approx(v,abs=1e-7,rel=1e-10)
        assert equity-c['initial_cash']==pytest.approx(realized+market-basis,abs=1e-7)
    m=metrics(result,c); l=result['ledger']
    assert m['exposicao_media']==pytest.approx(np.mean(l.quantity*d.Close/l.equity))
    assert m['tempo_posicionado']==pytest.approx(sum(l.quantity>0)/len(d))
    assert m['turnover']==pytest.approx(turnover/c['initial_cash'])
    assert m['custo_total']==pytest.approx(fees+slip)


def test_gap_lot_open_position_and_initial_drawdown(c):
    d=synthetic(c).iloc[:3].copy(); d['Open']=[10.,20.,20.]; d['Close']=[10.,18.,19.]
    c.update(initial_cash=101.,allocation=1.,lot_size=2,fixed_fee=1.,fee_bps=0.,slippage_bps=0.)
    sig=pd.DataFrame({'buy':[True,True,False],'sell':[False]*3})
    r=backtest(d,c,'ema',sig); l=r['ledger']; m=metrics(r,c)
    assert l.quantity.tolist()==[0,4,4]; assert l.cash.tolist()==[101,20,20]
    assert l.equity.tolist()==[101,92,96]
    assert l.drawdown.iloc[1]==pytest.approx(92/101-1)
    assert m['pnl_nao_realizado']==-5; assert m['pnl_realizado']==0
    assert m['operacoes_fechadas']==0; assert m['quantidade_aberta']==4


def test_simultaneous_signals_and_liquidation_priority(c):
    d=synthetic(c).iloc[:36]; sig=pd.DataFrame({'buy':True,'sell':True},index=d.index)
    r=backtest(d,c,'ema',sig); o=r['orders']
    assert o.side.iloc[:4].tolist()==['BUY','SELL','BUY','SELL']
    assert (o.timestamp.dt.strftime('%H:%M')<=c['liquidation_time']).all()
    assert o.iloc[-1].reason=='session'
    assert r['ledger'].quantity.iloc[-1]==0

@pytest.mark.parametrize('strategy',['ema','rsi','session_hold'])
def test_prefix_all_artifacts_at_session_boundary(c,strategy):
    d=synthetic(c); a=backtest(d,c,strategy)
    for length in (1,20,34,35,36,37,72,73):
        b=backtest(d.iloc[:length],c,strategy)
        for k in ('ledger','signals','indicators'): pd.testing.assert_frame_equal(a[k].iloc[:length],b[k])
        for k,timecol in [('orders','timestamp'),('trades','exit')]:
            pd.testing.assert_frame_equal(a[k][a[k][timecol]<=d.timestamp.iloc[length-1]].reset_index(drop=True),b[k],check_dtype=False)

@pytest.mark.parametrize('fault',['infinity','zero_price','second_asset','missing_column','absent_day','off_grid'])
def test_more_data_rejections(c,fault):
    d=synthetic(c)
    if fault=='infinity': d.loc[0,'Volume']=np.inf
    elif fault=='zero_price': d.loc[0,'Open']=0
    elif fault=='second_asset': d.loc[0,'asset']='OTHER'
    elif fault=='missing_column': d=d.drop(columns='Volume')
    elif fault=='absent_day': d=d[d.session!=c['session_dates'][1]]
    else: d.loc[0,'timestamp']+=pd.Timedelta(seconds=1)
    with pytest.raises(ValueError): validate_data(d,c)

def test_research_retains_reproducible_source(c,tmp_path):
    out,_,_=run_research(synthetic(c),c,tmp_path)
    manifest=json.loads((out/'manifest.json').read_text())
    assert (out/'source/trading_lab/backtest.py').is_file()
    assert (out/'source/strategies/ema/SPEC.md').is_file()
    assert manifest['spec_sha256']
    assert manifest['test_sample_status']=='synthetic_previously_observed'
