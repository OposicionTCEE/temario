# Generador de las figuras TikZ de la tanda A7 del anexo II (3.B.25): anx_sonrisa, anx_garch, anx_ciclo_arbitraje y
# anx_base_divisas. Escribe los .tikz con los valores calculados (parámetros en la cabecera de cada figura) y no necesita
# librerías externas.
# Uso, desde la carpeta del tema:  python3 Code/generar_figuras_A7.py Img
#   y después, para cada figura:  bash Code/generar_figura.sh anx_sonrisa  (etc.)

import math, random, sys
out = sys.argv[1]
N = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))


def coords(pts):
    return " ".join(f"({a:.3f},{b:.3f})" for a, b in pts)


def w(name, body):
    open(f"{out}/{name}.tikz", "w", encoding="utf-8").write(body)


# ---------- anx_sonrisa: modelo de saltos de MERTON (1976) ----------
def bs(S, K, r, s, T):
    d1 = (math.log(S / K) + (r + 0.5 * s * s) * T) / (s * math.sqrt(T)); d2 = d1 - s * math.sqrt(T)
    return S * N(d1) - K * math.exp(-r * T) * N(d2)


def merton(S, K, r, s, T, lam, m, nu):
    k = math.exp(m + 0.5 * nu * nu) - 1; lp = lam * (1 + k); tot = 0
    for n in range(0, 60):
        sn = math.sqrt(s * s + n * nu * nu / T); rn = r - lam * k + n * math.log(1 + k) / T
        tot += math.exp(-lp * T) * (lp * T) ** n / math.factorial(n) * bs(S, K, rn, sn, T)
    return tot


def iv(price, S, K, r, T):
    lo, hi = 1e-4, 3.0
    for _ in range(100):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if bs(S, K, r, mid, T) < price else (lo, mid)
    return (lo + hi) / 2


r, T = 0.02, 0.25
ACC = dict(s=0.13, lam=0.6, m=-0.12, nu=0.10)   # acciones: saltos a la baja
DIV = dict(s=0.07, lam=1.0, m=0.0, nu=0.05)     # divisas: saltos simétricos
Ks = [0.80 + 0.02 * i for i in range(0, 21)]
X1 = lambda K: (K - 0.8) * 12
Y1 = lambda v: (v - 0.06) * 15
eq = coords([(X1(K), Y1(iv(merton(1, K, r, ACC['s'], T, ACC['lam'], ACC['m'], ACC['nu']), 1, K, r, T))) for K in Ks])
fx = coords([(X1(K), Y1(iv(merton(1, K, r, DIV['s'], T, DIV['lam'], DIV['m'], DIV['nu']), 1, K, r, T))) for K in Ks])
atm = iv(merton(1, 1, r, ACC['s'], T, ACC['lam'], ACC['m'], ACC['nu']), 1, 1, r, T)
k = math.exp(ACC['m'] + 0.5 * ACC['nu'] ** 2) - 1


def dmerton(x):
    tot = 0
    for n in range(0, 40):
        wgt = math.exp(-ACC['lam'] * T) * (ACC['lam'] * T) ** n / math.factorial(n)
        mu = (r - ACC['lam'] * k - 0.5 * ACC['s'] ** 2) * T + n * ACC['m']; var = ACC['s'] ** 2 * T + n * ACC['nu'] ** 2
        tot += wgt * math.exp(-(math.log(x) - mu) ** 2 / (2 * var)) / (x * math.sqrt(2 * math.pi * var))
    return tot


def dlogn(x, sig):
    mu = (r - 0.5 * sig * sig) * T; var = sig * sig * T
    return math.exp(-(math.log(x) - mu) ** 2 / (2 * var)) / (x * math.sqrt(2 * math.pi * var))


xs = [0.60 + 0.01 * i for i in range(0, 71)]
X2 = lambda x: (x - 0.6) * 6.5
Y2 = lambda d: d / 5.5 * 2.8
DM = coords([(X2(x), Y2(dmerton(x))) for x in xs])
DL = coords([(X2(x), Y2(dlogn(x, atm))) for x in xs])
TAIL = coords([(X2(x), Y2(dmerton(x))) for x in xs if x <= 0.851])
w("anx_sonrisa", r"""% Figura (Anexo II, «Sonrisa y sesgo»): (a) volatilidad implícita de BLACK-SCHOLES frente al precio de ejercicio relativo,
% K/S_0, con sesgo en un índice bursátil (continua: saltos a la baja) y sonrisa en una divisa (discontinua: saltos
% simétricos); si el modelo de BLACK-SCHOLES fuera cierto, las dos serían horizontales. (b) Densidad neutral al riesgo de
% S_T/S_0 con saltos (continua) frente a la lognormal con la volatilidad en el dinero (discontinua); la cola izquierda
% sombreada es más gruesa (probabilidad de terminar por debajo de 0,8: 2,3 % frente a 0,2 %). Precios calculados con el
% modelo de saltos de MERTON (1976), T = 0,25 y r = 2 %: acciones sigma = 13 %, lambda = 0,6, salto medio del logaritmo
% -0,12 y desviación 0,10; divisas sigma = 7 %, lambda = 1, salto medio 0 y desviación 0,05.
% Generar con: bash Code/generar_figura.sh anx_sonrisa
\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]
  % ---------------- (a) Volatilidad implícita ----------------
  \begin{scope}
    \node[font=\footnotesize\bfseries] at (2.4,3.55) {(a) Volatilidad implícita};
    \draw[->] (0,0) -- (5.1,0) node[below] {$K/S_0$};
    \draw[->] (0,0) -- (0,3.2) node[left] {$\sigma_{\text{imp}}$};
    \draw[very thick] plot[smooth] coordinates {""" + eq + r"""};
    \draw[very thick, dashed] plot[smooth] coordinates {""" + fx + r"""};
    \foreach \x/\l in {1.2/{0{,}9}, 2.4/1, 3.6/{1{,}1}} { \draw (\x,0.06) -- (\x,-0.06); \node[below] at (\x,0) {$\l$}; }
    \node[anchor=west] at (0.25,2.95) {acciones};
    \node[anchor=east] at (4.8,1.0) {divisas};
  \end{scope}
  % ---------------- (b) Densidad neutral al riesgo ----------------
  \begin{scope}[xshift=7.3cm]
    \node[font=\footnotesize\bfseries] at (2.3,3.55) {(b) Densidad neutral al riesgo};
    \fill[black!20] (0,0) -- plot[smooth] coordinates {""" + TAIL + r"""} -- (""" + f"{X2(0.85):.3f}" + r""",0) -- cycle;
    \draw[->] (0,0) -- (4.8,0) node[below] {$S_T/S_0$};
    \draw[->] (0,0) -- (0,3.2);
    \draw[very thick] plot[smooth] coordinates {""" + DM + r"""};
    \draw[very thick, dashed] plot[smooth] coordinates {""" + DL + r"""};
    \draw (""" + f"{X2(1.0):.3f}" + r""",0.06) -- (""" + f"{X2(1.0):.3f}" + r""",-0.06); \node[below] at (""" + f"{X2(1.0):.3f}" + r""",0) {$1$};
    \node[anchor=east] at (""" + f"{X2(0.93):.3f},{Y2(3.6):.3f}" + r""") {saltos};
    \node[anchor=west] at (""" + f"{X2(1.12):.3f},{Y2(2.4):.3f}" + r""") {lognormal};
  \end{scope}
\end{tikzpicture}
""")

# ---------- anx_garch: rentabilidades con volatilidad constante y con GARCH(1,1) ----------
random.seed(3)
n, om, al, be = 250, 0.05, 0.10, 0.85
z = [random.gauss(0, 1) for _ in range(n)]
s2 = om / (1 - al - be); rg = []; sg = []
for t in range(n):
    sig = math.sqrt(s2); e = sig * z[t]; rg.append(e); sg.append(sig)
    s2 = om + al * e * e + be * s2
sx, sy = 0.024, 0.30
def bars(vals):
    return "\n".join(f"    \\draw[black!60] ({t*sx:.3f},0) -- ({t*sx:.3f},{v*sy:.3f});" for t, v in enumerate(vals))
band = coords([(t * sx, 2 * s * sy) for t, s in enumerate(sg)])
bandn = coords([(t * sx, -2 * s * sy) for t, s in enumerate(sg)])
lim = max(max(abs(v) for v in z), max(abs(v) for v in rg)) * sy
w("anx_garch", r"""% Figura (Anexo II, «Volatilidad aleatoria»): 250 rentabilidades simuladas con las mismas sorpresas normales y la misma
% varianza media (igual a 1). (a) Volatilidad constante. (b) GARCH(1,1) de BOLLERSLEV (1986) con omega = 0,05, alpha = 0,10 y
% beta = 0,85: las variaciones grandes se agrupan; las discontinuas son más y menos dos desviaciones típicas condicionales.
% Semilla 3 (Python, random.gauss).
% Generar con: bash Code/generar_figura.sh anx_garch
\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]
  % ---------------- (a) Volatilidad constante ----------------
  \begin{scope}
    \node[font=\footnotesize\bfseries] at (3.0,""" + f"{lim+0.45:.3f}" + r""") {(a) Volatilidad constante};
""" + bars(z) + r"""
    \draw[->] (0,0) -- (6.25,0) node[below] {$t$};
    \draw[->] (0,""" + f"{-lim-0.1:.3f}" + r""") -- (0,""" + f"{lim+0.15:.3f}" + r""") node[left] {$R_t$};
  \end{scope}
  % ---------------- (b) GARCH(1,1) ----------------
  \begin{scope}[xshift=7.1cm]
    \node[font=\footnotesize\bfseries] at (3.0,""" + f"{lim+0.45:.3f}" + r""") {(b) GARCH(1,1)};
""" + bars(rg) + r"""
    \draw[dashed] plot coordinates {""" + band + r"""};
    \draw[dashed] plot coordinates {""" + bandn + r"""};
    \draw[->] (0,0) -- (6.25,0) node[below] {$t$};
    \draw[->] (0,""" + f"{-lim-0.1:.3f}" + r""") -- (0,""" + f"{lim+0.15:.3f}" + r""") node[left] {$R_t$};
  \end{scope}
\end{tikzpicture}
""")

# ---------- anx_ciclo_arbitraje ----------
w("anx_ciclo_arbitraje", r"""% Figura (Anexo II, «Capital del arbitrajista»): ciclo de los límites del arbitraje (SHLEIFER y VISHNY, 1997): si el desajuste
% se amplía, el arbitrajista pierde, sus inversores retiran fondos y sus acreedores piden más garantías, tiene que vender sus
% posiciones y el desajuste se amplía todavía más.
% Generar con: bash Code/generar_figura.sh anx_ciclo_arbitraje
\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=5pt]},
    caja/.style={draw, rounded corners=2pt, text width=2.9cm, align=center, minimum height=0.9cm}]
  \node[caja] (A) at (0,1.75) {Se amplía el desajuste};
  \node[caja] (B) at (3.4,0) {Pérdidas del arbitrajista};
  \node[caja] (C) at (0,-1.75) {Retirada de fondos y más garantías};
  \node[caja] (D) at (-3.4,0) {Venta forzosa de las posiciones};
  \draw[->, thick] (A.east) to[out=0, in=90] (B.north);
  \draw[->, thick] (B.south) to[out=-90, in=0] (C.east);
  \draw[->, thick] (C.west) to[out=180, in=-90] (D.south);
  \draw[->, thick] (D.north) to[out=90, in=180] (A.west);
\end{tikzpicture}
""")

# ---------- anx_base_divisas ----------
Qbar, cap = 2.5, 1.6
sup = lambda q: 0.0 if q <= Qbar else 0.6 * (q - Qbar) ** 1.5
qcross = Qbar + (cap / 0.6) ** (2 / 3)
rise = coords([(Qbar + 0.05 * i, sup(Qbar + 0.05 * i)) for i in range(0, int((qcross - Qbar) / 0.05) + 1)] + [(qcross, cap)])
over = coords([(qcross + 0.05 * i, sup(qcross + 0.05 * i)) for i in range(0, 9)])
lo, hi = Qbar, 4.0
for _ in range(60):
    m = (lo + hi) / 2
    lo, hi = (m, hi) if 4.0 - m > sup(m) else (lo, m)
qe = (lo + hi) / 2; ye = 4.0 - qe
w("anx_base_divisas", r"""% Figura (Anexo II, «Paridad cubierta»): mercado de dólares sintéticos (FX swaps). Los arbitrajistas los ofrecen sin
% prima mientras tienen balance libre, hasta \bar Q; después, a un coste creciente (continua). Con la demanda D_1, la base es
% nula; con D_2, la base, -x^*, es el coste del balance. La línea swap del banco central pone un techo (discontinua).
% Valores ilustrativos: oferta 0,6 (Q - 2,5)^{1,5} desde \bar Q = 2,5; techo 1,6; D_1 = 2 - Q; D_2 = 4 - Q.
% Generar con: bash Code/generar_figura.sh anx_base_divisas
\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}, x=1.15cm, y=1.15cm]
  \draw[->] (0,0) -- (5.3,0) node[below] {$Q$};
  \draw[->] (0,0) -- (0,2.55) node[left] {$-x$};
  \draw[very thick] (0,0) -- (""" + f"{Qbar}" + r""",0) plot[smooth] coordinates {""" + rise + r"""} -- (5.0,""" + f"{cap}" + r""");
  \draw[dotted] plot[smooth] coordinates {""" + over + r"""};
  \draw[dashed] (0,""" + f"{cap}" + r""") -- (""" + f"{qcross:.3f},{cap}" + r""");
  \node[anchor=east] at (0,""" + f"{cap}" + r""") {línea swap};
  \draw (0.3,1.7) -- (2.0,0);
  \node[anchor=south] at (0.3,1.7) {$D_1$};
  \draw (2.0,2.0) -- (4.0,0);
  \node[anchor=south] at (2.0,2.0) {$D_2$};
  \fill (2.0,0) circle (1.6pt);
  \fill (""" + f"{qe:.3f},{ye:.3f}" + r""") circle (1.6pt);
  \draw[dotted] (0,""" + f"{ye:.3f}) -- ({qe:.3f},{ye:.3f}" + r""");
  \node[anchor=east] at (0,""" + f"{ye:.3f}" + r""") {$-x^*$};
  \draw (""" + f"{Qbar}" + r""",0.05) -- (""" + f"{Qbar}" + r""",-0.05); \node[below] at (""" + f"{Qbar}" + r""",0) {$\bar Q$};
\end{tikzpicture}
""")
print("atm", atm, "qe", qe, "ye", ye, "qcross", qcross, "lim", lim)
