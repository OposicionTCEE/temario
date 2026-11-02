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
\node[anchor=north west, font=\footnotesize] at (axis cs:{s_m:.3f},{mu_m:.3f}) {{$M$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{sT:.3f},{mT:.3f}) {{$T$}};
\node[anchor=north east, font=\footnotesize] at (axis cs:{s_z:.3f},{mu_z:.3f}) {{$Z$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:0.3,{RF - 0.15}) {{$r_f$}};
\end{{axis}}"""
    pts = " ".join(f"({bj:.3f},{m})" for bj, m in zip(beta, MU3))
    nodos_b = "\n".join(rf"\node[anchor={'south east' if n == 'A' else 'north west'}, font=\footnotesize] at (axis cs:{bj:.3f},{m}) {{${n}$}};" for bj, m, n in zip(beta, MU3, "ABC"))
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


# --- A7: APT, factores y factor de descuento estocástico ---

# Ejemplo de la APT (MARÍN y RUBIO, corregido): fondo j = 16 % + 2,5 F1 + 0,2 F2; carteras factoriales 15,4 % + F1 y
# 17,6 % + F2; tipo sin riesgo del 4 %.
APT_RF, APT_MU, APT_B, APT_FONDO = 4.0, (15.4, 17.6), (2.5, 0.2), 16.0
SECTORES_ES = {"Food": "Alimentación", "Beer": "Bebidas", "Smoke": "Tabaco", "Games": "Ocio", "Books": "Edición",
               "Hshld": "Hogar", "Clths": "Confección", "Hlth": "Sanidad", "Chems": "Química", "Txtls": "Textil",
               "Cnstr": "Construcción", "Steel": "Acero", "FabPr": "Maquinaria", "ElcEq": "Equipo eléctrico",
               "Autos": "Automóvil", "Carry": "Equipo de transporte", "Mines": "Minería", "Coal": "Carbón",
               "Oil": "Petróleo", "Util": "Suministros", "Telcm": "Telecomunicaciones", "Servs": "Servicios",
               "BusEq": "Equipo empresarial", "Paper": "Papel", "Trans": "Transporte", "Whlsl": "Mayoristas",
               "Rtail": "Comercio", "Meals": "Restauración", "Fin": "Finanzas", "Other": "Otros"}


def apt_ejemplo():
    lam = [m - APT_RF for m in APT_MU]
    replica = (1 - sum(APT_B)) * APT_RF + sum(b * m for b, m in zip(APT_B, APT_MU))
    return dict(lambdas=lam, replica=replica, apt=APT_RF + sum(b * l for b, l in zip(APT_B, lam)),
                pesos=(*APT_B, 1 - sum(APT_B)), ganancia=replica - APT_FONDO)


def apt_replica():
    """A7, II.5.3. (a) Un factor: sin riesgo específico, todo activo está en la recta r_f + β λ1 (r_f = 4 % y λ1 = 11,4,
    los del factor 1 del ejemplo); D, con β = 1,2 y μ = 22 %, queda por encima, y su réplica D′ (1,2 en la cartera
    factorial P1 y −0,2 en el activo sin riesgo) en la recta. (b) El fondo j del ejemplo y su réplica frente a la
    sorpresa del factor 1, con F2 = 0: rectas paralelas separadas por la ganancia del arbitraje."""
    e = apt_ejemplo()
    l1 = e["lambdas"][0]
    bA, bB, bD, mD = 0.5, 1.6, 1.2, 22.0
    mD_rep = APT_RF + bD * l1
    panel_a = rf"""\begin{{axis}}[name=a, width=7.6cm, height=6.6cm, xmin=0, xmax=2, ymin=0, ymax=30,
  xlabel={{Beta respecto del factor, $\beta_j$}}, ylabel={{Rentabilidad esperada, $\mu_j$ (\%)}}, title={{(a) Un factor}},
  legend pos=north west, {PREAMBULO_EJES}]
\addplot[very thick, black] coordinates {{(0,{APT_RF}) (2,{APT_RF + 2 * l1:.2f})}};
\addlegendentry{{$r_f+\beta_j\lambda_1$}}
\addplot[only marks, mark=*, mark size=1.6pt, black] coordinates {{({bA},{APT_RF + bA * l1:.2f}) ({bB},{APT_RF + bB * l1:.2f}) ({bD},{mD})}};
\addlegendentry{{Activos}}
\addplot[only marks, mark=o, thick, mark size=2.2pt, black] coordinates {{({bD},{mD_rep:.2f})}};
\addlegendentry{{Réplica de $D$}}
\addplot[only marks, mark=square*, mark size=1.9pt, black, forget plot] coordinates {{(0,{APT_RF}) (1,{APT_MU[0]})}};
\draw[{{Latex[length=1.6mm]}}-{{Latex[length=1.6mm]}}, thin] (axis cs:{bD + 0.06},{mD_rep:.2f}) -- (axis cs:{bD + 0.06},{mD});
\node[anchor=west, font=\scriptsize] at (axis cs:{bD + 0.08},{(mD + mD_rep) / 2:.2f}) {{$\alpha_D$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{bA},{APT_RF + bA * l1:.2f}) {{$A$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{bB},{APT_RF + bB * l1:.2f}) {{$B$}};
\node[anchor=south east, font=\footnotesize] at (axis cs:{bD},{mD}) {{$D$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{bD},{mD_rep:.2f}) {{$D'$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:1,{APT_MU[0]}) {{$P_1$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:0.03,{APT_RF - 0.2}) {{$r_f$}};
\end{{axis}}"""
    x0, x1 = -10, 10
    b1 = APT_B[0]
    xm = 5
    ganancia = f"{e['ganancia']:.1f}".replace(".", "{,}")
    panel_b = rf"""\begin{{axis}}[at={{(a.east)}}, anchor=west, xshift=1.9cm, width=7.6cm, height=6.6cm, xmin={x0}, xmax={x1}, ymin=-15, ymax=65,
  xlabel={{Sorpresa del factor 1, $F_1$ (\%)}}, ylabel={{Rentabilidad (\%)}}, title={{(b) Dos factores: el fondo $j$ y su réplica}},
  legend pos=north west, {PREAMBULO_EJES}]
\addplot[very thick, black] coordinates {{({x0},{e['replica'] + b1 * x0:.2f}) ({x1},{e['replica'] + b1 * x1:.2f})}};
\addlegendentry{{Réplica}}
\addplot[very thick, black!45] coordinates {{({x0},{APT_FONDO + b1 * x0:.2f}) ({x1},{APT_FONDO + b1 * x1:.2f})}};
\addlegendentry{{Fondo $j$}}
\draw[{{Latex[length=1.6mm]}}-{{Latex[length=1.6mm]}}, thin] (axis cs:{xm},{APT_FONDO + b1 * xm:.2f}) -- (axis cs:{xm},{e['replica'] + b1 * xm:.2f});
\node[anchor=west, font=\scriptsize] at (axis cs:{xm + 0.2},{(APT_FONDO + e['replica']) / 2 + b1 * xm:.2f}) {{${ganancia}$}};
\end{{axis}}"""
    tikz = "\\begin{tikzpicture}\n" + panel_a + "\n" + panel_b + "\n\\end{tikzpicture}\n"
    (IMG / "anx_apt_replica.tikz").write_text(tikz, encoding="utf-8")
    return e


def componentes():
    """A7, II.5.6. Componentes principales de la matriz de correlaciones de las rentabilidades mensuales en exceso de las
    30 carteras sectoriales de FRENCH (ponderadas por valor), julio de 1963 a diciembre de 2025 (con la de covarianzas,
    el carbón, el sector más volátil, acapara el segundo componente): (a) proporción de la varianza total de las
    rentabilidades tipificadas que explica cada uno de los diez primeros y la acumulada; (b) cargas de cada sector en el
    segundo y el tercero. El signo de cada componente es arbitrario: se elige con cargas positivas en el primero, la de
    la alimentación negativa en el segundo y la del petróleo positiva en el tercero."""
    from datos_french import SECTORES, carteras, factores
    meses, F3, F5, mom = factores(*PERIODO)
    cs, Y = carteras(SECTORES, "Average Value Weighted Returns -- Monthly", meses, F3["RF"])
    val, vec = np.linalg.eigh(np.corrcoef(Y.T))
    orden = np.argsort(val)[::-1]
    val, vec = val[orden], vec[:, orden]
    if vec[:, 0].sum() < 0:
        vec[:, 0] *= -1
    if vec[cs.index("Food"), 1] > 0:
        vec[:, 1] *= -1
    if vec[cs.index("Oil"), 2] < 0:
        vec[:, 2] *= -1
    cuota = val / val.sum() * 100
    acum = np.cumsum(cuota)
    z = (Y - Y.mean(0)) / Y.std(0, ddof=1)
    pesos1 = vec[:, 0] / vec[:, 0].sum()
    r1 = z @ vec[:, 0]
    corr_componentes = {j + 1: {k: np.corrcoef(z @ vec[:, j], x)[0, 1] for k, x in
                                (("Mkt-RF", F3["Mkt-RF"]), ("SMB", F3["SMB"]), ("HML", F3["HML"]), ("RMW", F5["RMW"]),
                                 ("CMA", F5["CMA"]), ("Mom", mom))} for j in range(4)}
    m = F3["Mkt-RF"]
    corr1 = np.corrcoef(r1, m)[0, 1]
    r2_mercado = []
    for j in range(Y.shape[1]):
        b = np.cov(Y[:, j], m, ddof=1)[0, 1] / m.var(ddof=1)
        r2_mercado.append(1 - (Y[:, j] - b * m).var() / Y[:, j].var())
    barras = " ".join(f"({k + 1},{cuota[k]:.2f})" for k in range(10))
    linea = " ".join(f"({k + 1},{acum[k]:.2f})" for k in range(10))
    panel_a = rf"""\begin{{axis}}[name=a, width=7.6cm, height=6.6cm, xmin=0.3, xmax=10.7, ymin=0, ymax=100, xtick={{1,...,10}},
  xlabel={{Componente principal}}, ylabel={{Varianza explicada (\% del total)}}, title={{(a) Varianza explicada}},
  legend pos=north east, legend style={{at={{(0.97,0.6)}}, anchor=east}}, {PREAMBULO_EJES}]
\addplot[ybar, bar width=8pt, fill=black!35, draw=black!60, area legend] coordinates {{{barras}}};
\addlegendentry{{Cada componente}}
\addplot[thick, black, mark=*, mark size=1.4pt] coordinates {{{linea}}};
\addlegendentry{{Acumulada}}
\end{{axis}}"""
    etiquetas = {"Food": "east", "Beer": "south east", "Smoke": "south", "Hlth": "north east", "Mines": "west",
                 "Steel": "north", "Coal": "south west", "Oil": "east", "Util": "south", "Rtail": "north",
                 "BusEq": "north east", "Games": "west", "Autos": "south"}
    x, y = vec[:, 1], vec[:, 2]
    x0, x1, y0, y1 = -0.5, 0.5, -0.4, 0.55
    pts = " ".join(f"({a:.4f},{b:.4f})" for a, b in zip(x, y))
    nodos = "\n".join(rf"\node[anchor={ancla}, font=\scriptsize, inner sep=1.5pt] at (axis cs:{x[cs.index(c)]:.4f},{y[cs.index(c)]:.4f}) {{{SECTORES_ES[c]}}};"
                      for c, ancla in etiquetas.items())
    panel_b = rf"""\begin{{axis}}[at={{(a.east)}}, anchor=west, xshift=1.9cm, width=7.6cm, height=6.6cm, xmin={x0}, xmax={x1}, ymin={y0}, ymax={y1},
  xlabel={{Carga en el segundo componente}}, ylabel={{Carga en el tercer componente}}, title={{(b) Cargas de los sectores}}, {PREAMBULO_EJES}]
\addplot[thin, black!30] coordinates {{({x0},0) ({x1},0)}};
\addplot[thin, black!30] coordinates {{(0,{y0}) (0,{y1})}};
\addplot[only marks, mark=*, mark size=1.4pt, black] coordinates {{{pts}}};
{nodos}
\end{{axis}}"""
    tikz = "\\begin{tikzpicture}\n" + panel_a + "\n" + panel_b + "\n\\end{tikzpicture}\n"
    (IMG / "anx_componentes.tikz").write_text(tikz, encoding="utf-8")
    return dict(sectores=cs, cuota=cuota, acum=acum, cargas=vec[:, :3], corr1=corr1, pesos1=pesos1,
                r2_mercado=np.array(r2_mercado), meses=meses)


def regresiones(Y, Z):
    """Regresiones de series temporales de cada columna de Y sobre los factores Z (meses × L), con constante:
    alfas, cargas, residuos, R², predicciones (cargas por primas medias) y estadístico GRS."""
    T, N = Y.shape
    L = Z.shape[1]
    X = np.column_stack([np.ones(T), Z])
    B = np.linalg.lstsq(X, Y, rcond=None)[0]
    E = Y - X @ B
    sigma = E.T @ E / (T - L - 1)
    alfa = B[0]
    mu = Z.mean(0)
    omega = np.atleast_2d(np.cov(Z.T, ddof=1))
    grs = (T - N - L) / N * (alfa @ np.linalg.solve(sigma, alfa)) / (1 + mu @ np.linalg.solve(omega, mu))
    r2 = 1 - E.var(0) / Y.var(0)
    return dict(alfa=alfa * 12, cargas=B[1:], r2=r2, prediccion=(B[1:].T @ mu) * 12, media=Y.mean(0) * 12, grs=grs,
                gl=(N, T - N - L))


def tres_factores():
    """A7, II.6.1. Rentabilidad media en exceso observada frente a la predicha por el CAPM (a) y por el modelo de tres
    factores de FAMA y FRENCH (b) en las 25 carteras de FRENCH por tamaño y valor contable sobre valor de mercado,
    julio de 1963 a diciembre de 2025. Predicción: cargas de la regresión de series temporales por las primas medias
    de los factores (anualizadas). También el modelo de cinco factores, para el texto."""
    from datos_french import TAMANO_VALOR, carteras, factores
    meses, F3, F5, mom = factores(*PERIODO)
    cs, Y = carteras(TAMANO_VALOR, "Average Value Weighted Returns -- Monthly", meses, F3["RF"])
    modelos = {"CAPM": np.column_stack([F3["Mkt-RF"]]),
               "FF3": np.column_stack([F3[k] for k in ("Mkt-RF", "SMB", "HML")]),
               "FF5": np.column_stack([F5[k] for k in ("Mkt-RF", "SMB", "HML", "RMW", "CMA")]),
               "FF5+Mom": np.column_stack([F5[k] for k in ("Mkt-RF", "SMB", "HML", "RMW", "CMA")] + [mom])}
    res = {k: regresiones(Y, Z) for k, Z in modelos.items()}
    esquinas = {"SMALL LoBM": ("pequeñas de crecimiento", "west"), "SMALL HiBM": ("pequeñas de valor", "east"),
                "BIG LoBM": ("grandes de crecimiento", "north west"), "BIG HiBM": ("grandes de valor", "north west")}
    paneles = []
    for i, (clave, titulo) in enumerate((("CAPM", "(a) CAPM"), ("FF3", "(b) Tres factores"))):
        r = res[clave]
        pts = " ".join(f"({p:.3f},{o:.3f})" for p, o in zip(r["prediccion"], r["media"]))
        nodos = "\n".join(rf"\node[anchor={ancla}, font=\scriptsize, inner sep=2pt] at (axis cs:{r['prediccion'][cs.index(c)]:.3f},{r['media'][cs.index(c)]:.3f}) {{{texto}}};"
                          for c, (texto, ancla) in esquinas.items())
        pos = "name=a" if i == 0 else r"at={(a.east)}, anchor=west, xshift=1.9cm"
        paneles.append(rf"""\begin{{axis}}[{pos}, width=7.6cm, height=6.6cm, xmin=2, xmax=14, ymin=2, ymax=14,
  xlabel={{Rentabilidad media predicha (\% anual)}}, ylabel={{Rentabilidad media observada (\% anual)}}, title={{{titulo}}},
  legend pos=north west, {PREAMBULO_EJES}]
\addplot[thin, black] coordinates {{(2,2) (14,14)}};
\addlegendentry{{Predicción exacta}}
\addplot[only marks, mark=*, mark size=1.5pt, black] coordinates {{{pts}}};
\addlegendentry{{Carteras}}
{nodos}
\end{{axis}}""")
    tikz = "\\begin{tikzpicture}\n" + "\n".join(paneles) + "\n\\end{tikzpicture}\n"
    (IMG / "anx_tres_factores.tikz").write_text(tikz, encoding="utf-8")
    primas = {k: F3[k].mean() * 12 for k in ("Mkt-RF", "SMB", "HML")}
    return dict(carteras=cs, res=res, primas=primas, meses=meses)


def _fecha(mes):
    return mes // 100 + (mes % 100 - 0.5) / 12


def factores_acumulados():
    """A7, II.6.3. Valor de un dólar invertido en julio de 1963 en cada factor (rentabilidad en exceso acumulada, sin el
    tipo sin riesgo; escala logarítmica), hasta diciembre de 2025. (a) mercado, tamaño y valor del modelo de tres
    factores; (b) rentabilidad e inversión del de cinco e impulso. Los puntos marcan el mes de publicación del estudio
    que documentó cada prima: BANZ (marzo de 1981), FAMA y FRENCH (junio de 1992), JEGADEESH y TITMAN (marzo de 1993),
    NOVY-MARX (abril de 2013) y FAMA y FRENCH (abril de 2015)."""
    from datos_french import factores
    meses, F3, F5, mom = factores(*PERIODO)
    series = {"Mkt-RF": F3["Mkt-RF"], "SMB": F3["SMB"], "HML": F3["HML"], "RMW": F5["RMW"], "CMA": F5["CMA"], "Mom": mom}
    acumulado = {k: np.concatenate([[1.0], np.cumprod(1 + v / 100)]) for k, v in series.items()}
    fechas = np.concatenate([[1963.5], [_fecha(m) + 1 / 24 for m in meses]])
    publicacion = {"SMB": 198103, "HML": 199206, "Mom": 199303, "RMW": 201304, "CMA": 201504}
    estilos = {"Mkt-RF": ("very thick, black", "Mercado (Mkt-RF)"), "SMB": ("thick, black!45", "Tamaño (SMB)"),
               "HML": ("thick, black, dashed", "Valor (HML)"), "RMW": ("thick, black", "Rentabilidad (RMW)"),
               "CMA": ("thick, black!45", "Inversión (CMA)"), "Mom": ("thick, black, dashed", "Impulso (Mom)")}
    paneles = []
    for i, (claves, titulo) in enumerate(((("Mkt-RF", "SMB", "HML"), "(a) Mercado, tamaño y valor"),
                                          (("RMW", "CMA", "Mom"), "(b) Rentabilidad, inversión e impulso"))):
        lineas = []
        for k in claves:
            est, nombre = estilos[k]
            pts = " ".join(f"({f:.3f},{v:.4f})" for f, v in zip(fechas, acumulado[k]))
            lineas += [rf"\addplot[{est}] coordinates {{{pts}}};", rf"\addlegendentry{{{nombre}}}"]
        marcas = " ".join(f"({_fecha(publicacion[k]) + 1 / 24:.3f},{acumulado[k][list(meses).index(publicacion[k]) + 1]:.4f})"
                          for k in claves if k in publicacion)
        lineas.append(rf"\addplot[only marks, mark=*, mark size=1.9pt, black, forget plot] coordinates {{{marcas}}};")
        pos = "name=a" if i == 0 else r"at={(a.east)}, anchor=west, xshift=1.9cm"
        paneles.append(rf"""\begin{{axis}}[{pos}, width=7.6cm, height=6.6cm, ymode=log, xmin=1963, xmax=2026, ymin=0.4, ymax=150,
  xtick={{1970,1980,1990,2000,2010,2020}}, ytick={{0.5,1,2,5,10,20,50,100}}, log ticks with fixed point,
  xlabel={{Año}}, ylabel={{Valor de un dólar invertido en 1963}}, title={{{titulo}}},
  legend pos=north west, {PREAMBULO_EJES}]
{chr(10).join(lineas)}
\end{{axis}}""")
    tikz = "\\begin{tikzpicture}\n" + "\n".join(paneles) + "\n\\end{tikzpicture}\n"
    (IMG / "anx_factores.tikz").write_text(tikz, encoding="utf-8")

    def tramo(k, a, b):
        s = (meses >= a) & (meses <= b)
        x = series[k][s]
        return dict(media=x.mean() * 12, t=x.mean() / x.std(ddof=1) * math.sqrt(s.sum()), meses=int(s.sum()),
                    acumulado=float(np.prod(1 + x / 100)))
    resumen = {k: dict(media=v.mean() * 12, vol=v.std(ddof=1) * math.sqrt(12),
                       sharpe=v.mean() / v.std(ddof=1) * math.sqrt(12), t=v.mean() / v.std(ddof=1) * math.sqrt(len(v)),
                       acumulado=acumulado[k][-1]) for k, v in series.items()}
    tramos = {(k, a, b): tramo(k, a, b) for k, a, b in (("SMB", 196307, 198102), ("SMB", 198103, 202512),
                                                         ("HML", 196307, 200612), ("HML", 200701, 202012),
                                                         ("HML", 202101, 202512), ("Mom", 196307, 200812),
                                                         ("Mom", 200903, 200905), ("Mom", 200901, 202512),
                                                         ("CMA", 196307, 201503), ("CMA", 201504, 202512),
                                                         ("RMW", 196307, 201303), ("RMW", 201304, 202512))}
    corr = np.corrcoef(np.column_stack([series[k] for k in estilos]).T)
    return dict(resumen=resumen, tramos=tramos, corr=corr, nombres=list(estilos), meses=meses, series=series)


def sharpe_maximo(Z):
    """Ratio de SHARPE anual de la cartera tangente de unos factores (rentabilidades en exceso mensuales, en %)."""
    mu = Z.mean(0)
    S = np.atleast_2d(np.cov(Z.T, ddof=1))
    return math.sqrt(mu @ np.linalg.solve(S, mu)) * math.sqrt(12)


def cota_hj():
    """A7, II.7.4. Cota de HANSEN y JAGANNATHAN: σ(m)/E[m] debe superar el mayor ratio de SHARPE alcanzable. Ratios de
    SHARPE anuales de la cartera tangente (en la muestra, julio de 1963 a diciembre de 2025) del mercado, de los tres
    factores, de los cinco y de los cinco con el impulso; frente a ellos, la volatilidad relativa del factor de
    descuento del CAPM de consumo con utilidad CRRA y crecimiento del consumo lognormal, sqrt(exp(γ²σc²) − 1), con la
    volatilidad del crecimiento del consumo real por habitante de Estados Unidos de 1964 a 2025 (FRED)."""
    from datos_french import FACTORES, anual, factores
    from datos_fred import crecimiento_anual, crecimiento_cuarto_trimestre
    meses, F3, F5, mom = factores(*PERIODO)
    conjuntos = {"Mercado": np.column_stack([F3["Mkt-RF"]]),
                 "Tres factores": np.column_stack([F3[k] for k in ("Mkt-RF", "SMB", "HML")]),
                 "Cinco factores": np.column_stack([F5[k] for k in ("Mkt-RF", "SMB", "HML", "RMW", "CMA")]),
                 "Cinco factores e impulso": np.column_stack([F5[k] for k in ("Mkt-RF", "SMB", "HML", "RMW", "CMA")] + [mom])}
    sr = {k: sharpe_maximo(Z) for k, Z in conjuntos.items()}
    g = crecimiento_anual(1964, 2025)
    gc = np.array([g[a] for a in sorted(g)]) / 100
    media_c, sigma_c = gc.mean(), gc.std(ddof=1)
    gamma_min = {k: math.sqrt(math.log(1 + s * s)) / sigma_c for k, s in sr.items()}
    rf_implicito = {k: math.exp(gm * media_c - (gm * sigma_c) ** 2 / 2) - 1 for k, gm in gamma_min.items()}
    q4 = crecimiento_cuarto_trimestre(1964, 2025)
    mk = anual(FACTORES, "Mkt-RF")
    años = [a for a in sorted(q4) if a in mk]
    corr_q4 = np.corrcoef([q4[a] for a in años], [mk[a] for a in años])[0, 1]
    corr_media = np.corrcoef([g[a] for a in años], [mk[a] for a in años])[0, 1]
    curva = " ".join(f"({x:.1f},{math.sqrt(math.exp((x * sigma_c) ** 2) - 1):.4f})" for x in np.arange(0, 80.01, 0.5))
    estilos = {"Mercado": "thick, black!45, dashed", "Tres factores": "thick, black!60, dash dot",
               "Cinco factores": "thick, black!75, densely dashed", "Cinco factores e impulso": "thick, black, dotted"}
    lineas = []
    for k, est in estilos.items():
        lineas += [rf"\addplot[{est}] coordinates {{(0,{sr[k]:.4f}) (80,{sr[k]:.4f})}};", rf"\addlegendentry{{{k}}}"]
    cortes = " ".join(f"({gamma_min[k]:.2f},{sr[k]:.4f})" for k in estilos)
    nodos = "\n".join(rf"\node[anchor=south east, font=\scriptsize, inner sep=1.5pt] at (axis cs:{gamma_min[k]:.2f},{sr[k]:.4f}) {{${gamma_min[k]:.0f}$}};"
                      for k in estilos)
    tikz = rf"""\begin{{tikzpicture}}
\begin{{axis}}[width=11cm, height=7.4cm, xmin=0, xmax=80, ymin=0, ymax=1.4,
  xlabel={{Aversión relativa al riesgo, $\gamma$}}, ylabel={{Volatilidad relativa del factor de descuento, $\sigma(m)/\mathbb E[m]$}},
  legend pos=north west, legend style={{fill=white, fill opacity=0.9}}, {PREAMBULO_EJES}]
\addplot[fill=black!10, draw=none, area legend] coordinates {{(1,0) (10,0) (10,1.4) (1,1.4)}} -- cycle;
\addlegendentry{{Aversión habitual, de 1 a 10}}
\addplot[very thick, black] coordinates {{{curva}}};
\addlegendentry{{CAPM de consumo}}
{chr(10).join(lineas)}
\addplot[only marks, mark=o, thick, mark size=2.2pt, black, forget plot] coordinates {{{cortes}}};
{nodos}
\end{{axis}}
\end{{tikzpicture}}
"""
    (IMG / "anx_hj.tikz").write_text(tikz, encoding="utf-8")
    return dict(sr=sr, media_c=media_c, sigma_c=sigma_c, gamma_min=gamma_min, rf_implicito=rf_implicito,
                corr_q4=corr_q4, corr_media=corr_media, n_años=len(gc), crecimiento=g)


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
    e = apt_replica()
    print(f"APT: primas {e['lambdas']}, réplica {e['replica']:.2f} % (pesos {e['pesos']}), APT {e['apt']:.2f} %,"
          f" ganancia {e['ganancia']:.2f}")
    c = componentes()
    print("componentes: cuota", np.round(c["cuota"][:6], 1), "acumulada", np.round(c["acum"][:6], 1),
          f"corr. del primero con el mercado {c['corr1']:.3f}; R² del mercado en los sectores: media"
          f" {c['r2_mercado'].mean():.2f}, mín. {c['r2_mercado'].min():.2f}, máx. {c['r2_mercado'].max():.2f}")
    tf = tres_factores()
    for k, r in tf["res"].items():
        print(f"{k:8s} GRS {r['grs']:.2f} {r['gl']} |alfa| medio {np.abs(r['alfa']).mean():.2f} R² medio {r['r2'].mean():.2f}"
              f" corr(pred, obs) {np.corrcoef(r['prediccion'], r['media'])[0, 1]:.2f}")
    i = tf["carteras"].index("SMALL LoBM")
    print("pequeñas de crecimiento:", {k: (round(r["media"][i], 2), round(r["prediccion"][i], 2), round(r["alfa"][i], 2))
                                     for k, r in tf["res"].items()}, "primas", {k: round(v, 2) for k, v in tf["primas"].items()})
    fa = factores_acumulados()
    for k, r in fa["resumen"].items():
        print(f"{k:7s} media {r['media']:.2f} vol {r['vol']:.2f} SR {r['sharpe']:.2f} t {r['t']:.2f} acumulado {r['acumulado']:.2f}")
    for (k, a, b), r in fa["tramos"].items():
        print(f"  {k} {a}-{b}: media {r['media']:.2f} t {r['t']:.2f} acumulado {r['acumulado']:.2f}")
    print("correlaciones", fa["nombres"], "\n", np.round(fa["corr"], 2))
    hj = cota_hj()
    print("HJ: SR", {k: round(v, 3) for k, v in hj["sr"].items()}, f"consumo: media {hj['media_c'] * 100:.2f} %,"
          f" σ {hj['sigma_c'] * 100:.2f} % ({hj['n_años']} años)", "γ mínima", {k: round(v, 1) for k, v in hj["gamma_min"].items()},
          "r_f implícito", {k: round(v * 100, 1) for k, v in hj["rf_implicito"].items()},
          f"corr consumo-mercado: cuarto trimestre {hj['corr_q4']:.2f}, medias anuales {hj['corr_media']:.2f}")
