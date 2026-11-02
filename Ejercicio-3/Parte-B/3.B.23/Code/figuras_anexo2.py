"""Figuras del anexo II del 3.B.23. Reutiliza el ejemplo de tres acciones del anexo I (Code/figuras_anexo1.py).

Supuesto de las figuras del CAPM (A5): si el mercado estuviera formado solo por las tres acciones del ejemplo y el tipo
sin riesgo fuera del 10 %, la cartera de mercado sería la tangente: M = (31,4 %; 29,3 %; 39,3 %), μ_M = 17,69 %,
σ_M = 17,57 %, y las betas de A, B y C serían 0,26, 1,04 y 1,56.
Uso, desde la carpeta del tema:  python3 Code/figuras_anexo2.py  y después  bash Code/generar_figura.sh <nombre>
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figuras_anexo1 import IMG, MU3, PREAMBULO_EJES, S3, constantes3, sigma_frontera, tangente_de  # noqa: E402

RF = 10.0


def mercado():
    wM, mM, sM = tangente_de(RF)
    beta = (S3 @ wM) / sM**2
    return wM, mM, sM, beta


def tangencia_sharpe():
    """A5, II.1.3. Combinaciones de una acción con la cartera de mercado: la curva pasa por M y es tangente a la CML.
    Con A (a entre -0,6 y 1) y con C (a entre -0,6 y 1)."""
    Si, a, b, c, d = constantes3()
    wM, mM, sM, beta = mercado()
    m_mv = a / c
    fr = " ".join(f"({sigma_frontera(m, a, b, c, d):.3f},{m:.3f})" for m in np.linspace(m_mv, 26, 100))
    cml = f"(0,{RF}) (45,{RF + 45 * (mM - RF) / sM:.3f})"
    sig = np.sqrt(np.diag(S3))
    curvas = []
    for j, est, nombre in ((0, "thick, black!60, dashed", "A"), (2, "thick, black!60, dash dot", "C")):
        pts = []
        for x in np.linspace(-0.6, 1.0, 81):
            m = x * MU3[j] + (1 - x) * mM
            v = x * x * S3[j, j] + (1 - x) ** 2 * sM**2 + 2 * x * (1 - x) * (S3[j] @ wM)
            pts.append(f"({math.sqrt(v):.3f},{m:.3f})")
        curvas.append(rf"\addplot[{est}] coordinates {{{' '.join(pts)}}};" + "\n" + rf"\addlegendentry{{Combinaciones de ${nombre}$ y $M$}}")
    t = rf"""\begin{{tikzpicture}}
\begin{{axis}}[width=11cm, height=7cm, xmin=0, xmax=45, ymin=8, ymax=26,
  xlabel={{Volatilidad, $\sigma_p$ (\%)}}, ylabel={{Rentabilidad esperada, $\mu_p$ (\%)}},
  legend pos=north west, legend style={{fill=none}}, {PREAMBULO_EJES}]
\addplot[thick, black!35] coordinates {{{fr}}};
\addlegendentry{{Frontera eficiente}}
\addplot[very thick, black] coordinates {{{cml}}};
\addlegendentry{{CML}}
{chr(10).join(curvas)}
\addplot[only marks, mark=*, mark size=1.6pt, black, forget plot] coordinates {{({sig[0]:.3f},{MU3[0]}) ({sig[2]:.3f},{MU3[2]})}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{sig[0]:.3f},{MU3[0]}) {{$A$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{sig[2]:.3f},{MU3[2]}) {{$C$}};
\addplot[only marks, mark=square*, mark size=1.9pt, black, forget plot] coordinates {{({sM:.3f},{mM:.3f}) (0,{RF})}};
\node[anchor=south east, font=\footnotesize] at (axis cs:{sM:.3f},{mM:.3f}) {{$M$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:0.3,{RF - 0.15}) {{$r_f$}};
\end{{axis}}
\end{{tikzpicture}}
"""
    (IMG / "anx_tangencia_sharpe.tikz").write_text(t, encoding="utf-8")


def cml_sml():
    """A5, II.1.5. (a) CML: las acciones quedan por debajo; (b) SML: las tres acciones sobre la recta y dos activos
    hipotéticos mal valorados, P (beta 0,6, μ 17 %) por encima y Q (beta 1,3, μ 17,5 %) por debajo."""
    Si, a, b, c, d = constantes3()
    wM, mM, sM, beta = mercado()
    m_mv = a / c
    fr = " ".join(f"({sigma_frontera(m, a, b, c, d):.3f},{m:.3f})" for m in np.linspace(m_mv, 26, 100))
    sig = np.sqrt(np.diag(S3))
    acc = " ".join(f"({s:.3f},{m})" for s, m in zip(sig, MU3))
    nodos_a = "\n".join(rf"\node[anchor=north west, font=\footnotesize] at (axis cs:{s:.3f},{m}) {{${n}$}};" for s, m, n in zip(sig, MU3, "ABC"))
    panel_a = rf"""\begin{{axis}}[name=a, width=7.6cm, height=6.6cm, xmin=0, xmax=45, ymin=8, ymax=26,
  xlabel={{Volatilidad, $\sigma_p$ (\%)}}, ylabel={{Rentabilidad esperada, $\mu_p$ (\%)}}, title={{(a) Recta del mercado de capitales}},
  {PREAMBULO_EJES}]
\addplot[thick, black!35] coordinates {{{fr}}};
\addplot[very thick, black] coordinates {{(0,{RF}) (45,{RF + 45 * (mM - RF) / sM:.3f})}};
\addplot[only marks, mark=*, mark size=1.6pt, black] coordinates {{{acc}}};
{nodos_a}
\addplot[only marks, mark=square*, mark size=1.9pt, black] coordinates {{({sM:.3f},{mM:.3f}) (0,{RF})}};
\node[anchor=south east, font=\footnotesize] at (axis cs:{sM:.3f},{mM:.3f}) {{$M$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:0.3,{RF - 0.15}) {{$r_f$}};
\end{{axis}}"""
    pend = mM - RF
    sml = f"(0,{RF}) (2,{RF + 2 * pend:.3f})"
    pts = " ".join(f"({bj:.3f},{m})" for bj, m in zip(beta, MU3))
    nodos_b = "\n".join(rf"\node[anchor=north west, font=\footnotesize] at (axis cs:{bj:.3f},{m}) {{${n}$}};" for bj, m, n in zip(beta, MU3, "ABC"))
    panel_b = rf"""\begin{{axis}}[at={{(a.east)}}, anchor=west, xshift=1.9cm, width=7.6cm, height=6.6cm, xmin=0, xmax=2, ymin=8, ymax=26,
  xlabel={{Beta, $\beta_j$}}, ylabel={{Rentabilidad esperada, $\mu_j$ (\%)}}, title={{(b) Recta del mercado de valores}},
  {PREAMBULO_EJES}]
\addplot[very thick, black] coordinates {{{sml}}};
\addplot[only marks, mark=*, mark size=1.6pt, black] coordinates {{{pts}}};
{nodos_b}
\addplot[only marks, mark=square*, mark size=1.9pt, black] coordinates {{(1,{mM:.3f}) (0,{RF})}};
\node[anchor=south east, font=\footnotesize] at (axis cs:1,{mM:.3f}) {{$M$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:0.02,{RF - 0.15}) {{$r_f$}};
\addplot[only marks, mark=o, mark size=2.2pt, black, thick] coordinates {{(0.6,17) (1.3,17.5)}};
\node[anchor=south east, font=\footnotesize] at (axis cs:0.6,17) {{$P$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:1.3,17.5) {{$Q$}};
\end{{axis}}"""
    tikz = "\\begin{tikzpicture}\n" + panel_a + "\n" + panel_b + "\n\\end{tikzpicture}\n"
    (IMG / "anx_cml_sml.tikz").write_text(tikz, encoding="utf-8")
    return beta, mM, sM


def desempeno():
    """A5, II.2. Dos carteras gestionadas: P (β 0,8, μ 17 %, σ 20 %) y Q (β 1,3, μ 19 %, σ 24 %), con el mercado del
    ejemplo. (a) Rectas de SHARPE frente a la CML; (b) SML, alfas de JENSEN y recta de TREYNOR de P."""
    wM, mM, sM, beta = mercado()
    carteras = {"P": (0.8, 17.0, 20.0), "Q": (1.3, 19.0, 24.0)}
    lineas = []
    for n, (bp, mp, sp) in carteras.items():
        lineas.append(rf"\addplot[thick, black!55, dashed, forget plot] coordinates {{(0,{RF}) (45,{RF + 45 * (mp - RF) / sp:.3f})}};")
    panel_a = rf"""\begin{{axis}}[name=a, width=7.6cm, height=6.6cm, xmin=0, xmax=45, ymin=8, ymax=30,
  xlabel={{Volatilidad, $\sigma_p$ (\%)}}, ylabel={{Rentabilidad media, $\bar r_p$ (\%)}}, title={{(a) Ratio de SHARPE}},
  {PREAMBULO_EJES}]
\addplot[very thick, black] coordinates {{(0,{RF}) (45,{RF + 45 * (mM - RF) / sM:.3f})}};
{chr(10).join(lineas)}
\addplot[only marks, mark=square*, mark size=1.9pt, black] coordinates {{({sM:.3f},{mM:.3f}) (0,{RF})}};
\addplot[only marks, mark=*, mark size=1.8pt, black] coordinates {{(20,17) (24,19)}};
\node[anchor=south east, font=\footnotesize] at (axis cs:{sM:.3f},{mM:.3f}) {{$M$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:20,17) {{$P$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:24,19) {{$Q$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:0.3,{RF - 0.15}) {{$r_f$}};
\end{{axis}}"""
    pend = mM - RF
    bP, mP, _ = carteras["P"]
    bQ, mQ, _ = carteras["Q"]
    sP, sQ = RF + bP * pend, RF + bQ * pend
    panel_b = rf"""\begin{{axis}}[at={{(a.east)}}, anchor=west, xshift=1.9cm, width=7.6cm, height=6.6cm, xmin=0, xmax=2, ymin=8, ymax=30,
  xlabel={{Beta, $\beta_p$}}, ylabel={{Rentabilidad media, $\bar r_p$ (\%)}}, title={{(b) Alfa de JENSEN y ratio de TREYNOR}},
  {PREAMBULO_EJES}]
\addplot[very thick, black] coordinates {{(0,{RF}) (2,{RF + 2 * pend:.3f})}};
\addplot[thick, black!55, dashed] coordinates {{(0,{RF}) (2,{RF + 2 * (mP - RF) / bP:.3f})}};
\addplot[thick, black] coordinates {{({bP},{sP:.3f}) ({bP},{mP})}};
\addplot[thick, black] coordinates {{({bQ},{sQ:.3f}) ({bQ},{mQ})}};
\addplot[only marks, mark=square*, mark size=1.9pt, black] coordinates {{(1,{mM:.3f}) (0,{RF})}};
\addplot[only marks, mark=*, mark size=1.8pt, black] coordinates {{({bP},{mP}) ({bQ},{mQ})}};
\node[anchor=south east, font=\footnotesize] at (axis cs:1,{mM:.3f}) {{$M$}};
\node[anchor=south east, font=\footnotesize] at (axis cs:{bP},{mP}) {{$P$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{bQ},{mQ}) {{$Q$}};
\node[anchor=west, font=\footnotesize] at (axis cs:{bP + 0.03},{(mP + sP) / 2:.3f}) {{$\alpha_P$}};
\node[anchor=west, font=\footnotesize] at (axis cs:{bQ + 0.03},{(mQ + sQ) / 2:.3f}) {{$\alpha_Q$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:0.02,{RF - 0.15}) {{$r_f$}};
\end{{axis}}"""
    tikz = "\\begin{tikzpicture}\n" + panel_a + "\n" + panel_b + "\n\\end{tikzpicture}\n"
    (IMG / "anx_desempeno.tikz").write_text(tikz, encoding="utf-8")
    res = {}
    for n, (bp, mp, sp) in carteras.items():
        alfa = mp - (RF + bp * pend)
        resid = math.sqrt(sp**2 - bp**2 * sM**2)
        res[n] = dict(sharpe=(mp - RF) / sp, treynor=(mp - RF) / bp, alfa=alfa, m2=RF + (mp - RF) / sp * sM,
                      resid=resid, ir=alfa / resid)
    return res, (mM - RF) / sM, mM - RF


def pesos_frontera(m):
    """Pesos de la cartera de la frontera con rentabilidad esperada m (en %), con las constantes de MERTON (1972)."""
    Si, a, b, c, d = constantes3()
    return ((c * m - a) * (Si @ MU3) + (b - a * m) * (Si @ np.ones(3))) / d


def beta_cero(mu_m=20.0):
    """A6, II.3.1. CAPM de beta nula de BLACK (1972) con el ejemplo de tres acciones. Si no se puede pedir prestado al
    tipo sin riesgo, la cartera de mercado queda por encima de la tangente T: aquí, la de la frontera con μ = 20 %.
    La tangente a la frontera en M corta el eje en μ_Z, la rentabilidad de su cartera de beta nula, Z, que está en la
    rama ineficiente. (a) Plano media-volatilidad; (b) SML de BLACK frente a la que se trazaría desde r_f."""
    Si, a, b, c, d = constantes3()
    wm = pesos_frontera(mu_m)
    s_m = math.sqrt(wm @ S3 @ wm)
    mu_z = a / c - (d / c**2) / (mu_m - a / c)
    s_z = sigma_frontera(mu_z, a, b, c, d)
    beta = (S3 @ wm) / s_m**2
    wT, mT, sT = tangente_de(RF)
    alta = " ".join(f"({sigma_frontera(m, a, b, c, d):.3f},{m:.3f})" for m in np.linspace(a / c, 26, 80))
    baja = " ".join(f"({sigma_frontera(m, a, b, c, d):.3f},{m:.3f})" for m in np.linspace(6, a / c, 60))
    pend = (mu_m - mu_z) / s_m
    sig = np.sqrt(np.diag(S3))
    acc = " ".join(f"({s:.3f},{m})" for s, m in zip(sig, MU3))
    nodos_a = "\n".join(rf"\node[anchor=north west, font=\footnotesize] at (axis cs:{s:.3f},{m}) {{${n}$}};" for s, m, n in zip(sig, MU3, "ABC"))
    panel_a = rf"""\begin{{axis}}[name=a, width=7.6cm, height=6.6cm, xmin=0, xmax=45, ymin=6, ymax=26,
  xlabel={{Volatilidad, $\sigma_p$ (\%)}}, ylabel={{Rentabilidad esperada, $\mu_p$ (\%)}}, title={{(a) Cartera de beta nula}},
  extra y ticks={{{mu_z:.3f}}}, extra y tick labels={{$\mu_Z$}}, legend pos=north west, {PREAMBULO_EJES}]
\addplot[thick, black!35] coordinates {{{alta}}};
\addlegendentry{{Frontera}}
\addplot[thick, black!35, forget plot] coordinates {{{baja}}};
\addplot[thick, black] coordinates {{(0,{RF}) ({sT:.3f},{mT:.3f})}};
\addlegendentry{{Préstamo sin riesgo}}
\addplot[thick, black, dashed] coordinates {{(0,{mu_z:.3f}) (42,{mu_z + 42 * pend:.3f})}};
\addlegendentry{{Tangente en $M$}}
\addplot[thin, black, dotted, forget plot] coordinates {{(0,{mu_z:.3f}) ({s_z:.3f},{mu_z:.3f})}};
\addplot[only marks, mark=*, mark size=1.6pt, black, forget plot] coordinates {{{acc}}};
{nodos_a}
\addplot[only marks, mark=square*, mark size=1.9pt, black, forget plot] coordinates {{({s_m:.3f},{mu_m:.3f}) (0,{RF}) (0,{mu_z:.3f})}};
\addplot[only marks, mark=o, mark size=2.2pt, black, thick, forget plot] coordinates {{({sT:.3f},{mT:.3f}) ({s_z:.3f},{mu_z:.3f})}};
\node[anchor=south east, font=\footnotesize] at (axis cs:{s_m:.3f},{mu_m:.3f}) {{$M$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{sT:.3f},{mT:.3f}) {{$T$}};
\node[anchor=north east, font=\footnotesize] at (axis cs:{s_z:.3f},{mu_z:.3f}) {{$Z$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:0.3,{RF - 0.15}) {{$r_f$}};
\end{{axis}}"""
    pts = " ".join(f"({bj:.3f},{m})" for bj, m in zip(beta, MU3))
    nodos_b = "\n".join(rf"\node[anchor=north west, font=\footnotesize] at (axis cs:{bj:.3f},{m}) {{${n}$}};" for bj, m, n in zip(beta, MU3, "ABC"))
    panel_b = rf"""\begin{{axis}}[at={{(a.east)}}, anchor=west, xshift=1.9cm, width=7.6cm, height=6.6cm, xmin=-0.25, xmax=2, ymin=6, ymax=30,
  xlabel={{Beta respecto de $M$, $\beta_j$}}, ylabel={{Rentabilidad esperada, $\mu_j$ (\%)}}, title={{(b) Recta del mercado de valores}},
  extra y ticks={{{mu_z:.3f}}}, extra y tick labels={{$\mu_Z$}}, legend pos=north west, {PREAMBULO_EJES}]
\addplot[very thick, black] coordinates {{(-0.25,{mu_z - 0.25 * (mu_m - mu_z):.3f}) (2,{mu_z + 2 * (mu_m - mu_z):.3f})}};
\addlegendentry{{BLACK: desde $\mu_Z$}}
\addplot[thick, black!55, dashed] coordinates {{(-0.25,{RF - 0.25 * (mu_m - RF):.3f}) (2,{RF + 2 * (mu_m - RF):.3f})}};
\addlegendentry{{Desde $r_f$}}
\addplot[only marks, mark=*, mark size=1.6pt, black, forget plot] coordinates {{{pts}}};
{nodos_b}
\addplot[only marks, mark=square*, mark size=1.9pt, black, forget plot] coordinates {{(1,{mu_m:.3f}) (0,{RF}) (0,{mu_z:.3f})}};
\node[anchor=south east, font=\footnotesize] at (axis cs:1,{mu_m:.3f}) {{$M$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:0.02,{RF - 0.15}) {{$r_f$}};
\end{{axis}}"""
    tikz = "\\begin{tikzpicture}\n" + panel_a + "\n" + panel_b + "\n\\end{tikzpicture}\n"
    (IMG / "anx_beta_cero.tikz").write_text(tikz, encoding="utf-8")
    return dict(pesos_m=wm, sigma_m=s_m, mu_z=mu_z, sigma_z=s_z, betas=beta, tangente=(wT, mT, sT))


DECILES_BETA = ["Lo 10", "Dec 2", "Dec 3", "Dec 4", "Dec 5", "Dec 6", "Dec 7", "Dec 8", "Dec 9", "Hi 10"]
DECILES_BM = ["Lo 10", "2-Dec", "3-Dec", "4-Dec", "5-Dec", "6-Dec", "7-Dec", "8-Dec", "9-Dec", "Hi 10"]
PERIODO = (196307, 202512)


def contraste_deciles():
    """Beta (MCO, todo el periodo), rentabilidad media en exceso anualizada (media mensual × 12), predicción del CAPM y
    alfa de las diez carteras por beta y por valor contable/valor de mercado de FRENCH, ponderadas por valor."""
    from datos_french import BETA, BM, excesos
    filas = []
    for clave, fichero, marca, columnas in (("beta", BETA, "Value Weighted Returns -- Monthly", DECILES_BETA),
                                            ("bm", BM, "Value Weight Returns -- Monthly", DECILES_BM)):
        meses, X, m, rf = excesos(fichero, marca, columnas, *PERIODO)
        prima = m.mean() * 12
        for k, col in enumerate(columnas):
            y = X[:, k]
            b = np.cov(y, m, ddof=1)[0, 1] / m.var(ddof=1)
            filas.append(dict(panel=clave, decil=k + 1, columna=col, beta=b, media=y.mean() * 12, capm=b * prima,
                              alfa=(y.mean() - b * m.mean()) * 12, vol=y.std(ddof=1) * math.sqrt(12),
                              meses=len(meses), prima=prima, rf=rf.mean() * 12))
    return filas


def sml_empirica():
    """A6, II.4.3. Rentabilidad media en exceso frente a beta de los deciles de FRENCH por beta (a) y por valor contable
    sobre valor de mercado (b), julio de 1963 a diciembre de 2025, con la SML del CAPM (ordenada 0 y pendiente igual a
    la prima media del mercado) y, en (a), la recta ajustada por mínimos cuadrados a los diez puntos."""
    filas = contraste_deciles()
    paneles = []
    for i, (clave, titulo, extremos) in enumerate((("beta", "(a) Carteras por beta", ("beta baja", "beta alta")),
                                                    ("bm", "(b) Carteras por valor contable sobre valor de mercado",
                                                     ("crecimiento", "valor")))):
        fs = [f for f in filas if f["panel"] == clave]
        prima = fs[0]["prima"]
        pts = " ".join(f"({f['beta']:.3f},{f['media']:.3f})" for f in fs)
        lineas = [rf"\addplot[very thick, black] coordinates {{(0,0) (1.9,{1.9 * prima:.3f})}};",
                  r"\addlegendentry{SML del CAPM}"]
        if clave == "beta":
            pend, orden = np.polyfit([f["beta"] for f in fs], [f["media"] for f in fs], 1)
            lineas += [rf"\addplot[thick, black!55, dashed] coordinates {{(0,{orden:.3f}) (1.9,{orden + 1.9 * pend:.3f})}};",
                       r"\addlegendentry{Recta ajustada}"]
        lineas += [rf"\addplot[only marks, mark=*, mark size=1.6pt, black] coordinates {{{pts}}};",
                   r"\addlegendentry{Deciles}",
                   rf"\addplot[only marks, mark=square*, mark size=1.9pt, black] coordinates {{(1,{prima:.3f})}};",
                   r"\addlegendentry{Mercado}"]
        abajo = "anchor=west, xshift=1mm" if clave == "bm" else "anchor=north, yshift=-1mm"
        for f, texto, ancla in ((fs[0], extremos[0], abajo), (fs[-1], extremos[1], "anchor=south, yshift=1mm")):
            lineas.append(rf"\node[{ancla}, font=\scriptsize] at (axis cs:{f['beta']:.3f},{f['media']:.3f}) {{{texto}}};")
        pos = "name=a" if i == 0 else r"at={(a.east)}, anchor=west, xshift=1.9cm"
        paneles.append(rf"""\begin{{axis}}[{pos}, width=7.6cm, height=6.6cm, xmin=0, xmax=1.9, ymin=0, ymax=14,
  xlabel={{Beta, $\beta_p$}}, ylabel={{Rentabilidad media en exceso (\% anual)}}, title={{{titulo}}},
  legend pos=north west, {PREAMBULO_EJES}]
{chr(10).join(lineas)}
\end{{axis}}""")
    tikz = "\\begin{tikzpicture}\n" + "\n".join(paneles) + "\n\\end{tikzpicture}\n"
    (IMG / "anx_sml_empirica.tikz").write_text(tikz, encoding="utf-8")
    return filas


if __name__ == "__main__":
    tangencia_sharpe()
    beta, mM, sM = cml_sml()
    print(f"mercado: μ = {mM:.2f} %, σ = {sM:.2f} %, betas A, B, C = {np.round(beta, 3)}")
    print("SML: P (β 0,6) exigida =", round(RF + 0.6 * (mM - RF), 2), "; Q (β 1,3) exigida =", round(RF + 1.3 * (mM - RF), 2))
    res, sh_m, tr_m = desempeno()
    print(f"mercado: SHARPE {sh_m:.3f}, TREYNOR {tr_m:.2f}")
    for n, r in res.items():
        print(n, {k: round(v, 3) for k, v in r.items()})
    bc = beta_cero()
    print(f"beta nula: M = {np.round(bc['pesos_m'] * 100, 1)} %, σ_M = {bc['sigma_m']:.2f} %, μ_Z = {bc['mu_z']:.2f} %,"
          f" σ_Z = {bc['sigma_z']:.2f} %, betas = {np.round(bc['betas'], 3)}")
    for f in sml_empirica():
        print(f"{f['panel']:4s} D{f['decil']:<2d} beta {f['beta']:.2f} media {f['media']:.2f} CAPM {f['capm']:.2f} alfa {f['alfa']:.2f}")
