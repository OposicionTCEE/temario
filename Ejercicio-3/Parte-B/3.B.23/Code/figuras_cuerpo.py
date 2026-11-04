"""Figuras del cuerpo del 3.B.23 (T11-T13): esquemas abstractos, con letras y sin cifras, cada uno para el apartado
que lo comenta. Las versiones con números del ejemplo están en los anexos (figuras_anexo1.py y siguientes).

Uso, desde la carpeta del tema:  python3 -B Code/figuras_cuerpo.py [b1]  y después  bash Code/generar_figura.sh <nombre>
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figuras_anexo1 import PREAMBULO_EJES, escribir_tikz  # noqa: E402

PLANO = (r"xlabel={Volatilidad, $\sigma_p$}, ylabel={Rentabilidad esperada, $\mu_p$}, xtick=\empty, ytick=\empty, "
         + PREAMBULO_EJES)

# Frontera abstracta de los esquemas del bloque 1: hipérbola sigma(mu) = raíz de (s0² + (mu - m0)²/k²).
S0, M0, K = 0.25, 0.40, 1.1
RF = 0.12


def _coords(x, y):
    return " ".join(f"({a:.4f},{b:.4f})" for a, b in zip(x, y))


def _sigma(mu):
    return np.sqrt(S0 ** 2 + (mu - M0) ** 2 / K ** 2)


def _tangente(rf=RF):
    """Cartera tangente a la frontera desde (0, rf): la de mayor pendiente (mu - rf)/sigma."""
    mu = np.linspace(M0, 1.6, 20001)
    pend = (mu - rf) / _sigma(mu)
    i = int(np.argmax(pend))
    return float(_sigma(mu[i])), float(mu[i]), float(pend[i])


def b1_residual():
    """B1, 1.1. El valor de los activos al vencimiento, V, se reparte entre los acreedores, que cobran mín(V, D), y los
    accionistas, que cobran lo que queda, máx(V - D, 0)."""
    D, V = 1.0, 2.4
    tikz = rf"""\begin{{tikzpicture}}
\begin{{axis}}[width=9.5cm, height=6.2cm, xmin=0, xmax={V}, ymin=0, ymax={V}, xtick={{{D}}}, xticklabels={{$D$}},
  ytick={{{D}}}, yticklabels={{$D$}}, xlabel={{Valor de los activos al vencimiento, $V$}}, ylabel={{Pago}},
  axis on top, {PREAMBULO_EJES}]
\fill[black!10] (axis cs:0,0) -- (axis cs:{D},{D}) -- (axis cs:{V},{D}) -- (axis cs:{V},0) -- cycle;
\fill[black!30] (axis cs:{D},{D}) -- (axis cs:{V},{V}) -- (axis cs:{V},{D}) -- cycle;
\addplot[thick, black] coordinates {{(0,0) ({V},{V})}};
\addplot[very thick, black] coordinates {{(0,0) ({D},{D}) ({V},{D})}};
\addplot[thin, black!50, dashed] coordinates {{({D},0) ({D},{D})}};
\node[font=\footnotesize] at (axis cs:1.75,0.45) {{Acreedores}};
\node[font=\footnotesize] at (axis cs:2.1,1.4) {{Accionistas}};
\end{{axis}}
\end{{tikzpicture}}
"""
    escribir_tikz("b1_residual", tikz)


def b1_dos_acciones():
    """B1, 1.2. Carteras de dos acciones A y B, con mu_A < mu_B y sigma_A < sigma_B, para tres correlaciones: la recta de
    rho = 1, la curva de rho = 0 y las dos rectas de rho = -1, que llegan al eje. Sin ventas en corto."""
    mA, sA, mB, sB = 0.30, 0.30, 0.75, 0.65
    w = np.linspace(0, 1, 401)
    mu = w * mA + (1 - w) * mB

    def sig(rho):
        return np.sqrt(np.maximum(w ** 2 * sA ** 2 + (1 - w) ** 2 * sB ** 2 + 2 * w * (1 - w) * rho * sA * sB, 0))

    w0 = sB / (sA + sB)
    m0 = w0 * mA + (1 - w0) * mB
    i0 = int(np.argmin(sig(0)))
    tikz = rf"""\begin{{tikzpicture}}
\begin{{axis}}[width=9.5cm, height=6.4cm, xmin=0, xmax=0.75, ymin=0.2, ymax=0.85, {PLANO}]
\addplot[very thick, black] coordinates {{{_coords(sig(1), mu)}}};
\addplot[thick, black, dashed] coordinates {{{_coords(sig(0), mu)}}};
\addplot[thick, black!60, dotted] coordinates {{({sA},{mA}) (0,{m0:.4f}) ({sB},{mB})}};
\addplot[only marks, mark=*, mark size=1.8pt, black] coordinates {{({sA},{mA}) ({sB},{mB})}};
\addplot[only marks, mark=square*, mark size=1.6pt, black] coordinates {{({sig(0)[i0]:.4f},{mu[i0]:.4f})}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{sA},{mA}) {{$A$}};
\node[anchor=south west, font=\footnotesize] at (axis cs:{sB},{mB}) {{$B$}};
\node[anchor=east, font=\footnotesize] at (axis cs:{sig(0)[i0] - 0.01:.4f},{mu[i0]:.4f}) {{$MV$}};
\node[anchor=north west, font=\scriptsize] at (axis cs:0.50,0.56) {{$\rho=1$}};
\node[anchor=west, font=\scriptsize] at (axis cs:0.31,0.45) {{$\rho=0$}};
\node[anchor=north west, font=\scriptsize] at (axis cs:0.08,0.37) {{$\rho=-1$}};
\end{{axis}}
\end{{tikzpicture}}
"""
    escribir_tikz("b1_dos_acciones", tikz)
    return w0, float(w[i0])


def b1_diversificacion():
    """B1, 1.3. Volatilidad de una cartera equiponderada de N acciones, raíz de sigma²/N + (1 - 1/N) cov, y su asíntota, la
    raíz de la covarianza media: lo que desaparece al diversificar es el riesgo específico y lo que queda, el
    sistemático."""
    var, cov, nmax = 1.0, 0.25, 40
    n = np.linspace(1, nmax, 400)
    s = np.sqrt(var / n + (1 - 1 / n) * cov)
    a = math.sqrt(cov)
    banda = _coords(n, s) + " " + _coords(n[::-1], np.full_like(n, a))
    tikz = rf"""\begin{{tikzpicture}}
\begin{{axis}}[width=9.5cm, height=6.2cm, xmin=1, xmax={nmax}, ymin=0, ymax=1.08, xtick={{1}}, xticklabels={{$1$}},
  ytick={{{a},1}}, yticklabels={{$\sqrt{{\bar\sigma_{{jk}}}}$,$\bar\sigma$}}, xlabel={{Número de acciones, $N$}},
  ylabel={{Volatilidad de la cartera, $\sigma_p$}}, axis on top, {PREAMBULO_EJES}]
\fill[black!10] plot coordinates {{{banda}}} -- cycle;
\fill[black!30] (axis cs:1,0) -- (axis cs:1,{a}) -- (axis cs:{nmax},{a}) -- (axis cs:{nmax},0) -- cycle;
\addplot[very thick, black] coordinates {{{_coords(n, s)}}};
\addplot[thick, black, dashed] coordinates {{(1,{a}) ({nmax},{a})}};
\node[font=\footnotesize] at (axis cs:{nmax * 0.55:.2f},{a + 0.09:.3f}) {{Riesgo específico}};
\node[font=\footnotesize] at (axis cs:{nmax * 0.55:.2f},{a / 2:.3f}) {{Riesgo sistemático}};
\end{{axis}}
\end{{tikzpicture}}
"""
    escribir_tikz("b1_diversificacion", tikz)


def b1_frontera():
    """B1, 1.4. Frontera de mínima varianza en el plano de volatilidad y rentabilidad esperada: hipérbola con la cartera
    de mínima varianza MV en su vértice, rama eficiente (por encima de MV) e ineficiente, y acciones en el interior."""
    mu_s = np.linspace(M0, 0.95, 200)
    mu_i = np.linspace(0.05, M0, 120)
    acciones = [(0.45, 0.35), (0.55, 0.62), (0.70, 0.78), (0.60, 0.45), (0.38, 0.50), (0.66, 0.30)]
    for s, m in acciones:
        assert s > _sigma(m), (s, m)
    tikz = rf"""\begin{{tikzpicture}}
\begin{{axis}}[width=9.5cm, height=6.4cm, xmin=0, xmax=0.85, ymin=0.05, ymax=0.95, legend pos=north west,
  legend style={{fill=none}}, {PLANO}]
\addplot[very thick, black] coordinates {{{_coords(_sigma(mu_s), mu_s)}}};
\addlegendentry{{Frontera eficiente}}
\addplot[thick, black, dashed] coordinates {{{_coords(_sigma(mu_i), mu_i)}}};
\addlegendentry{{Rama ineficiente}}
\addplot[only marks, mark=*, mark size=1.6pt, black!70] coordinates {{{" ".join(f"({s},{m})" for s, m in acciones)}}};
\addlegendentry{{Acciones}}
\addplot[only marks, mark=square*, mark size=1.8pt, black, forget plot] coordinates {{({S0},{M0})}};
\node[anchor=east, font=\footnotesize] at (axis cs:{S0 - 0.01},{M0}) {{$MV$}};
\end{{axis}}
\end{{tikzpicture}}
"""
    escribir_tikz("b1_frontera", tikz)


def b1_dos_fondos():
    """B1, 1.4. Propiedad de los dos fondos (BLACK, 1972): combinando dos carteras de la frontera, C1 y C2, con pesos ω y
    1 - ω se recorre la frontera entera; entre ellas con pesos positivos, más allá de C2 vendiendo en corto C1 (ω < 0) y
    hacia MV y la rama ineficiente vendiendo en corto C2 (ω > 1)."""
    m1, m2 = M0 + 0.15, M0 + 0.40
    s1, s2 = float(_sigma(m1)), float(_sigma(m2))
    tramo = np.linspace(m1, m2, 120)
    arriba = np.linspace(m2, 0.95, 80)
    abajo = np.linspace(0.05, m1, 160)
    todo = np.linspace(0.05, 0.95, 300)
    tikz = rf"""\begin{{tikzpicture}}
\begin{{axis}}[width=9.5cm, height=6.4cm, xmin=0, xmax=0.85, ymin=0.05, ymax=0.95, legend pos=south east,
  legend style={{fill=none}}, {PLANO}]
\addplot[line width=3pt, black!12, forget plot] coordinates {{{_coords(_sigma(todo), todo)}}};
\addplot[very thick, black] coordinates {{{_coords(_sigma(tramo), tramo)}}};
\addlegendentry{{Entre los dos fondos, $0\le\omega\le 1$}}
\addplot[thick, black, dashed] coordinates {{{_coords(_sigma(arriba), arriba)}}};
\addlegendentry{{Venta en corto de $C_1$, $\omega<0$}}
\addplot[thick, black, dotted] coordinates {{{_coords(_sigma(abajo), abajo)}}};
\addlegendentry{{Venta en corto de $C_2$, $\omega>1$}}
\addplot[only marks, mark=*, mark size=1.8pt, black, forget plot] coordinates {{({s1:.4f},{m1:.4f}) ({s2:.4f},{m2:.4f})}};
\addplot[only marks, mark=square*, mark size=1.8pt, black, forget plot] coordinates {{({S0},{M0})}};
\node[anchor=west, font=\footnotesize] at (axis cs:{s1 + 0.012:.4f},{m1:.4f}) {{$C_1$}};
\node[anchor=west, font=\footnotesize] at (axis cs:{s2 + 0.012:.4f},{m2:.4f}) {{$C_2$}};
\node[anchor=east, font=\footnotesize] at (axis cs:{S0 - 0.01},{M0}) {{$MV$}};
\end{{axis}}
\end{{tikzpicture}}
"""
    escribir_tikz("b1_dos_fondos", tikz)


def b1_tangente():
    """B1, 1.5. Desde el activo sin riesgo, las combinaciones con cada cartera de la frontera forman una recta cuya
    pendiente es su ratio de SHARPE; la de mayor pendiente toca la frontera en la cartera tangente T."""
    sT, mT, pT = _tangente()
    mu_s = np.linspace(M0, 0.95, 200)
    mE = M0 + 0.12
    sE = float(_sigma(mE))

    def recta(s, m, xmax=0.85):
        return f"(0,{RF}) ({xmax},{RF + xmax * (m - RF) / s:.4f})"

    tikz = rf"""\begin{{tikzpicture}}
\begin{{axis}}[width=9.5cm, height=6.4cm, xmin=0, xmax=0.85, ymin=0.05, ymax=0.95, legend pos=south east,
  legend style={{fill=none}}, {PLANO}]
\addplot[thick, black!40, forget plot] coordinates {{{_coords(_sigma(mu_s), mu_s)}}};
\addplot[thick, black!60, dashed] coordinates {{{recta(S0, M0)}}};
\addlegendentry{{Con $MV$}}
\addplot[thick, black!60, dash dot] coordinates {{{recta(sE, mE)}}};
\addlegendentry{{Con otra cartera eficiente}}
\addplot[very thick, black] coordinates {{{recta(sT, mT)}}};
\addlegendentry{{Con la tangente, $T$}}
\addplot[only marks, mark=square*, mark size=1.8pt, black, forget plot] coordinates {{({S0},{M0}) ({sE:.4f},{mE:.4f}) ({sT:.4f},{mT:.4f}) (0,{RF})}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{S0},{M0}) {{$MV$}};
\node[anchor=south east, font=\footnotesize] at (axis cs:{sT:.4f},{mT:.4f}) {{$T$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:0.01,{RF - 0.005}) {{$r_f$}};
\end{{axis}}
\end{{tikzpicture}}
"""
    escribir_tikz("b1_tangente", tikz)
    return sT, mT, pT


def b1_eleccion():
    """B1, 1.5. Dos inversores con utilidad de media y varianza eligen puntos distintos de la misma recta: el más averso
    presta parte de su riqueza (L, y = 1/2) y el menos averso se endeuda (E, y = 3/2); los dos tienen T."""
    sT, mT, pT = _tangente()
    mu_s = np.linspace(M0, 0.95, 200)
    curvas, puntos = [], []
    for y, estilo in ((0.5, "thick, black!70"), (1.5, "thick, black!70, dashed")):
        theta = (mT - RF) / (y * sT ** 2)
        s0, m0 = y * sT, RF + y * (mT - RF)
        u = m0 - theta / 2 * s0 ** 2
        s = np.linspace(0, 0.85, 120)
        curvas.append(rf"\addplot[{estilo}] coordinates {{{_coords(s, u + theta / 2 * s ** 2)}}};")
        puntos.append((s0, m0))
    tikz = rf"""\begin{{tikzpicture}}
\begin{{axis}}[width=9.5cm, height=6.4cm, xmin=0, xmax=0.85, ymin=0.05, ymax=1.05, legend pos=south east,
  legend style={{fill=none}}, {PLANO}]
\addplot[thick, black!25, forget plot] coordinates {{{_coords(_sigma(mu_s), mu_s)}}};
\addplot[very thick, black, forget plot] coordinates {{(0,{RF}) (0.85,{RF + 0.85 * pT:.4f})}};
{curvas[0]}
\addlegendentry{{Más averso}}
{curvas[1]}
\addlegendentry{{Menos averso}}
\addplot[only marks, mark=*, mark size=1.8pt, black, forget plot] coordinates {{({puntos[0][0]:.4f},{puntos[0][1]:.4f}) ({puntos[1][0]:.4f},{puntos[1][1]:.4f}) ({sT:.4f},{mT:.4f}) (0,{RF})}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{puntos[0][0]:.4f},{puntos[0][1]:.4f}) {{$L$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{puntos[1][0]:.4f},{puntos[1][1]:.4f}) {{$E$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{sT:.4f},{mT:.4f}) {{$T$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:0.01,{RF - 0.005}) {{$r_f$}};
\end{{axis}}
\end{{tikzpicture}}
"""
    escribir_tikz("b1_eleccion", tikz)


if __name__ == "__main__" and (len(sys.argv) == 1 or sys.argv[1] == "b1"):
    b1_residual()
    print("dos acciones: peso de A sin riesgo con rho = -1 y de mínima varianza con rho = 0:", b1_dos_acciones())
    b1_diversificacion()
    b1_frontera()
    b1_dos_fondos()
    print("tangente (sigma, mu, pendiente):", b1_tangente())
    b1_eleccion()


# --- T12: bloque 2 ---

BETA = (r"xlabel={Beta, $\beta_j$}, ylabel={Rentabilidad esperada, $\mu_j$}, " + PREAMBULO_EJES)
LAMBDA = 0.30  # prima del mercado en los esquemas de beta (unidades arbitrarias)


def b2_cml():
    """B2, 2.1. En equilibrio, la cartera tangente es la de mercado, M, y la recta que la une con el activo sin riesgo es la
    línea del mercado de capitales; las acciones quedan por debajo, porque tienen riesgo específico."""
    sT, mT, pT = _tangente()
    mu_s = np.linspace(M0, 0.95, 200)
    mu_i = np.linspace(0.05, M0, 120)
    acciones = [(0.45, 0.35), (0.55, 0.62), (0.70, 0.78), (0.60, 0.45), (0.38, 0.50), (0.75, 0.60)]
    tikz = rf"""\begin{{tikzpicture}}
\begin{{axis}}[width=9.5cm, height=6.4cm, xmin=0, xmax=0.85, ymin=0.05, ymax=1.05, legend pos=south east,
  legend style={{fill=none}}, {PLANO}]
\addplot[very thick, black] coordinates {{(0,{RF}) (0.85,{RF + 0.85 * pT:.4f})}};
\addlegendentry{{Línea del mercado de capitales}}
\addplot[thick, black!35] coordinates {{{_coords(_sigma(mu_s), mu_s)}}};
\addlegendentry{{Frontera de las acciones}}
\addplot[thick, black!35, dashed, forget plot] coordinates {{{_coords(_sigma(mu_i), mu_i)}}};
\addplot[only marks, mark=*, mark size=1.6pt, black!70] coordinates {{{" ".join(f"({s},{m})" for s, m in acciones)}}};
\addlegendentry{{Acciones}}
\addplot[only marks, mark=square*, mark size=1.8pt, black, forget plot] coordinates {{({sT:.4f},{mT:.4f}) (0,{RF})}};
\node[anchor=south east, font=\footnotesize] at (axis cs:{sT:.4f},{mT:.4f}) {{$M$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:0.01,{RF - 0.005}) {{$r_f$}};
\end{{axis}}
\end{{tikzpicture}}
"""
    escribir_tikz("b2_cml", tikz)


def b2_sml():
    """B2, 2.2. Línea del mercado de valores: rentabilidad esperada frente a beta, por (0, r_f) y (1, mu_M). En equilibrio
    todas las acciones están sobre ella, como A y B. Las acciones fuera de la recta se dibujan aparte, en b2_alfa."""
    linea = lambda b: RF + LAMBDA * b  # noqa: E731
    bA, bB = 0.55, 1.5
    tikz = rf"""\begin{{tikzpicture}}
\begin{{axis}}[width=9.5cm, height=6.4cm, xmin=0, xmax=2, ymin=0, ymax=0.82, xtick={{0,1}}, ytick={{{RF},{RF + LAMBDA}}},
  yticklabels={{$r_f$,$\mu_M$}}, {BETA}]
\addplot[very thick, black] coordinates {{(0,{RF}) (2,{linea(2):.4f})}};
\addplot[thin, black!40, dashed] coordinates {{(1,0) (1,{RF + LAMBDA})}};
\addplot[thin, black!40, dashed] coordinates {{(0,{RF + LAMBDA}) (1,{RF + LAMBDA})}};
\addplot[only marks, mark=*, mark size=1.8pt, black] coordinates {{({bA},{linea(bA):.4f}) ({bB},{linea(bB):.4f})}};
\addplot[only marks, mark=square*, mark size=1.8pt, black] coordinates {{(1,{RF + LAMBDA}) (0,{RF})}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{bA},{linea(bA):.4f}) {{$A$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{bB},{linea(bB):.4f}) {{$B$}};
\node[anchor=south east, font=\footnotesize] at (axis cs:1,{RF + LAMBDA}) {{$M$}};
\end{{axis}}
\end{{tikzpicture}}
"""
    escribir_tikz("b2_sml", tikz)


def b2_cml_sml():
    """B2, 2.2. Las mismas acciones en los dos planos. (a) En el de volatilidad y rentabilidad esperada, A y B quedan por
    debajo de la CML; A' y B', combinaciones del mercado con el activo sin riesgo con la misma beta, están sobre ella y
    ofrecen la misma rentabilidad esperada con menos volatilidad. (b) En el de la beta, A y A' (B y B') coinciden sobre la
    SML. Números arbitrarios: r_f = 0,12, mu_M = 0,42, sigma_M = 0,30."""
    sM, mM = 0.30, RF + LAMBDA
    pend = (mM - RF) / sM
    acc = {"A": (0.55, 0.36), "B": (1.5, 0.62)}  # beta, volatilidad total
    puntos_a, prima, nodos = [], [], []
    for n, (b, s) in acc.items():
        m = RF + b * LAMBDA
        se = b * sM
        assert s > se and m < RF + pend * s
        puntos_a.append((n, s, m, se))
    lineas = "\n".join(
        rf"\addplot[thin, black, dotted] coordinates {{({se:.4f},{m:.4f}) ({s:.4f},{m:.4f})}};" for n, s, m, se in puntos_a)
    marcas = " ".join(f"({s:.4f},{m:.4f})" for n, s, m, se in puntos_a)
    marcas2 = " ".join(f"({se:.4f},{m:.4f})" for n, s, m, se in puntos_a)
    etiquetas = "\n".join(
        rf"\node[anchor=west, font=\footnotesize] at (axis cs:{s + 0.01:.4f},{m:.4f}) {{${n}$}};" "\n"
        rf"\node[anchor=south east, font=\footnotesize] at (axis cs:{se:.4f},{m:.4f}) {{${n}'$}};" for n, s, m, se in puntos_a)
    linea_b = lambda b: RF + LAMBDA * b  # noqa: E731
    tikz = rf"""\begin{{tikzpicture}}
\begin{{axis}}[name=a, width=7.6cm, height=5.6cm, xmin=0, xmax=0.75, ymin=0, ymax=0.82, title={{(a) Volatilidad}},
  xlabel={{Volatilidad, $\sigma_j$}}, ylabel={{Rentabilidad esperada, $\mu_j$}}, xtick=\empty, ytick={{{RF}}}, yticklabels={{$r_f$}},
  {PREAMBULO_EJES}]
\addplot[very thick, black] coordinates {{(0,{RF}) (0.70,{RF + 0.70 * pend:.4f})}};
\node[anchor=south east, font=\scriptsize] at (axis cs:0.62,{RF + 0.62 * pend:.4f}) {{CML}};
{lineas}
\addplot[only marks, mark=*, mark size=1.8pt, black] coordinates {{{marcas}}};
\addplot[only marks, mark=o, mark size=1.8pt, black] coordinates {{{marcas2}}};
\addplot[only marks, mark=square*, mark size=1.8pt, black] coordinates {{({sM},{mM:.4f})}};
\node[anchor=south east, font=\footnotesize] at (axis cs:{sM},{mM:.4f}) {{$M$}};
{etiquetas}
\end{{axis}}
\begin{{axis}}[at={{(a.east)}}, anchor=west, xshift=0.5cm, width=7.6cm, height=5.6cm, xmin=0, xmax=2, ymin=0, ymax=0.82,
  title={{(b) Beta}}, xtick={{0,1}}, ytick={{{RF}}}, yticklabels={{$r_f$}}, {BETA}, ylabel={{}}]
\addplot[very thick, black] coordinates {{(0,{RF}) (2,{linea_b(2):.4f})}};
\node[anchor=south east, font=\scriptsize] at (axis cs:1.85,{linea_b(1.85):.4f}) {{SML}};
\addplot[only marks, mark=*, mark size=1.8pt, black] coordinates {{({acc["A"][0]},{linea_b(acc["A"][0]):.4f}) ({acc["B"][0]},{linea_b(acc["B"][0]):.4f})}};
\addplot[only marks, mark=square*, mark size=1.8pt, black] coordinates {{(1,{mM:.4f})}};
\node[anchor=south east, font=\footnotesize] at (axis cs:1,{mM:.4f}) {{$M$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{acc["A"][0]},{linea_b(acc["A"][0]):.4f}) {{$A=A'$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{acc["B"][0]},{linea_b(acc["B"][0]):.4f}) {{$B=B'$}};
\end{{axis}}
\end{{tikzpicture}}
"""
    escribir_tikz("b2_cml_sml", tikz)


def b2_alfa():
    """B2, 2.2. Acciones fuera de la SML: P, por encima, con alfa positivo (infravalorada), y Q, por debajo, con alfa
    negativo (sobrevalorada). Las flechas indican el ajuste: la beta no cambia, la rentabilidad esperada vuelve a la
    recta, en sentido contrario al del precio."""
    linea = lambda b: RF + LAMBDA * b  # noqa: E731
    bP, bQ = 0.8, 1.25
    mP, mQ = linea(bP) + 0.10, linea(bQ) - 0.09
    tikz = rf"""\begin{{tikzpicture}}
\begin{{axis}}[width=9.5cm, height=6.4cm, xmin=0, xmax=2, ymin=0, ymax=0.82, xtick={{0,1}}, ytick={{{RF},{RF + LAMBDA}}},
  yticklabels={{$r_f$,$\mu_M$}}, {BETA}]
\addplot[very thick, black] coordinates {{(0,{RF}) (2,{linea(2):.4f})}};
\addplot[thin, black!40, dashed] coordinates {{(1,0) (1,{RF + LAMBDA})}};
\addplot[thin, black!40, dashed] coordinates {{(0,{RF + LAMBDA}) (1,{RF + LAMBDA})}};
\addplot[only marks, mark=*, mark size=1.8pt, black] coordinates {{({bP},{mP:.4f}) ({bQ},{mQ:.4f})}};
\addplot[only marks, mark=square*, mark size=1.8pt, black] coordinates {{(1,{RF + LAMBDA}) (0,{RF})}};
\draw[-{{Stealth[length=2mm]}}, thick] (axis cs:{bP},{mP - 0.012:.4f}) -- (axis cs:{bP},{linea(bP) + 0.008:.4f});
\draw[-{{Stealth[length=2mm]}}, thick] (axis cs:{bQ},{mQ + 0.012:.4f}) -- (axis cs:{bQ},{linea(bQ) - 0.008:.4f});
\node[anchor=south, font=\footnotesize] at (axis cs:{bP},{mP:.4f}) {{$P$}};
\node[anchor=north, font=\footnotesize] at (axis cs:{bQ},{mQ:.4f}) {{$Q$}};
\node[anchor=east, font=\scriptsize] at (axis cs:{bP - 0.03},{(linea(bP) + mP) / 2:.4f}) {{$\alpha_P>0$}};
\node[anchor=west, font=\scriptsize] at (axis cs:{bQ + 0.03},{(linea(bQ) + mQ) / 2:.4f}) {{$\alpha_Q<0$}};
\node[anchor=south east, font=\footnotesize] at (axis cs:1,{RF + LAMBDA}) {{$M$}};
\end{{axis}}
\end{{tikzpicture}}
"""
    escribir_tikz("b2_alfa", tikz)


def b2_contraste():
    """B2, 2.3. Lo que encuentran los contrastes: las carteras ordenadas por beta se alinean en una recta más plana que la
    del CAPM, con más rentabilidad que la predicha para las de beta baja y menos para las de beta alta. Esquema sin datos
    (los datos, en la figura anx_sml_empirica del anexo II)."""
    rng = np.random.default_rng(21)
    b = np.linspace(0.6, 1.6, 10)
    a0, a1 = 0.14, 0.12
    m = a0 + a1 * b + rng.normal(0, 0.012, b.size)
    tikz = rf"""\begin{{tikzpicture}}
\begin{{axis}}[width=9.5cm, height=6.4cm, xmin=0, xmax=1.9, ymin=0, ymax=0.6, xtick={{0,1}}, ytick=\empty,
  xlabel={{Beta, $\beta_p$}}, ylabel={{Rentabilidad media en exceso}}, legend pos=north west, legend style={{fill=none}},
  {PREAMBULO_EJES}]
\addplot[very thick, black] coordinates {{(0,0) (1.9,{1.9 * LAMBDA:.4f})}};
\addlegendentry{{SML del CAPM}}
\addplot[thick, black!60, dashed] coordinates {{(0,{a0}) (1.9,{a0 + 1.9 * a1:.4f})}};
\addlegendentry{{Recta estimada}}
\addplot[only marks, mark=*, mark size=1.6pt, black] coordinates {{{_coords(b, m)}}};
\addlegendentry{{Carteras ordenadas por su beta}}
\end{{axis}}
\end{{tikzpicture}}
"""
    escribir_tikz("b2_contraste", tikz)


def b2_apt():
    """B2, 2.4. Arbitraje con un factor y sin riesgo específico: todos los activos tienen que estar en la recta
    r_f + beta lambda_1; D, por encima, rinde más que su réplica D' (P_1 y el activo sin riesgo con su misma beta):
    comprar D y vender D' es un arbitraje que devuelve D a la recta."""
    linea = lambda b: RF + LAMBDA * b  # noqa: E731
    bA, bB, bD = 0.5, 1.6, 1.15
    mD = linea(bD) + 0.11
    tikz = rf"""\begin{{tikzpicture}}
\begin{{axis}}[width=9.5cm, height=6.4cm, xmin=0, xmax=2, ymin=0, ymax=0.82, xtick={{0,1}}, ytick={{{RF}}},
  yticklabels={{$r_f$}}, xlabel={{Beta respecto del factor, $\beta_j$}}, ylabel={{Rentabilidad esperada, $\mu_j$}},
  {PREAMBULO_EJES}]
\addplot[very thick, black] coordinates {{(0,{RF}) (2,{linea(2):.4f})}};
\addplot[only marks, mark=*, mark size=1.8pt, black] coordinates {{({bA},{linea(bA):.4f}) ({bB},{linea(bB):.4f}) ({bD},{mD:.4f})}};
\addplot[only marks, mark=o, thick, mark size=2.2pt, black] coordinates {{({bD},{linea(bD):.4f})}};
\addplot[only marks, mark=square*, mark size=1.8pt, black] coordinates {{(0,{RF}) (1,{RF + LAMBDA})}};
\draw[{{Latex[length=1.6mm]}}-{{Latex[length=1.6mm]}}, thin] (axis cs:{bD - 0.06},{linea(bD) + 0.012:.4f}) -- (axis cs:{bD - 0.06},{mD - 0.008:.4f});
\node[anchor=east, font=\scriptsize] at (axis cs:{bD - 0.08},{(mD + linea(bD)) / 2:.4f}) {{$\alpha_D$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{bA},{linea(bA):.4f}) {{$A$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{bB},{linea(bB):.4f}) {{$B$}};
\node[anchor=south east, font=\footnotesize] at (axis cs:{bD},{mD:.4f}) {{$D$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{bD},{linea(bD):.4f}) {{$D'$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:1,{RF + LAMBDA}) {{$P_1$}};
\end{{axis}}
\end{{tikzpicture}}
"""
    escribir_tikz("b2_apt", tikz)


def b2_factores():
    """B2, 2.5. Construcción de los factores de FAMA y FRENCH (1993): seis carteras por tamaño (mediana de NYSE) y por
    valor contable sobre valor de mercado (percentiles 30 y 70 de NYSE); SMB compara las filas y HML, las columnas."""
    celdas = []
    for i, fila in enumerate(("Pequeñas", "Grandes")):
        for j, col in enumerate(("Crecimiento", "Neutras", "Valor")):
            x, y = 2.6 * j, -1.3 * i
            tono = ("black!8", "black!16", "black!28")[j]
            celdas.append(rf"\draw[fill={tono}] ({x},{y}) rectangle ({x + 2.4},{y - 1.1});")
            celdas.append(rf"\node[font=\footnotesize] at ({x + 1.2},{y - 0.55}) {{{fila[:1]}{col[:1]}}};")
    tikz = r"""\begin{tikzpicture}
""" + "\n".join(celdas) + r"""
\node[font=\footnotesize, anchor=east] at (-0.2,-0.55) {Pequeñas};
\node[font=\footnotesize, anchor=east] at (-0.2,-1.85) {Grandes};
\node[font=\footnotesize] at (1.2,0.35) {Crecimiento};
\node[font=\footnotesize] at (3.8,0.35) {Neutras};
\node[font=\footnotesize] at (6.4,0.35) {Valor};
\node[font=\scriptsize, align=center] at (3.8,0.95) {Valor contable sobre valor de mercado (percentiles $30$ y $70$)};
\node[font=\scriptsize, rotate=90] at (-2.0,-1.2) {Tamaño (mediana)};
\draw[{Latex[length=2mm]}-{Latex[length=2mm]}, thick] (8.2,-0.55) -- (8.2,-1.85) node[midway, right, font=\footnotesize] {SMB};
\draw[{Latex[length=2mm]}-{Latex[length=2mm]}, thick] (1.2,-2.8) -- (6.4,-2.8) node[midway, below, font=\footnotesize] {HML};
\end{tikzpicture}
"""
    escribir_tikz("b2_factores", tikz)


def b2_tres_factores():
    """B2, 2.5. Prima esperada de dos acciones con la misma carga en el mercado, en cascada: la pequeña de valor (cargas
    positivas en SMB y HML) suma las dos primas al escalón del mercado, que es lo que le pagaría el CAPM; la grande de
    crecimiento (cargas negativas) las resta. Alturas arbitrarias."""
    hm = 1.8
    grupos = [(0.0, "Acción pequeña de valor", (0.8, 1.0)), (6.0, "Acción grande de crecimiento", (-0.45, -0.6))]
    w, paso = 0.9, 1.4
    lineas = []
    for x0, titulo, (ds, dh) in grupos:
        xs = [x0 + paso * i for i in range(4)]
        y1, y2 = hm + ds, hm + ds + dh
        tramos = [(0, hm, "black!25", r"$b\,(\mu_M-r_f)$"), (hm, y1, "black!45", r"$s\,\lambda_{\text{SMB}}$"),
                  (y1, y2, "black!65", r"$h\,\lambda_{\text{HML}}$"), (0, y2, "black!10", r"$\mu_j-r_f$")]
        for i, (x, (a, b, tono, etq)) in enumerate(zip(xs, tramos)):
            borde = "very thick" if i == 3 else "thin"
            lineas.append(rf"\draw[{borde}, fill={tono}] ({x - w / 2:.2f},{a:.2f}) rectangle ({x + w / 2:.2f},{b:.2f});")
            arriba = b >= a
            ancla, y = ("south", max(a, b) + 0.05) if arriba else ("north", min(a, b) - 0.05)
            lineas.append(rf"\node[anchor={ancla}, font=\scriptsize] at ({x:.2f},{y:.2f}) {{{etq}}};")
        for (xa, ya), xb in zip([(xs[0], hm), (xs[1], y1), (xs[2], y2)], xs[1:]):
            lineas.append(rf"\draw[densely dotted] ({xa + w / 2:.2f},{ya:.2f}) -- ({xb - w / 2:.2f},{ya:.2f});")
        for x, n in zip(xs, ("Mercado", "Tamaño", "Valor", "Prima")):
            lineas.append(rf"\node[anchor=north, font=\footnotesize] at ({x:.2f},-0.08) {{{n}}};")
        lineas.append(rf"\node[anchor=north, font=\footnotesize\itshape] at ({(xs[0] + xs[3]) / 2:.2f},-0.6) {{{titulo}}};")
    xfin = grupos[1][0] + 3 * paso + 0.9
    tikz = r"""\begin{tikzpicture}
\draw[thin] (-0.9,0) -- (""" + f"{xfin:.2f}" + r""",0);
\draw[-{Stealth[length=2mm]}, thin] (-0.9,0) -- (-0.9,4.3) node[midway, above, rotate=90, font=\footnotesize] {Prima esperada, $\mu_j-r_f$};
\draw[dashed, black!60] (-0.9,""" + f"{hm}" + r""") -- (""" + f"{xfin:.2f},{hm}" + r""");
\node[anchor=south east, font=\scriptsize, black!70] at (""" + f"{xfin:.2f},{hm}" + r""") {Prima según el CAPM};
""" + "\n".join(lineas) + r"""
\end{tikzpicture}
"""
    escribir_tikz("b2_tres_factores", tikz)


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "b2":
    b2_cml()
    b2_sml()
    b2_cml_sml()
    b2_alfa()
    b2_contraste()
    b2_apt()
    b2_factores()


# --- T13: bloque 3 ---

def b3_conjuntos():
    """B3, 4.1. Las tres formas de eficiencia como conjuntos de información anidados y la práctica que apuesta contra
    cada una."""
    tikz = r"""\begin{tikzpicture}[font=\footnotesize]
\draw[fill=black!5, rounded corners=8pt] (0,0) rectangle (13,5.2);
\draw[fill=black!13, rounded corners=8pt] (0.45,0.4) rectangle (9.0,4.8);
\draw[fill=black!24, rounded corners=8pt] (0.9,0.8) rectangle (5.0,4.4);
\node[align=center] at (2.95,2.6) {\textbf{Forma débil}\\[2pt]Precios y volúmenes\\pasados\\[6pt]\textit{Análisis técnico}};
\node[align=center] at (7.0,2.6) {\textbf{Forma semifuerte}\\[2pt]Toda la información\\pública\\[6pt]\textit{Análisis fundamental}};
\node[align=center] at (11.0,2.6) {\textbf{Forma fuerte}\\[2pt]Toda la información,\\también la privada\\[6pt]\textit{Información privilegiada}};
\end{tikzpicture}
"""
    escribir_tikz("b3_conjuntos", tikz)


def b3_grossman():
    """B3, 4.2. Equilibrio de GROSSMAN y STIGLITZ (1980): la ventaja de informarse, psi(kappa), cae con la proporción de
    informados, kappa, y en equilibrio iguala el coste, chi, en kappa* < 1."""
    k = np.linspace(0, 1, 101)
    ventaja = 1.2 * (1 - k) ** 1.6
    C = 0.36
    k1 = 1 - (C / 1.2) ** (1 / 1.6)
    tikz = rf"""\begin{{tikzpicture}}
\begin{{axis}}[width=9.5cm, height=6.2cm, xmin=0, xmax=1, ymin=0, ymax=1.3, xtick={{0,{k1:.3f},1}},
  xticklabels={{$0$,$\kappa^*$,$1$}}, ytick={{{C}}}, yticklabels={{$\chi$}},
  xlabel={{Proporción de inversores informados, $\kappa$}}, ylabel={{Ventaja y coste de informarse}}, {PREAMBULO_EJES}]
\addplot[very thick, black] coordinates {{{_coords(k, ventaja)}}};
\node[anchor=south west, font=\footnotesize] at (axis cs:0.08,{1.2 * 0.92 ** 1.6:.3f}) {{$\psi(\kappa)$}};
\addplot[thick, black!60, dashed] coordinates {{(0,{C}) (1,{C})}};
\addplot[thin, black!40, dotted] coordinates {{({k1:.3f},0) ({k1:.3f},{C})}};
\addplot[only marks, mark=*, mark size=1.8pt, black] coordinates {{({k1:.3f},{C})}};
\end{{axis}}
\end{{tikzpicture}}
"""
    escribir_tikz("b3_grossman", tikz)


def b3_tecnico(n=50):
    """B3, 4.3. Una regla técnica convierte la historia del precio en una posición: estar en el mercado (omega = 1) cuando
    el precio supera su media móvil de n sesiones y fuera (omega = 0) cuando cae por debajo. Trayectoria simulada con
    tramos de tendencia alcista, bajista y alcista (semilla 41)."""
    rng = np.random.default_rng(41)
    deriva = np.concatenate([np.full(140, 0.0025), np.full(110, -0.0035), np.full(150, 0.003)])
    r = deriva + rng.normal(0, 0.011, deriva.size)
    p = 100 * np.exp(np.cumsum(r))
    media = np.convolve(p, np.ones(n) / n, mode="valid")
    t = np.arange(n - 1, p.size)
    precio = p[n - 1:]
    dentro = precio > media
    zonas = []
    i = 0
    while i < len(t):
        if dentro[i]:
            j = i
            while j + 1 < len(t) and dentro[j + 1]:
                j += 1
            zonas.append((t[i], t[j]))
            i = j + 1
        else:
            i += 1
    ymin, ymax = float(np.floor(p.min() / 5) * 5 - 5), float(np.ceil(p.max() / 5) * 5 + 5)
    bandas = "\n".join(rf"\fill[black!10] (axis cs:{a},{ymin}) rectangle (axis cs:{b},{ymax});" for a, b in zonas if b > a)
    tikz = rf"""\begin{{tikzpicture}}
\begin{{axis}}[width=13cm, height=6.2cm, xmin={n - 1}, xmax={p.size - 1}, ymin={ymin}, ymax={ymax}, xtick=\empty, ytick=\empty,
  xlabel={{Sesiones}}, ylabel={{Precio}}, axis on top, legend pos=south west, {PREAMBULO_EJES}]
{bandas}
\addplot[thin, black] coordinates {{{_coords(t, precio)}}};
\addlegendentry{{Precio}}
\addplot[very thick, black!55] coordinates {{{_coords(t, media)}}};
\addlegendentry{{Media móvil}}
\addlegendimage{{area legend, fill=black!10, draw=none}}
\addlegendentry{{En el mercado, $\omega_t=1$}}
\end{{axis}}
\end{{tikzpicture}}
"""
    escribir_tikz("b3_tecnico", tikz)
    return len(zonas)


def b3_valor():
    """B3, 4.4. Ratio entre precio y valor contable en función de la ROE, P/VC = (ROE - g)/(k - g), sin crecimiento y con
    crecimiento: las dos rectas se cortan en ROE = k, donde la ratio es uno, y crecer eleva el valor a la derecha de ese
    punto y lo reduce a su izquierda."""
    x = np.linspace(0, 2, 201)
    c = 0.5
    xg = np.linspace(c, 2, 151)
    tikz = rf"""\begin{{tikzpicture}}
\begin{{axis}}[width=9.5cm, height=6cm, xmin=0, xmax=2.1, ymin=0, ymax=3.2, xtick={{0,1,2}}, xticklabels={{$0$,$k$,$2k$}},
  ytick={{1}}, xlabel={{Rentabilidad de los recursos propios, ROE}}, ylabel={{P/VC}}, {PREAMBULO_EJES}]
\addplot[thin, black!45, dashed] coordinates {{(1,0) (1,3.2)}};
\addplot[thin, black!45, dashed] coordinates {{(0,1) (2.1,1)}};
\addplot[thick, black] coordinates {{{_coords(x, x)}}};
\addplot[very thick, black!55] coordinates {{{_coords(xg, (xg - c) / (1 - c))}}};
\node[anchor=north west, font=\scriptsize] at (axis cs:1.75,1.68) {{$g=0$}};
\node[anchor=south east, font=\scriptsize] at (axis cs:1.9,2.75) {{$g>0$}};
\end{{axis}}
\end{{tikzpicture}}
"""
    escribir_tikz("b3_valor", tikz)


def b3_treynor_black():
    """B3, 4.4. Cartera activa de TREYNOR y BLACK en el plano de volatilidad y rentabilidad esperada: A, con las acciones
    que el analista cree infravaloradas, queda por debajo de la CML (su alfa no compensa su riesgo específico), pero la
    curva de combinaciones con M se separa de ella, y la mejor combinación, T*, da una recta más empinada que la CML.
    Números arbitrarios: r_f = 0,12; M con prima 0,30 y volatilidad 0,30; A con beta 0,5, alfa 0,17 y riesgo específico 0,32."""
    sM, lam = 0.30, LAMBDA
    mM = RF + lam
    bA, aA, se = 0.5, 0.17, 0.32
    mA = RF + bA * lam + aA
    sA = math.sqrt(bA ** 2 * sM ** 2 + se ** 2)
    cov = bA * sM ** 2
    w = np.linspace(-0.35, 1.45, 300)
    mu = w * mA + (1 - w) * mM
    sig = np.sqrt(w ** 2 * sA ** 2 + (1 - w) ** 2 * sM ** 2 + 2 * w * (1 - w) * cov)
    w0 = (aA / se ** 2) / (lam / sM ** 2)
    wT = w0 / (1 + (1 - bA) * w0)
    mT = wT * mA + (1 - wT) * mM
    sT = math.sqrt(wT ** 2 * sA ** 2 + (1 - wT) ** 2 * sM ** 2 + 2 * wT * (1 - wT) * cov)
    pM, pT = lam / sM, (mT - RF) / sT
    assert (mA - RF) / sA < pM < pT
    tikz = rf"""\begin{{tikzpicture}}
\begin{{axis}}[width=9.5cm, height=6.4cm, xmin=0, xmax=0.5, ymin=0, ymax=0.78, legend pos=north west, legend style={{fill=none}}, {PLANO}]
\addplot[very thick, black] coordinates {{(0,{RF}) (0.48,{RF + 0.48 * pM:.4f})}};
\addlegendentry{{Línea del mercado de capitales}}
\addplot[thick, black!40] coordinates {{{_coords(sig, mu)}}};
\addlegendentry{{Combinaciones de $M$ y $A$}}
\addplot[thick, black, dashed] coordinates {{(0,{RF}) (0.48,{RF + 0.48 * pT:.4f})}};
\addlegendentry{{Recta con la mejor combinación, $T^*$}}
\addplot[only marks, mark=square*, mark size=1.8pt, black, forget plot] coordinates {{({sM},{mM:.4f}) (0,{RF})}};
\addplot[only marks, mark=*, mark size=1.8pt, black, forget plot] coordinates {{({sA:.4f},{mA:.4f}) ({sT:.4f},{mT:.4f})}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{sM},{mM:.4f}) {{$M$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:0.005,{RF - 0.005}) {{$r_f$}};
\node[anchor=west, font=\footnotesize] at (axis cs:{sA + 0.005:.4f},{mA:.4f}) {{$A$}};
\node[anchor=south east, font=\footnotesize] at (axis cs:{sT:.4f},{mT:.4f}) {{$T^*$}};
\end{{axis}}
\end{{tikzpicture}}
"""
    escribir_tikz("b3_treynor_black", tikz)
    return round(wT, 3), round(pM, 3), round(pT, 3), round((mA - RF) / sA, 3)


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "b3":
    b3_conjuntos()
    b3_grossman()
    print("tramos dentro del mercado:", b3_tecnico())
    b3_valor()
    print("Treynor-Black (peso de A, Sharpe de M, de T*, de A):", b3_treynor_black())
