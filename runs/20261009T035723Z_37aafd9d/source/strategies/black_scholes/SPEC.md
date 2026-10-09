# P01 — preços e Greeks europeus; experimento isolado

Congelada em 07/10/2026, antes da primeira execução. Não integra o motor intraday.
Fonte S044, Martin Haugh, The Black-Scholes Model (2016): página física 2,
equações 9–12; p.3 eq.13 (dividendos); p.7 delta; p.8 gamma; p.9 vega/theta.
Fórmulas conferidas nas páginas originais. Put e rho derivados por paridade e
diferenciação: adaptações matemáticas explícitas, não outra estratégia empírica.

Entradas escalares S>0 e K>0 na mesma moeda; T>=0 em anos; sigma>=0 por raiz de ano;
r e q taxas contínuas anuais, inclusive negativas. Todos finitos; bool rejeitado.
Dividendos contínuos q; opção europeia, sem exercício antecipado, custos ou jumps.

d1=(ln(S/K)+(r-q+sigma²/2)T)/(sigma sqrt(T)), d2=d1-sigma sqrt(T).
C=S exp(-qT)N(d1)-K exp(-rT)N(d2); P pela expressão simétrica.
Em T=0, payoff intrínseco; em sigma=0, payoff determinístico descontado.
Delta por unidade de spot, gamma por spot², vega por 1.0 de sigma (não 1%),
rho por 1.0 de r. Theta=-dV/dT por ano de passagem do calendário, não por dia.
Greeks em T=0 ou sigma=0 são rejeitados explicitamente (convenções singulares fora
do escopo), embora preços nesses limites sejam definidos. Não inferir IV no vencimento.

Tolerâncias antes dos testes: preço conhecido atol=1e-10; paridade/bounds 1e-9;
quadratura independente da expectativa descontada atol=1e-7, rtol=1e-9;
diferenças finitas delta/vega/rho/theta rtol=2e-5, atol=2e-6; gamma atol=2e-6.
Referência independente: integração Gauss-Legendre de payoff lognormal, dividida
no strike e truncada a +/-12 desvios padrão, 128 pontos. Não usar função BS no oráculo.
Casos: call/put, ITM/ATM/OTM, q não zero, r negativo, limites, homogeneidade,
monotonicidade em volatilidade e convexidade. Resultado valida numericamente os
casos testados, não calibração ou eficácia real. Domínios extremos próximos de
overflow/underflow de float64 não são certificados.

P02 (IV) exige P01 aprovado e SPEC própria. P03/P04/P05 não são entregues por
implicação deste documento. Sem dados reais de opções, validação empírica bloqueada.
