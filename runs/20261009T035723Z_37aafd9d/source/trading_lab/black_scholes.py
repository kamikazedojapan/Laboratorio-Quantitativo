"""Isolated European Black-Scholes calculator. See strategies/black_scholes/SPEC.md."""
from math import erfc, exp, isfinite, log, pi, sqrt
from numbers import Real


def _inputs(spot, strike, maturity, rate, volatility, dividend, kind):
    values = (spot, strike, maturity, rate, volatility, dividend)
    if any(isinstance(x, bool) or not isinstance(x, Real) or not isfinite(x) for x in values):
        raise ValueError('Parameters must be finite real numbers, not booleans')
    if spot <= 0 or strike <= 0 or maturity < 0 or volatility < 0:
        raise ValueError('Require S,K > 0 and T,sigma >= 0')
    if kind not in ('call', 'put'):
        raise ValueError('kind must be call or put')


def _cdf(x):
    return .5 * erfc(-x / sqrt(2))


def price(spot, strike, maturity, rate, volatility, dividend=0., kind='call'):
    _inputs(spot, strike, maturity, rate, volatility, dividend, kind)
    side = 1 if kind == 'call' else -1
    if maturity == 0:
        return max(side*(spot-strike), 0.)
    s, k = spot*exp(-dividend*maturity), strike*exp(-rate*maturity)
    if volatility == 0:
        return max(side*(s-k), 0.)
    vol = volatility*sqrt(maturity)
    d1 = (log(spot)-log(strike)+(rate-dividend)*maturity)/vol + vol/2
    d2 = d1-vol
    return max(side*(s*_cdf(side*d1)-k*_cdf(side*d2)), 0.)


def greeks(spot, strike, maturity, rate, volatility, dividend=0., kind='call'):
    _inputs(spot, strike, maturity, rate, volatility, dividend, kind)
    if maturity == 0 or volatility == 0:
        raise ValueError('Greeks require positive maturity and volatility')
    side = 1 if kind == 'call' else -1
    root = sqrt(maturity)
    vol = volatility*root
    d1 = (log(spot)-log(strike)+(rate-dividend)*maturity)/vol + vol/2
    d2 = d1-vol
    dq, dr = exp(-dividend*maturity), exp(-rate*maturity)
    density = exp(-d1*d1/2)/sqrt(2*pi)
    return dict(delta=side*dq*_cdf(side*d1),
        gamma=dq*density/(spot*vol),
        vega=spot*dq*density*root,
        theta=-spot*dq*density*volatility/(2*root)
              +side*dividend*spot*dq*_cdf(side*d1)-side*rate*strike*dr*_cdf(side*d2),
        rho=side*strike*maturity*dr*_cdf(side*d2))
