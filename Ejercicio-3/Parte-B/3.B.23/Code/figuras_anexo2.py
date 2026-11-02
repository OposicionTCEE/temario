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


if __name__ == "__main__":
    tangencia_sharpe()
    beta, mM, sM = cml_sml()
    print(f"mercado: μ = {mM:.2f} %, σ = {sM:.2f} %, betas A, B, C = {np.round(beta, 3)}")
    print("SML: P (β 0,6) exigida =", round(RF + 0.6 * (mM - RF), 2), "; Q (β 1,3) exigida =", round(RF + 1.3 * (mM - RF), 2))
    res, sh_m, tr_m = desempeno()
    print(f"mercado: SHARPE {sh_m:.3f}, TREYNOR {tr_m:.2f}")
    for n, r in res.items():
        print(n, {k: round(v, 3) for k, v in r.items()})
