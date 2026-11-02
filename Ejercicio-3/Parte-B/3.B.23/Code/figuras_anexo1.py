"""Figuras del anexo I del 3.B.23 (A1): anx_residual, anx_ergodicidad y anx_colas.

Escribe los .tikz en Img/ con los datos incrustados; después, desde la carpeta del tema:
    bash Code/generar_figura.sh anx_residual   (y lo mismo con los otros dos)

anx_ergodicidad: apuesta multiplicativa con +50 % o -40 % con probabilidad 1/2 en cada ronda.
  Esperanza por ronda 1,05; crecimiento temporal sqrt(1,5 * 0,6) = 0,9487. Panel (a): 20 trayectorias
  simuladas (semilla 7) durante 60 rondas, con la esperanza y la mediana teóricas. Panel (b): distribución
  exacta (binomial) de la riqueza tras 60 rondas.
anx_colas: panel (a) densidad normal estándar frente a t de Student con 4 grados de libertad reescalada a
  varianza 1; panel (b) 1.000 rentabilidades diarias simuladas (semilla 3): i.i.d. normales con sigma = 1 % y
  GARCH(1,1) con a0 = 2e-6, a1 = 0,08, b1 = 0,90 (varianza incondicional 1e-4, es decir, sigma = 1 %).
"""
import math
from pathlib import Path

import numpy as np

IMG = Path(__file__).resolve().parent.parent / "Img"

PREAMBULO_EJES = (
    r"/pgf/number format/use comma, /pgf/number format/1000 sep={},"
    r" tick label style={font=\scriptsize}, label style={font=\footnotesize},"
    r" title style={font=\footnotesize\bfseries, yshift=-1mm}, legend style={font=\scriptsize, draw=none, fill=white, fill opacity=0.85, text opacity=1}"
)


def residual():
    """Pagos al vencimiento de acreedores y accionistas en función del valor de los activos."""
    panel = []
    for i, (titulo, formula, tipo) in enumerate(
        [("(a) Acreedores", r"$\min(V_T,D)$", "deuda"), ("(b) Accionistas", r"$\max(V_T-D,\,0)$", "acciones")]
    ):
        x0 = i * 8.0
        p = []
        p.append(rf"\begin{{scope}}[xshift={x0}cm]")
        p.append(r"\draw[-{Stealth[length=2mm]}] (0,0) -- (6.6,0) node[below left, font=\footnotesize] {$V_T$};")
        p.append(r"\draw[-{Stealth[length=2mm]}] (0,0) -- (0,4.3) node[above, font=\footnotesize] {Pago};")
        p.append(r"\draw[dashed, gray] (2.6,0) -- (2.6,4.0);")
        p.append(r"\node[below, font=\footnotesize] at (2.6,0) {$D$};")
        if tipo == "deuda":
            p.append(r"\draw[dashed, gray] (0,2.6) -- (6.2,2.6);")
            p.append(r"\node[left, font=\footnotesize] at (0,2.6) {$D$};")
            p.append(r"\draw[very thick, black] (0,0) -- (2.6,2.6) -- (6.2,2.6);")
            p.append(rf"\node[above, font=\footnotesize] at (4.6,2.6) {{{formula}}};")
        else:
            p.append(r"\draw[very thick, black] (0,0) -- (2.6,0) -- (6.2,3.6);")
            p.append(rf"\node[above left, font=\footnotesize] at (5.4,2.8) {{{formula}}};")
        p.append(rf"\node[font=\footnotesize\bfseries] at (3.1,4.75) {{{titulo}}};")
        p.append(r"\end{scope}")
        panel.append("\n".join(p))
    tikz = "\\begin{tikzpicture}\n" + "\n".join(panel) + "\n\\end{tikzpicture}\n"
    (IMG / "anx_residual.tikz").write_text(tikz, encoding="utf-8")


def ergodicidad():
    """Apuesta multiplicativa: la esperanza crece y la trayectoria típica decrece."""
    rng = np.random.default_rng(7)
    rondas, n_tray = 60, 20
    up, down = 1.5, 0.6
    tiradas = rng.integers(0, 2, size=(n_tray, rondas))
    factores = np.where(tiradas == 1, up, down)
    riqueza = np.hstack([np.ones((n_tray, 1)), np.cumprod(factores, axis=1)])

    lineas = []
    for k in range(n_tray):
        coords = " ".join(f"({t},{riqueza[k, t]:.6g})" for t in range(rondas + 1))
        lineas.append(rf"\addplot[gray!55, thin, forget plot] coordinates {{{coords}}};")
    esperanza = " ".join(f"({t},{1.05**t:.6g})" for t in range(rondas + 1))
    mediana = " ".join(f"({t},{math.sqrt(up*down)**t:.6g})" for t in range(rondas + 1))

    panel_a = rf"""\begin{{axis}}[name=a, width=8.1cm, height=6.2cm, ymode=log, xmin=0, xmax={rondas}, ymin=1e-5, ymax=1e3,
  xlabel={{Ronda, $t$}}, ylabel={{Riqueza, $W_t$ (escala logarítmica)}}, title={{(a) Veinte trayectorias}},
  legend pos=south west, {PREAMBULO_EJES}]
{chr(10).join(lineas)}
\addplot[very thick, black] coordinates {{{esperanza}}};
\addlegendentry{{Esperanza: $\mathbb E[W_t]=1{{,}}05^t$}}
\addplot[very thick, black, dashed] coordinates {{{mediana}}};
\addlegendentry{{Mediana: $0{{,}}949^t$}}
\addplot[thin, black, dotted, forget plot] coordinates {{(0,1) ({rondas},1)}};
\end{{axis}}"""

    # Distribución exacta de la riqueza final: W = 1,5^h * 0,6^(T-h), h ~ Binomial(T, 1/2)
    barras = []
    for h in range(rondas + 1):
        prob = math.comb(rondas, h) / 2**rondas
        if prob < 1e-4:
            continue
        logw = h * math.log10(up) + (rondas - h) * math.log10(down)
        barras.append(f"({logw:.4f},{prob:.5f})")
    p_ganar = sum(math.comb(rondas, h) for h in range(rondas + 1) if up**h * down ** (rondas - h) > 1) / 2**rondas
    log_media = rondas * math.log10(1.05)
    log_mediana = rondas * math.log10(math.sqrt(up * down))
    panel_b = rf"""\begin{{axis}}[at={{(a.east)}}, anchor=west, xshift=1.3cm, width=8.1cm, height=6.2cm, ybar, bar width=1.2pt,
  xmin=-6, xmax=3, ymin=0, ymax=0.12, xtick={{-6,-4,-2,0,2}}, xticklabels={{$10^{{-6}}$,$10^{{-4}}$,$10^{{-2}}$,$1$,$10^{{2}}$}},
  xlabel={{Riqueza tras {rondas} rondas, $W_{{{rondas}}}$}}, ylabel={{Probabilidad}}, title={{(b) Distribución de $W_{{{rondas}}}$}},
  legend pos=north west, {PREAMBULO_EJES}]
\addplot[fill=gray!50, draw=gray!70, forget plot] coordinates {{{" ".join(barras)}}};
\addplot[ybar=0pt, sharp plot, very thick, black] coordinates {{({log_media:.4f},0) ({log_media:.4f},0.12)}};
\addlegendentry{{Esperanza}}
\addplot[ybar=0pt, sharp plot, very thick, black, dashed] coordinates {{({log_mediana:.4f},0) ({log_mediana:.4f},0.12)}};
\addlegendentry{{Mediana}}
\addplot[ybar=0pt, sharp plot, thin, black, dotted, forget plot] coordinates {{(0,0) (0,0.12)}};
\end{{axis}}"""
    tikz = "\\begin{tikzpicture}\n" + panel_a + "\n" + panel_b + "\n\\end{tikzpicture}\n"
    (IMG / "anx_ergodicidad.tikz").write_text(tikz, encoding="utf-8")
    return p_ganar, 1.05**rondas, math.sqrt(up * down) ** rondas


def colas():
    """Colas gruesas (densidades) y agrupamiento de la volatilidad (simulación)."""
    xs = np.linspace(-6, 6, 241)
    normal = np.exp(-xs**2 / 2) / math.sqrt(2 * math.pi)
    nu = 4
    escala = math.sqrt((nu - 2) / nu)  # t reescalada a varianza 1
    c = math.gamma((nu + 1) / 2) / (math.sqrt(nu * math.pi) * math.gamma(nu / 2))
    t = (c * (1 + (xs / escala) ** 2 / nu) ** (-(nu + 1) / 2)) / escala
    coords_n = " ".join(f"({x:.3f},{y:.6g})" for x, y in zip(xs, normal))
    coords_t = " ".join(f"({x:.3f},{y:.6g})" for x, y in zip(xs, t))
    panel_a = rf"""\begin{{axis}}[name=a, width=8.1cm, height=6.6cm, ymode=log, xmin=-6, xmax=6, ymin=1e-8, ymax=1,
  xlabel={{Rentabilidad tipificada, $(r-\mu)/\sigma$}}, ylabel={{Densidad (escala logarítmica)}}, title={{(a) Colas}},
  legend pos=south center, {PREAMBULO_EJES}]
\addplot[very thick, black, dashed] coordinates {{{coords_n}}};
\addlegendentry{{Normal}}
\addplot[very thick, black] coordinates {{{coords_t}}};
\addlegendentry{{$t$ de Student, $\nu=4$, varianza 1}}
\end{{axis}}"""

    rng = np.random.default_rng(3)
    n = 1000
    iid = rng.normal(0, 0.01, n)
    a0, a1, b1 = 2e-6, 0.08, 0.90
    var = a0 / (1 - a1 - b1)
    garch = np.empty(n)
    eps_prev = 0.0
    for i in range(n):
        var = a0 + a1 * eps_prev**2 + b1 * var
        eps_prev = math.sqrt(var) * rng.normal()
        garch[i] = eps_prev
    def serie(v):
        return " ".join(f"({i},{100*x:.3f})" for i, x in enumerate(v))
    comun = rf"width=8.1cm, height=3.75cm, xmin=0, xmax={n}, ymin=-7, ymax=7, ytick={{-5,0,5}}, {PREAMBULO_EJES}"
    panel_b1 = rf"""\begin{{axis}}[name=b1, at={{(a.north east)}}, anchor=north west, xshift=1.3cm, {comun},
  xticklabels={{}}, ylabel={{\%}}, title={{(b) Sin y con agrupamiento}}]
\addplot[black, thin] coordinates {{{serie(iid)}}};
\node[anchor=north west, font=\scriptsize, fill=white] at (rel axis cs:0.01,0.98) {{Normal i.i.d.}};
\end{{axis}}"""
    panel_b2 = rf"""\begin{{axis}}[at={{(b1.south west)}}, anchor=north west, yshift=-0.25cm, {comun},
  xlabel={{Día}}, ylabel={{\%}}]
\addplot[black, thin] coordinates {{{serie(garch)}}};
\node[anchor=north west, font=\scriptsize, fill=white] at (rel axis cs:0.01,0.98) {{GARCH(1,1)}};
\end{{axis}}"""
    tikz = "\\begin{tikzpicture}\n" + panel_a + "\n" + panel_b1 + "\n" + panel_b2 + "\n\\end{tikzpicture}\n"
    (IMG / "anx_colas.tikz").write_text(tikz, encoding="utf-8")
    exceso_curtosis = float(np.mean((garch - garch.mean()) ** 4) / np.var(garch) ** 2 - 3)
    return exceso_curtosis, float(garch.std() * 100), float(iid.std() * 100)


if __name__ == "__main__":
    residual()
    p, esp, med = ergodicidad()
    print(f"ergodicidad: P(W60 > 1) = {p:.4f}; E[W60] = {esp:.2f}; mediana = {med:.4f}")
    k, sg, si = colas()
    print(f"colas: exceso de curtosis GARCH simulado = {k:.2f}; sigma GARCH = {sg:.2f} %; sigma iid = {si:.2f} %")
