# Datos de las figuras de la tanda A5 del anexo II (3.B.25), que se copiaron en los .tikz correspondientes:
#   anx_cotas      precios de BLACK-SCHOLES de call y put con K = 2, e^{-rT} = 0,8 y sigma raíz de T = 0,8, y el punto
#                  \bar S en que la put europea cae por debajo de su valor intrínseco.
#   anx_arbol      precio binomial de COX-ROSS-RUBINSTEIN de una call con n = 1, ..., 60 periodos (S_0 = K = 100,
#                  r = 5 %, sigma = 20 %, T = 1), frente al de BLACK-SCHOLES (10,45); en la figura, desplazado (c_n - 9,3).
#   anx_frontera   put americana (árbol de 300 periodos) y europea con K = 100, r = 10 %, sigma = 25 %, T = 1, escaladas
#                  (dividido por 50, K = 2); la frontera de ejercicio de la figura es una forma estilizada ajustada a la
#                  del árbol, S^*(t) = K [1 - 0,19 ((T - t)/T)^{0,25}].
#   anx_lognormal  cuatro trayectorias de un movimiento browniano geométrico (S_0 = 1, mu = 8 %, sigma = 35 %, T = 4,
#                  160 pasos, semilla 21; eje de tiempo multiplicado por 1,375) y la densidad lognormal de S_T.
#   anx_bsm        densidad neutral al riesgo (multiplicada por 3) y precio de la call con S_0 = 2, K = 2,4, rT = 0,05,
#                  sigma raíz de T = 0,4.
# La figura anx_binomial no usa datos calculados (S_0 d = 1,2, S_0 u = 3, K = 2).
# Uso, desde la carpeta del tema:  python3 Code/datos_figuras_A5.py
import math, random

N = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))


def bs(S, K, r, sig, T, tipo="c"):
    if S <= 0:
        return 0.0 if tipo == "c" else K * math.exp(-r * T)
    d1 = (math.log(S / K) + (r + 0.5 * sig * sig) * T) / (sig * math.sqrt(T))
    d2 = d1 - sig * math.sqrt(T)
    if tipo == "c":
        return S * N(d1) - K * math.exp(-r * T) * N(d2)
    return K * math.exp(-r * T) * N(-d2) - S * N(-d1)


def crr(S, K, r, sig, T, n, tipo="c", americana=False):
    dt = T / n
    u = math.exp(sig * math.sqrt(dt)); d = 1 / u
    q = (math.exp(r * dt) - d) / (u - d); desc = math.exp(-r * dt)
    pago = (lambda x: max(x - K, 0)) if tipo == "c" else (lambda x: max(K - x, 0))
    v = [pago(S * u ** j * d ** (n - j)) for j in range(n + 1)]
    for i in range(n - 1, -1, -1):
        v = [desc * (q * v[j + 1] + (1 - q) * v[j]) for j in range(i + 1)]
        if americana:
            v = [max(v[j], pago(S * u ** j * d ** (i - j))) for j in range(i + 1)]
    return v[0]


def coords(pts):
    return " ".join(f"({a:.3f},{b:.3f})" for a, b in pts)


# ---- anx_cotas
K, rT, s = 2.0, math.log(1.25), 0.8
print("anx_cotas call:", coords([(x, bs(x, K, rT, s, 1)) for x in [0.1 * i for i in range(1, 37)]]))
print("anx_cotas put:", coords([(x, bs(x, K, rT, s, 1, "p")) for x in [0.1 * i for i in range(0, 37)]]))
lo, hi = 0.01, 2.0
for _ in range(60):
    m = (lo + hi) / 2
    lo, hi = (m, hi) if bs(m, K, rT, s, 1, "p") < K - m else (lo, m)
print("anx_cotas Sbar:", round((lo + hi) / 2, 3))

# ---- anx_arbol
print("anx_arbol BS:", round(bs(100, 100, 0.05, 0.2, 1), 4))
print("anx_arbol CRR:", " ".join(f"({n},{crr(100, 100, 0.05, 0.2, 1, n) - 9.3:.3f})" for n in range(1, 61)))

# ---- anx_frontera (precios divididos por 50)
Ss = [10, 20, 30, 40, 50, 60, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120, 130, 140, 150, 160, 170, 180, 190, 200]
print("anx_frontera americana:", " ".join(f"({S/50:.2f},{crr(S, 100, 0.10, 0.25, 1, 300, 'p', True)/50:.3f})" for S in Ss))
print("anx_frontera europea:", " ".join(f"({S/50:.2f},{bs(S, 100, 0.10, 0.25, 1, 'p')/50:.3f})" for S in Ss))

# ---- anx_lognormal
random.seed(21)
mu, sig, T, n = 0.08, 0.35, 4.0, 160
dt = T / n
for k in range(4):
    S = 1.0; pts = [(0.0, S)]
    for i in range(1, n + 1):
        S *= math.exp((mu - 0.5 * sig * sig) * dt + sig * math.sqrt(dt) * random.gauss(0, 1))
        pts.append((i * dt, S))
    print(f"anx_lognormal trayectoria {k}:", " ".join(f"({t*1.375:.3f},{x:.3f})" for t, x in pts[::2]))
m, sd = (mu - 0.5 * sig * sig) * T, sig * math.sqrt(T)
dens = lambda x: math.exp(-(math.log(x) - m) ** 2 / (2 * sd * sd)) / (x * sd * math.sqrt(2 * math.pi))
print("anx_lognormal densidad (x = 5,5 + 2 f(S), S):", " ".join(f"({5.5 + 2*dens(x):.3f},{x:.2f})" for x in [0.05 * i for i in range(1, 57)]))

# ---- anx_bsm
S0, KK, rr, sg = 2.0, 2.4, 0.05, 0.4
mq = math.log(S0) + rr - 0.5 * sg * sg
dq = lambda x: math.exp(-(math.log(x) - mq) ** 2 / (2 * sg * sg)) / (x * sg * math.sqrt(2 * math.pi))
print("anx_bsm densidad x3:", coords([(x, 3 * dq(x)) for x in [0.2 * i for i in range(1, 26)]]))
print("anx_bsm call:", coords([(x, bs(x, KK, rr, sg, 1)) for x in [0.2 * i for i in range(3, 22)]]))
d1 = (math.log(S0 / KK) + rr + 0.5 * sg * sg) / sg
print("anx_bsm N(d1), K e^{-rT} N(d2):", round(N(d1), 3), round(KK * math.exp(-rr) * N(d1 - sg), 3))
