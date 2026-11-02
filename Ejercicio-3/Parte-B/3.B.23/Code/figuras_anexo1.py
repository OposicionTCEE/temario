"""Figuras del anexo I del 3.B.23 (A1): anx_residual, anx_ergodicidad y anx_colas.

Escribe los .tikz en Img/ con los datos incrustados; después, desde la carpeta del tema:
    bash Code/generar_figura.sh anx_residual   (y lo mismo con los otros dos)

anx_ergodicidad: apuesta multiplicativa con +50 % o -40 % con probabilidad 1/2 en cada ronda.
  Esperanza por ronda 1,05; crecimiento temporal sqrt(1,5 * 0,6) = 0,9487. Panel (a): 20 trayectorias
  simuladas (semilla 7) durante 60 rondas, con la esperanza y la mediana teóricas. Panel (b): distribución
  exacta (binomial) de la riqueza tras 60 rondas.
anx_colas: panel (a) densidad normal estándar frente a t de Student con 4 grados de libertad reescalada a
  varianza 1; panel (b) 1.000 rentabilidades diarias simuladas (semilla 3): i.i.d. normales con sigma = 1 % y
  GARCH(1,1) con a0 = 2e-6, a1 = 0,10, b1 = 0,88 (varianza incondicional 1e-4, es decir, sigma = 1 %),
  semilla 48, elegida entre 59 por mostrar con claridad el agrupamiento (exceso de curtosis de la muestra: 6,7).
"""
import math
from pathlib import Path

import numpy as np

IMG = Path(__file__).resolve().parent.parent / "Img"

PREAMBULO_EJES = (
    r"/pgf/number format/use comma, /pgf/number format/1000 sep={},"
    r" tick label style={font=\scriptsize}, label style={font=\footnotesize},"
    r" title style={font=\footnotesize\bfseries, yshift=-1mm}, legend cell align=left,"
    r" legend style={font=\scriptsize, draw=none, fill=white, fill opacity=0.85, text opacity=1}"
)
MARGEN = r"\path ([yshift=1.5pt]current bounding box.north east) ([yshift=-1.5pt]current bounding box.south west);"


def escribir_tikz(nombre, tikz):
    """Escribe Img/<nombre>.tikz con un margen de 1,5 pt arriba y abajo, para que el borde superior del eje no quede
    cortado cuando la figura no lleva título dentro. Lo usan también figuras_anexo2.py y figuras_anexo3.py."""
    (IMG / f"{nombre}.tikz").write_text(tikz.replace("\\end{tikzpicture}", MARGEN + "\n\\end{tikzpicture}"),
                                        encoding="utf-8")


def residual():
    """Pagos al vencimiento de acreedores y accionistas en función del valor de los activos."""
    panel = []
    for i, (titulo, formula, tipo) in enumerate(
        # mín y máx con tilde, como los escribe babel (spanish) en el texto del tema
        [("(a) Acreedores", r"$\text{mín}(V_T,D)$", "deuda"),
         ("(b) Accionistas", r"$\text{máx}(V_T-D,\,0)$", "acciones")]
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

    panel_a = rf"""\begin{{axis}}[name=a, width=7.4cm, height=6.2cm, ymode=log, xmin=0, xmax={rondas}, ymin=1e-5, ymax=1e3,
  xlabel={{Ronda, $t$}}, ylabel={{Riqueza, $W_t$ (escala logarítmica)}}, title={{(a) Veinte trayectorias simuladas}},
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
    panel_b = rf"""\begin{{axis}}[at={{(a.east)}}, anchor=west, xshift=1.9cm, width=7.4cm, height=6.2cm,
  xmin=-6, xmax=3, ymin=0, ymax=0.12, ytick={{0,0.04,0.08,0.12}}, scaled y ticks=false,
  yticklabel style={{/pgf/number format/fixed, /pgf/number format/precision=2, /pgf/number format/fixed zerofill}}, xtick={{-6,-4,-2,0,2}}, xticklabels={{$10^{{-6}}$,$10^{{-4}}$,$10^{{-2}}$,$1$,$10^{{2}}$}},
  xlabel={{Riqueza tras ${rondas}$ rondas, $W_{{{rondas}}}$}}, ylabel={{Probabilidad}}, title={{(b) Distribución de $W_{{{rondas}}}$}},
  legend pos=north west, {PREAMBULO_EJES}]
\addplot[ybar, bar width=0.28, fill=gray!45, draw=gray!70, forget plot] coordinates {{{" ".join(barras)}}};
\addplot[very thick, black] coordinates {{({log_media:.4f},0) ({log_media:.4f},0.12)}};
\addlegendentry{{Esperanza}}
\addplot[very thick, black, dashed] coordinates {{({log_mediana:.4f},0) ({log_mediana:.4f},0.12)}};
\addlegendentry{{Mediana}}
\addplot[thin, black, dotted, forget plot] coordinates {{(0,0) (0,0.12)}};
\end{{axis}}"""
    tikz = "\\begin{tikzpicture}\n" + panel_a + "\n" + panel_b + "\n\\end{tikzpicture}\n"
    (IMG / "anx_ergodicidad.tikz").write_text(tikz, encoding="utf-8")
    return p_ganar, 1.05**rondas, math.sqrt(up * down) ** rondas


def colas():
    """Dos figuras, porque se comentan en párrafos distintos: anx_colas, densidades de la normal y de la t de Student,
    y anx_volatilidad, rentabilidades simuladas sin y con agrupamiento de la volatilidad."""
    xs = np.linspace(-6, 6, 241)
    normal = np.exp(-xs**2 / 2) / math.sqrt(2 * math.pi)
    nu = 4
    escala = math.sqrt((nu - 2) / nu)  # t reescalada a varianza 1
    c = math.gamma((nu + 1) / 2) / (math.sqrt(nu * math.pi) * math.gamma(nu / 2))
    t = (c * (1 + (xs / escala) ** 2 / nu) ** (-(nu + 1) / 2)) / escala
    coords_n = " ".join(f"({x:.3f},{y:.6g})" for x, y in zip(xs, normal))
    coords_t = " ".join(f"({x:.3f},{y:.6g})" for x, y in zip(xs, t))
    panel_a = rf"""\begin{{axis}}[width=10cm, height=6.6cm, ymode=log, xmin=-6, xmax=6, ymin=1e-8, ymax=1,
  xlabel={{Rentabilidad tipificada, $(r-\mu)/\sigma$}}, ylabel={{Densidad (escala logarítmica)}},
  legend style={{at={{(0.5,0.03)}}, anchor=south}}, {PREAMBULO_EJES}]
\addplot[very thick, black, dashed] coordinates {{{coords_n}}};
\addlegendentry{{Normal}}
\addplot[very thick, black] coordinates {{{coords_t}}};
\addlegendentry{{$t$ de Student, $\nu=4$, varianza $1$}}
\end{{axis}}"""

    n = 1000
    iid = np.random.default_rng(3).normal(0, 0.01, n)
    rng = np.random.default_rng(48)
    a0, a1, b1 = 2e-6, 0.10, 0.88
    var = a0 / (1 - a1 - b1)
    garch = np.empty(n)
    eps_prev = 0.0
    for i in range(n):
        var = a0 + a1 * eps_prev**2 + b1 * var
        eps_prev = math.sqrt(var) * rng.normal()
        garch[i] = eps_prev
    def serie(v):
        return " ".join(f"({i},{100*x:.3f})" for i, x in enumerate(v))
    lim = math.ceil(100 * max(abs(garch).max(), abs(iid).max())) + 1
    comun = rf"width=10cm, height=3.75cm, xmin=0, xmax={n}, ymin=-{lim}, ymax={lim}, ytick={{-8,-4,0,4,8}}, {PREAMBULO_EJES}"
    panel_b1 = rf"""\begin{{axis}}[name=b1, {comun},
  xticklabels={{}}, ylabel={{\%}}]
\addplot[black, thin] coordinates {{{serie(iid)}}};
\node[anchor=north west, font=\scriptsize, fill=white] at (rel axis cs:0.01,0.98) {{Normal i.i.d.}};
\end{{axis}}"""
    panel_b2 = rf"""\begin{{axis}}[at={{(b1.south west)}}, anchor=north west, yshift=-0.25cm, {comun},
  xlabel={{Día}}, ylabel={{\%}}]
\addplot[black, thin] coordinates {{{serie(garch)}}};
\node[anchor=north west, font=\scriptsize, fill=white] at (rel axis cs:0.01,0.98) {{GARCH$(1,1)$}};
\end{{axis}}"""
    escribir_tikz("anx_colas", "\\begin{tikzpicture}\n" + panel_a + "\n\\end{tikzpicture}\n")
    escribir_tikz("anx_volatilidad", "\\begin{tikzpicture}\n" + panel_b1 + "\n" + panel_b2 + "\n\\end{tikzpicture}\n")
    exceso_curtosis = float(np.mean((garch - garch.mean()) ** 4) / np.var(garch) ** 2 - 3)
    return exceso_curtosis, float(garch.std() * 100), float(iid.std() * 100)


def correlacion():
    """A2, I.3.1. Tres nubes de 150 pares de rentabilidades normales simuladas (semilla 11) con correlación
    0,8, 0 y -0,6, misma media (0) y misma volatilidad (1) en las dos acciones."""
    rng = np.random.default_rng(11)
    paneles = []
    for i, (rho, etiqueta) in enumerate([(0.8, "0{,}8"), (0.0, "0"), (-0.6, "-0{,}6")]):
        z1 = rng.normal(size=150)
        z2 = rng.normal(size=150)
        a = z1
        b = rho * z1 + math.sqrt(1 - rho**2) * z2
        pts = " ".join(f"({x:.3f},{y:.3f})" for x, y in zip(a, b))
        pos = "name=p0" if i == 0 else rf"at={{(p{i-1}.east)}}, anchor=west, xshift=1.3cm, name=p{i}"
        paneles.append(rf"""\begin{{axis}}[{pos}, width=5.3cm, height=5.3cm, xmin=-3.5, xmax=3.5, ymin=-3.5, ymax=3.5,
  xtick={{-2,0,2}}, ytick={{-2,0,2}}, xlabel={{$r_A$}}, ylabel={{$r_B$}}, title={{({"abc"[i]}) $\rho_{{AB}}={etiqueta}$}},
  {PREAMBULO_EJES}]
\addplot[only marks, mark=*, mark size=0.9pt, black!70] coordinates {{{pts}}};
\addplot[thin, gray, dashed] coordinates {{(-3.5,0) (3.5,0)}};
\addplot[thin, gray, dashed] coordinates {{(0,-3.5) (0,3.5)}};
\end{{axis}}""")
    tikz = "\\begin{tikzpicture}\n" + "\n".join(paneles) + "\n\\end{tikzpicture}\n"
    (IMG / "anx_correlacion.tikz").write_text(tikz, encoding="utf-8")


def dos_acciones():
    """A2, I.3.2. Combinaciones de dos acciones: A con media 12 % y volatilidad 20 %; B con 18 % y 32 % (ejemplo del
    texto viejo). Panel (a): pesos entre 0 y 1 con rho = 1, 0,5, 0, -0,5, -1. Panel (b): rho = 0 con ventas en corto
    (peso de A entre -0,6 y 1,6), rama eficiente continua e ineficiente discontinua; cartera de mínima varianza."""
    mA, sA, mB, sB = 12.0, 20.0, 18.0, 32.0

    def cartera(w, rho):
        m = w * mA + (1 - w) * mB
        v = w**2 * sA**2 + (1 - w) ** 2 * sB**2 + 2 * w * (1 - w) * rho * sA * sB
        return math.sqrt(max(v, 0.0)), m

    estilos = {1.0: "very thick, black", 0.5: "thick, black!75", 0.0: "thick, black!60, dashed",
               -0.5: "thick, black!45, dash dot", -1.0: "very thick, black!35"}
    nombres = {1.0: "1", 0.5: "0{,}5", 0.0: "0", -0.5: "-0{,}5", -1.0: "-1"}
    curvas = []
    for rho in (1.0, 0.5, 0.0, -0.5, -1.0):
        pts = " ".join("({:.3f},{:.3f})".format(*cartera(w / 200, rho)) for w in range(0, 201))
        curvas.append(rf"\addplot[{estilos[rho]}] coordinates {{{pts}}};" + "\n"
                      + rf"\addlegendentry{{$\rho_{{AB}}={nombres[rho]}$}}")
    puntos = (r"\addplot[only marks, mark=*, mark size=1.8pt, black] coordinates {(20,12) (32,18)};" "\n"
              r"\node[anchor=north west, font=\footnotesize] at (axis cs:20,12) {$A$};" "\n"
              r"\node[anchor=south east, font=\footnotesize] at (axis cs:32,18) {$B$};")
    panel_a = rf"""\begin{{axis}}[name=a, width=7.6cm, height=6.6cm, xmin=0, xmax=36, ymin=10, ymax=20,
  xlabel={{Volatilidad, $\sigma_p$ (\%)}}, ylabel={{Rentabilidad esperada, $\mu_p$ (\%)}}, title={{(a) Pesos entre $0$ y $1$}},
  legend pos=north west, {PREAMBULO_EJES}, legend style={{fill=none}}]
{chr(10).join(curvas)}
{puntos}
\end{{axis}}"""

    rho = 0.0
    w_min = (sB**2 - rho * sA * sB) / (sA**2 + sB**2 - 2 * rho * sA * sB)
    s_min, m_min = cartera(w_min, rho)
    sup = " ".join("({:.3f},{:.3f})".format(*cartera(w_min - k * (w_min + 0.6) / 200, rho)) for k in range(0, 201))
    inf = " ".join("({:.3f},{:.3f})".format(*cartera(w_min + k * (1.6 - w_min) / 200, rho)) for k in range(0, 201))
    panel_b = rf"""\begin{{axis}}[at={{(a.east)}}, anchor=west, xshift=1.9cm, width=7.6cm, height=6.6cm, xmin=0, xmax=50, ymin=6, ymax=24,
  xlabel={{Volatilidad, $\sigma_p$ (\%)}}, ylabel={{Rentabilidad esperada, $\mu_p$ (\%)}}, title={{(b) Ramas, con $\rho_{{AB}}=0$}},
  legend pos=north west, {PREAMBULO_EJES}]
\addplot[very thick, black] coordinates {{{sup}}};
\addlegendentry{{Rama eficiente}}
\addplot[very thick, black, dashed] coordinates {{{inf}}};
\addlegendentry{{Rama ineficiente}}
\addplot[only marks, mark=*, mark size=1.8pt, black, forget plot] coordinates {{(20,12) (32,18) ({s_min:.3f},{m_min:.3f})}};
\node[anchor=north east, font=\footnotesize] at (axis cs:20,12) {{$A$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:32,18) {{$B$}};
\node[anchor=east, font=\footnotesize] at (axis cs:{s_min:.3f},{m_min:.3f}) {{$MV$}};
\end{{axis}}"""
    tikz = "\\begin{tikzpicture}\n" + panel_a + "\n" + panel_b + "\n\\end{tikzpicture}\n"
    (IMG / "anx_dos_acciones.tikz").write_text(tikz, encoding="utf-8")
    w_cero = sB / (sA + sB)
    return w_min, s_min, m_min, w_cero, w_cero * mA + (1 - w_cero) * mB


def diversificacion():
    """A2, I.4.1. Volatilidad de una cartera equiponderada de N acciones con volatilidad media 35 % y correlación
    media 0,30 (panel a, con las dos zonas) o 0,15 y 0,30 (panel b). Valores ilustrativos."""
    sbar = 35.0

    def sigma(n, rho):
        return math.sqrt(sbar**2 / n + (1 - 1 / n) * rho * sbar**2)

    ns = list(range(1, 51))
    c30 = " ".join(f"({n},{sigma(n, 0.30):.3f})" for n in ns)
    c15 = " ".join(f"({n},{sigma(n, 0.15):.3f})" for n in ns)
    a30, a15 = sbar * math.sqrt(0.30), sbar * math.sqrt(0.15)
    panel_a = rf"""\begin{{axis}}[name=a, width=7.6cm, height=6.4cm, xmin=1, xmax=50, ymin=0, ymax=37,
  xlabel={{Número de acciones, $N$}}, ylabel={{Volatilidad de la cartera, $\sigma_p$ (\%)}}, title={{(a) Las dos partes del riesgo}},
  legend pos=north east, {PREAMBULO_EJES}]
\addplot[draw=none, fill=gray!30, area legend] coordinates {{{c30} (50,{a30:.3f}) (1,{a30:.3f})}} -- cycle;
\addlegendentry{{Riesgo específico}}
\addplot[draw=none, fill=gray!65, area legend] coordinates {{(1,0) (50,0) (50,{a30:.3f}) (1,{a30:.3f})}} -- cycle;
\addlegendentry{{Riesgo sistemático}}
\addplot[very thick, black, forget plot] coordinates {{{c30}}};
\end{{axis}}"""
    panel_b = rf"""\begin{{axis}}[at={{(a.east)}}, anchor=west, xshift=1.9cm, width=7.6cm, height=6.4cm, xmin=1, xmax=50, ymin=0, ymax=37,
  xlabel={{Número de acciones, $N$}}, ylabel={{Volatilidad de la cartera, $\sigma_p$ (\%)}}, title={{(b) Dos correlaciones medias}},
  legend pos=north east, {PREAMBULO_EJES}]
\addplot[very thick, black] coordinates {{{c30}}};
\addlegendentry{{$\bar\rho=0{{,}}30$}}
\addplot[very thick, black!55, dashed] coordinates {{{c15}}};
\addlegendentry{{$\bar\rho=0{{,}}15$}}
\addplot[thin, black, dotted, forget plot] coordinates {{(1,{a30:.3f}) (50,{a30:.3f})}};
\addplot[thin, black!55, dotted, forget plot] coordinates {{(1,{a15:.3f}) (50,{a15:.3f})}};
\end{{axis}}"""
    tikz = "\\begin{tikzpicture}\n" + panel_a + "\n" + panel_b + "\n\\end{tikzpicture}\n"
    (IMG / "anx_diversificacion.tikz").write_text(tikz, encoding="utf-8")
    return a30, a15, sigma(10, 0.30), sigma(30, 0.30)


# --- A3: ejemplo de tres acciones del texto viejo (A y B son las de I.3.2; C se añade), en % y %² ---
MU3 = np.array([12.0, 18.0, 22.0])
S3 = np.array([[0.040, 0.002, -0.013], [0.002, 0.102, 0.004], [-0.013, 0.004, 0.130]]) * 1e4
ACTIVOS3 = [("A", 12.0), ("B", 18.0), ("C", 22.0)]


def constantes3():
    """Constantes de la frontera de MERTON (1972): a = 1'Σ⁻¹μ, b = μ'Σ⁻¹μ, c = 1'Σ⁻¹1, d = bc − a²."""
    Si = np.linalg.inv(S3)
    one = np.ones(3)
    a, b, c = one @ Si @ MU3, MU3 @ Si @ MU3, one @ Si @ one
    return Si, a, b, c, b * c - a * a


def sigma_frontera(m, a, b, c, d):
    return math.sqrt((c * m * m - 2 * a * m + b) / d)


def tangente_de(rf):
    """Cartera tangente para un tipo sin riesgo rf (en %): ω_T = Σ⁻¹(μ − rf·1) / 1'Σ⁻¹(μ − rf·1)."""
    Si = np.linalg.inv(S3)
    z = Si @ (MU3 - rf)
    w = z / z.sum()
    return w, float(w @ MU3), float(math.sqrt(w @ S3 @ w))


def puntos_activos(etiquetas=True):
    sig = np.sqrt(np.diag(S3))
    pts = " ".join(f"({s:.3f},{m:.3f})" for s, (_, m) in zip(sig, ACTIVOS3))
    out = [rf"\addplot[only marks, mark=*, mark size=1.6pt, black, forget plot] coordinates {{{pts}}};"]
    if etiquetas:
        for s, (n, m) in zip(sig, ACTIVOS3):
            out.append(rf"\node[anchor=north west, font=\footnotesize] at (axis cs:{s:.3f},{m:.3f}) {{${n}$}};")
    return "\n".join(out)


def dominancia():
    """A3, I.5.1. Criterio de media y varianza: regiones que dominan a una cartera P, dominadas por ella y no
    comparables. Figura abstracta, sin cifras."""
    t = r"""\begin{tikzpicture}[font=\footnotesize]
\fill[gray!22] (0,3.0) rectangle (3.6,5.4);
\fill[gray!55] (3.6,0) rectangle (7.4,3.0);
\draw[-{Stealth[length=2mm]}] (0,0) -- (7.8,0) node[below left] {Volatilidad, $\sigma_p$};
\draw[-{Stealth[length=2mm]}] (0,0) -- (0,5.8) node[above] {Rentabilidad esperada, $\mu_p$};
\draw[dashed] (3.6,0) -- (3.6,5.4);
\draw[dashed] (0,3.0) -- (7.4,3.0);
\fill (3.6,3.0) circle (2.2pt) node[above right] {$P$};
\node[align=center] at (1.8,4.25) {Dominan\\a $P$};
\node[align=center] at (5.5,1.5) {Dominadas\\por $P$};
\node[align=center] at (5.5,4.25) {No\\comparables};
\node[align=center] at (1.8,1.5) {No\\comparables};
\end{tikzpicture}
"""
    (IMG / "anx_dominancia.tikz").write_text(t, encoding="utf-8")


def frontera():
    """A3, I.5.2-I.5.4. Tres figuras, porque se comentan en párrafos distintos: anx_frontera_simulacion, 3000 carteras
    sin ventas en corto con pesos aleatorios (Dirichlet(1,1,1), semilla 5); anx_frontera, frontera analítica con ventas
    en corto (rama eficiente e ineficiente) y cartera de mínima varianza MV; y anx_frontera_cortos, la rama eficiente
    frente a la frontera sin ventas en corto (programación cuadrática con SLSQP)."""
    from scipy.optimize import minimize

    Si, a, b, c, d = constantes3()
    rng = np.random.default_rng(5)
    W = rng.dirichlet([1, 1, 1], 3000)
    sims = " ".join(f"({math.sqrt(w @ S3 @ w):.2f},{w @ MU3:.2f})" for w in W)
    panel_a = rf"""\begin{{axis}}[width=10cm, height=6.6cm, xmin=0, xmax=45, ymin=8, ymax=26,
  xlabel={{Volatilidad, $\sigma_p$ (\%)}}, ylabel={{Rentabilidad esperada, $\mu_p$ (\%)}},
  {PREAMBULO_EJES}]
\addplot[only marks, mark=*, mark size=0.35pt, gray!70, forget plot] coordinates {{{sims}}};
{puntos_activos()}
\end{{axis}}"""
    m_mv, s_mv = a / c, math.sqrt(1 / c)
    sup = " ".join(f"({sigma_frontera(m, a, b, c, d):.3f},{m:.3f})" for m in np.linspace(m_mv, 26, 120))
    inf = " ".join(f"({sigma_frontera(m, a, b, c, d):.3f},{m:.3f})" for m in np.linspace(8, m_mv, 80))
    largos = []
    for m in np.linspace(12.0, 22.0, 81):
        res = minimize(lambda w: w @ S3 @ w, np.ones(3) / 3, method="SLSQP", bounds=[(0, 1)] * 3,
                       constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1},
                                    {"type": "eq", "fun": lambda w, m=m: w @ MU3 - m}])
        largos.append(f"({math.sqrt(res.fun):.3f},{m:.3f})")
    ejes = (r"width=10cm, height=6.6cm, xmin=0, xmax=45, ymin=8, ymax=26,"
            r" xlabel={Volatilidad, $\sigma_p$ (\%)}, ylabel={Rentabilidad esperada, $\mu_p$ (\%)},"
            r" legend pos=north west, legend style={fill=none}, ")
    mv = (rf"\addplot[only marks, mark=square*, mark size=1.8pt, black, forget plot] coordinates {{({s_mv:.3f},{m_mv:.3f})}};"
          "\n" rf"\node[anchor=east, font=\footnotesize] at (axis cs:{s_mv - 0.5:.3f},{m_mv:.3f}) {{$MV$}};")
    panel_b = (rf"\begin{{axis}}[{ejes}{PREAMBULO_EJES}]" "\n"
               rf"\addplot[very thick, black] coordinates {{{sup}}};" "\n" r"\addlegendentry{Eficiente}" "\n"
               rf"\addplot[thick, black, dashed] coordinates {{{inf}}};" "\n" r"\addlegendentry{Ineficiente}" "\n"
               + puntos_activos() + "\n" + mv + "\n\\end{axis}")
    panel_c = (rf"\begin{{axis}}[{ejes}{PREAMBULO_EJES}]" "\n"
               rf"\addplot[very thick, black] coordinates {{{sup}}};" "\n" r"\addlegendentry{Con ventas en corto}" "\n"
               rf"\addplot[thick, black!55, dotted] coordinates {{{' '.join(largos)}}};" "\n"
               r"\addlegendentry{Sin ventas en corto}" "\n" + puntos_activos() + "\n" + mv + "\n\\end{axis}")
    for nombre, eje in (("anx_frontera_simulacion", panel_a), ("anx_frontera", panel_b), ("anx_frontera_cortos", panel_c)):
        escribir_tikz(nombre, "\\begin{tikzpicture}\n" + eje + "\n\\end{tikzpicture}\n")
    return m_mv, s_mv, a, b, c, d


def tangente():
    """A3, I.6.1-I.6.3. Tipo sin riesgo del 10 %; tres rectas de asignación de capital: con MV, con A y con la
    cartera tangente T."""
    Si, a, b, c, d = constantes3()
    rf = 10.0
    wT, mT, sT = tangente_de(rf)
    m_mv, s_mv = a / c, math.sqrt(1 / c)
    sup = " ".join(f"({sigma_frontera(m, a, b, c, d):.3f},{m:.3f})" for m in np.linspace(m_mv, 26, 120))
    inf = " ".join(f"({sigma_frontera(m, a, b, c, d):.3f},{m:.3f})" for m in np.linspace(9, m_mv, 80))

    def recta(m, s):
        pend = (m - rf) / s
        return f"(0,{rf:.3f}) (45,{rf + 45 * pend:.3f})"

    t = rf"""\begin{{tikzpicture}}
\begin{{axis}}[width=11cm, height=7.4cm, xmin=0, xmax=45, ymin=8, ymax=26,
  xlabel={{Volatilidad, $\sigma_p$ (\%)}}, ylabel={{Rentabilidad esperada, $\mu_p$ (\%)}},
  legend pos=north west, legend style={{fill=none}}, {PREAMBULO_EJES}]
\addplot[thick, black!40] coordinates {{{sup}}};
\addlegendentry{{Frontera eficiente}}
\addplot[thick, black!40, dashed, forget plot] coordinates {{{inf}}};
\addplot[thick, black!55, dash dot] coordinates {{{recta(12.0, 20.0)}}};
\addlegendentry{{Recta con $A$}}
\addplot[thick, black!70, dashed] coordinates {{{recta(m_mv, s_mv)}}};
\addlegendentry{{Recta con $MV$}}
\addplot[very thick, black] coordinates {{{recta(mT, sT)}}};
\addlegendentry{{Recta con $T$}}
{puntos_activos()}
\addplot[only marks, mark=square*, mark size=1.8pt, black, forget plot] coordinates {{({s_mv:.3f},{m_mv:.3f}) ({sT:.3f},{mT:.3f}) (0,{rf})}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{s_mv:.3f},{m_mv:.3f}) {{$MV$}};
\node[anchor=south east, font=\footnotesize] at (axis cs:{sT:.3f},{mT:.3f}) {{$T$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:0.3,{rf - 0.15}) {{$r_f$}};
\end{{axis}}
\end{{tikzpicture}}
"""
    (IMG / "anx_tangente.tikz").write_text(t, encoding="utf-8")
    return wT, mT, sT, (mT - rf) / sT, (m_mv - rf) / s_mv, (12.0 - rf) / 20.0


def separacion():
    """A3, I.6.4. Dos figuras, porque se comentan en párrafos distintos: anx_separacion, dos inversores sobre la misma
    recta con la tangente (r_f = 10 %), con curvas de indiferencia de media y varianza que llevan a invertir y = 0,5 e
    y = 1,5 en T; y anx_separacion_tipos, tipo de préstamo del 8 % y de endeudamiento del 12 %, con las tangentes T_L y
    T_B y el conjunto eficiente quebrado."""
    Si, a, b, c, d = constantes3()
    m_mv = a / c
    rf = 10.0
    wT, mT, sT = tangente_de(rf)
    sup = " ".join(f"({sigma_frontera(m, a, b, c, d):.3f},{m:.3f})" for m in np.linspace(m_mv, 26, 120))
    curvas, puntos = [], []
    for y, est in ((0.5, "thick, black!60"), (1.5, "thick, black!60, dashed")):
        # en decimales: y* = (mu_T − rf) / (gamma sigma_T²)  ⇒  gamma = (mu_T − rf) / (y* sigma_T²)
        g = ((mT - rf) / 100) / (y * (sT / 100) ** 2)
        s0, m0 = y * sT, rf + y * (mT - rf)
        u = m0 / 100 - g / 2 * (s0 / 100) ** 2
        pts = " ".join(f"({s:.3f},{100 * (u + g / 2 * (s / 100) ** 2):.3f})" for s in np.linspace(0, 45, 90))
        curvas.append(rf"\addplot[{est}] coordinates {{{pts}}};")
        puntos.append((s0, m0))
    panel_a = rf"""\begin{{axis}}[width=10cm, height=6.6cm, xmin=0, xmax=45, ymin=8, ymax=26,
  xlabel={{Volatilidad, $\sigma_p$ (\%)}}, ylabel={{Rentabilidad esperada, $\mu_p$ (\%)}},
  legend pos=south east, legend style={{fill=none}}, {PREAMBULO_EJES}]
\addplot[thick, black!35, forget plot] coordinates {{{sup}}};
\addplot[very thick, black, forget plot] coordinates {{(0,{rf}) (45,{rf + 45 * (mT - rf) / sT:.3f})}};
{curvas[0]}
\addlegendentry{{Más averso}}
{curvas[1]}
\addlegendentry{{Menos averso}}
\addplot[only marks, mark=*, mark size=1.8pt, black, forget plot] coordinates {{({puntos[0][0]:.3f},{puntos[0][1]:.3f}) ({puntos[1][0]:.3f},{puntos[1][1]:.3f}) ({sT:.3f},{mT:.3f}) (0,{rf})}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{puntos[0][0]:.3f},{puntos[0][1]:.3f}) {{$L$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{puntos[1][0]:.3f},{puntos[1][1]:.3f}) {{$E$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{sT:.3f},{mT:.3f}) {{$T$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:0.3,{rf - 0.15}) {{$r_f$}};
\end{{axis}}"""

    rl, rb = 8.0, 12.0
    _, mL, sL = tangente_de(rl)
    _, mB, sB = tangente_de(rb)
    arco = " ".join(f"({sigma_frontera(m, a, b, c, d):.3f},{m:.3f})" for m in np.linspace(mL, mB, 60))
    resto = " ".join(f"({sigma_frontera(m, a, b, c, d):.3f},{m:.3f})" for m in np.linspace(m_mv, 26, 120))
    pB = (mB - rb) / sB
    panel_b = rf"""\begin{{axis}}[width=10cm, height=6.6cm, xmin=0, xmax=45, ymin=6, ymax=26,
  xlabel={{Volatilidad, $\sigma_p$ (\%)}}, ylabel={{Rentabilidad esperada, $\mu_p$ (\%)}},
  {PREAMBULO_EJES}]
\addplot[thick, black!35, forget plot] coordinates {{{resto}}};
\addplot[thin, black!50, dotted, forget plot] coordinates {{({sL:.3f},{mL:.3f}) (45,{rl + 45 * (mL - rl) / sL:.3f})}};
\addplot[thin, black!50, dotted, forget plot] coordinates {{(0,{rb}) ({sB:.3f},{mB:.3f})}};
\addplot[very thick, black, forget plot] coordinates {{(0,{rl}) ({sL:.3f},{mL:.3f})}};
\addplot[very thick, black, forget plot] coordinates {{{arco}}};
\addplot[very thick, black, forget plot] coordinates {{({sB:.3f},{mB:.3f}) (45,{rb + 45 * pB:.3f})}};
\addplot[only marks, mark=*, mark size=1.8pt, black, forget plot] coordinates {{({sL:.3f},{mL:.3f}) ({sB:.3f},{mB:.3f}) (0,{rl}) (0,{rb})}};
\node[anchor=south east, font=\footnotesize] at (axis cs:{sL:.3f},{mL:.3f}) {{$T_L$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:{sB:.3f},{mB:.3f}) {{$T_B$}};
\node[anchor=north west, font=\footnotesize] at (axis cs:0.3,{rl - 0.15}) {{$r_L$}};
\node[anchor=south west, font=\footnotesize] at (axis cs:0.3,{rb}) {{$r_B$}};
\end{{axis}}"""
    escribir_tikz("anx_separacion", "\\begin{tikzpicture}\n" + panel_a + "\n\\end{tikzpicture}\n")
    escribir_tikz("anx_separacion_tipos", "\\begin{tikzpicture}\n" + panel_b + "\n\\end{tikzpicture}\n")
    return puntos, (sL, mL), (sB, mB)


def eleccion():
    """A4, I.7. Dos figuras, porque se comentan en apartados distintos: anx_eleccion, curvas de indiferencia de media y
    varianza, mu = U + (theta/2) sigma², para theta = 2 y 6 y dos niveles de utilidad cada una; y anx_proporcion,
    proporción óptima en la tangente del ejemplo (rf = 10 %), y* = S_T/(theta sigma_T), con los inversores L (y = 0,5),
    el de y = 1 y E (y = 1,5)."""
    curvas = []
    for g, us, est, nombre in ((2.0, (10.0, 14.0), "thick, black", "2"), (6.0, (10.0, 14.0), "thick, black!55, dashed", "6")):
        for k, u in enumerate(us):
            pts = " ".join(f"({s:.2f},{u + g / 2 * s * s / 100:.3f})" for s in np.linspace(0, 40, 81))
            if k == 0:
                curvas.append(rf"\addplot[{est}] coordinates {{{pts}}};" + "\n" + rf"\addlegendentry{{$\theta={nombre}$}}")
            else:
                curvas.append(rf"\addplot[{est}, forget plot] coordinates {{{pts}}};")
    panel_a = rf"""\begin{{axis}}[width=10cm, height=6.6cm, xmin=0, xmax=40, ymin=8, ymax=30,
  xlabel={{Volatilidad, $\sigma_p$ (\%)}}, ylabel={{Rentabilidad esperada, $\mu_p$ (\%)}},
  legend pos=north west, legend style={{fill=none}}, {PREAMBULO_EJES}]
{chr(10).join(curvas)}
\end{{axis}}"""
    wT, mT, sT = tangente_de(10.0)
    S_T = (mT - 10.0) / sT
    k = S_T / (sT / 100)
    curva = " ".join(f"({g:.3f},{k / g:.4f})" for g in np.linspace(0.75, 10, 120))
    marcas = [(k / 0.5, 0.5, "L"), (k / 1.0, 1.0, ""), (k / 1.5, 1.5, "E")]
    nodos = "\n".join(rf"\node[anchor=south west, font=\footnotesize] at (axis cs:{g:.3f},{y:.3f}) {{${n}$}};" for g, y, n in marcas if n)
    pts = " ".join(f"({g:.3f},{y:.3f})" for g, y, _ in marcas)
    panel_b = rf"""\begin{{axis}}[width=10cm, height=6.6cm, xmin=0, xmax=10, ymin=0, ymax=3.4,
  xlabel={{Aversión relativa al riesgo, $\theta$}}, ylabel={{Proporción en la tangente, $y^*$}},
  {PREAMBULO_EJES}]
\addplot[very thick, black] coordinates {{{curva}}};
\addplot[thin, black, dotted] coordinates {{(0,1) (10,1)}};
\addplot[only marks, mark=*, mark size=1.8pt, black] coordinates {{{pts}}};
{nodos}
\node[anchor=south east, font=\footnotesize] at (axis cs:9.8,1.02) {{Se endeudan}};
\node[anchor=north east, font=\footnotesize] at (axis cs:9.8,0.98) {{Prestan}};
\end{{axis}}"""
    escribir_tikz("anx_eleccion", "\\begin{tikzpicture}\n" + panel_a + "\n\\end{tikzpicture}\n")
    escribir_tikz("anx_proporcion", "\\begin{tikzpicture}\n" + panel_b + "\n\\end{tikzpicture}\n")
    return S_T, k, [g for g, _, _ in marcas]


def indice_unico():
    """A4, I.8. Rectas características simuladas (semilla 9): 60 rentabilidades mensuales del mercado, N(0,8 %; 4,5 %),
    y de dos acciones: beta 1,4 con riesgo específico mensual del 6 % y beta 0,6 con el 3 %; recta de MCO."""
    rng = np.random.default_rng(9)
    rm = rng.normal(0.8, 4.5, 60)
    paneles = []
    for i, (beta, se, etiqueta) in enumerate(((1.4, 6.0, "1{,}4"), (0.6, 3.0, "0{,}6"))):
        rj = 0.2 + beta * rm + rng.normal(0, se, 60)
        bh, ah = np.polyfit(rm, rj, 1)
        pts = " ".join(f"({x:.2f},{y:.2f})" for x, y in zip(rm, rj))
        recta = f"(-12,{ah + bh * -12:.3f}) (12,{ah + bh * 12:.3f})"
        pos = "name=a" if i == 0 else r"at={(a.east)}, anchor=west, xshift=1.9cm"
        paneles.append(rf"""\begin{{axis}}[{pos}, width=7.6cm, height=6.6cm, xmin=-12, xmax=12, ymin=-24, ymax=24,
  xlabel={{Rentabilidad del mercado, $r_M$ (\%)}}, ylabel={{Rentabilidad de la acción, $r_j$ (\%)}},
  title={{({"ab"[i]}) $\beta_j={etiqueta}$}}, {PREAMBULO_EJES}]
\addplot[only marks, mark=*, mark size=1pt, black!65] coordinates {{{pts}}};
\addplot[very thick, black] coordinates {{{recta}}};
\addplot[thin, gray, dashed] coordinates {{(-12,0) (12,0)}};
\addplot[thin, gray, dashed] coordinates {{(0,-24) (0,24)}};
\end{{axis}}""")
    tikz = "\\begin{tikzpicture}\n" + "\n".join(paneles) + "\n\\end{tikzpicture}\n"
    (IMG / "anx_indice_unico.tikz").write_text(tikz, encoding="utf-8")


def estimacion():
    """A4, I.9.1. Error de estimación (al estilo de BROADIE, 1993): con los parámetros verdaderos del ejemplo de tres
    acciones, 1000 muestras de 120 rentabilidades mensuales normales (semilla 21). En cada muestra se estiman μ y Σ, se
    calcula la frontera eficiente estimada desde su cartera de mínima varianza en pasos de 1 punto de rentabilidad
    esperada, y se evalúa cada cartera con los parámetros verdaderos. Se promedian, paso a paso, los puntos estimados
    (lo que cree el inversor) y los realizados (lo que obtiene), frente a la frontera verdadera."""
    mu = MU3 / 100
    S = S3 / 1e4
    rng = np.random.default_rng(21)
    T, nsim, K = 120, 1000, 13
    L = np.linalg.cholesky(S / 12)
    est = np.zeros((nsim, K, 2))
    rea = np.zeros((nsim, K, 2))
    one = np.ones(3)
    for k in range(nsim):
        X = mu / 12 + rng.standard_normal((T, 3)) @ L.T
        muh, Sh = X.mean(0) * 12, np.cov(X, rowvar=False) * 12
        Si = np.linalg.inv(Sh)
        a, b, c = one @ Si @ muh, muh @ Si @ muh, one @ Si @ one
        d = b * c - a * a
        for i in range(K):
            m = a / c + 0.01 * i
            w = ((c * m - a) * (Si @ muh) + (b - a * m) * (Si @ one)) / d
            est[k, i] = (math.sqrt(w @ Sh @ w), m)
            rea[k, i] = (math.sqrt(w @ S @ w), w @ mu)
    E = est.mean(0) * 100
    R = rea.mean(0) * 100
    Si, a, b, c, d = constantes3()
    m_mv = a / c
    ver = " ".join(f"({sigma_frontera(m, a, b, c, d):.3f},{m:.3f})" for m in np.linspace(m_mv, 27, 100))
    ce = " ".join(f"({s:.3f},{m:.3f})" for s, m in E)
    cr = " ".join(f"({s:.3f},{m:.3f})" for s, m in R)
    tikz = rf"""\begin{{tikzpicture}}
\begin{{axis}}[width=11cm, height=7cm, xmin=10, xmax=50, ymin=12, ymax=28,
  xlabel={{Volatilidad, $\sigma_p$ (\%)}}, ylabel={{Rentabilidad esperada, $\mu_p$ (\%)}},
  legend pos=north west, legend style={{fill=none}}, {PREAMBULO_EJES}]
\addplot[very thick, black] coordinates {{{ver}}};
\addlegendentry{{Verdadera}}
\addplot[thick, black, dashed, mark=*, mark size=1pt] coordinates {{{ce}}};
\addlegendentry{{Estimada (en la muestra)}}
\addplot[thick, black!50, mark=square*, mark size=1pt] coordinates {{{cr}}};
\addlegendentry{{Realizada (fuera de la muestra)}}
\end{{axis}}
\end{{tikzpicture}}
"""
    (IMG / "anx_estimacion.tikz").write_text(tikz, encoding="utf-8")
    return E, R


if __name__ == "__main__":
    residual()
    p, esp, med = ergodicidad()
    print(f"ergodicidad: P(W60 > 1) = {p:.4f}; E[W60] = {esp:.2f}; mediana = {med:.4f}")
    k, sg, si = colas()
    print(f"colas: exceso de curtosis GARCH simulado = {k:.2f}; sigma GARCH = {sg:.2f} %; sigma iid = {si:.2f} %")
    correlacion()
    w_min, s_min, m_min, w_cero, m_cero = dos_acciones()
    print(f"dos acciones (rho=0): w_A min = {w_min:.4f}, sigma = {s_min:.2f} %, mu = {m_min:.2f} %;"
          f" rho=-1: w_A sin riesgo = {w_cero:.4f}, mu = {m_cero:.2f} %")
    a30, a15, s10, s30 = diversificacion()
    print(f"diversificación: asíntotas {a30:.2f} % y {a15:.2f} %; sigma(10) = {s10:.2f} %; sigma(30) = {s30:.2f} %")
    dominancia()
    m_mv, s_mv, a, b, c, d = frontera()
    print(f"frontera: a={a:.6f} b={b:.6f} c={c:.8f} d={d:.8f} (en %); MV: mu={m_mv:.2f} %, sigma={s_mv:.2f} %")
    wT, mT, sT, shT, shMV, shA = tangente()
    print(f"tangente (rf=10 %): pesos={np.round(wT, 4)}, mu={mT:.2f} %, sigma={sT:.2f} %, SHARPE T={shT:.3f}, MV={shMV:.3f}, A={shA:.3f}")
    puntos, TL, TB = separacion()
    print(f"separación: L={puntos[0]}, E={puntos[1]}, T_L={TL}, T_B={TB}")
    S_T, kk, gammas = eleccion()
    print(f"elección: S_T = {S_T:.4f}; y* = {kk:.4f}/gamma; gammas de L, y=1 y E: {np.round(gammas, 3)}")
    indice_unico()
    E, R = estimacion()
    print("estimación (σ, μ) en %, pasos 0, 6 y 12:", np.round(E[[0, 6, 12]], 1).tolist(), np.round(R[[0, 6, 12]], 1).tolist())
