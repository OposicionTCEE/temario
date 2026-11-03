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
    """B2, 2.2. Línea del mercado de valores: rentabilidad esperada frente a beta, por (0, r_f) y (1, mu_M). Las acciones
    bien valoradas, A y B, están sobre ella; P, por encima, tiene un alfa positivo y está infravalorada; Q, por debajo,
    un alfa negativo y está sobrevalorada."""
    linea = lambda b: RF + LAMBDA * b  # noqa: E731
    bA, bB, bP, bQ = 0.55, 1.5, 0.8, 1.25
    mP, mQ = linea(bP) + 0.10, linea(bQ) - 0.09
    tikz = rf"""\begin{{tikzpicture}}
\begin{{axis}}[width=9.5cm, height=6.4cm, xmin=0, xmax=2, ymin=0, ymax=0.82, xtick={{0,1}}, ytick={{{RF},{RF + LAMBDA}}},
  yticklabels={{$r_f$,$\mu_M$}}, {BETA}]
\addplot[very thick, black] coordinates {{(0,{RF}) (2,{linea(2):.4f})}};
\addplot[thin, black!40, dashed] coordinates {{(1,0) (1,{RF + LAMBDA})}};
\addplot[thin, black!40, dashed] coordinates {{(0,{RF + LAMBDA}) (1,{RF + LAMBDA})}};
\addplot[only marks, mark=*, mark size=1.8pt, black] coordinates {{({bA},{linea(bA):.4f}) ({bB},{linea(bB):.4f}) ({bP},{mP:.4f}) ({bQ},{mQ:.4f})}};
\addplot[only marks, mark=square*, mark size=1.8pt, black] coordinates {{(1,{RF + LAMBDA}) (0,{RF})}};
\addplot[thin, black, dotted] coordinates {{({bP},{linea(bP):.4f}) ({bP},{mP:.4f})}};
\addplot[thin, black, dotted] coordinates {{({bQ},{linea(bQ):.4f}) ({bQ},{mQ:.4f})}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{bA},{linea(bA):.4f}) {{$A$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{bB},{linea(bB):.4f}) {{$B$}};
\node[anchor=south east, font=\footnotesize] at (axis cs:1,{RF + LAMBDA}) {{$M$}};
\node[anchor=south, font=\footnotesize] at (axis cs:{bP},{mP:.4f}) {{$P$}};
\node[anchor=north, font=\footnotesize] at (axis cs:{bQ},{mQ:.4f}) {{$Q$}};
\node[anchor=east, font=\scriptsize] at (axis cs:{bP - 0.02},{(linea(bP) + mP) / 2:.4f}) {{$\alpha_P$}};
\node[anchor=west, font=\scriptsize] at (axis cs:{bQ + 0.02},{(linea(bQ) + mQ) / 2:.4f}) {{$\alpha_Q$}};
\end{{axis}}
\end{{tikzpicture}}
"""
    escribir_tikz("b2_sml", tikz)


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
    r_f + beta lambda_1; D, por encima, puede venderse caro frente a su réplica D' con el factor y el activo sin riesgo."""
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


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "b2":
    b2_cml()
    b2_sml()
    b2_contraste()
    b2_apt()
    b2_factores()
