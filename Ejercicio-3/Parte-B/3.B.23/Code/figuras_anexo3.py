"""Figuras del anexo III del 3.B.23 (eficiencia y análisis de inversiones).

Las de datos usan la biblioteca de FRENCH (Code/datos_french.py): rentabilidades del mercado de Estados Unidos, todas
las acciones de CRSP ponderadas por su valor, Mkt-RF + RF. Las demás son esquemas sin datos.
Uso, desde la carpeta del tema:  python3 -B Code/figuras_anexo3.py  y después  bash Code/generar_figura.sh <nombre>
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figuras_anexo1 import IMG, PREAMBULO_EJES  # noqa: E402

DECENIOS = [(1926, 1935), (1936, 1945), (1946, 1955), (1956, 1965), (1966, 1975), (1976, 1985), (1986, 1995),
            (1996, 2005), (2006, 2015), (2016, 2025)]


def conjuntos_informacion():
    """A8, III.1.1. Las tres formas de eficiencia de FAMA (1970) como conjuntos de información anidados."""
    tikz = r"""\begin{tikzpicture}[font=\footnotesize]
\draw[fill=black!5, rounded corners=8pt] (0,0) rectangle (12,5);
\draw[fill=black!13, rounded corners=8pt] (0.45,0.4) rectangle (8.7,4.6);
\draw[fill=black!24, rounded corners=8pt] (0.9,0.8) rectangle (5.1,4.2);
\node[align=center] at (3.0,2.5) {\textbf{Forma débil}\\[2pt]Precios y volúmenes\\pasados};
\node[align=center] at (6.9,2.5) {\textbf{Forma semifuerte}\\[2pt]Toda la información\\pública};
\node[align=center] at (10.35,2.5) {\textbf{Forma fuerte}\\[2pt]Toda la información,\\también la privada};
\end{tikzpicture}
"""
    (IMG / "anx_conjuntos_informacion.tikz").write_text(tikz, encoding="utf-8")


def reaccion_noticias():
    """A8, III.1.3. Rentabilidad anormal acumulada en torno a una noticia que eleva el valor en ΔV: reacción eficiente,
    insuficiente (deriva posterior), excesiva (corrección posterior) y con filtración previa. Esquema sin datos."""
    t = np.arange(-10, 10.01, 0.25)


    eficiente = "(-10,0) (0,0) (0,1) (10,1)"
    puntos_ins = [(x, 0.5 + 0.5 * (1 - math.exp(-x / 2.5))) for x in t if x >= 0]
    insuficiente = "(-10,0) (0,0) " + " ".join(f"({x:.2f},{y:.4f})" for x, y in puntos_ins)
    puntos_exc = [(x, 1 + 0.4 * math.exp(-x / 2.5)) for x in t if x >= 0]
    excesiva = "(-10,0) (0,0) " + " ".join(f"({x:.2f},{y:.4f})" for x, y in puntos_exc)
    puntos_fil = [(x, 0.0 if x < -6 else 0.6 * (1 - math.exp(-(x + 6) / 2)) / (1 - math.exp(-6 / 2))) for x in t if x < 0]
    filtracion = " ".join(f"({x:.2f},{y:.4f})" for x, y in puntos_fil) + " (0,0.6) (0,1) (10,1)"
    tikz = rf"""\begin{{tikzpicture}}
\begin{{axis}}[width=11cm, height=6.6cm, xmin=-10, xmax=10, ymin=-0.15, ymax=1.55, ytick={{0,1}}, yticklabels={{$0$, $\Delta V$}},
  xlabel={{Días respecto del anuncio}}, ylabel={{Rentabilidad anormal acumulada}},
  legend pos=north west, {PREAMBULO_EJES}]
\addplot[thin, black!30, forget plot] coordinates {{(0,-0.15) (0,1.55)}};
\addplot[very thick, black] coordinates {{{eficiente}}};
\addlegendentry{{Eficiente}}
\addplot[thick, black!60, dashed] coordinates {{{insuficiente}}};
\addlegendentry{{Insuficiente}}
\addplot[thick, black!60, dash dot] coordinates {{{excesiva}}};
\addlegendentry{{Excesiva}}
\addplot[thick, black, dotted] coordinates {{{filtracion}}};
\addlegendentry{{Con filtración previa}}
\end{{axis}}
\end{{tikzpicture}}
"""
    (IMG / "anx_reaccion_noticias.tikz").write_text(tikz, encoding="utf-8")


def razon_varianzas_mensual(x, q):
    """Razón de varianzas de LO y MacKINLAY (1988) con solapamiento y corrección del sesgo, y su error típico con
    rentabilidades independientes e idénticamente distribuidas."""
    T = len(x)
    mu = x.mean()
    var1 = ((x - mu) ** 2).sum() / (T - 1)
    sumas = np.convolve(x, np.ones(q), mode="valid")
    m = q * (T - q + 1) * (1 - q / T)
    varq = ((sumas - q * mu) ** 2).sum() / m
    error = math.sqrt(2 * (2 * q - 1) * (q - 1) / (3 * q * T))
    return varq / var1, error


def razon_varianzas():
    """A8, III.1.3. (a) Razón de varianzas de las rentabilidades logarítmicas mensuales del mercado de Estados Unidos
    para horizontes de 1 a 60 meses, julio de 1926 a diciembre de 2025 y julio de 1963 a diciembre de 2025, con la
    banda del 95 % de un paseo aleatorio (muestra larga). (b) Autocorrelación de primer orden de las rentabilidades
    diarias del mercado en cada decenio, de julio de 1926 a diciembre de 2025, con la banda ±2/raíz(n)."""
    from datos_french import FACTORES, diaria, seccion
    meses, cols, f = seccion(FACTORES, ",Mkt-RF")
    dentro = meses <= 202512
    total = f[dentro, cols.index("Mkt-RF")] + f[dentro, cols.index("RF")]
    x_largo = np.log1p(total / 100)
    x_corto = np.log1p(total[meses[dentro] >= 196307] / 100)
    qs = list(range(1, 61))
    vr_largo = [razon_varianzas_mensual(x_largo, q) for q in qs]
    vr_corto = [razon_varianzas_mensual(x_corto, q) for q in qs]
    fechas, cd, d = diaria()
    rd = d[:, cd.index("Mkt-RF")] + d[:, cd.index("RF")]
    anios = fechas // 10000
    autoc = []
    for a, b in DECENIOS:
        s = (anios >= a) & (anios <= b)
        y = rd[s]
        autoc.append((a, b, np.corrcoef(y[:-1], y[1:])[0, 1], int(s.sum())))
    linea_l = " ".join(f"({q},{v:.4f})" for q, (v, _) in zip(qs, vr_largo))
    linea_c = " ".join(f"({q},{v:.4f})" for q, (v, _) in zip(qs, vr_corto))
    sup = " ".join(f"({q},{1 + 1.96 * e:.4f})" for q, (_, e) in zip(qs, vr_largo))
    inf = " ".join(f"({q},{1 - 1.96 * e:.4f})" for q, (_, e) in zip(reversed(qs), reversed(vr_largo)))
    panel_a = rf"""\begin{{axis}}[name=a, width=7.6cm, height=6.6cm, xmin=1, xmax=60, ymin=0.3, ymax=1.7, xtick={{1,12,24,36,48,60}},
  xlabel={{Horizonte, $q$ (meses)}}, ylabel={{Razón de varianzas}}, title={{(a) Razón de varianzas mensual}},
  legend pos=north west, {PREAMBULO_EJES}, legend style={{fill=none}}]
\addplot[fill=black!10, draw=none, area legend] coordinates {{{sup} {inf}}} -- cycle;
\addlegendentry{{Paseo aleatorio ($95\%$)}}
\addplot[very thick, black] coordinates {{{linea_l}}};
\addlegendentry{{$1926$-$2025$}}
\addplot[thick, black!50, dashed] coordinates {{{linea_c}}};
\addlegendentry{{$1963$-$2025$}}
\addplot[thin, black!40, forget plot] coordinates {{(1,1) (60,1)}};
\end{{axis}}"""
    barras = " ".join(f"({k + 1},{c:.4f})" for k, (_, _, c, _) in enumerate(autoc))
    banda = 2 / math.sqrt(np.mean([n for *_, n in autoc]))
    etiquetas = ",".join(f"{{${str(a)[2:]}$-${str(b)[2:]}$}}" for a, b, _, _ in autoc)
    panel_b = rf"""\begin{{axis}}[at={{(a.east)}}, anchor=west, xshift=1.9cm, width=7.6cm, height=6.6cm, xmin=0.4, xmax=10.6, ymin=-0.15, ymax=0.35,
  xtick={{1,...,10}}, xticklabels={{{etiquetas}}}, x tick label style={{rotate=60, anchor=east, font=\scriptsize}},
  xlabel={{Decenio}}, ylabel={{Autocorrelación de primer orden}}, title={{(b) Rentabilidades diarias}}, {PREAMBULO_EJES}]
\addplot[fill=black!8, draw=none, forget plot] coordinates {{(0.4,{-banda:.4f}) (10.6,{-banda:.4f}) (10.6,{banda:.4f}) (0.4,{banda:.4f})}} -- cycle;
\addplot[ybar, bar width=10pt, fill=black!45, draw=black!70] coordinates {{{barras}}};
\addplot[thin, black!40] coordinates {{(0.4,0) (10.6,0)}};
\end{{axis}}"""
    tikz = "\\begin{tikzpicture}\n" + panel_a + "\n" + panel_b + "\n\\end{tikzpicture}\n"
    (IMG / "anx_razon_varianzas.tikz").write_text(tikz, encoding="utf-8")
    return dict(qs=qs, vr_largo=vr_largo, vr_corto=vr_corto, autoc=autoc, banda=banda,
                meses=int(dentro.sum()), meses_corto=len(x_corto), dias=len(rd))


def grossman_stiglitz():
    """A8, III.2.1. Equilibrio de GROSSMAN y STIGLITZ (1980): la ventaja de informarse, ψ(κ), cae con la proporción de
    informados, κ, porque el precio revela más; los inversores se informan hasta que la ventaja iguala el coste, χ. Con
    un coste menor, χ', hay más informados. Esquema sin datos."""
    k = np.linspace(0, 1, 101)
    ventaja = 1.2 * (1 - k) ** 1.6
    curva = " ".join(f"({a:.3f},{b:.4f})" for a, b in zip(k, ventaja))
    C, C2 = 0.42, 0.14
    k1 = 1 - (C / 1.2) ** (1 / 1.6)
    k2 = 1 - (C2 / 1.2) ** (1 / 1.6)
    tikz = rf"""\begin{{tikzpicture}}
\begin{{axis}}[width=10cm, height=6.6cm, xmin=0, xmax=1, ymin=0, ymax=1.3, xtick={{0,{k1:.3f},{k2:.3f},1}},
  xticklabels={{$0$,$\kappa^*$,$\kappa^{{*\prime}}$,$1$}}, ytick={{{C2},{C}}}, yticklabels={{$\chi'$,$\chi$}},
  xlabel={{Proporción de inversores informados, $\kappa$}}, ylabel={{Ventaja y coste de informarse}}, {PREAMBULO_EJES}]
\addplot[very thick, black] coordinates {{{curva}}};
\node[anchor=south west, font=\footnotesize] at (axis cs:0.08,{1.2 * (0.92) ** 1.6:.3f}) {{$\psi(\kappa)$}};
\addplot[thick, black!60, dashed] coordinates {{(0,{C}) (1,{C})}};
\addplot[thick, black!60, dashed] coordinates {{(0,{C2}) (1,{C2})}};
\addplot[thin, black!40, dotted] coordinates {{({k1:.3f},0) ({k1:.3f},{C})}};
\addplot[thin, black!40, dotted] coordinates {{({k2:.3f},0) ({k2:.3f},{C2})}};
\addplot[only marks, mark=*, mark size=1.8pt, black] coordinates {{({k1:.3f},{C}) ({k2:.3f},{C2})}};
\end{{axis}}
\end{{tikzpicture}}
"""
    (IMG / "anx_grossman_stiglitz.tikz").write_text(tikz, encoding="utf-8")
    return k1, k2


if __name__ == "__main__":
    conjuntos_informacion()
    reaccion_noticias()
    r = razon_varianzas()
    print(f"meses {r['meses']} (desde 1963: {r['meses_corto']}), días {r['dias']}")
    for q in (2, 3, 6, 12, 24, 36, 48, 60):
        (vl, el), (vc, ec) = r["vr_largo"][q - 1], r["vr_corto"][q - 1]
        print(f"  q={q:2d}: VR 1926-2025 {vl:.3f} (z {(vl - 1) / el:+.2f}) | 1963-2025 {vc:.3f} (z {(vc - 1) / ec:+.2f})")
    for a, b, c, n in r["autoc"]:
        print(f"  {a}-{b}: autocorrelación diaria {c:+.3f} (n {n})")
    print("banda ±", round(r["banda"], 4))
    print("Grossman-Stiglitz", grossman_stiglitz())


# --- A9: análisis técnico ---

def _indice_diario():
    """Fechas e índice de rentabilidad total diaria del mercado (Mkt-RF + RF de FRENCH), base 1 el 30/06/1926."""
    from datos_french import diaria
    fechas, cd, d = diaria()
    r = (d[:, cd.index("Mkt-RF")] + d[:, cd.index("RF")]) / 100
    rf = d[:, cd.index("RF")] / 100
    return fechas, np.cumprod(1 + r), r, rf


def _media(x, n):
    salida = np.full(len(x), np.nan)
    c = np.cumsum(np.insert(x, 0, 0.0))
    salida[n - 1:] = (c[n:] - c[:-n]) / n
    return salida


def _exponencial(x, n):
    a = 2 / (n + 1)
    salida = np.empty(len(x))
    salida[0] = x[0]
    for t in range(1, len(x)):
        salida[t] = a * x[t] + (1 - a) * salida[t - 1]
    return salida


def _rsi(p, n=14):
    """RSI de WILDER (1978) con medias suavizadas de WILDER (factor 1/n)."""
    d = np.diff(p)
    sube, baja = np.clip(d, 0, None), np.clip(-d, 0, None)
    ms, mb = np.full(len(p), np.nan), np.full(len(p), np.nan)
    ms[n], mb[n] = sube[:n].mean(), baja[:n].mean()
    for t in range(n + 1, len(p)):
        ms[t] = (ms[t - 1] * (n - 1) + sube[t - 1]) / n
        mb[t] = (mb[t - 1] * (n - 1) + baja[t - 1]) / n
    return 100 - 100 / (1 + ms / mb)


def regla_media_movil(n=200, coste=0.001):
    """A9, III.3.5. Regla de la media móvil de n días sobre el índice diario del mercado de Estados Unidos: se está en
    el mercado al día siguiente de un cierre por encima de la media y en letras del Tesoro al día siguiente de uno por
    debajo; coste de cada cambio de posición en tanto por uno. Resultados por tramos: rentabilidad anual compuesta,
    volatilidad, ratio de SHARPE y máxima caída, frente a mantener el índice."""
    fechas, indice, r, rf = _indice_diario()
    sma = _media(indice, n)
    dentro = (indice > sma).astype(float)
    posicion = np.concatenate([[np.nan], dentro[:-1]])
    valido = ~np.isnan(sma)
    posicion[~np.concatenate([[False], valido[:-1]])] = np.nan
    ok = ~np.isnan(posicion)
    cambios = np.concatenate([[0.0], np.abs(np.diff(np.nan_to_num(posicion)))])
    r_regla = np.where(posicion == 1, r, rf) - coste * cambios
    anios = fechas // 10000

    def medidas(serie, libre, mascara):
        s, lr = serie[mascara], libre[mascara]
        riqueza = np.cumprod(1 + s)
        anual = riqueza[-1] ** (252 / len(s)) - 1
        exceso = s - lr
        sharpe = exceso.mean() / exceso.std(ddof=1) * math.sqrt(252)
        caida = (riqueza / np.maximum.accumulate(riqueza) - 1).min()
        return dict(anual=anual * 100, vol=s.std(ddof=1) * math.sqrt(252) * 100, sharpe=sharpe, caida=caida * 100)
    tramos = {}
    for a, b in ((1927, 2025), (1927, 1986), (1987, 2025), (1927, 1945), (1946, 1986), (1987, 2006), (2007, 2025)):
        m = ok & (anios >= a) & (anios <= b)
        tramos[(a, b)] = dict(mercado=medidas(r, rf, m), regla=medidas(r_regla, rf, m),
                              en_mercado=float(posicion[m].mean()), cambios=int(cambios[m].sum()))
    return dict(fechas=fechas, ok=ok, r=r, r_regla=r_regla, rf=rf, tramos=tramos, posicion=posicion)


def grafico_regla_media_movil():
    """Figura de la regla: (a) valor de un dólar invertido a principios de 1927 en el mercado y con la regla
    (escala logarítmica); (b) ratio de SHARPE de cada estrategia por tramos."""
    res = regla_media_movil()
    fechas, ok = res["fechas"], res["ok"]
    m = ok & (fechas >= 19270101) & (fechas <= 20251231)
    f = fechas[m]
    x = f // 10000 + ((f // 100) % 100 - 0.5) / 12
    w_m = np.cumprod(1 + res["r"][m])
    w_r = np.cumprod(1 + res["r_regla"][m])
    paso = 21
    lin_m = " ".join(f"({a:.3f},{b:.4f})" for a, b in zip(x[::paso], w_m[::paso]))
    lin_r = " ".join(f"({a:.3f},{b:.4f})" for a, b in zip(x[::paso], w_r[::paso]))
    panel_a = rf"""\begin{{axis}}[name=a, width=7.6cm, height=6.6cm, ymode=log, xmin=1927, xmax=2026, ymin=0.1, ymax=50000,
  xtick={{1930,1950,1970,1990,2010}}, ytick={{0.1,1,10,100,1000,10000}}, log ticks with fixed point,
  xlabel={{Año}}, ylabel={{Valor de un dólar invertido en $1927$}}, title={{(a) Riqueza acumulada}},
  legend pos=north west, {PREAMBULO_EJES}]
\addplot[very thick, black] coordinates {{{lin_m}}};
\addlegendentry{{Mantener el mercado}}
\addplot[thick, black!50] coordinates {{{lin_r}}};
\addlegendentry{{Media móvil de $200$ días}}
\end{{axis}}"""
    claves = [(1927, 1945), (1946, 1986), (1987, 2006), (2007, 2025)]
    barras_m = " ".join(f"({k + 1},{res['tramos'][c]['mercado']['sharpe']:.3f})" for k, c in enumerate(claves))
    barras_r = " ".join(f"({k + 1},{res['tramos'][c]['regla']['sharpe']:.3f})" for k, c in enumerate(claves))
    etiquetas = ",".join(f"{{${a}$-${b}$}}" for a, b in claves)
    panel_b = rf"""\begin{{axis}}[at={{(a.east)}}, anchor=west, xshift=1.9cm, width=7.6cm, height=6.6cm, ybar, bar width=9pt, xmin=0.4, xmax=4.6,
  ymin=0, ymax=1.0, xtick={{1,2,3,4}}, xticklabels={{{etiquetas}}}, x tick label style={{font=\scriptsize}},
  xlabel={{Periodo}}, ylabel={{Ratio de SHARPE anual}}, title={{(b) Rentabilidad por unidad de riesgo}},
  legend pos=north east, {PREAMBULO_EJES}]
\addplot[fill=black!75, draw=black] coordinates {{{barras_m}}};
\addlegendentry{{Mantener el mercado}}
\addplot[fill=black!30, draw=black!60] coordinates {{{barras_r}}};
\addlegendentry{{Media móvil de $200$ días}}
\end{{axis}}"""
    tikz = "\\begin{tikzpicture}\n" + panel_a + "\n" + panel_b + "\n\\end{tikzpicture}\n"
    (IMG / "anx_tecnico_regla.tikz").write_text(tikz, encoding="utf-8")
    return res


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "a9":
    res = grafico_regla_media_movil()
    for (a, b), t in res["tramos"].items():
        mm, rg = t["mercado"], t["regla"]
        print(f"{a}-{b}: mercado {mm['anual']:.1f}% vol {mm['vol']:.1f} SR {mm['sharpe']:.2f} caída {mm['caida']:.0f}% | regla {rg['anual']:.1f}% vol {rg['vol']:.1f} SR {rg['sharpe']:.2f} caída {rg['caida']:.0f}% | en mercado {t['en_mercado']:.0%} cambios {t['cambios']}")
