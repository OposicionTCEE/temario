# -*- coding: utf-8 -*-
# Libro de datos del tema (Code/datos_3A42.xlsx) y figuras calculadas del anexo I (A1, 06/11/2026):
#   anx_tres_ciclos, anx_componentes y anx_espurio (series sintéticas, sin cifras en los ejes);
#   anx_eeuu_nber, anx_espana_aee, anx_probabilidad, anx_filtros, anx_extremos y anx_ganancia (datos y filtros).
# Fuentes: FRED (Banco de la Reserva Federal de San Luis): GDPC1 (PIB real de EE. UU., miles de millones de dólares
# encadenados de 2017, tasa anual desestacionalizada), CLVMNACSCAB1GQES (PIB real de España, millones de euros
# encadenados de 2010, desestacionalizado; origen Eurostat), RECPROUSM156N (probabilidades suavizadas de recesión de
# CHAUVET y PIGER), USREC y USRECQ (indicadores de recesión según las fechas del NBER). Cronologías: NBER (tabla de
# expansiones y contracciones, 14/03/2023), Asociación Española de Economía (Comité de Fechado del Ciclo Económico
# Español) y CEPR (comité de la zona del euro).
# Uso, desde la carpeta del tema:  python3 -I Code/libro_y_figuras.py [carpeta con los CSV de FRED]
#   Sin carpeta, descarga los CSV en una carpeta temporal. Después, para cada figura:  bash Code/generar_figura.sh <nombre>
# Filtros: HODRICK-PRESCOTT (lambda = 1600), HAMILTON (h = 8, p = 4), BAXTER-KING (6-32 trimestres, K = 12); todos sobre
# 100 x logaritmo del PIB real, de modo que el ciclo se lee en porcentaje de desviación respecto a la tendencia.

import csv, math, os, sys, tempfile, urllib.request

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

sys.path.insert(0, "/Users/marceloortega/TCEE/main/herramientas")
from xlsx_simple import escribir_xlsx

TEMA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(TEMA, "Img")
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="
FECHA_DESCARGA = "06/11/2026"
SERIES = {
    "GDPC1": ("PIB real de Estados Unidos", "Estados Unidos", "miles de millones de dólares encadenados de 2017, tasa anual desestacionalizada", "trimestral"),
    "CLVMNACSCAB1GQES": ("PIB real de España", "España", "millones de euros encadenados de 2010, desestacionalizado", "trimestral"),
    "RECPROUSM156N": ("Probabilidad suavizada de recesión (CHAUVET y PIGER)", "Estados Unidos", "porcentaje", "mensual"),
    "USREC": ("Indicador de recesión del NBER", "Estados Unidos", "1 recesión, 0 expansión", "mensual"),
    "USRECQ": ("Indicador de recesión del NBER", "Estados Unidos", "1 recesión, 0 expansión", "trimestral"),
}
# Cronologías: (pico, valle, duración de la recesión en trimestres según la fuente).
AEE = [("1974T4", "1975T2", 2), ("1978T3", "1979T2", 3), ("1992T1", "1993T3", 6), ("2008T2", "2009T4", 6),
       ("2010T4", "2013T2", 12), ("2019T4", "2020T2", 2)]
CEPR = [("1974T3", "1975T1"), ("1980T1", "1982T3"), ("1992T1", "1993T3"), ("2008T1", "2009T2"), ("2011T3", "2013T1"),
        ("2019T4", "2020T2")]  # 2008T1-2009T2 sin comprobar en la página del comité (rechaza las descargas)
NBER_DESDE_1990 = [("julio de 1990", "marzo de 1991", 8, "25/04/1991", "22/12/1992"),
                   ("marzo de 2001", "noviembre de 2001", 8, "26/11/2001", "17/07/2003"),
                   ("diciembre de 2007", "junio de 2009", 18, "01/12/2008", "20/09/2010"),
                   ("febrero de 2020", "abril de 2020", 2, "08/06/2020", "19/07/2021")]


# ---------------------------------------------------------------- lectura
def descargar(carpeta):
    for s in SERIES:
        destino = os.path.join(carpeta, s + ".csv")
        if not os.path.exists(destino):
            urllib.request.urlretrieve(FRED + s, destino)


def leer(carpeta, serie):
    filas = []
    with open(os.path.join(carpeta, serie + ".csv"), encoding="utf-8") as f:
        lector = csv.reader(f)
        next(lector)
        for fecha, valor in lector:
            if valor not in (".", ""):
                filas.append((fecha, float(valor)))
    return filas


def decimal(fecha):  # "1947-04-01" -> 1947.25 (trimestres y meses, al inicio del periodo)
    a, m, _ = fecha.split("-")
    return int(a) + (int(m) - 1) / 12.0


def mates(etiqueta):  # "2007T4" -> "$2007$T$4$": cifras modernas en las figuras (EB Garamond pone cifras antiguas)
    a, t = etiqueta.split("T")
    return "$%s$T$%s$" % (a, t)


def trimestre(x):  # 1947.25 -> "1947T2"
    a = int(math.floor(x + 1e-9))
    return "%dT%d" % (a, int(round((x - a) * 4)) + 1)


def xt(etiqueta):  # "2008T2" -> 2008.25
    a, t = etiqueta.split("T")
    return int(a) + (int(t) - 1) / 4.0


def tramos(xs, indicador, paso):  # recesiones: del pico (periodo anterior al primer 1) al valle (último 1)
    salida, inicio = [], None
    for x, v in zip(xs, indicador):
        if v >= 0.5 and inicio is None:
            inicio = x - paso
        if v < 0.5 and inicio is not None:
            salida.append((inicio, x - paso))
            inicio = None
    if inicio is not None:
        salida.append((inicio, xs[-1]))
    return salida


# ---------------------------------------------------------------- filtros
def hp(y, lam=1600.0):
    n = len(y)
    d = sparse.diags([np.ones(n - 2), -2 * np.ones(n - 2), np.ones(n - 2)], [0, 1, 2], shape=(n - 2, n))
    tendencia = spsolve((sparse.eye(n) + lam * d.T @ d).tocsc(), y)
    return y - tendencia, tendencia


def hamilton(y, h=8, p=4):
    n = len(y)
    ciclo = np.full(n, np.nan)
    filas = [t for t in range(p - 1, n - h)]
    x = np.array([[1.0] + [y[t - j] for j in range(p)] for t in filas])
    objetivo = np.array([y[t + h] for t in filas])
    coef, *_ = np.linalg.lstsq(x, objetivo, rcond=None)
    for t, fila, obj in zip(filas, x, objetivo):
        ciclo[t + h] = obj - fila @ coef
    return ciclo


def pesos_bk(bajo=6, alto=32, k=12):
    w1, w2 = 2 * math.pi / alto, 2 * math.pi / bajo
    b = [(w2 - w1) / math.pi] + [(math.sin(j * w2) - math.sin(j * w1)) / (math.pi * j) for j in range(1, k + 1)]
    completos = b[:0:-1] + b  # j = -k ... k
    ajuste = -sum(completos) / (2 * k + 1)  # suma nula: elimina la tendencia
    return [v + ajuste for v in completos]


def bk(y, bajo=6, alto=32, k=12):
    a = pesos_bk(bajo, alto, k)
    n = len(y)
    ciclo = np.full(n, np.nan)
    for t in range(k, n - k):
        ciclo[t] = sum(a[j + k] * y[t - j] for j in range(-k, k + 1))
    return ciclo


def ganancias(periodos):
    salida = {"hp": [], "bk": [], "d1": [], "d8": []}
    a = pesos_bk()
    for per in periodos:
        w = 2 * math.pi / per
        g = 4 * 1600.0 * (1 - math.cos(w)) ** 2
        salida["hp"].append(g / (1 + g))
        salida["bk"].append(abs(sum(a[j + 12] * math.cos(j * w) for j in range(-12, 13))))
        salida["d1"].append(2 * abs(math.sin(w / 2)))
        salida["d8"].append(2 * abs(math.sin(4 * w)))
    return salida


# ---------------------------------------------------------------- utilidades de las figuras
def coords(xs, ys, dec=3):
    return " ".join("(%.4f,%.*f)" % (x, dec, y) for x, y in zip(xs, ys) if y is not None and not math.isnan(y))


ESTILO = ("font=\\footnotesize, tick label style={font=\\footnotesize}, label style={font=\\footnotesize},\n"
          "    xticklabel style={/pgf/number format/1000 sep={}}, yticklabel style={/pgf/number format/use comma},\n"
          "    axis lines*=left, tick align=outside, tick pos=left, set layers")


def sombras(intervalos, y_ref=1):
    lineas = ["\\begin{pgfonlayer}{axis background}"]
    for a, b in intervalos:
        lineas.append("\\fill[black!12] ({rel axis cs:0,0} -| {axis cs:%.4f,%s}) rectangle ({rel axis cs:0,1} -| {axis cs:%.4f,%s});"
                      % (a, y_ref, b, y_ref))
    lineas.append("\\end{pgfonlayer}")
    return "\n".join(lineas)


def escribir(nombre, cuerpo, comentario):
    texto = "%% " + comentario + "\n%% Generada por Code/libro_y_figuras.py; PDF con: bash Code/generar_figura.sh " + nombre + "\n" + cuerpo + "\n"
    with open(os.path.join(IMG, nombre + ".tikz"), "w", encoding="utf-8") as f:
        f.write(texto)


# ---------------------------------------------------------------- figuras sintéticas
def sinteticas(filas_series):
    t = np.arange(0, 97)
    amplitud = 3.75 - 1.25 * np.cos(2 * math.pi * (t - 48) / 64.0)  # ciclo central suave: baja la desviación, no el nivel
    ciclo = amplitud * np.sin(2 * math.pi * t / 32.0)
    tendencia = 0.75 * t
    y = tendencia + ciclo
    tasa = np.r_[np.nan, np.diff(y)]

    def bajadas(serie, desde=1):  # tramos en que la serie cae (para sombrear)
        tramos_, inicio = [], None
        for i in range(desde, len(serie)):
            cae = serie[i] < serie[i - 1]
            if cae and inicio is None:
                inicio = i - 1
            if not cae and inicio is not None:
                tramos_.append((inicio, i - 1)); inicio = None
        if inicio is not None:
            tramos_.append((inicio, len(serie) - 1))
        return tramos_

    def eje(nombre, titulo, extra, cuerpo, ancho="14.5cm", alto="3.4cm", ylab="", xlab="", xmax=96):
        return ("\\begin{axis}[name=%s, at={%s}, anchor=north west, width=%s, height=%s, scale only axis, %s,\n"
                "    xmin=0, xmax=%s, xtick=\\empty, ytick=\\empty, title={%s}, title style={font=\\footnotesize, yshift=-1ex},\n"
                "    ylabel={%s}, xlabel={%s}, xlabel style={at={(1,0)}, anchor=north east},\n"
                "    legend style={draw=none, fill=none, font=\\footnotesize, at={(0.01,0.99)}, anchor=north west}, legend cell align=left]\n%s\n\\end{axis}\n"
                % (nombre, extra, ancho, alto, ESTILO, xmax, titulo, ylab, xlab, cuerpo))

    # anx_tres_ciclos: el mismo PIB visto en niveles, en desviaciones y en tasas
    b_nivel, b_desv, b_tasa = bajadas(y), bajadas(ciclo), bajadas(np.nan_to_num(tasa, nan=tasa[1]), 2)
    p1 = sombras(b_nivel, 1) + "\n\\addplot[black, thick] coordinates {%s};\n\\addlegendentry{$y_t$}\n\\addplot[black!55, dashed] coordinates {%s};\n\\addlegendentry{$y^g_t$}" % (
        coords(t, y), coords(t, tendencia))
    p2 = sombras(b_desv, 0) + "\n\\addplot[black, thick] coordinates {%s};\n\\addplot[black!55, dashed] coordinates {(0,0) (96,0)};" % coords(t, ciclo)
    p3 = sombras(b_tasa, 0) + "\n\\addplot[black, thick] coordinates {%s};\n\\addplot[black!55, dashed] coordinates {(0,0) (96,0)};" % coords(t[1:], tasa[1:])
    fig = "\\begin{tikzpicture}\n"
    fig += eje("a", "(a) Nivel: ciclo clásico", "{(0,0)}", p1, ylab="$y_t$")
    fig += eje("b", "(b) Desviación respecto a la tendencia: ciclo de crecimiento", "{($(a.south west)+(0,-1.3cm)$)}", p2, ylab="$y^c_t$")
    fig += eje("c", "(c) Tasa de crecimiento: ciclo de tasas", "{($(b.south west)+(0,-1.3cm)$)}", p3, ylab="$\\Delta y_t$", xlab="tiempo")
    fig += "\\end{tikzpicture}"
    escribir("anx_tres_ciclos", fig, "El mismo PIB sintético, con las fases sombreadas según cada definición del ciclo.")

    # anx_componentes: serie observada = tendencia + ciclo + estacional + irregular
    rng = np.random.default_rng(42)
    estacional = np.tile([1.6, -0.6, 1.0, -2.0], 25)[: len(t)]
    irregular = rng.normal(0, 0.45, len(t))
    observada = tendencia + ciclo + estacional + irregular
    filas = [("a", "Serie observada, $y^{obs}_t$", coords(t, observada), coords(t, tendencia), "$y^{obs}_t$"),
             ("b", "Ciclo, $y^c_t$", coords(t, ciclo), None, "$y^c_t$"),
             ("c", "Componente estacional", coords(t, estacional), None, "$y^e_t$"),
             ("d", "Componente irregular", coords(t, irregular), None, "$y^i_t$")]
    fig = "\\begin{tikzpicture}\n"
    anterior = None
    for nombre, titulo, serie, extra_serie, etiqueta in filas:
        cuerpo = "\\addplot[black, thick] coordinates {%s};" % serie
        if extra_serie:
            cuerpo += "\n\\addlegendentry{$y^{obs}_t$}\n\\addplot[black!55, dashed] coordinates {%s};\n\\addlegendentry{$y^g_t$}" % extra_serie
        else:
            cuerpo += "\n\\addplot[black!55, dashed] coordinates {(0,0) (96,0)};"
        lugar = "{(0,0)}" if anterior is None else "{($(%s.south west)+(0,-1.1cm)$)}" % anterior
        fig += eje(nombre, titulo, lugar, cuerpo, alto="2.0cm" if nombre != "a" else "3.0cm", ylab=etiqueta,
                   xlab="tiempo" if nombre == "d" else "")
        anterior = nombre
    fig += "\\end{tikzpicture}"
    escribir("anx_componentes", fig, "Descomposición de una serie sintética en tendencia, ciclo, componente estacional e irregular.")

    # anx_espurio: paseo aleatorio con deriva; tendencia lineal y filtro HP le fabrican ciclos
    rng = np.random.default_rng(7)
    n = 160
    paseo = np.cumsum(0.5 + rng.normal(0, 1.0, n))
    tt = np.arange(n)
    coef = np.polyfit(tt, paseo, 1)
    lineal = np.polyval(coef, tt)
    ciclo_hp, _ = hp(paseo)
    fig = "\\begin{tikzpicture}\n"
    p1 = "\\addplot[black, thick] coordinates {%s};\n\\addplot[black!55, dashed] coordinates {%s};" % (coords(tt, paseo), coords(tt, lineal))
    p2 = "\\addplot[black, thick] coordinates {%s};\n\\addplot[black!55, dashed] coordinates {(0,0) (159,0)};" % coords(tt, paseo - lineal)
    p3 = "\\addplot[black, thick] coordinates {%s};\n\\addplot[black!55, dashed] coordinates {(0,0) (159,0)};" % coords(tt, ciclo_hp)
    for nombre, titulo, lugar, cuerpo in (("a", "(a) Paseo aleatorio y tendencia lineal", "{(0,0)}", p1),
                                          ("b", "(b) Desviación respecto a la tendencia lineal", "{($(a.south west)+(0,-1.3cm)$)}", p2),
                                          ("c", "(c) Ciclo del filtro de HODRICK-PRESCOTT", "{($(b.south west)+(0,-1.3cm)$)}", p3)):
        fig += eje(nombre, titulo, lugar, cuerpo, alto="2.8cm", xmax=159, xlab="tiempo" if nombre == "c" else "")
    fig += "\\end{tikzpicture}"
    escribir("anx_espurio", fig, "Un paseo aleatorio no tiene ciclo, pero la tendencia lineal y el filtro HP le fabrican uno (semilla 7).")
    filas_series.append(("Simulación", "Paseo aleatorio con deriva 0,5 y desviación típica 1 (semilla 7); 160 periodos", "anx_espurio"))


# ---------------------------------------------------------------- figuras con datos
def con_datos(carpeta, filas_series, cifras):
    pib = leer(carpeta, "GDPC1")
    xs = np.array([decimal(f) for f, _ in pib])
    y = np.array([100 * math.log(v) for _, v in pib])
    nivel = np.array([v for _, v in pib])
    base = np.mean([v for f, v in pib if f.startswith("2019")])
    recq = leer(carpeta, "USRECQ")
    mapa = {decimal(f): v for f, v in recq}
    rec_q = tramos(list(xs), [mapa.get(x, 0) for x in xs], 0.25)

    # anx_eeuu_nber
    indice = 100 * nivel / base
    cuerpo = sombras(rec_q, 50) + "\n\\addplot[black, thick] coordinates {%s};" % coords(xs, indice)
    fig = ("\\begin{tikzpicture}\n\\begin{axis}[width=14.5cm, height=5.6cm, scale only axis, %s,\n"
           "    ymode=log, ytick={10,20,50,100}, yticklabels={$10$,$20$,$50$,$100$}, ymin=9, ymax=130, xmin=1947, xmax=2027,\n"
           "    xtick={1950,1960,...,2020}, ylabel={Índice, $2019=100$ (escala logarítmica)}]\n%s\n\\end{axis}\n\\end{tikzpicture}"
           % (ESTILO, cuerpo))
    escribir("anx_eeuu_nber", fig, "PIB real de EE. UU. (FRED, GDPC1) con las recesiones del NBER (USRECQ) sombreadas.")

    # anx_espana_aee
    esp = leer(carpeta, "CLVMNACSCAB1GQES")
    xe = np.array([decimal(f) for f, _ in esp])
    base_e = np.mean([v for f, v in esp if f.startswith("2019")])
    ie = np.array([100 * v / base_e for _, v in esp])
    rec_e = [(xt(p), xt(v)) for p, v, _ in AEE if xt(p) >= 1995]
    cuerpo = sombras(rec_e, 80) + "\n\\addplot[black, thick] coordinates {%s};" % coords(xe, ie)
    fig = ("\\begin{tikzpicture}\n\\begin{axis}[width=14.5cm, height=5.2cm, scale only axis, %s,\n"
           "    ymin=50, ymax=120, ytick={60,80,100,120}, xmin=1995, xmax=2026.75, xtick={1995,2000,...,2025}, ylabel={Índice, $2019=100$}]\n%s\n\\end{axis}\n\\end{tikzpicture}"
           % (ESTILO, cuerpo))
    escribir("anx_espana_aee", fig, "PIB real de España (FRED, CLVMNACSCAB1GQES) con las recesiones del comité de la AEE sombreadas.")

    # anx_probabilidad
    pr = leer(carpeta, "RECPROUSM156N")
    xp = np.array([decimal(f) for f, _ in pr])
    vp = np.array([v for _, v in pr])
    recm = leer(carpeta, "USREC")
    mapa_m = {decimal(f): v for f, v in recm}
    xm = [x for x in sorted(mapa_m) if x >= xp[0] - 1]
    rec_m = tramos(xm, [mapa_m[x] for x in xm], 1 / 12.0)
    cuerpo = sombras(rec_m, 50) + "\n\\addplot[black, thick] coordinates {%s};" % coords(xp, vp, 2)
    fig = ("\\begin{tikzpicture}\n\\begin{axis}[width=14.5cm, height=4.8cm, scale only axis, %s,\n"
           "    ymin=0, ymax=105, ytick={0,20,...,100}, xmin=1967, xmax=2027, xtick={1970,1980,...,2020}, ylabel={Probabilidad de recesión (\\%%)}]\n%s\n\\end{axis}\n\\end{tikzpicture}"
           % (ESTILO, cuerpo))
    escribir("anx_probabilidad", fig, "Probabilidades suavizadas de recesión (FRED, RECPROUSM156N) con las recesiones del NBER (USREC) sombreadas.")

    # ciclos de EE. UU. con tres filtros
    c_hp, tend_hp = hp(y)
    c_ham = hamilton(y)
    c_bk = bk(y)
    ini = 1950.0
    sel = xs >= ini

    def panel(nombre, titulo, lugar, lineas):
        cuerpo = sombras([r for r in rec_q if r[1] >= ini], 0)
        for estilo, serie, etiqueta in lineas:
            cuerpo += "\n\\addplot[%s] coordinates {%s};\n\\addlegendentry{%s}" % (estilo, coords(xs[sel], serie[sel]), etiqueta)
        cuerpo += "\n\\addplot[black!40, thin, forget plot] coordinates {(1950,0) (2027,0)};"
        return ("\\begin{axis}[name=%s, at={%s}, anchor=north west, width=14.5cm, height=4.3cm, scale only axis, %s,\n"
                "    xmin=1950, xmax=2027, xtick={1950,1960,...,2020}, ylabel={Desviación (\\%%)}, title={%s},\n"
                "    title style={font=\\footnotesize, yshift=-1ex}, legend style={draw=none, fill=none, font=\\footnotesize, at={(0.99,0.03)}, anchor=south east},\n"
                "    legend columns=2, legend cell align=left]\n%s\n\\end{axis}\n" % (nombre, lugar, ESTILO, titulo, cuerpo))

    fig = "\\begin{tikzpicture}\n"
    fig += panel("a", "(a) HODRICK-PRESCOTT y HAMILTON", "{(0,0)}",
                 [("black, thick", c_hp, "HODRICK-PRESCOTT ($\\lambda=1600$)"), ("black!55", c_ham, "HAMILTON ($h=8$, $p=4$)")])
    fig += panel("b", "(b) HODRICK-PRESCOTT y BAXTER-KING", "{($(a.south west)+(0,-1.4cm)$)}",
                 [("black, thick", c_hp, "HODRICK-PRESCOTT ($\\lambda=1600$)"), ("black!55, dashed", c_bk, "BAXTER-KING ($6$-$32$ trimestres)")])
    fig += "\\end{tikzpicture}"
    escribir("anx_filtros", fig, "Ciclo del PIB real de EE. UU. según tres filtros, con las recesiones del NBER sombreadas.")

    # anx_extremos: el ciclo HP estimado con muestras que terminan en 2007T4, 2008T2, 2008T4 y 2009T2, frente a la muestra completa
    finales = ["2007T4", "2008T2", "2008T4", "2009T2"]
    estilos = ["black!35", "black!55, dashed", "black!70, dotted, thick", "black!85, dashdotted"]
    cuerpo = sombras([(2007.75, 2009.25)], 0)
    vent = (xs >= 2003) & (xs <= 2010.75)
    cuerpo += "\n\\addplot[black, very thick] coordinates {%s};\n\\addlegendentry{muestra completa (hasta %s)}" % (
        coords(xs[vent], c_hp[vent]), mates(trimestre(xs[-1])))
    revisiones = []
    for fin, estilo in zip(finales, estilos):
        k = int(np.where(np.isclose(xs, xt(fin)))[0][0]) + 1
        c_parcial, _ = hp(y[:k])
        v2 = (xs[:k] >= 2003)
        cuerpo += "\n\\addplot[%s] coordinates {%s};\n\\addlegendentry{datos hasta %s}" % (estilo, coords(xs[:k][v2], c_parcial[v2]), mates(fin))
        revisiones.append((fin, c_parcial[-1], c_hp[k - 1]))
    cuerpo += "\n\\addplot[black!40, thin, forget plot] coordinates {(2003,0) (2010.75,0)};"
    fig = ("\\begin{tikzpicture}\n\\begin{axis}[width=14.5cm, height=5.4cm, scale only axis, %s,\n"
           "    xmin=2003, xmax=2010.75, xtick={2003,2004,...,2010}, ylabel={Ciclo HODRICK-PRESCOTT (\\%%)},\n"
           "    legend style={draw=none, fill=none, font=\\footnotesize, at={(0.01,0.99)}, anchor=north west}, legend cell align=left]\n%s\n\\end{axis}\n\\end{tikzpicture}"
           % (ESTILO, cuerpo))
    escribir("anx_extremos", fig, "El problema de los extremos: ciclo HP del PIB real de EE. UU. estimado con muestras que terminan en fechas distintas.")
    for fin, parcial, final in revisiones:
        cifras.append(("Ciclo HP de EE. UU. en %s con datos hasta esa fecha" % fin, round(parcial, 2), "%", "I.3 (anx_extremos)"))
        cifras.append(("Ciclo HP de EE. UU. en %s con la muestra completa" % fin, round(final, 2), "%", "I.3 (anx_extremos)"))

    # anx_ganancia: qué ciclos deja pasar cada filtro
    periodos = list(np.exp(np.linspace(math.log(2), math.log(200), 400)))
    g = ganancias(periodos)

    def panel_g(nombre, titulo, lugar, lineas, ymax):
        cuerpo = "\\begin{pgfonlayer}{axis background}\n\\fill[black!12] ({rel axis cs:0,0} -| {axis cs:6,1}) rectangle ({rel axis cs:0,1} -| {axis cs:32,1});\n\\end{pgfonlayer}"
        for estilo, clave, etiqueta in lineas:
            cuerpo += "\n\\addplot[%s] coordinates {%s};\n\\addlegendentry{%s}" % (estilo, coords(periodos, g[clave], 4), etiqueta)
        return ("\\begin{axis}[name=%s, at={%s}, anchor=north west, width=6.6cm, height=4.4cm, scale only axis, %s,\n"
                "    xmode=log, xmin=2, xmax=200, xtick={2,4,8,16,32,64,128}, xticklabels={$2$,$4$,$8$,$16$,$32$,$64$,$128$},\n"
                "    ymin=0, ymax=%s, xlabel={Periodo del ciclo (trimestres)}, ylabel={Ganancia}, title={%s}, title style={font=\\footnotesize},\n"
                "    legend style={draw=none, fill=none, font=\\footnotesize, at={(0.5,0.99)}, anchor=north}, legend columns=2, legend cell align=left]\n%s\n\\end{axis}\n"
                % (nombre, lugar, ESTILO, ymax, titulo, cuerpo))

    fig = "\\begin{tikzpicture}\n"
    fig += panel_g("a", "(a) Filtros que dejan pasar el ciclo", "{(0,0)}",
                   [("black, thick", "hp", "HODRICK-PRESCOTT"), ("black!55, dashed", "bk", "BAXTER-KING")], "1.45")
    fig += panel_g("b", "(b) Diferencias", "{($(a.north east)+(1.4cm,0)$)}",
                   [("black, thick", "d1", "primera diferencia"), ("black!55, dashed", "d8", "diferencia de $8$ trimestres")], "2.55")
    fig += "\\end{tikzpicture}"
    escribir("anx_ganancia", fig, "Ganancia de cada filtro según el periodo del ciclo; banda sombreada: de 6 a 32 trimestres.")
    w50 = math.acos(1 - 1 / (2 * math.sqrt(1600.0)))
    cifras.append(("Periodo en que la ganancia del filtro HP (lambda = 1600) vale 1/2", round(2 * math.pi / w50, 1), "trimestres", "I.3 (anx_ganancia)"))

    # cifras y series para el libro
    def resumen(c, desde=1950.0, hasta=2019.75):
        m = (xs >= desde) & (xs <= hasta) & ~np.isnan(c)
        return float(np.std(c[m]))
    cifras.append(("Desviación típica del ciclo HP de EE. UU., 1950T1-2019T4", round(resumen(c_hp), 2), "%", "I.3"))
    cifras.append(("Desviación típica del ciclo de HAMILTON de EE. UU., 1950T1-2019T4", round(resumen(c_ham), 2), "%", "I.3"))
    cifras.append(("Desviación típica del ciclo BK de EE. UU., 1950T1-2019T4", round(resumen(c_bk), 2), "%", "I.3"))
    m = (xs >= 1950) & ~np.isnan(c_ham) & ~np.isnan(c_bk)
    cifras.append(("Correlación entre los ciclos HP y HAMILTON de EE. UU. (1950T1-fin)", round(float(np.corrcoef(c_hp[m], c_ham[m])[0, 1]), 2), "", "I.3"))
    cifras.append(("Correlación entre los ciclos HP y BK de EE. UU. (1950T1-fin)", round(float(np.corrcoef(c_hp[m], c_bk[m])[0, 1]), 2), "", "I.3"))
    k20 = int(np.where(np.isclose(xs, 2020.25))[0][0])
    cifras.append(("Ciclo HP de EE. UU. en 2020T2", round(float(c_hp[k20]), 1), "%", "I.3"))
    cifras.append(("Ciclo de HAMILTON de EE. UU. en 2020T2", round(float(c_ham[k20]), 1), "%", "I.3"))
    cifras.append(("Caída del PIB real de EE. UU. entre 2019T4 y 2020T2", round(100 * (nivel[k20] / nivel[k20 - 2] - 1), 1), "%", "I.1"))
    k08, k09 = int(np.where(np.isclose(xs, 2007.75))[0][0]), int(np.where(np.isclose(xs, 2009.25))[0][0])
    cifras.append(("Caída del PIB real de EE. UU. entre 2007T4 y 2009T2", round(100 * (nivel[k09] / nivel[k08] - 1), 1), "%", "I.1"))
    maximo = int(np.argmax(nivel[:k09 + 1]))  # máximo previo al valle con los datos revisados (2008T2, no 2007T4)
    recupera = next(trimestre(xs[i]) for i in range(k09 + 1, len(nivel)) if nivel[i] > nivel[maximo])
    cifras.append(("Trimestre del máximo del PIB real de EE. UU. antes del valle de 2009T2 (datos revisados)", trimestre(xs[maximo]), "", "I.1"))
    cifras.append(("Primer trimestre tras 2009T2 en que el PIB real de EE. UU. supera ese máximo", recupera, "", "I.1"))
    e = {f: v for f, v in esp}
    for p, v, _ in AEE:
        fp, fv = "%s-%02d-01" % (p[:4], 3 * int(p[-1]) - 2), "%s-%02d-01" % (v[:4], 3 * int(v[-1]) - 2)
        if fp in e and fv in e:
            cifras.append(("Variación del PIB real de España del pico %s al valle %s" % (p, v), round(100 * (e[fv] / e[fp] - 1), 1), "%", "I.2"))
    e08 = e["2008-04-01"]
    rec_es = next(f for f, v in esp if f > "2009-01-01" and v > e08)
    cifras.append(("Primer trimestre en que el PIB real de España supera el de 2008T2", trimestre(decimal(rec_es)), "", "I.2"))

    for (f, v), c1, c2, c3, ten in zip(pib, c_hp, c_ham, c_bk, tend_hp):
        filas_series.append(("GDPC1", "Estados Unidos", f, v, SERIES["GDPC1"][2], "FRED", "nivel", "anx_eeuu_nber"))
        for nombre, valor in (("ciclo HP (lambda 1600), %", c1), ("ciclo HAMILTON (h 8, p 4), %", c2), ("ciclo BAXTER-KING (6-32, K 12), %", c3)):
            if not math.isnan(valor):
                filas_series.append(("GDPC1", "Estados Unidos", f, round(float(valor), 4), "porcentaje", "FRED; cálculo propio", nombre, "anx_filtros"))
    for f, v in esp:
        filas_series.append(("CLVMNACSCAB1GQES", "España", f, v, SERIES["CLVMNACSCAB1GQES"][2], "FRED (Eurostat)", "nivel", "anx_espana_aee"))
    for f, v in pr:
        filas_series.append(("RECPROUSM156N", "Estados Unidos", f, v, "porcentaje", "FRED (CHAUVET y PIGER)", "nivel", "anx_probabilidad"))


def main():
    carpeta = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
    descargar(carpeta)
    series, cifras, sint = [], [], []
    sinteticas(sint)
    con_datos(carpeta, series, cifras)
    leeme = [["Libro de datos del tema 3.A.42 (Teorías de los ciclos económicos)"],
             ["Generado por Code/libro_y_figuras.py el %s con los datos de FRED descargados ese día." % FECHA_DESCARGA],
             ["Hojas: Fuentes (series y su origen), Series (formato largo: serie, país, fecha, valor, unidad, fuente, tratamiento, figura),"],
             ["Cronologías (picos y valles del NBER, de la AEE y del CEPR), Cifras_citadas (las que da el texto) y Simulaciones."],
             ["Tratamientos: nivel; ciclo HP con lambda 1600; ciclo HAMILTON con h 8 y p 4; ciclo BAXTER-KING con banda de 6 a 32 trimestres y K 12;"],
             ["todos los ciclos sobre 100 x logaritmo del PIB real (desviación en porcentaje)."]]
    fuentes = [["Código", "Serie", "País", "Unidad", "Frecuencia", "Institución", "Enlace", "Descarga"]]
    for s, (nombre, pais, unidad, frec) in SERIES.items():
        fuentes.append([s, nombre, pais, unidad, frec, "FRED, Banco de la Reserva Federal de San Luis", FRED + s, FECHA_DESCARGA])
    fuentes.append(["NBER", "Cronología de expansiones y contracciones de EE. UU.", "Estados Unidos", "meses", "mensual y trimestral",
                    "National Bureau of Economic Research", "https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions", FECHA_DESCARGA])
    fuentes.append(["AEE", "Fechado histórico del ciclo económico español", "España", "trimestres", "trimestral",
                    "Asociación Española de Economía, Comité de Fechado", "http://www.asesec.org/CFCweb/index.php/archivo-historico-del-ciclo-economico-espanol/", FECHA_DESCARGA])
    fuentes.append(["CEPR", "Cronología del ciclo de la zona del euro", "Zona del euro", "trimestres", "trimestral",
                    "Centre for Economic Policy Research, comité de fechado de la zona del euro", "https://eabcn.org/dc", FECHA_DESCARGA])
    filas = [["Serie", "País", "Fecha", "Valor", "Unidad", "Fuente", "Tratamiento", "Figura"]] + [list(f) for f in series]
    cron = [["Comité", "Ámbito", "Pico", "Valle", "Duración de la recesión", "Unidad", "Fuente"]]
    for p, v, d in AEE:
        cron.append(["AEE", "España", p, v, d, "trimestres", "AEE (2015), fechado histórico"])
    for p, v in CEPR:
        cron.append(["CEPR", "Zona del euro", p, v, None, "trimestres", "CEPR; 2008T1-2009T2 sin comprobar en la página del comité"])
    for p, v, d, ap, av in NBER_DESDE_1990:
        cron.append(["NBER", "Estados Unidos", p, v, d, "meses", "NBER; anuncios del pico el %s y del valle el %s" % (ap, av)])
    cif = [["Cifra", "Valor", "Unidad", "Apartado"]] + [list(c) for c in cifras]
    simul = [["Simulación", "Descripción", "Figura"]] + [list(s) for s in sint]
    escribir_xlsx(os.path.join(TEMA, "Code", "datos_3A42.xlsx"),
                  [("Léeme", leeme), ("Fuentes", fuentes), ("Series", filas), ("Cronologías", cron), ("Cifras_citadas", cif), ("Simulaciones", simul)])
    for c in cifras:
        print("%-75s %s %s" % (c[0], c[1], c[2]))


if __name__ == "__main__":
    main()
