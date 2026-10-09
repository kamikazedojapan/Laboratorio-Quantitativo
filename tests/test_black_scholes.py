import math
import numpy as np
import pytest
from trading_lab.black_scholes import price, greeks


def quadrature(s,k,t,r,v,q,kind):
    # Risk-neutral terminal distribution and payoff, no N(d1)/N(d2) formula.
    cut=(math.log(k/s)-(r-q-v*v/2)*t)/(v*math.sqrt(t))
    lo,hi=(max(-12,cut),12) if kind=='call' else (-12,min(12,cut))
    if hi<=lo: return 0.
    x,w=np.polynomial.legendre.leggauss(128)
    z=(hi-lo)*x/2+(lo+hi)/2
    terminal=s*np.exp((r-q-v*v/2)*t+v*math.sqrt(t)*z)
    payoff=np.maximum((terminal-k)*(1 if kind=='call' else -1),0)
    return math.exp(-r*t)*(hi-lo)/2*np.dot(w,payoff*np.exp(-z*z/2)/math.sqrt(2*math.pi))


@pytest.mark.parametrize('kind,expected',[('call',10.450583572185565),('put',5.573526022256971)])
def test_known_price(kind,expected):
    assert price(100,100,1,.05,.2,kind=kind)==pytest.approx(expected,abs=1e-10)


@pytest.mark.parametrize('kind',['call','put'])
@pytest.mark.parametrize('s,k,t,r,v,q',[(80,100,.2,-.01,.4,.03),(100,100,1,.05,.2,0),(130,100,2,.01,.15,.06),(50,60,.01,.02,.8,.01)])
def test_quadrature_reference(s,k,t,r,v,q,kind):
    assert price(s,k,t,r,v,q,kind)==pytest.approx(quadrature(s,k,t,r,v,q,kind),abs=1e-7,rel=1e-9)


@pytest.mark.parametrize('kind',['call','put'])
@pytest.mark.parametrize('s,k,t,r,v,q',[(80,100,.2,-.01,.4,.03),(100,100,1,.05,.2,0),(130,100,2,.01,.15,.06)])
def test_finite_difference_greeks(s,k,t,r,v,q,kind):
    args=[s,k,t,r,v,q,kind]; g=greeks(*args)
    for index,key,h,sign in [(0,'delta',s*1e-5,1),(2,'theta',1e-5,-1),(3,'rho',1e-5,1),(4,'vega',1e-5,1)]:
        a,b=args.copy(),args.copy();a[index]+=h;b[index]-=h
        fd=sign*(price(*a)-price(*b))/(2*h)
        assert g[key]==pytest.approx(fd,rel=2e-5,abs=2e-6)
    h=s*1e-4
    fd2=(price(s+h,k,t,r,v,q,kind)-2*price(*args)+price(s-h,k,t,r,v,q,kind))/(h*h)
    assert g['gamma']==pytest.approx(fd2,abs=2e-6)


@pytest.mark.parametrize('s',[40.,100.,240.])
@pytest.mark.parametrize('v',[0.,.1,.8])
def test_parity_bounds_and_homogeneity(s,v):
    k,t,r,q=100,1.3,-.02,.04
    a,b=price(s,k,t,r,v,q),price(s,k,t,r,v,q,'put')
    ds,dk=s*math.exp(-q*t),k*math.exp(-r*t)
    assert a-b==pytest.approx(ds-dk,abs=1e-9)
    assert max(ds-dk,0)-1e-9<=a<=ds+1e-9
    assert max(dk-ds,0)-1e-9<=b<=dk+1e-9
    assert price(3*s,3*k,t,r,v,q)==pytest.approx(3*a,abs=1e-9)


def test_limits_and_convexity():
    assert price(110,100,0,.03,.2)==10
    assert price(90,100,0,.03,.2,kind='put')==10
    assert price(100,100,1,0,0)==0
    assert price(100,100,1,.05,0)==pytest.approx(100-100*math.exp(-.05))
    vals=[price(100,100,1,.03,v) for v in [0,.01,.1,.2,1]]
    assert vals==sorted(vals)
    assert price(99,100,1,.03,.2)+price(101,100,1,.03,.2)>=2*price(100,100,1,.03,.2)
    for t,v in [(0,.2),(1,0)]:
        with pytest.raises(ValueError): greeks(100,100,t,.03,v)


@pytest.mark.parametrize('index,bad',[(0,0),(1,-1),(2,-1),(4,-1),(0,float('nan')),(3,float('inf')),(5,True),(6,'american')])
def test_invalid_inputs(index,bad):
    a=[100.,100.,1.,.05,.2,0.,'call'];a[index]=bad
    with pytest.raises(ValueError):price(*a)
    with pytest.raises(ValueError):greeks(*a)
