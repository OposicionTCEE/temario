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

    def eje(nombre, titulo, extra, cuerpo, ancho="14.5cm", alto="2.6cm", ylab="", xlab="", xmax=96):
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
        fig += eje(nombre, titulo, lugar, cuerpo, alto="1.5cm" if nombre != "a" else "2.4cm", ylab=etiqueta,
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
        fig += eje(nombre, titulo, lugar, cuerpo, alto="2.2cm", xmax=159, xlab="tiempo" if nombre == "c" else "")
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


# ================================================================ A2 (06/11/2026): producto potencial, hechos estilizados y ciclo financiero
# Figuras: anx_potencial, anx_tiempo_real, anx_volatilidad, anx_adelantos, anx_desplome, anx_moderacion,
# anx_ciclo_financiero y anx_brecha_credito. Fuentes adicionales: FRED (GDPPOT, potencial de la CBO; componentes del
# gasto, horas, empleo, productividad, salario real, deflactor, tipo de las letras del Tesoro y paro), ALFRED (ediciones
# del PIB real de EE. UU. de diciembre de 1991 a 2019, unos dos meses y medio después de cada trimestre), Eurostat
# (namq_10_gdp y namq_10_a10_e: PIB, componentes, empleo y horas de España, desde 1995) y BPI (WS_TC, crédito al sector
# privado no financiero en porcentaje del PIB; WS_CREDIT_GAP, brecha de crédito; WS_SPP, precios reales de la vivienda).
SERIES_A2 = {
    "GDPPOT": "PIB potencial real de la CBO", "PCECC96": "Consumo privado real", "DDURRA3Q086SBEA": "Consumo de bienes duraderos (índice de cantidad)",
    "DNDGRA3Q086SBEA": "Consumo de bienes no duraderos (índice de cantidad)", "DSERRA3Q086SBEA": "Consumo de servicios (índice de cantidad)",
    "GPDIC1": "Inversión privada real", "A008RA3Q086SBEA": "Inversión fija no residencial (índice de cantidad)",
    "A011RA3Q086SBEA": "Inversión residencial (índice de cantidad)", "GCEC1": "Consumo e inversión públicos reales",
    "EXPGSC1": "Exportaciones reales", "IMPGSC1": "Importaciones reales", "HOANBS": "Horas del sector empresarial no agrícola",
    "PAYEMS": "Empleo asalariado no agrícola", "OPHNFB": "Producción por hora", "COMPRNFB": "Remuneración real por hora",
    "GDPDEF": "Deflactor del PIB", "TB3MS": "Tipo de las letras del Tesoro a tres meses", "UNRATE": "Tasa de paro"}
BIS_FICHEROS = ["WS_TC", "WS_CREDIT_GAP", "WS_SPP"]
EUROSTAT = {"gdp_clv.json": "namq_10_gdp?geo=ES&geo=EA20&unit=CLV10_MEUR&s_adj=SCA&na_item=B1GQ&na_item=P31_S14&na_item=P51G&na_item=P3_S13&na_item=P6&na_item=P7",
            "gdp_pd.json": "namq_10_gdp?geo=ES&unit=PD10_EUR&s_adj=SCA&na_item=B1GQ",
            "emp.json": "namq_10_a10_e?geo=ES&geo=EA20&unit=THS_PER&unit=THS_HW&s_adj=SCA&na_item=EMP_DC&nace_r2=TOTAL"}
CRISIS = {"ES": [1977.0, 2008.0], "US": [1988.0, 2007.75]}  # crisis bancarias sistémicas de LAEVEN y VALENCIA, sin comprobar en la base


def descargar_a2(carpeta):
    import datetime, zipfile, time
    for s in SERIES_A2:
        destino = os.path.join(carpeta, s + ".csv")
        if not os.path.exists(destino):
            urllib.request.urlretrieve(FRED + s, destino); time.sleep(0.3)
    for b in BIS_FICHEROS:
        sub = os.path.join(carpeta, "bis_" + b)
        if not os.path.isdir(sub):
            z = os.path.join(carpeta, b + ".zip")
            urllib.request.urlretrieve("https://data.bis.org/static/bulk/%s_csv_flat.zip" % b, z)
            zipfile.ZipFile(z).extractall(sub)
    os.makedirs(os.path.join(carpeta, "eurostat"), exist_ok=True)
    for nombre, consulta in EUROSTAT.items():
        destino = os.path.join(carpeta, "eurostat", nombre)
        if not os.path.exists(destino):
            urllib.request.urlretrieve("https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/%s&format=JSON&lang=EN" % consulta, destino)
    os.makedirs(os.path.join(carpeta, "alfred"), exist_ok=True)
    for a in range(1991, 2020):
        for q in range(4):
            fin = (datetime.date(a, 3 * q + 3, 1) + datetime.timedelta(days=31)).replace(day=1) - datetime.timedelta(days=1)
            v = fin + datetime.timedelta(days=75)
            destino = os.path.join(carpeta, "alfred", "GDPC1_%s.csv" % v.isoformat())
            if v < datetime.date(1991, 12, 1) or os.path.exists(destino):
                continue
            for desfase in (0, 10, 20):  # la edición del 14/12/2003 (revisión general) termina un trimestre antes: se toma la del 24/12
                w = v + datetime.timedelta(days=desfase)
                urllib.request.urlretrieve("https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=GDPC1&vintage_date=%s" % w.isoformat(), destino)
                filas = [r for r in list(csv.reader(open(destino)))[1:] if r[1] not in (".", "")]
                if filas and filas[-1][0] == "%d-%02d-01" % (a, 3 * q + 1):
                    break
                time.sleep(0.4)


def trimestral(filas):  # media de los meses de cada trimestre
    acum = {}
    for f, v in filas:
        a, m, _ = f.split("-")
        clave = "%s-%02d-01" % (a, 3 * ((int(m) - 1) // 3) + 1)
        acum.setdefault(clave, []).append(v)
    return [(k, sum(v) / len(v)) for k, v in sorted(acum.items()) if len(v) == 3]


def leer_eurostat(ruta, **sel):
    import json
    d = json.load(open(ruta, encoding="utf-8"))
    ids, tam = d["id"], d["size"]
    pos = {k: d["dimension"][k]["category"]["index"] for k in ids}
    salida = {}
    for t, it in pos["time"].items():
        indice = 0
        for k, n in zip(ids, tam):
            i = it if k == "time" else (pos[k][sel[k]] if k in sel else 0)
            indice = indice * n + i
        v = d["value"].get(str(indice))
        if v is not None:
            a, q = t.split("-Q")
            salida["%s-%02d-01" % (a, 3 * int(q) - 2)] = float(v)
    return sorted(salida.items())


def leer_bis(carpeta, fichero, **sel):
    ruta = os.path.join(carpeta, "bis_" + fichero, fichero + "_csv_flat.csv")
    salida = []
    with open(ruta, encoding="utf-8") as f:
        lector = csv.reader(f)
        cab = next(lector)
        idx = {c.split(":")[0]: i for i, c in enumerate(cab)}
        for fila in lector:
            if all(fila[idx[k]].split(":")[0] == v for k, v in sel.items()) and fila[idx["OBS_VALUE"]] not in ("", "NaN"):
                per = fila[idx["TIME_PERIOD"]]
                if "-Q" in per:
                    a, q = per.split("-Q")
                    salida.append(("%s-%02d-01" % (a, 3 * int(q) - 2), float(fila[idx["OBS_VALUE"]])))
    return sorted(salida)


def cf(x, bajo, alto):
    """Filtro de banda de CHRISTIANO y FITZGERALD (2003), asimétrico, con toda la muestra y supuesto de paseo aleatorio
    con deriva (se resta la deriva antes de filtrar). Comprobado con una serie sintética: aísla la onda de la banda con
    correlación 0,99."""
    x = np.asarray(x, float)
    n = len(x)
    a, b = 2 * math.pi / alto, 2 * math.pi / bajo
    x = x - np.arange(n) * (x[-1] - x[0]) / (n - 1.0)
    j = np.arange(1, n + 1)
    pesos = np.r_[(b - a) / math.pi, (np.sin(b * j) - np.sin(a * j)) / (math.pi * j)]
    y = np.zeros(n)
    for i in range(n):
        bb = -0.5 * pesos[0] - np.sum(pesos[1:-i - 2])
        aa = -pesos[0] - np.sum(pesos[1:-i - 2]) - np.sum(pesos[1:i]) - bb
        y[i] = pesos[0] * x[i] + np.dot(pesos[1:-i - 2], x[i + 1:-1]) + bb * x[-1] + np.dot(pesos[1:i], x[1:i][::-1]) + aa * x[0]
    return y


def a_dict(filas):
    return {f: v for f, v in filas}


def alinear(dics, desde, hasta):
    fechas = sorted(set.intersection(*[set(d) for d in dics]))
    fechas = [f for f in fechas if desde <= f <= hasta]
    return fechas, [np.array([d[f] for f in fechas]) for d in dics]


def con_datos_a2(carpeta, filas_series, cifras, momentos):
    import datetime
    pib = a_dict(leer(carpeta, "GDPC1"))
    recq = a_dict(leer(carpeta, "USRECQ"))

    # ---- anx_potencial: brecha de la CBO frente al ciclo HP
    pot = a_dict(leer(carpeta, "GDPPOT"))
    fechas, (y, p) = alinear([pib, pot], "1949-01-01", "2026-07-01")
    xs = np.array([decimal(f) for f in fechas])
    brecha_cbo = 100 * (y / p - 1)
    fechas_hp = sorted(f for f in pib if f >= "1947-01-01")
    c_hp_todo, _ = hp(np.array([100 * math.log(pib[f]) for f in fechas_hp]))
    hp_d = dict(zip(fechas_hp, c_hp_todo))
    c_hp = np.array([hp_d[f] for f in fechas])
    rec = tramos(list(xs), [recq.get(f, 0) for f in fechas], 0.25)
    cuerpo = sombras([r for r in rec if r[1] >= 1950], 0)
    sel = xs >= 1950
    cuerpo += "\n\\addplot[black, thick] coordinates {%s};\n\\addlegendentry{brecha respecto al potencial de la CBO}" % coords(xs[sel], brecha_cbo[sel])
    cuerpo += "\n\\addplot[black!50, dashed] coordinates {%s};\n\\addlegendentry{ciclo de HODRICK-PRESCOTT}" % coords(xs[sel], c_hp[sel])
    cuerpo += "\n\\addplot[black!40, thin, forget plot] coordinates {(1950,0) (2027,0)};"
    fig = ("\\begin{tikzpicture}\n\\begin{axis}[width=14.5cm, height=5.6cm, scale only axis, %s,\n"
           "    xmin=1950, xmax=2027, xtick={1950,1960,...,2020}, ymin=-11, ymax=8, ylabel={Porcentaje del PIB potencial o de la tendencia},\n"
           "    legend style={draw=none, fill=none, font=\\footnotesize, at={(0.01,0.02)}, anchor=south west}, legend cell align=left]\n%s\n\\end{axis}\n\\end{tikzpicture}"
           % (ESTILO, cuerpo))
    escribir("anx_potencial", fig, "Brecha de producción de EE. UU. con el potencial de la CBO (FRED, GDPPOT) frente al ciclo HP; recesiones del NBER.")
    for f, v1, v2 in zip(fechas, brecha_cbo, c_hp):
        filas_series.append(("GDPC1/GDPPOT", "Estados Unidos", f, round(float(v1), 3), "porcentaje del potencial", "FRED (BEA y CBO); cálculo propio", "brecha de la CBO", "anx_potencial"))
    m = (xs >= 1950) & (xs <= 2019.75)
    cifras.append(("Brecha media de la CBO, 1950T1-2019T4", round(float(np.mean(brecha_cbo[m])), 2), "%", "I.4"))
    cifras.append(("Brecha media del ciclo HP, 1950T1-2019T4", round(float(np.mean(c_hp[m])), 2), "%", "I.4"))
    cifras.append(("Correlación entre la brecha de la CBO y el ciclo HP, 1950T1-2019T4", round(float(np.corrcoef(brecha_cbo[m], c_hp[m])[0, 1]), 2), "", "I.4"))
    for f in ("2009-04-01", "2011-04-01", "2014-01-01", "2016-01-01"):
        k = fechas.index(f)
        cifras.append(("Brecha de la CBO y ciclo HP en %s" % trimestre(decimal(f)), "%.1f y %.1f" % (brecha_cbo[k], c_hp[k]), "%", "I.4"))
    cierre = next((trimestre(xs[k]) for k in range(len(xs)) if xs[k] > 2010 and brecha_cbo[k] >= 0), None)
    cifras.append(("Primer trimestre tras 2009 con brecha de la CBO no negativa", cierre, "", "I.4"))
    cierre_hp = next((trimestre(xs[k]) for k in range(len(xs)) if xs[k] > 2009.5 and c_hp[k] >= 0), None)
    cifras.append(("Primer trimestre tras 2009T2 con ciclo HP no negativo", cierre_hp, "", "I.4"))

    # ---- anx_tiempo_real: brecha HP en tiempo real (ALFRED), cuasi tiempo real y final (ORPHANIDES y VAN NORDEN, 2002)
    final = np.array([100 * math.log(pib[f]) for f in fechas_hp if f >= "1959-01-01"])
    f_final = [f for f in fechas_hp if f >= "1959-01-01"]
    c_final, _ = hp(final)
    d_final = dict(zip(f_final, c_final))
    rt, qr, fi, xt_ = [], [], [], []
    for nombre in sorted(os.listdir(os.path.join(carpeta, "alfred"))):
        filas = [r for r in list(csv.reader(open(os.path.join(carpeta, "alfred", nombre))))[1:] if r[1] not in (".", "") and r[0] >= "1959-01-01"]
        t = filas[-1][0]
        if t > "2019-10-01":
            continue
        serie = np.array([100 * math.log(float(r[1])) for r in filas])
        c_rt, _ = hp(serie)
        k = f_final.index(t)
        c_qr, _ = hp(final[:k + 1])
        rt.append(c_rt[-1]); qr.append(c_qr[-1]); fi.append(d_final[t]); xt_.append(decimal(t))
        filas_series.append(("GDPC1 (ALFRED %s)" % nombre[6:16], "Estados Unidos", t, round(float(c_rt[-1]), 3), "porcentaje", "ALFRED; cálculo propio", "brecha HP en tiempo real", "anx_tiempo_real"))
    rt, qr, fi, xt_ = map(np.array, (rt, qr, fi, xt_))
    cuerpo = sombras([r for r in rec if r[1] >= 1991.5 and r[0] <= 2019.75], 0)
    for estilo, serie, etiqueta in (("black, very thick", fi, "final (datos de $2026$)"), ("black!45", qr, "cuasi tiempo real (datos de $2026$ cortados)"),
                                    ("black!75, dashed", rt, "tiempo real (datos de cada momento)")):
        cuerpo += "\n\\addplot[%s] coordinates {%s};\n\\addlegendentry{%s}" % (estilo, coords(xt_, serie), etiqueta)
    cuerpo += "\n\\addplot[black!40, thin, forget plot] coordinates {(1991.5,0) (2020,0)};"
    fig = ("\\begin{tikzpicture}\n\\begin{axis}[width=14.2cm, height=5.6cm, scale only axis, %s,\n"
           "    xmin=1991.5, xmax=2020, xtick={1992,1996,...,2020}, ylabel={Ciclo HODRICK-PRESCOTT (\\%%)},\n"
           "    legend style={draw=none, fill=none, font=\\footnotesize, at={(0.01,0.02)}, anchor=south west}, legend cell align=left]\n%s\n\\end{axis}\n\\end{tikzpicture}"
           % (ESTILO, cuerpo))
    escribir("anx_tiempo_real", fig, "Brecha HP de EE. UU. en tiempo real (ALFRED), en cuasi tiempo real y final, 1991T3-2019T4; recesiones del NBER.")
    total, datos, filtro = fi - rt, qr - rt, fi - qr
    cifras.append(("Trimestres de la muestra en tiempo real (1991T3-2019T4)", len(rt), "", "I.4"))
    cifras.append(("Correlación entre la brecha HP en tiempo real y la final", round(float(np.corrcoef(rt, fi)[0, 1]), 2), "", "I.4"))
    cifras.append(("Correlación entre la brecha HP en cuasi tiempo real y la final", round(float(np.corrcoef(qr, fi)[0, 1]), 2), "", "I.4"))
    cifras.append(("Cociente ruido-señal: desv. típica de la revisión total / desv. típica de la brecha final", round(float(np.std(total) / np.std(fi)), 2), "", "I.4"))
    cifras.append(("Desviación típica de la revisión por los datos", round(float(np.std(datos)), 2), "puntos", "I.4"))
    cifras.append(("Desviación típica de la revisión por el filtro", round(float(np.std(filtro)), 2), "puntos", "I.4"))
    cifras.append(("Desviación típica de la brecha final en la muestra", round(float(np.std(fi)), 2), "%", "I.4"))
    cifras.append(("Porcentaje de trimestres en que la brecha en tiempo real y la final tienen signo distinto", round(100 * float(np.mean(np.sign(rt) != np.sign(fi))), 0), "%", "I.4"))
    for f in (2000.75, 2007.75, 2008.75):
        k = int(np.where(np.isclose(xt_, f))[0][0])
        cifras.append(("Brecha HP en %s: tiempo real, cuasi tiempo real y final" % trimestre(f), "%.1f / %.1f / %.1f" % (rt[k], qr[k], fi[k]), "%", "I.4"))

    # ---- momentos del ciclo: EE. UU. (1950T1-2019T4) y España (1995T1-2019T4), filtro HP sobre toda la muestra disponible
    def ciclo_hp(filas, log=True, desde="1947-01-01"):
        d = [(f, v) for f, v in filas if f >= desde]
        serie = np.array([100 * math.log(v) if log else v for _, v in d])
        c, _ = hp(serie)
        return dict(zip([f for f, _ in d], c))

    us = {"PIB": ciclo_hp(leer(carpeta, "GDPC1")),
          "Consumo": ciclo_hp(leer(carpeta, "PCECC96")),
          "Consumo de duraderos": ciclo_hp(leer(carpeta, "DDURRA3Q086SBEA")),
          "Consumo de no duraderos": ciclo_hp(leer(carpeta, "DNDGRA3Q086SBEA")),
          "Consumo de servicios": ciclo_hp(leer(carpeta, "DSERRA3Q086SBEA")),
          "Inversión": ciclo_hp(leer(carpeta, "GPDIC1")),
          "Inversión no residencial": ciclo_hp(leer(carpeta, "A008RA3Q086SBEA")),
          "Inversión residencial": ciclo_hp(leer(carpeta, "A011RA3Q086SBEA")),
          "Gasto público": ciclo_hp(leer(carpeta, "GCEC1")),
          "Exportaciones": ciclo_hp(leer(carpeta, "EXPGSC1")),
          "Importaciones": ciclo_hp(leer(carpeta, "IMPGSC1")),
          "Horas": ciclo_hp(leer(carpeta, "HOANBS")),
          "Empleo": ciclo_hp(trimestral(leer(carpeta, "PAYEMS"))),
          "Productividad por hora": ciclo_hp(leer(carpeta, "OPHNFB")),
          "Salario real por hora": ciclo_hp(leer(carpeta, "COMPRNFB")),
          "Tasa de paro": ciclo_hp(trimestral(leer(carpeta, "UNRATE")), log=False),
          "Nivel de precios": ciclo_hp(leer(carpeta, "GDPDEF")),
          "Tipo de interés a corto": ciclo_hp(trimestral(leer(carpeta, "TB3MS")), log=False)}
    defl = leer(carpeta, "GDPDEF")
    infl = [(defl[i][0], 400 * math.log(defl[i][1] / defl[i - 1][1])) for i in range(1, len(defl))]
    us["Inflación"] = ciclo_hp(infl, log=False)

    def tabla(cic, desde, hasta, pais):
        fy = [f for f in sorted(cic["PIB"]) if desde <= f <= hasta]
        y_ = np.array([cic["PIB"][f] for f in fy])
        sy = float(np.std(y_))
        salida = {}
        for nombre, d in cic.items():
            ff = [f for f in fy if f in d]
            x_ = np.array([d[f] for f in ff])
            yy = np.array([cic["PIB"][f] for f in ff])
            sx = float(np.std(x_))
            cc = {}
            for k in range(-4, 5):  # corr(x_{t+k}, y_t)
                pares = [(d[ff[i + k]], yy[i]) for i in range(len(ff)) if 0 <= i + k < len(ff)]
                a1, a2 = zip(*pares)
                cc[k] = float(np.corrcoef(a1, a2)[0, 1])
            rho = float(np.corrcoef(x_[1:], x_[:-1])[0, 1])
            salida[nombre] = (sx, sx / sy, cc, rho)
            for est, val in (("desviación típica (%)", sx), ("desviación relativa al PIB", sx / sy), ("correlación contemporánea con el PIB", cc[0]),
                             ("autocorrelación de orden 1", rho), ("retardo k de la correlación máxima en valor absoluto", max(cc, key=lambda q: abs(cc[q])))):
                momentos.append((pais, nombre, est, round(val, 3), "%s-%s" % (trimestre(decimal(desde)), trimestre(decimal(hasta))), "HP, lambda 1600"))
        return salida

    t_us = tabla(us, "1950-01-01", "2019-10-01", "Estados Unidos")
    e_gdp = os.path.join(carpeta, "eurostat", "gdp_clv.json")
    e_emp = os.path.join(carpeta, "eurostat", "emp.json")
    pib_es = leer_eurostat(e_gdp, na_item="B1GQ", geo="ES")
    horas_es = leer_eurostat(e_emp, unit="THS_HW", geo="ES")
    prod_es = [(f, v / dict(horas_es)[f]) for f, v in pib_es if f in dict(horas_es)]
    es = {"PIB": ciclo_hp(pib_es, desde="1995-01-01"),
          "Consumo": ciclo_hp(leer_eurostat(e_gdp, na_item="P31_S14", geo="ES"), desde="1995-01-01"),
          "Inversión": ciclo_hp(leer_eurostat(e_gdp, na_item="P51G", geo="ES"), desde="1995-01-01"),
          "Gasto público": ciclo_hp(leer_eurostat(e_gdp, na_item="P3_S13", geo="ES"), desde="1995-01-01"),
          "Exportaciones": ciclo_hp(leer_eurostat(e_gdp, na_item="P6", geo="ES"), desde="1995-01-01"),
          "Importaciones": ciclo_hp(leer_eurostat(e_gdp, na_item="P7", geo="ES"), desde="1995-01-01"),
          "Empleo": ciclo_hp(leer_eurostat(e_emp, unit="THS_PER", geo="ES"), desde="1995-01-01"),
          "Horas": ciclo_hp(horas_es, desde="1995-01-01"),
          "Productividad por hora": ciclo_hp(prod_es, desde="1995-01-01"),
          "Nivel de precios": ciclo_hp(leer_eurostat(os.path.join(carpeta, "eurostat", "gdp_pd.json"), na_item="B1GQ", geo="ES"), desde="1995-01-01")}
    t_es = tabla(es, "1995-01-01", "2019-10-01", "España")
    print("\nMOMENTOS (desv. %, relativa, corr, retardo de la corr. máx., rho1)")
    for pais, t_ in (("EE. UU.", t_us), ("España", t_es)):
        for nombre, (sx, rel, cc, rho) in t_.items():
            kmax = max(cc, key=lambda q: abs(cc[q]))
            print("%-8s %-28s %6.2f %5.2f %6.2f %3d %5.2f" % (pais, nombre, sx, rel, cc[0], kmax, rho))
    # productividad antes y después de 1984 (GALÍ y VAN RENS, 2021)
    for desde, hasta in (("1950-01-01", "1983-10-01"), ("1984-01-01", "2019-10-01")):
        ff = [f for f in sorted(us["PIB"]) if desde <= f <= hasta]
        cpy = float(np.corrcoef([us["Productividad por hora"][f] for f in ff], [us["PIB"][f] for f in ff])[0, 1])
        cph = float(np.corrcoef([us["Productividad por hora"][f] for f in ff], [us["Horas"][f] for f in ff])[0, 1])
        shy = float(np.std([us["Horas"][f] for f in ff]) / np.std([us["PIB"][f] for f in ff]))
        cifras.append(("EE. UU. %s-%s: corr(productividad, PIB), corr(productividad, horas), desv. horas/PIB" % (trimestre(decimal(desde)), trimestre(decimal(hasta))),
                       "%.2f / %.2f / %.2f" % (cpy, cph, shy), "", "I.5"))
    # sincronización: ciclos HP del PIB de España, de la zona del euro (Eurostat, EA20) y de EE. UU., 1995T1-2019T4
    ea = ciclo_hp(leer_eurostat(e_gdp, na_item="B1GQ", geo="EA20"), desde="1995-01-01")
    ff = [f for f in sorted(es["PIB"]) if "1995-01-01" <= f <= "2019-10-01" and f in ea and f in us["PIB"]]
    c_es_ea = float(np.corrcoef([es["PIB"][f] for f in ff], [ea[f] for f in ff])[0, 1])
    c_es_us = float(np.corrcoef([es["PIB"][f] for f in ff], [us["PIB"][f] for f in ff])[0, 1])
    c_ea_us = float(np.corrcoef([ea[f] for f in ff], [us["PIB"][f] for f in ff])[0, 1])
    cifras.append(("Correlación de los ciclos HP del PIB, 1995T1-2019T4: España-zona del euro, España-EE. UU., zona del euro-EE. UU.",
                   "%.2f / %.2f / %.2f" % (c_es_ea, c_es_us, c_ea_us), "", "I.5"))

    # ---- anx_volatilidad: desviación típica relativa al PIB
    filas_v = [("Consumo", "Consumo"), ("Consumo de duraderos", None), ("Inversión", "Inversión"), ("Gasto público", "Gasto público"),
               ("Exportaciones", "Exportaciones"), ("Importaciones", "Importaciones"), ("Empleo", "Empleo"), ("Horas", "Horas"),
               ("Productividad por hora", "Productividad por hora")]
    n = len(filas_v)
    etiquetas = ",".join("{%s}" % a for a, _ in filas_v)
    c_us = " ".join("(%.3f,%d)" % (t_us[a][1], n - i) for i, (a, _) in enumerate(filas_v))
    c_es = " ".join("(%.3f,%d)" % (t_es[b][1], n - i) for i, (a, b) in enumerate(filas_v) if b)
    fig = ("\\begin{tikzpicture}\n\\begin{axis}[width=10cm, height=7.2cm, scale only axis, %s,\n"
           "    xbar, bar width=5pt, xmin=0, xmax=5.6, ymin=0.4, ymax=%d.6, ytick={%s}, yticklabels={%s}, area legend,\n"
           "    xticklabel style={/pgf/number format/use comma},\n"
           "    xlabel={Desviación típica del ciclo de la variable dividida por la del PIB}, y dir=normal,\n"
           "    legend style={draw=none, fill=none, font=\\footnotesize, at={(0.98,0.02)}, anchor=south east}, legend cell align=left]\n"
           "\\addplot[fill=black!75, draw=none, bar shift=3pt] coordinates {%s};\n\\addlegendentry{Estados Unidos, $1950$-$2019$}\n"
           "\\addplot[fill=black!30, draw=none, bar shift=-3pt] coordinates {%s};\n\\addlegendentry{España, $1995$-$2019$}\n"
           "\\draw[black!60, dashed] (axis cs:1,0.4) -- (axis cs:1,%d.6);\n\\end{axis}\n\\end{tikzpicture}"
           % (ESTILO, n, ",".join(str(n - i) for i in range(n)), ",".join(a for a, _ in filas_v), c_us, c_es, n))
    escribir("anx_volatilidad", fig, "Volatilidad relativa de los componentes del gasto y del mercado de trabajo (ciclo HP).")

    # ---- anx_adelantos: correlación de x_{t+k} con el PIB_t (EE. UU.)
    ks = list(range(-4, 5))

    def linea(nombre, estilo, etiqueta):
        return "\\addplot[%s] coordinates {%s};\n\\addlegendentry{%s}" % (estilo, " ".join("(%d,%.3f)" % (k, t_us[nombre][2][k]) for k in ks), etiqueta)

    def panel_c(nombre, titulo, lugar, lineas, pos_ley=("{(0.5,-0.24)}", "north")):
        return ("\\begin{axis}[name=%s, at={%s}, anchor=north west, width=6.2cm, height=4.6cm, scale only axis, %s,\n"
                "    xmin=-4, xmax=4, xtick={-4,...,4}, ymin=-1, ymax=1, xlabel={$k$ (trimestres)}, ylabel={Correlación de $x_{t+k}$ con $y_t$},\n"
                "    title={%s}, title style={font=\\footnotesize}, legend style={draw=none, fill=none, font=\\footnotesize, at={%s}, anchor=%s}, legend columns=3,\n"
                "    legend cell align=left]\n\\addplot[black!40, thin, forget plot] coordinates {(-4,0) (4,0)};\n\\addplot[black!40, thin, forget plot] coordinates {(0,-1) (0,1)};\n%s\n\\end{axis}\n"
                % (nombre, lugar, ESTILO, titulo, pos_ley[0], pos_ley[1], "\n".join(lineas)))

    fig = "\\begin{tikzpicture}\n"
    fig += panel_c("a", "(a) Variables reales", "{(0,0)}", [linea("Horas", "black, thick, mark=*, mark size=1.2pt", "horas"),
                                                              linea("Productividad por hora", "black!55, dashed, mark=square*, mark size=1.2pt", "productividad"),
                                                              linea("Tasa de paro", "black!80, dotted, thick, mark=triangle*, mark size=1.5pt", "tasa de paro")])
    fig += panel_c("b", "(b) Variables nominales", "{($(a.north east)+(1.5cm,0)$)}", [linea("Nivel de precios", "black, thick, mark=*, mark size=1.2pt", "nivel de precios"),
                                                                                     linea("Inflación", "black!55, dashed, mark=square*, mark size=1.2pt", "inflación"),
                                                                                     linea("Tipo de interés a corto", "black!80, dotted, thick, mark=triangle*, mark size=1.5pt", "tipo de interés")],
                   pos_ley=("{(0.5,-0.24)}", "north"))
    fig += "\\end{tikzpicture}"
    escribir("anx_adelantos", fig, "Correlaciones cruzadas del ciclo HP de cada variable con el del PIB de EE. UU., 1950-2019.")

    # ---- anx_desplome: modelo de los tirones (FRIEDMAN, 1993; DUPRAZ, NAKAMURA y STEINSSON, 2019) con la tasa de paro y las
    # recesiones mensuales del NBER: subida del paro en cada recesión (del mínimo previo al máximo posterior) frente a su
    # bajada en la expansión siguiente, y bajada en una expansión frente a la subida de la recesión siguiente.
    fq = sorted(pib)
    lq = np.array([100 * math.log(pib[f]) for f in fq])
    paro = leer(carpeta, "UNRATE")
    fm = [f for f, _ in paro]
    um = np.array([v for _, v in paro])
    recm = a_dict(leer(carpeta, "USREC"))
    ind = [recm.get(f, 0) for f in fm]
    picos_m, valles_m = [], []
    for i in range(1, len(fm)):
        if ind[i] >= 0.5 and ind[i - 1] < 0.5:
            picos_m.append(i - 1)
        if ind[i] < 0.5 and ind[i - 1] >= 0.5:
            valles_m.append(i - 1)
    episodios = []
    for k, (pk, vl) in enumerate(zip(picos_m, valles_m)):
        bajo = int(np.argmin(um[max(0, pk - 12):pk + 7])) + max(0, pk - 12)  # mínimo del paro alrededor del pico
        sig = picos_m[k + 1] if k + 1 < len(picos_m) else len(fm) - 1
        alto = int(np.argmax(um[pk:min(len(fm), vl + 25, sig + 1)])) + pk  # máximo del paro tras el valle, antes del pico siguiente
        sube = um[alto] - um[bajo]
        bajo_sig = int(np.argmin(um[alto:sig + 7])) + alto if k + 1 < len(picos_m) else None
        baja = um[alto] - um[bajo_sig] if bajo_sig is not None else None
        episodios.append((fm[pk], fm[vl], sube, baja))
    pares_a = [(e[2], e[3]) for e in episodios if e[3] is not None]
    pares_b = [(episodios[i][3], episodios[i + 1][2]) for i in range(len(episodios) - 1) if episodios[i][3] is not None]
    ca = float(np.corrcoef(*zip(*pares_a))[0, 1])
    cb = float(np.corrcoef(*zip(*pares_b))[0, 1])
    sin20a = [(a1, a2) for (a1, a2), e in zip(pares_a, episodios) if not e[0].startswith("2020")]
    sin20b = [pb for pb, e in zip(pares_b, episodios[1:]) if not e[0].startswith("2020")]
    ca2 = float(np.corrcoef(*zip(*sin20a))[0, 1]); cb2 = float(np.corrcoef(*zip(*sin20b))[0, 1])
    cifras.append(("Recesiones del NBER con tasa de paro mensual (desde 1948)", len(episodios), "", "I.5"))
    cifras.append(("Correlación entre la subida del paro en la recesión y su bajada en la expansión siguiente", round(ca, 2), "", "I.5"))
    cifras.append(("Correlación entre la bajada del paro en una expansión y su subida en la recesión siguiente", round(cb, 2), "", "I.5"))
    cifras.append(("Las mismas correlaciones sin la recesión de 2020", "%.2f y %.2f" % (ca2, cb2), "", "I.5"))
    for e in episodios:
        filas_series.append(("Recesión del NBER %s a %s" % (e[0][:7], e[1][:7]), "Estados Unidos", e[0], round(float(e[2]), 2), "puntos de la tasa de paro",
                             "FRED (UNRATE, USREC); cálculo propio", "subida del paro; bajada posterior %s" % ("%.2f" % e[3] if e[3] is not None else "sin dato"), "anx_desplome"))

    def panel_d(nombre, titulo, lugar, pares, xlab, ylab, r):
        puntos = " ".join("(%.2f,%.2f)" % p for p in pares)
        return ("\\begin{axis}[name=%s, at={%s}, anchor=north west, width=6.3cm, height=5.0cm, scale only axis, %s,\n"
                "    xmin=0, ymin=0, xlabel={%s}, ylabel={%s}, title={%s}, title style={font=\\footnotesize}]\n"
                "\\addplot[only marks, mark=*, mark size=1.6pt, black] coordinates {%s};\n"
                "\\node[font=\\footnotesize, anchor=north west] at (rel axis cs:0.03,0.97) {$r=%s$};\n\\end{axis}\n"
                % (nombre, lugar, ESTILO, xlab, ylab, titulo, puntos, ("%.2f" % r).replace(".", "{,}")))

    fig = "\\begin{tikzpicture}\n"
    fig += panel_d("a", "(a) De la recesión a la expansión siguiente", "{(0,0)}", pares_a, "Subida del paro en la recesión (puntos)", "Bajada del paro en la expansión (puntos)", ca)
    fig += panel_d("b", "(b) De la expansión a la recesión siguiente", "{($(a.north east)+(1.7cm,0)$)}", pares_b, "Bajada del paro en la expansión (puntos)", "Subida del paro en la recesión (puntos)", cb)
    fig += "\\end{tikzpicture}"
    escribir("anx_desplome", fig, "Modelo de los tirones con la tasa de paro de EE. UU. y las recesiones mensuales del NBER desde 1948.")

    # ---- anx_moderacion: volatilidad del crecimiento (desviación típica móvil de diez años)
    g = 4 * np.diff(lq)  # crecimiento trimestral anualizado, en puntos porcentuales
    xg = np.array([decimal(f) for f in fq[1:]])
    vol = [(xg[k], float(np.std(g[k - 39:k + 1]))) for k in range(39, len(g))]
    for (a_, b_) in (("1947-04-01", "1983-10-01"), ("1984-01-01", "2007-10-01"), ("2008-01-01", "2019-10-01")):
        m_ = np.array([a_ <= f <= b_ for f in fq[1:]])
        cifras.append(("Desviación típica del crecimiento trimestral anualizado del PIB de EE. UU., %s-%s" % (trimestre(decimal(a_)), trimestre(decimal(b_))),
                       round(float(np.std(g[m_])), 2), "puntos", "I.5"))
    cuerpo = sombras([r for r in rec if r[1] >= 1957], 0)
    cuerpo += "\n\\addplot[black, thick] coordinates {%s};" % " ".join("(%.4f,%.3f)" % v for v in vol)
    cuerpo += "\n\\addplot[black!55, dashed] coordinates {(1984,0) (1984,9)};"
    fig = ("\\begin{tikzpicture}\n\\begin{axis}[width=14.5cm, height=5.0cm, scale only axis, %s,\n"
           "    xmin=1957, xmax=2027, xtick={1960,1970,...,2020}, ymin=0, ymax=9, ylabel={Desviación típica (puntos)}]\n%s\n\\end{axis}\n\\end{tikzpicture}"
           % (ESTILO, cuerpo))
    escribir("anx_moderacion", fig, "Desviación típica del crecimiento trimestral anualizado del PIB de EE. UU. en los diez años anteriores; línea discontinua: 1984.")

    # ---- anx_ciclo_financiero: componente de medio plazo (8-30 años) del crédito/PIB y de los precios reales de la vivienda
    def financiero(pais, desde, hasta):
        cred = a_dict(leer_bis(carpeta, "WS_TC", BORROWERS_CTY=pais, TC_BORROWERS="P", TC_LENDERS="A", VALUATION="M", UNIT_TYPE="770", TC_ADJUST="A"))
        viv = a_dict(leer_bis(carpeta, "WS_SPP", REF_AREA=pais, VALUE="R", UNIT_MEASURE="628"))
        ff, (c_, v_) = alinear([cred, viv], desde, hasta)
        cc_ = cf(100 * np.log(c_), 32, 120)
        cv_ = cf(100 * np.log(v_), 32, 120)
        return ff, cc_, cv_, (cc_ + cv_) / 2, c_, v_

    paneles = []
    for pais, titulo, rec_p in (("ES", "(a) España", [(xt(p), xt(v)) for p, v, _ in AEE]), ("US", "(b) Estados Unidos", rec)):
        ff, cc_, cv_, comp, c_, v_ = financiero(pais, "1971-01-01" if pais == "ES" else "1970-01-01", "2025-10-01")
        xf = np.array([decimal(f) for f in ff])
        for f, a1, a2, a3 in zip(ff, cc_, cv_, comp):
            filas_series.append(("BPI %s crédito/PIB y vivienda real" % pais, "España" if pais == "ES" else "Estados Unidos", f, round(float(a3), 3),
                                 "porcentaje", "BPI; cálculo propio", "ciclo financiero CF 32-120 (media de crédito/PIB %.2f y vivienda %.2f)" % (a1, a2), "anx_ciclo_financiero"))
        # picos del ciclo financiero: máximos locales en una ventana de +/- 20 trimestres
        picos = [trimestre(xf[k]) for k in range(len(comp)) if comp[k] > 0 and comp[k] == max(comp[max(0, k - 20):k + 21])]
        cifras.append(("Picos del ciclo financiero de %s (máximos locales a +/- 5 años)" % pais, ", ".join(picos), "", "I.6"))
        cifras.append(("Desviación típica del ciclo financiero de %s y del ciclo CF 6-32 de su crédito/PIB" % pais,
                       "%.1f y %.1f" % (np.std(comp), np.std(cf(100 * np.log(c_), 6, 32))), "%", "I.6"))
        cuerpo = sombras([r for r in rec_p if r[1] >= xf[0]], 0)
        cuerpo += "\n\\addplot[black, very thick] coordinates {%s};\n\\addlegendentry{ciclo financiero}" % coords(xf, comp)
        cuerpo += "\n\\addplot[black!50] coordinates {%s};\n\\addlegendentry{crédito sobre el PIB}" % coords(xf, cc_)
        cuerpo += "\n\\addplot[black!50, dashed] coordinates {%s};\n\\addlegendentry{precio real de la vivienda}" % coords(xf, cv_)
        for k, c0 in enumerate(CRISIS[pais]):
            cuerpo += "\n\\addplot[black, densely dotted, thick%s] coordinates {(%.2f,-45) (%.2f,45)};%s" % (
                "" if k == 0 else ", forget plot", c0, c0, "\n\\addlegendentry{crisis bancaria}" if k == 0 else "")
        cuerpo += "\n\\addplot[black!40, thin, forget plot] coordinates {(1970,0) (2026,0)};"
        lugar = "{(0,0)}" if pais == "ES" else "{($(a.south west)+(0,-1.5cm)$)}"
        paneles.append("\\begin{axis}[name=%s, at={%s}, anchor=north west, width=14.2cm, height=4.6cm, scale only axis, %s,\n"
                       "    xmin=1970, xmax=2026, xtick={1970,1975,...,2025}, ymin=-45, ymax=45, ylabel={Desviación (\\%%)}, title={%s}, title style={font=\\footnotesize},\n"
                       "    legend style={draw=none, fill=none, font=\\footnotesize, at={(0.01,0.02)}, anchor=south west}, legend columns=2, legend cell align=left]\n%s\n\\end{axis}\n"
                       % ("a" if pais == "ES" else "b", lugar, ESTILO, titulo, cuerpo))
    fig = "\\begin{tikzpicture}\n" + "".join(paneles) + "\\end{tikzpicture}"
    escribir("anx_ciclo_financiero", fig, "Ciclo financiero de España y EE. UU.: componente de 8 a 30 años (CHRISTIANO-FITZGERALD) del crédito/PIB y del precio real de la vivienda (BPI).")

    # ---- anx_brecha_credito: España, ratio de crédito, tendencia HP unilateral (lambda 400.000) y brecha del BPI
    r_ = a_dict(leer_bis(carpeta, "WS_CREDIT_GAP", BORROWERS_CTY="ES", CG_DTYPE="A"))
    t_ = a_dict(leer_bis(carpeta, "WS_CREDIT_GAP", BORROWERS_CTY="ES", CG_DTYPE="B"))
    b_ = a_dict(leer_bis(carpeta, "WS_CREDIT_GAP", BORROWERS_CTY="ES", CG_DTYPE="C"))
    ff, (rr, tt, bb) = alinear([r_, t_, b_], "1980-01-01", "2026-10-01")
    xb = np.array([decimal(f) for f in ff])
    for f, a1, a2, a3 in zip(ff, rr, tt, bb):
        filas_series.append(("BPI ES brecha de crédito", "España", f, a3, "puntos del PIB", "BPI (WS_CREDIT_GAP)", "ratio %.1f; tendencia %.1f" % (a1, a2), "anx_brecha_credito"))
    kmax = int(np.argmax(bb)); kmin = int(np.argmin(bb))
    cifras.append(("Brecha de crédito de España: máximo", "%.1f en %s" % (bb[kmax], trimestre(xb[kmax])), "puntos", "I.6"))
    cifras.append(("Brecha de crédito de España: mínimo", "%.1f en %s" % (bb[kmin], trimestre(xb[kmin])), "puntos", "I.6"))
    cifras.append(("Ratio de crédito de España: máximo", "%.1f en %s" % (max(rr), trimestre(xb[int(np.argmax(rr))])), "% del PIB", "I.6"))
    cifras.append(("Brecha de crédito de España en el último dato", "%.1f en %s" % (bb[-1], trimestre(xb[-1])), "puntos", "I.6"))
    primer_neg = next((trimestre(xb[k]) for k in range(len(bb)) if xb[k] > 2008 and bb[k] < 0), None)
    ult_pos = next((trimestre(xb[k]) for k in range(len(bb) - 1, -1, -1) if bb[k] > 2), None)
    cifras.append(("Brecha de España: primer trimestre negativo tras 2008 y último por encima de 2 puntos", "%s y %s" % (primer_neg, ult_pos), "", "I.6"))
    supera2 = next((trimestre(xb[k]) for k in range(len(bb)) if xb[k] > 1995 and bb[k] > 2), None)
    supera10 = next((trimestre(xb[k]) for k in range(len(bb)) if xb[k] > 1995 and bb[k] > 10), None)
    cifras.append(("Brecha de España: primer trimestre tras 1995 por encima de 2 y de 10 puntos", "%s y %s" % (supera2, supera10), "", "I.6"))
    cuerpo_a = sombras([(xt(p), xt(v)) for p, v, _ in AEE if xt(v) >= 1980], 50)
    cuerpo_a += "\n\\addplot[black, thick] coordinates {%s};\n\\addlegendentry{crédito al sector privado no financiero}" % coords(xb, rr)
    cuerpo_a += "\n\\addplot[black!50, dashed] coordinates {%s};\n\\addlegendentry{tendencia (HP unilateral, $\\lambda=400.000$)}" % coords(xb, tt)
    cuerpo_b = sombras([(xt(p), xt(v)) for p, v, _ in AEE if xt(v) >= 1980], 0)
    cuerpo_b += "\n\\addplot[black, thick] coordinates {%s};\n\\addlegendentry{brecha de crédito}" % coords(xb, bb)
    cuerpo_b += "\n\\addplot[black!55, dashed] coordinates {(1980,2) (2027,2)};\n\\addlegendentry{umbrales de $2$ y $10$ puntos}"
    cuerpo_b += "\n\\addplot[black!55, dashed, forget plot] coordinates {(1980,10) (2027,10)};\n\\addplot[black!40, thin, forget plot] coordinates {(1980,0) (2027,0)};"
    fig = "\\begin{tikzpicture}\n"
    fig += ("\\begin{axis}[name=a, at={(0,0)}, anchor=north west, width=14.5cm, height=4.4cm, scale only axis, %s,\n"
            "    xmin=1980, xmax=2027, xtick={1980,1985,...,2025}, ylabel={Porcentaje del PIB}, title={(a) Ratio de crédito y su tendencia}, title style={font=\\footnotesize},\n"
            "    legend style={draw=none, fill=none, font=\\footnotesize, at={(0.01,0.98)}, anchor=north west}, legend cell align=left]\n%s\n\\end{axis}\n" % (ESTILO, cuerpo_a))
    fig += ("\\begin{axis}[name=b, at={($(a.south west)+(0,-1.5cm)$)}, anchor=north west, width=14.5cm, height=4.4cm, scale only axis, %s,\n"
            "    xmin=1980, xmax=2027, xtick={1980,1985,...,2025}, ylabel={Puntos del PIB}, title={(b) Brecha de crédito}, title style={font=\\footnotesize},\n"
            "    legend style={draw=none, fill=none, font=\\footnotesize, at={(0.01,0.02)}, anchor=south west}, legend cell align=left]\n%s\n\\end{axis}\n" % (ESTILO, cuerpo_b))
    fig += "\\end{tikzpicture}"
    escribir("anx_brecha_credito", fig, "España: crédito al sector privado no financiero (% del PIB), tendencia HP unilateral y brecha de crédito del BPI.")


# ---------------------------------------------------------------- A3 (06-07/11/2026): identificación y predicción
# Figuras: anx_var_monetario (VAR recursivo de EE. UU. a la manera de CHRISTIANO, EICHENBAUM y EVANS, 1999),
# anx_proyeccion_local (proyección local del PIB, JORDÀ 2005, frente al VAR), anx_probit_recesion (probit de la
# pendiente de la curva, ESTRELLA y MISHKIN 1998) y anx_regla_sahm (regla de SAHM con los datos de cada momento). Fuentes adicionales de
# FRED: FEDFUNDS (tipo efectivo de los fondos federales), PPIACO (índice de precios de producción de todas las materias
# primas), GS10 (bono del Tesoro a diez años), SAHMREALTIME y SAHMCURRENT (indicador de SAHM).
SERIES_A3 = {"FEDFUNDS": "Tipo de interés efectivo de los fondos federales",
             "PPIACO": "Índice de precios de producción de todas las materias primas",
             "GS10": "Rendimiento del bono del Tesoro a diez años (vencimiento constante)",
             "SAHMREALTIME": "Indicador de recesión de SAHM con los datos de cada momento",
             "SAHMCURRENT": "Indicador de recesión de SAHM con los datos actuales"}
MUESTRA_CEE = ("1965-07-01", "1995-07-01")  # la de CHRISTIANO, EICHENBAUM y EVANS (1999), 1965T3-1995T3
MUESTRA_LARGA = ("1965-01-01", "2007-10-01")
RETARDOS, HORIZONTE = 4, 20


def descargar_a3(carpeta):
    import time
    for s in SERIES_A3:
        destino = os.path.join(carpeta, s + ".csv")
        if not os.path.exists(destino):
            urllib.request.urlretrieve(FRED + s, destino); time.sleep(0.3)


def var_mco(X, p=RETARDOS):  # VAR con constante estimado por mínimos cuadrados, ecuación a ecuación
    Y = X[p:]
    Z = np.hstack([np.ones((X.shape[0] - p, 1))] + [X[p - j:X.shape[0] - j] for j in range(1, p + 1)])
    B = np.linalg.lstsq(Z, Y, rcond=None)[0]
    E = Y - Z @ B
    return B, E, E.T @ E / (Y.shape[0] - Z.shape[1])


def var_respuestas(B, S, p=RETARDOS, H=HORIZONTE):
    """Respuestas con identificación recursiva (CHOLESKY): matriz [h, variable, perturbación] para h = 0..H."""
    N = S.shape[0]
    Phi = [B[1 + N * (j - 1):1 + N * j].T for j in range(1, p + 1)]
    Psi = [np.eye(N)]
    for h in range(1, H + 1):
        Psi.append(sum(Phi[j] @ Psi[h - 1 - j] for j in range(min(p, h))))
    G = np.linalg.cholesky(S)
    return np.array([P @ G for P in Psi])


def var_bootstrap(X, B, E, reps=1000, semilla=1, p=RETARDOS):
    """Bandas por remuestreo de los residuos, con las condiciones iniciales fijas; respuestas a una subida de un punto."""
    rng = np.random.default_rng(semilla)
    T, salida = E.shape[0], []
    for _ in range(reps):
        e = E[rng.integers(0, T, T)]
        Xb = np.array(X, float)
        for t in range(p, X.shape[0]):
            Xb[t] = np.r_[1.0, np.concatenate([Xb[t - j] for j in range(1, p + 1)])] @ B + e[t - p]
        Bb, _, Sb = var_mco(Xb)
        R = var_respuestas(Bb, Sb)
        salida.append(R[:, :, 3] / R[0, 3, 3])
    return np.array(salida)


def proyeccion_local(X, H=HORIZONTE, p=RETARDOS):
    """PIB en t+h (respecto a t-1) sobre el tipo de t, con las variables lentas de t y p retardos de todas como controles:
    la versión recursiva, que en población estima la misma respuesta que el VAR (PLAGBORG-MØLLER y WOLF, 2021).
    Errores típicos de NEWEY y WEST con h + 1 retardos."""
    salida = []
    for h in range(H + 1):
        A, y = [], []
        for t in range(p, X.shape[0] - h):
            A.append(np.r_[X[t, 3], 1.0, X[t, :3], np.concatenate([X[t - j] for j in range(1, p + 1)])])
            y.append(X[t + h, 0] - X[t - 1, 0])
        A, y = np.array(A), np.array(y)
        b = np.linalg.lstsq(A, y, rcond=None)[0]
        Au = A * (y - A @ b)[:, None]
        Q, Sg = np.linalg.inv(A.T @ A), Au.T @ Au
        for l in range(1, h + 2):
            G = Au[l:].T @ Au[:-l]
            Sg = Sg + (1 - l / (h + 2.0)) * (G + G.T)
        salida.append((b[0], math.sqrt((Q @ Sg @ Q)[0, 0])))
    return salida


def normal(z):
    return 0.5 * (1 + np.vectorize(math.erf)(np.asarray(z, float) / math.sqrt(2)))


def probit(x, y, iteraciones=60):  # máxima verosimilitud por NEWTON-RAPHSON
    X = np.c_[np.ones(len(x)), x]
    b = np.zeros(2)
    for _ in range(iteraciones):
        z = X @ b
        pr = np.clip(normal(z), 1e-10, 1 - 1e-10)
        f = np.exp(-z ** 2 / 2) / math.sqrt(2 * math.pi)
        b = b + np.linalg.solve(X.T @ (X * (f ** 2 / (pr * (1 - pr)))[:, None]), X.T @ ((y - pr) * f / (pr * (1 - pr))))
    return b


def con_datos_a3(carpeta, filas_series, cifras):
    gdp, dfl = a_dict(leer(carpeta, "GDPC1")), a_dict(leer(carpeta, "GDPDEF"))
    pc, ff = a_dict(trimestral(leer(carpeta, "PPIACO"))), a_dict(trimestral(leer(carpeta, "FEDFUNDS")))
    fechas = sorted(set(gdp) & set(dfl) & set(pc) & set(ff))
    nombres = ["PIB real", "Deflactor del PIB", "Precios de las materias primas", "Tipo de los fondos federales"]

    def datos(desde, hasta):
        i0, i1 = fechas.index(desde), fechas.index(hasta)
        fs = fechas[i0 - RETARDOS:i1 + 1]
        return fs, np.array([[100 * math.log(gdp[f]), 100 * math.log(dfl[f]), 100 * math.log(pc[f]), ff[f]] for f in fs])

    # ---- VAR recursivo (orden: PIB, deflactor, materias primas, tipo): muestra de CEE y muestra larga
    fs, X = datos(*MUESTRA_CEE)
    B, E, S = var_mco(X)
    R = var_respuestas(B, S)
    r = R[:, :, 3] / R[0, 3, 3]
    boot = var_bootstrap(X, B, E)
    lo, hi = np.percentile(boot, 5, axis=0), np.percentile(boot, 95, axis=0)
    fl, XL = datos(*MUESTRA_LARGA)
    BL, EL, SL = var_mco(XL)
    RL = var_respuestas(BL, SL)
    rl = RL[:, :, 3] / RL[0, 3, 3]
    for f, fila in zip(fl, XL):
        for k in range(4):
            filas_series.append(("VAR " + nombres[k], "Estados Unidos", f, round(float(fila[k]), 4), "punto porcentual" if k == 3 else "100 x logaritmo",
                                 "FRED (GDPC1, GDPDEF, PPIACO, FEDFUNDS)", "media trimestral de los datos mensuales" if k >= 2 else "trimestral", "anx_var_monetario"))
    for h in range(HORIZONTE + 1):
        for k in range(4):
            filas_series.append(("Respuesta a una subida de un punto del tipo: " + nombres[k], "Estados Unidos", "h = %d trimestres" % h, round(float(r[h, k]), 4),
                                 "puntos" if k == 3 else "%", "elaboración propia con FRED",
                                 "VAR recursivo %s-%s, 4 retardos; banda del 90%% [%.3f, %.3f]; muestra 1965T1-2007T4: %.3f"
                                 % (trimestre(decimal(MUESTRA_CEE[0])), trimestre(decimal(MUESTRA_CEE[1])), lo[h, k], hi[h, k], rl[h, k]), "anx_var_monetario"))
    kmin = int(np.argmin(r[:, 0]))
    cifras.append(("VAR: desviación típica de la perturbación monetaria (1965T3-1995T3)", "%.2f" % R[0, 3, 3], "puntos", "I.7"))
    cifras.append(("VAR: caída máxima del PIB tras una subida de un punto (trimestre, banda del 90%)", "%.2f en h = %d [%.2f, %.2f]" % (r[kmin, 0], kmin, lo[kmin, 0], hi[kmin, 0]), "%", "I.7"))
    cifras.append(("VAR: PIB en h = 20", "%.2f [%.2f, %.2f]" % (r[20, 0], lo[20, 0], hi[20, 0]), "%", "I.7"))
    cifras.append(("VAR: deflactor, máximo de los dos primeros años y valores en h = 12, 16 y 20", "%.2f (h = %d); %.2f; %.2f; %.2f [%.2f, %.2f]"
                   % (max(r[:9, 1]), int(np.argmax(r[:9, 1])), r[12, 1], r[16, 1], r[20, 1], lo[20, 1], hi[20, 1]), "%", "I.7"))
    cifras.append(("VAR: materias primas en h = 4, 8 y 20", "%.2f; %.2f; %.2f" % (r[4, 2], r[8, 2], r[20, 2]), "%", "I.7"))
    vuelta = next(h for h in range(1, HORIZONTE + 1) if r[h, 3] < 0.05)
    cifras.append(("VAR: tipo en h = 4 y primer trimestre por debajo de 0,05", "%.2f; h = %d" % (r[4, 3], vuelta), "puntos", "I.7"))
    kml = int(np.argmin(rl[:, 0]))
    cifras.append(("VAR 1965T1-2007T4: deflactor máximo (h) y PIB mínimo (h) y en h = 20", "%.2f (h = %d); %.2f (h = %d); %.2f"
                   % (max(rl[:, 1]), int(np.argmax(rl[:, 1])), rl[kml, 0], kml, rl[20, 0]), "%", "I.7"))
    for etiqueta, RR in (("1965T3-1995T3", R), ("1965T1-2007T4", RL)):
        cuotas = []
        for h in (4, 8, 12, 20):
            num = sum(RR[s, 0, 3] ** 2 for s in range(h))
            den = sum(RR[s, 0, j] ** 2 for s in range(h) for j in range(4))
            cuotas.append("%d: %.1f" % (h, 100 * num / den))
        cifras.append(("VAR %s: parte de la varianza del error de previsión del PIB debida a la perturbación monetaria (h: %%)" % etiqueta, "; ".join(cuotas), "%", "I.7"))

    def banda(ys_lo, ys_hi):
        ida = " ".join("(%d,%.4f)" % (h, v) for h, v in enumerate(ys_lo))
        vuelta_ = " ".join("(%d,%.4f)" % (h, ys_hi[h]) for h in range(len(ys_hi) - 1, -1, -1))
        return "\\addplot[fill=black!15, draw=none, area legend] coordinates {%s %s};" % (ida, vuelta_)

    def linea_h(ys, estilo):
        return "\\addplot[%s] coordinates {%s};" % (estilo, " ".join("(%d,%.4f)" % (h, v) for h, v in enumerate(ys)))

    def panel_irf(nombre, titulo, lugar, k, ylab, ymin, ymax, ytick, leyenda=False):
        cuerpo = [banda(lo[:, k], hi[:, k]), linea_h(r[:, k], "black, thick"), linea_h(rl[:, k], "black!60, dashed, thick"),
                  "\\addplot[black!40, thin] coordinates {(0,0) (20,0)};"]
        if leyenda:
            cuerpo = [banda(lo[:, k], hi[:, k]) + "\n\\addlegendentry{banda del $90\\%$}",
                      linea_h(r[:, k], "black, thick") + "\n\\addlegendentry{muestra $1965$-$1995$}",
                      linea_h(rl[:, k], "black!60, dashed, thick") + "\n\\addlegendentry{muestra $1965$-$2007$}",
                      "\\addplot[black!40, thin, forget plot] coordinates {(0,0) (20,0)};"]
        return ("\\begin{axis}[name=%s, at={%s}, anchor=north west, width=6.2cm, height=3.3cm, scale only axis, %s,\n"
                "    xmin=0, xmax=20, xtick={0,4,...,20}, ymin=%s, ymax=%s, ytick={%s}, xlabel={Trimestres}, ylabel={%s},\n"
                "    title={%s}, title style={font=\\footnotesize}, legend style={draw=none, fill=none, font=\\footnotesize, at={(0.98,0.98)}, anchor=north east},\n"
                "    legend cell align=left]\n%s\n\\end{axis}\n" % (nombre, lugar, ESTILO, ymin, ymax, ytick, ylab, titulo, "\n".join(cuerpo)))

    fig = "\\begin{tikzpicture}\n"
    fig += panel_irf("a", "(a) Tipo de los fondos federales", "{(0,0)}", 3, "Puntos", -0.6, 1.4, "-0.5,0,0.5,1", leyenda=True)
    fig += panel_irf("b", "(b) PIB real", "{($(a.north east)+(1.6cm,0)$)}", 0, "\\%", -1.4, 0.6, "-1.2,-0.8,-0.4,0,0.4")
    fig += panel_irf("c", "(c) Deflactor del PIB", "{($(a.south west)+(0,-2.1cm)$)}", 1, "\\%", -1.6, 0.8, "-1.5,-1,-0.5,0,0.5")
    fig += panel_irf("d", "(d) Precios de las materias primas", "{($(c.north east)+(1.6cm,0)$)}", 2, "\\%", -3, 1.5, "-3,-2,-1,0,1")
    fig += "\\end{tikzpicture}"
    escribir("anx_var_monetario", fig, "Respuestas a una perturbación monetaria que sube un punto el tipo de los fondos federales: VAR recursivo de EE. UU. (PIB, deflactor, materias primas, tipo).")

    # ---- proyección local del PIB frente al VAR (muestra de CEE)
    lp = proyeccion_local(X)
    for h, (b_, s_) in enumerate(lp):
        filas_series.append(("Proyección local del PIB", "Estados Unidos", "h = %d trimestres" % h, round(b_, 4), "%", "elaboración propia con FRED",
                             "error típico de NEWEY y WEST %.4f; banda del 90%% [%.3f, %.3f]" % (s_, b_ - 1.645 * s_, b_ + 1.645 * s_), "anx_proyeccion_local"))
    klp = int(np.argmin([b_ for b_, _ in lp]))
    cifras.append(("Proyección local: caída máxima del PIB (h) y banda del 90%", "%.2f (h = %d) [%.2f, %.2f]" % (lp[klp][0], klp, lp[klp][0] - 1.645 * lp[klp][1], lp[klp][0] + 1.645 * lp[klp][1]), "%", "I.7"))
    cifras.append(("Proyección local frente al VAR en h = 4, 8, 12, 16 y 20", "; ".join("%d: %.2f ± %.2f frente a %.2f ± %.2f" % (h, lp[h][0], 1.645 * lp[h][1], r[h, 0], (hi[h, 0] - lo[h, 0]) / 2)
                                                                            for h in (4, 8, 12, 16, 20)), "%", "I.7"))
    lp_b, lp_lo, lp_hi = [b_ for b_, _ in lp], [b_ - 1.645 * s_ for b_, s_ in lp], [b_ + 1.645 * s_ for b_, s_ in lp]
    cuerpo = [banda(lo[:, 0], hi[:, 0]) + "\n\\addlegendentry{VAR: banda del $90\\%$}",
              linea_h(r[:, 0], "black, thick") + "\n\\addlegendentry{VAR}",
              linea_h(lp_b, "black!70, dashed, thick, mark=*, mark size=1pt") + "\n\\addlegendentry{proyección local}",
              linea_h(lp_lo, "black!60, densely dotted") + "\n\\addlegendentry{proyección local: banda del $90\\%$}",
              linea_h(lp_hi, "black!60, densely dotted, forget plot"),
              "\\addplot[black!40, thin, forget plot] coordinates {(0,0) (20,0)};"]
    fig = ("\\begin{tikzpicture}\n\\begin{axis}[width=14.2cm, height=4.6cm, scale only axis, %s,\n"
           "    xmin=0, xmax=20, xtick={0,2,...,20}, ymin=-1.9, ymax=0.6, ytick={-1.5,-1,-0.5,0,0.5}, xlabel={Trimestres}, ylabel={\\%%},\n"
           "    legend style={draw=none, fill=none, font=\\footnotesize, at={(0.01,0.03)}, anchor=south west}, legend columns=2, legend cell align=left]\n%s\n\\end{axis}\n\\end{tikzpicture}"
           % (ESTILO, "\n".join(cuerpo)))
    escribir("anx_proyeccion_local", fig, "Respuesta del PIB de EE. UU. a una subida de un punto del tipo: proyección local (JORDÀ, 2005) frente al VAR recursivo, 1965T3-1995T3.")

    # ---- señales de recesión: probit de la pendiente (10 años menos 3 meses) y regla de SAHM en tiempo real
    gs10, tb3, rec = a_dict(leer(carpeta, "GS10")), a_dict(leer(carpeta, "TB3MS")), a_dict(leer(carpeta, "USREC"))
    sahm = a_dict(leer(carpeta, "SAHMREALTIME"))

    def equivalente(d):  # letras a tres meses: del tipo de descuento al rendimiento equivalente al de un bono
        d = d / 100.0
        return 100 * 365 * d / (360 - 91 * d)

    def mas_meses(f, n):
        a, m = int(f[:4]), int(f[5:7]) - 1 + n
        return "%d-%02d-01" % (a + m // 12, m % 12 + 1)

    meses = sorted(f for f in gs10 if f in tb3)
    pend = {f: gs10[f] - equivalente(tb3[f]) for f in meses}
    estimaciones = {}
    for fin in ("2018-12-01", "2024-10-01"):
        ts = [f for f in meses if "1959-01-01" <= f <= fin and mas_meses(f, 12) in rec]
        estimaciones[fin] = probit(np.array([pend[f] for f in ts]), np.array([rec[mas_meses(f, 12)] for f in ts]))
    b0, b1 = estimaciones["2018-12-01"]
    prob = {f: 100 * float(normal(b0 + b1 * pend[f])) for f in meses if f >= "1959-01-01"}
    for f in meses:
        if f >= "1959-01-01":
            filas_series.append(("Probabilidad de recesión dentro de doce meses (probit de la pendiente)", "Estados Unidos", f, round(prob[f], 2), "%",
                                 "elaboración propia con FRED (GS10, TB3MS, USREC)", "pendiente %.2f; probit estimado con 1959-2018 (recesiones hasta 2019)" % pend[f], "anx_probit_recesion"))
    for f in sorted(sahm):
        filas_series.append(("Indicador de SAHM con los datos de cada momento", "Estados Unidos", f, sahm[f], "puntos", "FRED (SAHMREALTIME)", "", "anx_regla_sahm"))
    cifras.append(("Probit (estimado 1959-2018): constante y pendiente", "%.3f; %.3f" % (b0, b1), "", "I.8"))
    c0, c1 = estimaciones["2024-10-01"]
    cifras.append(("Probit con datos hasta 2025 (como el 3.B.24): probabilidad en mayo de 2023", "%.1f" % (100 * float(normal(c0 + c1 * pend["2023-05-01"]))), "%", "I.8"))
    m23 = max((v, f) for f, v in prob.items() if f >= "2019-01-01")
    cifras.append(("Probit (1959-2018): máximo desde 2019 (fecha) y pendiente de ese mes", "%.1f en %s; %.2f" % (m23[0], m23[1][:7], pend[m23[1]]), "% y puntos", "I.8"))
    m81 = max((v, f) for f, v in prob.items() if "1982-01-01" <= f < "2022-01-01")
    cifras.append(("Probit (1959-2018): máximo entre 1982 y 2021", "%.1f en %s" % m81, "%", "I.8"))
    fr = sorted(rec)
    picos = [fr[i - 1] for i in range(1, len(fr)) if rec[fr[i]] == 1 and rec[fr[i - 1]] == 0 and fr[i] >= "1960-01-01"]
    previas = []
    for p_ in picos:
        ventana = [f for f in prob if mas_meses(p_, -18) <= f <= p_]
        previas.append("%s: %.0f" % (p_[:7], max(prob[f] for f in ventana)))
    cifras.append(("Probit: probabilidad máxima en los 18 meses anteriores a cada pico del NBER", "; ".join(previas), "%", "I.8"))
    episodios, dentro = [], False
    for f in sorted(prob):
        if prob[f] >= 40 and not dentro:
            episodios.append(f); dentro = True
        elif prob[f] < 40:
            dentro = False
    falsas = [f[:7] for f in episodios if not any(rec.get(mas_meses(f, k), 0) == 1 for k in range(0, 25))]
    cifras.append(("Probit: episodios con probabilidad de al menos 40% (inicio) y los no seguidos de recesión en 24 meses", "%s | falsas: %s" % (", ".join(f[:7] for f in episodios), ", ".join(falsas)), "", "I.8"))
    fs_ = sorted(sahm)
    cruces = [f for i, f in enumerate(fs_) if sahm[f] >= 0.5 and (i == 0 or sahm[fs_[i - 1]] < 0.5)]
    cifras.append(("SAHM (datos de cada momento): meses en que cruza 0,5", ", ".join(f[:7] for f in cruces), "", "I.8"))
    desfases = []
    for p_ in picos:
        c_ = next((f for f in cruces if mas_meses(p_, -3) <= f <= mas_meses(p_, 12)), None)
        if c_:
            a1, m1, a2, m2 = int(p_[:4]), int(p_[5:7]), int(c_[:4]), int(c_[5:7])
            desfases.append("%s: %+d" % (p_[:7], (a2 - a1) * 12 + m2 - m1))
    cifras.append(("SAHM: meses entre cada pico del NBER y el cruce de 0,5", "; ".join(desfases), "meses", "I.8"))
    cifras.append(("SAHM en 2024: julio, agosto y septiembre", "%.2f; %.2f; %.2f" % (sahm["2024-07-01"], sahm["2024-08-01"], sahm["2024-09-01"]), "puntos", "I.8"))
    m20 = max((v, f) for f, v in sahm.items() if "2020-01-01" <= f <= "2021-12-01")
    cifras.append(("SAHM: máximo de 2020", "%.2f en %s" % (m20[0], m20[1][:7]), "puntos", "I.8"))
    xm = [decimal(f) for f in sorted(prob)]
    sombra = tramos([decimal(f) for f in fr if f >= "1959-01-01"], [rec[f] for f in fr if f >= "1959-01-01"], 1 / 12.0)
    cuerpo_a = sombras(sombra, 50) + "\n\\addplot[black, thick] coordinates {%s};" % coords(xm, [prob[f] for f in sorted(prob)], 2)
    cuerpo_a += "\n\\addplot[black!55, dashed] coordinates {(1959,50) (2027,50)};"
    xs_ = [decimal(f) for f in fs_]
    cuerpo_b = sombras(sombra, 0) + "\n\\addplot[black, thick] coordinates {%s};" % coords(xs_, [sahm[f] for f in fs_], 2)
    cuerpo_b += "\n\\addplot[black!55, dashed] coordinates {(1959,0.5) (2027,0.5)};\n\\addplot[black!40, thin] coordinates {(1959,0) (2027,0)};"
    # dos figuras separadas, porque cada una se comenta en su párrafo
    fig = ("\\begin{tikzpicture}\n\\begin{axis}[width=14.2cm, height=4.2cm, scale only axis, %s,\n"
           "    xmin=1959, xmax=2027, xtick={1960,1965,...,2025}, ymin=0, ymax=100, ytick={0,25,50,75,100}, ylabel={Porcentaje}]\n%s\n\\end{axis}\n\\end{tikzpicture}"
           % (ESTILO, cuerpo_a))
    escribir("anx_probit_recesion", fig, "EE. UU.: probabilidad de estar en recesión doce meses después según un probit sobre la pendiente (10 años menos 3 meses), estimado con 1959-2018.")
    fig = ("\\begin{tikzpicture}\n\\begin{axis}[width=14.2cm, height=4.2cm, scale only axis, %s,\n"
           "    xmin=1959, xmax=2027, xtick={1960,1965,...,2025}, ymin=-0.5, ymax=3, ytick={0,0.5,1,2,3}, ylabel={Puntos}]\n%s\n\\end{axis}\n\\end{tikzpicture}"
           % (ESTILO, cuerpo_b))
    escribir("anx_regla_sahm", fig, "EE. UU.: regla de SAHM con los datos de cada momento (media de tres meses del paro menos su mínimo de los doce meses anteriores).")


# ---------------------------------------------------------------- A4 (07/11/2026): impulso y propagación; prueba de LUCAS
# Figuras sintéticas: anx_slutsky (suma móvil de diez cifras aleatorias, SLUTSKY 1927/1937) y anx_frisch (un proceso
# autorregresivo de orden dos con raíces complejas, el esquema de YULE 1927 y FRISCH 1933: respuesta a un impulso y a una
# sucesión de impulsos). Figura con datos: anx_lucas_pendiente (réplica de LUCAS 1973 y de BALL, MANKIW y ROMER 1988 con
# el PIB nominal y real de los Indicadores del Desarrollo Mundial del Banco Mundial, NY.GDP.MKTP.CN y NY.GDP.MKTP.KN).
BANCO_MUNDIAL = {"NY.GDP.MKTP.CN": "PIB a precios corrientes, moneda nacional", "NY.GDP.MKTP.KN": "PIB a precios constantes, moneda nacional"}


def descargar_a4(carpeta):
    for s in BANCO_MUNDIAL:
        destino = os.path.join(carpeta, s + ".json")
        if not os.path.exists(destino):
            urllib.request.urlretrieve("https://api.worldbank.org/v2/country/all/indicator/%s?format=json&per_page=20000&date=1960:2024" % s, destino)
    destino = os.path.join(carpeta, "paises.json")
    if not os.path.exists(destino):
        urllib.request.urlretrieve("https://api.worldbank.org/v2/country?format=json&per_page=400", destino)


def sinteticas_a4(sim):
    def eje(nombre, titulo, lugar, cuerpo, alto, ylab, xmax, xlab=""):
        return ("\\begin{axis}[name=%s, at={%s}, anchor=north west, width=14.2cm, height=%s, scale only axis, %s,\n"
                "    xmin=0, xmax=%d, xtick=\\empty, ytick=\\empty, title={%s}, title style={font=\\footnotesize, yshift=-1ex},\n"
                "    ylabel={%s}, xlabel={%s}, xlabel style={at={(1,0)}, anchor=north east}]\n%s\n\\end{axis}\n"
                % (nombre, lugar, alto, ESTILO, xmax, titulo, ylab, xlab, cuerpo))

    # anx_slutsky: cifras aleatorias de 0 a 9 y su suma móvil de diez términos
    rng = np.random.default_rng(1927)
    cifras_ = rng.integers(0, 10, 170)
    suma = np.convolve(cifras_, np.ones(10), mode="valid")  # y_t = suma de la cifra de t y las nueve anteriores
    tt = np.arange(9, 170)
    p1 = "\\addplot[black, thin, mark=*, mark size=0.6pt] coordinates {%s};" % coords(np.arange(170), cifras_, 0)
    p2 = ("\\addplot[black, thick] coordinates {%s};\n\\addplot[black!55, dashed] coordinates {(0,45) (169,45)};" % coords(tt, suma, 0))
    fig = "\\begin{tikzpicture}\n"
    fig += eje("a", "(a) Cifras aleatorias, independientes entre sí", "{(0,0)}", p1, "2.4cm", "$\\nu_t$", 169)
    fig += eje("b", "(b) Suma móvil de diez términos de las mismas cifras", "{($(a.south west)+(0,-1.3cm)$)}", p2, "3.2cm", "$y_t$", 169, "tiempo")
    fig += "\\end{tikzpicture}"
    escribir("anx_slutsky", fig, "Efecto SLUTSKY: la suma móvil de diez cifras aleatorias (semilla 1927) ondula como un ciclo.")
    sim.append(("Simulación", "170 cifras aleatorias uniformes de 0 a 9 (semilla 1927) y su suma móvil de diez términos", "anx_slutsky"))

    # anx_frisch: y_t = a1 y_{t-1} + a2 y_{t-2} + nu_t con raíces complejas de módulo 0,93 y periodo 32
    r, periodo = 0.93, 32.0
    a1, a2 = 2 * r * math.cos(2 * math.pi / periodo), -r * r
    n = 121
    imp = np.zeros(n)
    imp[0] = 1.0
    for t_ in range(1, n):
        imp[t_] = a1 * imp[t_ - 1] + (a2 * imp[t_ - 2] if t_ >= 2 else 0.0)
    rng = np.random.default_rng(1933)
    nu = rng.normal(0, 1, 300)
    y = np.zeros(300)
    for t_ in range(300):
        y[t_] = nu[t_] + (a1 * y[t_ - 1] if t_ >= 1 else 0.0) + (a2 * y[t_ - 2] if t_ >= 2 else 0.0)
    nu, y = nu[100:], y[100:]
    t2 = np.arange(200)
    p1 = "\\addplot[black, thick] coordinates {%s};\n\\addplot[black!55, dashed] coordinates {(0,0) (120,0)};" % coords(np.arange(n), imp)
    p2 = "\\addplot[ycomb, black!60, thin] coordinates {%s};\n\\addplot[black!40, thin] coordinates {(0,0) (199,0)};" % coords(t2, nu)
    p3 = "\\addplot[black, thick] coordinates {%s};\n\\addplot[black!55, dashed] coordinates {(0,0) (199,0)};" % coords(t2, y)
    fig = "\\begin{tikzpicture}\n"
    fig += eje("a", "(a) Respuesta a un único impulso", "{(0,0)}", p1, "2.4cm", "$\\Theta_j$", 120)
    fig += eje("b", "(b) Una sucesión de impulsos aleatorios", "{($(a.south west)+(0,-1.3cm)$)}", p2, "2.0cm", "$\\nu_t$", 199)
    fig += eje("c", "(c) Respuesta del mismo sistema a esos impulsos", "{($(b.south west)+(0,-1.3cm)$)}", p3, "2.6cm", "$y_t$", 199, "tiempo")
    fig += "\\end{tikzpicture}"
    escribir("anx_frisch", fig, "Esquema de FRISCH: AR(2) con a1 = %.3f y a2 = %.4f (módulo 0,93, periodo 32); impulsos normales (semilla 1933)." % (a1, a2))
    sim.append(("Simulación", "AR(2) con a1 = %.3f y a2 = %.4f (raíces complejas de módulo 0,93 y periodo 32); respuesta a un impulso unitario y a 300 "
                "impulsos normales (semilla 1933), sin los 100 primeros" % (a1, a2), "anx_frisch"))
    return a1, a2


def con_datos_a4(carpeta, filas_series, cifras):
    import json
    meta = json.load(open(os.path.join(carpeta, "paises.json"), encoding="utf-8"))[1]
    reales = {m["iso2Code"] for m in meta if m["region"]["value"] != "Aggregates"}  # los datos identifican el país con el código de dos letras

    def serie(indicador):
        salida = {}
        for r in json.load(open(os.path.join(carpeta, indicador + ".json"), encoding="utf-8"))[1]:
            if r["country"]["id"] in reales and r["value"] is not None and r["value"] > 0:
                salida.setdefault(r["countryiso3code"], {})[int(r["date"])] = float(r["value"])
        return salida

    nom, real = serie("NY.GDP.MKTP.CN"), serie("NY.GDP.MKTP.KN")
    res = []
    for c in sorted(set(nom) & set(real)):
        anos = [a for a in range(1960, 2020) if a in nom[c] and a in real[c]]
        mejor, act = [], []
        for a in anos:  # tramo de años consecutivos más largo
            act = act + [a] if act and a == act[-1] + 1 else [a]
            if len(act) > len(mejor):
                mejor = list(act)
        if len(mejor) < 41:
            continue
        x = np.array([100 * math.log(nom[c][a]) for a in mejor])
        yv = np.array([100 * math.log(real[c][a]) for a in mejor])
        dx, dp = np.diff(x), np.diff(x - yv)
        # LUCAS (1973): y_t = a + b t + tau Dx_t + c y_{t-1}; tau, parte de un cambio de la renta nominal que va a la producción real
        X = np.c_[np.ones(len(dx)), np.arange(len(dx)), dx, yv[:-1]]
        b = np.linalg.lstsq(X, yv[1:], rcond=None)[0]
        res.append((c, mejor[0], mejor[-1], b[2], dx.std(ddof=1), dp.mean()))
        filas_series.append(("Prueba de LUCAS: respuesta de la producción a la renta nominal", c, "%d-%d" % (mejor[0], mejor[-1]), round(b[2], 4), "proporción",
                             "Banco Mundial (NY.GDP.MKTP.CN y NY.GDP.MKTP.KN)", "desv. típica del crecimiento nominal %.2f; inflación media %.2f" % (dx.std(ddof=1), dp.mean()),
                             "anx_lucas_pendiente"))
    tau = np.array([r[3] for r in res]); sig = np.array([r[4] for r in res]); inf = np.array([r[5] for r in res])

    def mco(yy, xx):
        X = np.c_[np.ones(len(yy)), xx]
        b = np.linalg.lstsq(X, yy, rcond=None)[0]
        u = yy - X @ b
        Q = np.linalg.inv(X.T @ X)
        V = Q @ ((X * u[:, None]).T @ (X * u[:, None])) @ Q * len(yy) / (len(yy) - X.shape[1])
        return b, b / np.sqrt(np.diag(V)), 1 - (u @ u) / ((yy - yy.mean()) @ (yy - yy.mean()))

    ls, li = np.log(sig), np.log(np.maximum(inf, 0.5))
    cifras.append(("Prueba de LUCAS: países con al menos 41 años seguidos entre 1960 y 2019", "%d" % len(res), "países", "II.2"))
    cifras.append(("Prueba de LUCAS: mediana de la respuesta, de la volatilidad nominal y de la inflación media", "%.2f; %.1f; %.1f" % (np.median(tau), np.median(sig), np.median(inf)), "proporción y %", "II.2"))
    cifras.append(("Correlación de la respuesta con el log de la volatilidad nominal y con el log de la inflación media", "%.2f; %.2f" % (np.corrcoef(tau, ls)[0, 1], np.corrcoef(tau, li)[0, 1]), "", "II.2"))
    cifras.append(("Correlación entre los logs de la volatilidad nominal y de la inflación media", "%.2f" % np.corrcoef(ls, li)[0, 1], "", "II.2"))
    for etiqueta, xx in (("volatilidad", ls), ("inflación", li), ("ambas", np.c_[ls, li])):
        b, tst, r2 = mco(tau, xx)
        cifras.append(("Regresión de la respuesta sobre log(%s): coeficientes, t robustos y R2" % etiqueta,
                       "; ".join("%.3f (t = %.2f)" % (bi, ti) for bi, ti in zip(b[1:], tst[1:])) + "; R2 = %.2f" % r2, "", "II.2"))
    k = inf < 30
    b, tst, r2 = mco(tau[k], np.c_[ls[k], li[k]])
    cifras.append(("Lo mismo sin los países con inflación media de al menos el 30 %% (%d países)" % k.sum(),
                   "; ".join("%.3f (t = %.2f)" % (bi, ti) for bi, ti in zip(b[1:], tst[1:])) + "; R2 = %.2f" % r2, "", "II.2"))
    for c in ("ESP", "USA", "DEU", "ARG", "BRA"):
        r = [r for r in res if r[0] == c][0]
        cifras.append(("Prueba de LUCAS: %s" % c, "respuesta %.2f; volatilidad %.1f; inflación media %.1f" % (r[3], r[4], r[5]), "proporción y %", "II.2"))
    cifras.append(("Prueba de LUCAS: respuesta mínima y máxima", "%.2f; %.2f" % (tau.min(), tau.max()), "proporción", "II.2"))

    def panel(nombre, lugar, titulo, xs, xmin, xmax, xlab, leyenda):
        b, _, _ = mco(tau, np.log(xs))
        rejilla = np.exp(np.linspace(math.log(min(xs)), math.log(max(xs)), 30))  # el ajuste solo en el recorrido de los datos
        resto = [(x_, t_) for x_, t_, r in zip(xs, tau, res) if r[0] not in ("ESP", "USA")]
        cuerpo = "\\addplot[only marks, mark=o, mark size=1.3pt, black!50] coordinates {%s};" % " ".join("(%.4f,%.4f)" % p for p in resto)
        if leyenda:
            cuerpo += "\n\\addlegendentry{otros países}"
        for c, marca, etiqueta in (("ESP", "square*", "España"), ("USA", "triangle*", "Estados Unidos")):
            r = [(x_, t_) for x_, t_, rr in zip(xs, tau, res) if rr[0] == c][0]
            cuerpo += "\n\\addplot[only marks, mark=%s, mark size=2.2pt, black] coordinates {(%.4f,%.4f)};" % (marca, r[0], r[1])
            if leyenda:
                cuerpo += "\n\\addlegendentry{%s}" % etiqueta
        cuerpo += "\n\\addplot[black, dashed, thick] coordinates {%s};" % " ".join("(%.4f,%.4f)" % (x_, b[0] + b[1] * math.log(x_)) for x_ in rejilla)
        if leyenda:
            cuerpo += "\n\\addlegendentry{ajuste lineal en logaritmos}"
        cuerpo += "\n\\addplot[black!40, thin, forget plot] coordinates {(%s,0) (%s,0)};" % (xmin, xmax)
        return ("\\begin{axis}[name=%s, at={%s}, anchor=north west, width=6.2cm, height=5.2cm, scale only axis, %s,\n"
                "    xmode=log, xmin=%s, xmax=%s, xtick={1,2,5,10,20,50,100}, xticklabels={$1$,$2$,$5$,$10$,$20$,$50$,$100$},\n"
                "    ymin=-0.4, ymax=1.2, ytick={-0.4,0,0.4,0.8,1.2}, xlabel={%s}, ylabel={Respuesta de la producción real},\n"
                "    title={%s}, title style={font=\\footnotesize},\n"
                "    legend style={draw=none, fill=none, font=\\footnotesize, at={(0.5,-0.25)}, anchor=north}, legend columns=4, legend cell align=left]\n%s\n\\end{axis}\n"
                % (nombre, lugar, ESTILO, xmin, xmax, xlab, titulo, cuerpo))

    fig = "\\begin{tikzpicture}\n"
    fig += panel("a", "{(0,0)}", "(a) Volatilidad de la demanda nominal", sig, 1, 150, "Desviación típica del crecimiento nominal (\\%, escala log.)", False)
    fig += panel("b", "{($(a.north east)+(1.6cm,0)$)}", "(b) Inflación media", np.maximum(inf, 0.5), 0.5, 150, "Inflación media anual (\\%, escala log.)", False)
    fig += ("\\node[anchor=north, font=\\footnotesize] at ($(a.south east)!0.5!(b.south west)+(0,-1.0cm)$) {\\tikz{\\draw[black!50] (0,0) circle (1.3pt);}~otros países\\quad "
            "\\tikz{\\fill (0,0) rectangle (2.6pt,2.6pt);}~España\\quad \\tikz{\\fill (0,0) -- (3pt,0) -- (1.5pt,2.6pt) -- cycle;}~Estados Unidos\\quad "
            "\\tikz{\\draw[black, dashed, thick] (0,0) -- (0.5cm,0);}~ajuste lineal en logaritmos};\n")
    fig += "\\end{tikzpicture}"
    escribir("anx_lucas_pendiente", fig, "Réplica de LUCAS (1973) y BALL, MANKIW y ROMER (1988): parte de un cambio de la renta nominal que va a la producción real en %d países, 1960-2019." % len(res))


# ---------------------------------------------------------------- A5 (07/11/2026): el modelo básico del ciclo real
# Modelo de crecimiento estocástico con trabajo elástico (KYDLAND y PRESCOTT, 1982; KING, PLOSSER y REBELO, 1988):
# u = ln C + chi ln(1 - h) (trabajo divisible, elasticidad de FRISCH (1 - h)/h = 2) o u = ln C - B h (trabajo
# indivisible de HANSEN, 1985); Y = Z k^eta h^(1-eta); k' = (1 - d) k + I; z' = rho z + nu. Log-linealizado y resuelto por
# coeficientes indeterminados (la regla del consumo es lineal en el capital y la productividad; se elige la raíz estable).
# Calibración trimestral: delta 0,99 (tipo real del 4 % anual), eta 0,36, d 0,025, h 1/3, rho 0,95, sigma 0,7 %.
RBC = dict(eta=0.36, delta=0.99, d=0.025, hbar=1 / 3.0, rho=0.95, sigma=0.7)


def rbc_resolver(rho, indivisible, eta=RBC["eta"], delta=RBC["delta"], d=RBC["d"], hbar=RBC["hbar"]):
    rbar = 1 / delta - 1
    yk = (rbar + d) / eta
    s_i = d / yk
    s_c = 1 - s_i
    fh = 1.0 if indivisible else 1 / (1 - hbar)  # condición intratemporal: c = y - fh h
    den = fh - (1 - eta)
    a = delta * (rbar + d)

    def mapas(ck, cz, k, z):  # variables en desviación logarítmica (en %) dadas la regla del consumo, el capital y z
        c = ck * k + cz * z
        h = (z + eta * k - c) / den
        y = z + eta * k + (1 - eta) * h
        i = (y - s_c * c) / s_i
        return c, h, y, i, (1 - d) * k + d * i

    def resid(ck, cz, k, z):  # ecuación de EULER: E c' - c = delta (r + d) E[y' - k']
        c, h, y, i, kp = mapas(ck, cz, k, z)
        ez = rho * z
        ec = ck * kp + cz * ez
        ey = ez + eta * kp + (1 - eta) * (ez + eta * kp - ec) / den
        return (ec - c) - a * (ey - kp)

    xs = np.array([0.0, 0.5, 1.0])
    raices = np.roots(np.polyfit(xs, [resid(x, 0.0, 1.0, 0.0) for x in xs], 2)).real
    ck = [x for x in raices if x > 0 and abs(mapas(x, 0.0, 1.0, 0.0)[4]) < 1][0]
    f0, f1 = resid(ck, 0.0, 0.0, 1.0), resid(ck, 1.0, 0.0, 1.0)
    return dict(ck=ck, cz=-f0 / (f1 - f0), mapas=mapas, rbar=rbar, d=d, s_i=s_i, yk=yk)


def rbc_trayectoria(sol, z):
    salida = {v: np.zeros(len(z)) for v in ("y", "c", "h", "i", "w", "r", "k", "z")}
    k = 0.0
    for t, zt in enumerate(z):
        c, h, y, i, kp = sol["mapas"](sol["ck"], sol["cz"], k, zt)
        for v, x in (("y", y), ("c", c), ("h", h), ("i", i), ("w", y - h), ("k", k), ("z", zt)):
            salida[v][t] = x
        salida["r"][t] = 4 * (sol["rbar"] + sol["d"]) * (y - k)  # tipo de interés real, puntos porcentuales anualizados
        k = kp
    return salida


def con_datos_a5(carpeta, filas_series, cifras, momentos, sim):
    H = 40
    soluciones = {(rho, ind): rbc_resolver(rho, ind) for rho in (RBC["rho"], 0.0) for ind in (False, True)}
    persistente = RBC["rho"] ** np.arange(H + 1)
    unico = np.zeros(H + 1)
    unico[0] = 1.0
    irf = {ind: rbc_trayectoria(soluciones[(RBC["rho"], ind)], persistente) for ind in (False, True)}
    irf0 = rbc_trayectoria(soluciones[(0.0, False)], unico)
    nombres = {"y": "Producción", "c": "Consumo", "i": "Inversión", "h": "Horas", "w": "Salario real", "r": "Tipo de interés real", "k": "Capital", "z": "Productividad total de los factores"}
    for ind, et in ((False, "trabajo divisible"), (True, "trabajo indivisible")):
        for v in ("y", "c", "i", "h", "w", "r", "k"):
            for h_ in range(H + 1):
                filas_series.append(("Ciclo real: respuesta de %s (%s)" % (nombres[v].lower(), et), "Modelo", "h = %d trimestres" % h_, round(float(irf[ind][v][h_]), 4),
                                     "puntos" if v == "r" else "%", "simulación propia", "mejora del 1 % de la PTF con rho = 0,95", "anx_rbc_respuestas"))
        s = soluciones[(RBC["rho"], ind)]
        cifras.append(("Ciclo real (%s): impacto en producción, consumo, inversión, horas, salario y tipo" % et,
                       "; ".join("%.2f" % irf[ind][v][0] for v in ("y", "c", "i", "h", "w", "r")), "% (tipo en puntos anuales)", "II.3"))
        cifras.append(("Ciclo real (%s): consumo en h = 12 y capital en h = 12" % et, "%.2f; %.2f" % (irf[ind]["c"][12], irf[ind]["k"][12]), "%", "II.3"))
    s = soluciones[(RBC["rho"], False)]
    cifras.append(("Ciclo real: capital/producción trimestral, inversión/producción y tipo real anual de estado estacionario",
                   "%.2f; %.3f; %.2f" % (1 / s["yk"], s["s_i"], 400 * s["rbar"]), "", "II.3"))
    cifras.append(("Ciclo real con rho = 0: producción en h = 0, 1 y 4", "%.2f; %.2f; %.2f" % (irf0["y"][0], irf0["y"][1], irf0["y"][4]), "%", "II.3"))
    sim.append(("Simulación", "Modelo básico del ciclo real log-linealizado (delta 0,99; eta 0,36; d 0,025; h 1/3; rho 0,95 y 0; sigma 0,7 %%), trabajo divisible "
                "(elasticidad de FRISCH 2) e indivisible; respuestas a una mejora del 1 %% de la PTF", "anx_rbc_respuestas y anx_rbc_propagacion"))

    # ---- momentos simulados: 500 muestras de 200 trimestres (tras 100 de arranque), filtro HP
    rng = np.random.default_rng(1982)
    for ind, et in ((False, "divisible"), (True, "indivisible")):
        acum = {}
        for _ in range(500):
            nu = rng.normal(0, RBC["sigma"], 300)
            z = np.zeros(300)
            for t in range(300):
                z[t] = (RBC["rho"] * z[t - 1] if t else 0.0) + nu[t]
            o = rbc_trayectoria(soluciones[(RBC["rho"], ind)], z)
            cic = {v: hp(o[v][100:])[0] for v in ("y", "c", "i", "h", "w")}
            sy = cic["y"].std()
            vals = {"sy": sy, "ry": np.corrcoef(cic["y"][1:], cic["y"][:-1])[0, 1], "chw": np.corrcoef(cic["h"], cic["w"])[0, 1]}
            for v in ("c", "i", "h", "w"):
                vals["s" + v] = cic[v].std() / sy
                vals["c" + v] = np.corrcoef(cic[v], cic["y"])[0, 1]
            for k_, x in vals.items():
                acum.setdefault(k_, []).append(x)
        m = {k_: float(np.mean(x)) for k_, x in acum.items()}
        for v, etiqueta in (("c", "Consumo"), ("i", "Inversión"), ("h", "Horas"), ("w", "Productividad por hora")):
            momentos.append(("Modelo (%s)" % et, etiqueta, "sigma_x/sigma_y", round(m["s" + v], 2), "500 simulaciones de 200 trimestres", "HP 1600"))
            momentos.append(("Modelo (%s)" % et, etiqueta, "corr(x, y)", round(m["c" + v], 2), "500 simulaciones de 200 trimestres", "HP 1600"))
        momentos.append(("Modelo (%s)" % et, "PIB", "sigma (%)", round(m["sy"], 2), "500 simulaciones de 200 trimestres", "HP 1600"))
        momentos.append(("Modelo (%s)" % et, "PIB", "rho(1)", round(m["ry"], 2), "500 simulaciones de 200 trimestres", "HP 1600"))
        momentos.append(("Modelo (%s)" % et, "Horas y productividad", "corr", round(m["chw"], 2), "500 simulaciones de 200 trimestres", "HP 1600"))
        cifras.append(("Momentos del ciclo real (%s): sigma_y; rel. c, i, h, w; corr c, i, h, w; rho(1); corr(h, w)" % et,
                       "%.2f; %.2f, %.2f, %.2f, %.2f; %.2f, %.2f, %.2f, %.2f; %.2f; %.2f" % (m["sy"], m["sc"], m["si"], m["sh"], m["sw"], m["cc"], m["ci"], m["ch"], m["cw"], m["ry"], m["chw"]),
                       "", "II.3"))
    # ---- dato que falta en el cuadro del I.5: correlación entre las horas y la productividad, EE. UU. 1950-2019
    horas, prod = a_dict(leer(carpeta, "HOANBS")), a_dict(leer(carpeta, "OPHNFB"))
    fs, (hh, pp) = alinear([horas, prod], "1947-01-01", "2026-12-31")
    ch, _ = hp(np.array([100 * math.log(v) for v in hh]))
    cp, _ = hp(np.array([100 * math.log(v) for v in pp]))
    k = [i for i, f in enumerate(fs) if "1950-01-01" <= f <= "2019-10-01"]
    cifras.append(("Datos de EE. UU. 1950-2019: correlación de los ciclos HP de las horas y de la productividad por hora", "%.2f" % np.corrcoef(ch[k], cp[k])[0, 1], "", "II.3"))

    # ---- anx_rbc_respuestas: seis paneles, trabajo divisible (continua) e indivisible (discontinua)
    def panel(nombre, lugar, titulo, v, ylab, ymin, ymax, ytick, xlab=False, leyenda=False):
        cuerpo = ["\\addplot[black, thick] coordinates {%s};" % " ".join("(%d,%.4f)" % (h_, irf[False][v][h_]) for h_ in range(H + 1)),
                  "\\addplot[black!60, dashed, thick] coordinates {%s};" % " ".join("(%d,%.4f)" % (h_, irf[True][v][h_]) for h_ in range(H + 1))]
        if leyenda:
            cuerpo[0] += "\n\\addlegendentry{trabajo divisible}"
            cuerpo[1] += "\n\\addlegendentry{trabajo indivisible}"
        cuerpo.append("\\addplot[black!40, thin, forget plot] coordinates {(0,0) (40,0)};")
        return ("\\begin{axis}[name=%s, at={%s}, anchor=north west, width=6.2cm, height=2.6cm, scale only axis, %s,\n"
                "    xmin=0, xmax=40, xtick={0,8,...,40}, ymin=%s, ymax=%s, ytick={%s}, %sylabel={%s},\n"
                "    title={%s}, title style={font=\\footnotesize}, legend style={draw=none, fill=none, font=\\footnotesize, at={(0.98,0.98)}, anchor=north east}, legend cell align=left]\n%s\n\\end{axis}\n"
                % (nombre, lugar, ESTILO, ymin, ymax, ytick, "xlabel={Trimestres}, " if xlab else "", ylab, titulo, "\n".join(cuerpo)))

    fig = "\\begin{tikzpicture}\n"
    fig += panel("a", "{(0,0)}", "(a) Producción", "y", "\\%", 0, 2.2, "0,0.5,1,1.5,2", leyenda=True)
    fig += panel("b", "{($(a.north east)+(1.6cm,0)$)}", "(b) Consumo", "c", "\\%", 0, 1, "0,0.25,0.5,0.75,1")
    fig += panel("c", "{($(a.south west)+(0,-1.4cm)$)}", "(c) Inversión", "i", "\\%", -1, 7, "0,2,4,6")
    fig += panel("d", "{($(c.north east)+(1.6cm,0)$)}", "(d) Horas", "h", "\\%", -0.4, 1.6, "0,0.5,1,1.5")
    fig += panel("e", "{($(c.south west)+(0,-1.4cm)$)}", "(e) Salario real", "w", "\\%", 0, 1, "0,0.25,0.5,0.75,1", xlab=True)
    fig += panel("f", "{($(e.north east)+(1.6cm,0)$)}", "(f) Tipo de interés real", "r", "Puntos", -0.1, 0.3, "-0.1,0,0.1,0.2,0.3", xlab=True)
    fig += "\\end{tikzpicture}"
    escribir("anx_rbc_respuestas", fig, "Respuestas del modelo básico del ciclo real a una mejora del 1 % de la PTF con rho = 0,95: trabajo divisible e indivisible.")

    # ---- anx_rbc_propagacion: la producción sigue a la productividad (trabajo divisible)
    def panel_p(nombre, lugar, titulo, tray, leyenda):
        cuerpo = "\\addplot[black!55, dashed, thick] coordinates {%s};\n" % " ".join("(%d,%.4f)" % (h_, tray["z"][h_]) for h_ in range(H + 1))
        if leyenda:
            cuerpo += "\\addlegendentry{productividad total de los factores}\n"
        cuerpo += "\\addplot[black, thick] coordinates {%s};\n" % " ".join("(%d,%.4f)" % (h_, tray["y"][h_]) for h_ in range(H + 1))
        if leyenda:
            cuerpo += "\\addlegendentry{producción}\n"
        cuerpo += "\\addplot[black!40, thin, forget plot] coordinates {(0,0) (40,0)};"
        return ("\\begin{axis}[name=%s, at={%s}, anchor=north west, width=6.2cm, height=3.4cm, scale only axis, %s,\n"
                "    xmin=0, xmax=40, xtick={0,8,...,40}, ymin=-0.2, ymax=1.8, ytick={0,0.5,1,1.5}, xlabel={Trimestres}, ylabel={\\%%},\n"
                "    title={%s}, title style={font=\\footnotesize}, legend style={draw=none, fill=none, font=\\footnotesize, at={(0.98,0.98)}, anchor=north east}, legend cell align=left]\n%s\n\\end{axis}\n"
                % (nombre, lugar, ESTILO, titulo, cuerpo))

    fig = "\\begin{tikzpicture}\n"
    fig += panel_p("a", "{(0,0)}", "(a) Mejora persistente ($\\rho_z=0{,}95$)", irf[False], True)
    fig += panel_p("b", "{($(a.north east)+(1.6cm,0)$)}", "(b) Mejora de un solo trimestre ($\\rho_z=0$)", irf0, False)
    fig += "\\end{tikzpicture}"
    escribir("anx_rbc_propagacion", fig, "La producción sigue a la productividad: respuesta a una mejora del 1 % de la PTF persistente (rho 0,95) y de un trimestre (rho 0), trabajo divisible.")


# ---------------------------------------------------------------- A6 (07/11/2026): contrastación del ciclo real
# anx_gali_horas: VAR bivariante de la productividad del trabajo (OPHNFB) y las horas (HOANBS por habitante de 16 años o
# más, CNP16OV) con la restricción de largo plazo de GALÍ (1999): solo la perturbación tecnológica altera la productividad
# a largo plazo; horas en diferencias (GALÍ) o en niveles (CHRISTIANO, EICHENBAUM y VIGFUSSON); 1948-2007, 4 retardos.
# anx_rbc_autocorrelacion: autocorrelaciones del crecimiento del PIB en los datos y en el modelo básico (COGLEY y NASON, 1995b).
def svar_largo_plazo(X, p=RETARDOS, H=HORIZONTE):
    Y = X[p:]
    Z = np.hstack([np.ones((len(Y), 1))] + [X[p - j:len(X) - j] for j in range(1, p + 1)])
    B = np.linalg.lstsq(Z, Y, rcond=None)[0]
    E = Y - Z @ B
    S = E.T @ E / (len(Y) - Z.shape[1])
    Phi = [B[1 + 2 * (j - 1):1 + 2 * j].T for j in range(1, p + 1)]
    C1 = np.linalg.inv(np.eye(2) - sum(Phi))  # efecto acumulado a largo plazo de los errores
    G = np.linalg.inv(C1) @ np.linalg.cholesky(C1 @ S @ C1.T)  # efecto a largo plazo triangular: la tecnológica, primera
    if (C1 @ G)[0, 0] < 0:
        G[:, 0] = -G[:, 0]
    Psi = [np.eye(2)]
    for h in range(1, H + 1):
        Psi.append(sum(Phi[j] @ Psi[h - 1 - j] for j in range(min(p, h))))
    R = np.array([P @ G[:, 0] for P in Psi])
    return R, B, E


def con_datos_a6(carpeta, filas_series, cifras):
    prod, horas = a_dict(leer(carpeta, "OPHNFB")), a_dict(leer(carpeta, "HOANBS"))
    pob = a_dict(trimestral(leer(carpeta, "CNP16OV")))
    fs = sorted(f for f in prod if f in horas and f in pob and "1948-01-01" <= f <= "2007-10-01")
    lp = np.array([100 * math.log(prod[f]) for f in fs])
    lh = np.array([100 * math.log(horas[f] / pob[f]) for f in fs])
    resultados = {}
    for niveles in (False, True):
        X = np.c_[np.diff(lp), lh[1:] if niveles else np.diff(lh)]
        R, B, E = svar_largo_plazo(X)

        def a_niveles(R):
            return np.cumsum(R[:, 0]), (R[:, 1] if niveles else np.cumsum(R[:, 1]))

        pn, hn = a_niveles(R)
        rng = np.random.default_rng(1999)
        boot = []
        for _ in range(1000):
            e = E[rng.integers(0, len(E), len(E))]
            Xb = np.array(X, float)
            for t in range(RETARDOS, len(X)):
                Xb[t] = np.r_[1.0, np.concatenate([Xb[t - j] for j in range(1, RETARDOS + 1)])] @ B + e[t - RETARDOS]
            boot.append(a_niveles(svar_largo_plazo(Xb)[0])[1])
        lo, hi = np.percentile(boot, 16, axis=0), np.percentile(boot, 84, axis=0)
        resultados[niveles] = (pn, hn, lo, hi)
        et = "niveles" if niveles else "diferencias"
        for h_ in range(HORIZONTE + 1):
            filas_series.append(("VAR de largo plazo (horas en %s): respuesta de las horas a la perturbación tecnológica" % et, "Estados Unidos", "h = %d trimestres" % h_,
                                 round(float(hn[h_]), 4), "%", "elaboración propia con FRED (OPHNFB, HOANBS, CNP16OV)",
                                 "1948-2007, 4 retardos; banda del 68 %% [%.3f, %.3f]; productividad %.3f" % (lo[h_], hi[h_], pn[h_]), "anx_gali_horas"))
        cifras.append(("GALÍ (horas en %s), 1948-2007: horas en h = 0, 4 y 12 (banda del 68 %% en h = 0 y 4); productividad en h = 0 y 20" % et,
                       "%.2f [%.2f; %.2f]; %.2f [%.2f; %.2f]; %.2f; productividad %.2f y %.2f" % (hn[0], lo[0], hi[0], hn[4], lo[4], hi[4], hn[12], pn[0], pn[20]), "%", "II.4"))

    def panel(nombre, lugar, titulo, niveles, leyenda):
        pn, hn, lo, hi = resultados[niveles]
        cuerpo = "\\addplot[fill=black!15, draw=none, area legend] coordinates {%s %s};\n" % (
            " ".join("(%d,%.4f)" % (h_, lo[h_]) for h_ in range(HORIZONTE + 1)), " ".join("(%d,%.4f)" % (h_, hi[h_]) for h_ in range(HORIZONTE, -1, -1)))
        if leyenda:
            cuerpo += "\\addlegendentry{banda del $68\\%$}\n"
        cuerpo += "\\addplot[black, thick] coordinates {%s};\n" % " ".join("(%d,%.4f)" % (h_, hn[h_]) for h_ in range(HORIZONTE + 1))
        if leyenda:
            cuerpo += "\\addlegendentry{horas}\n"
        cuerpo += "\\addplot[black!40, thin, forget plot] coordinates {(0,0) (20,0)};"
        return ("\\begin{axis}[name=%s, at={%s}, anchor=north west, width=6.2cm, height=3.6cm, scale only axis, %s,\n"
                "    xmin=0, xmax=20, xtick={0,4,...,20}, ymin=-0.6, ymax=1.2, ytick={-0.5,0,0.5,1}, xlabel={Trimestres}, ylabel={\\%%},\n"
                "    title={%s}, title style={font=\\footnotesize}, legend style={draw=none, fill=none, font=\\footnotesize, at={(0.98,0.98)}, anchor=north east}, legend cell align=left]\n%s\n\\end{axis}\n"
                % (nombre, lugar, ESTILO, titulo, cuerpo))

    fig = "\\begin{tikzpicture}\n"
    fig += panel("a", "{(0,0)}", "(a) Horas en diferencias", False, True)
    fig += panel("b", "{($(a.north east)+(1.6cm,0)$)}", "(b) Horas por habitante en niveles", True, False)
    fig += "\\end{tikzpicture}"
    escribir("anx_gali_horas", fig, "Respuesta de las horas a una perturbación tecnológica identificada a largo plazo (GALÍ, 1999), EE. UU. 1948-2007, con las horas en diferencias y en niveles.")

    # ---- autocorrelaciones del crecimiento: datos (PIB real, 1950-2019) y modelo básico (500 simulaciones)
    pib = a_dict(leer(carpeta, "GDPC1"))
    fp = sorted(f for f in pib if "1949-10-01" <= f <= "2019-10-01")
    g = np.diff([100 * math.log(pib[f]) for f in fp])
    g = g - g.mean()

    def acf(x, k):
        return float(np.sum(x[k:] * x[:-k]) / np.sum(x * x))

    datos = [acf(g, k) for k in range(1, 9)]
    sol = rbc_resolver(RBC["rho"], False)
    rng = np.random.default_rng(1995)
    mod = np.zeros(8)
    for _ in range(500):
        nu = rng.normal(0, RBC["sigma"], 300)
        z = np.zeros(300)
        for t in range(300):
            z[t] = (RBC["rho"] * z[t - 1] if t else 0.0) + nu[t]
        gy = np.diff(rbc_trayectoria(sol, z)["y"][100:])
        gy = gy - gy.mean()
        mod += np.array([acf(gy, k) for k in range(1, 9)]) / 500
    for k in range(8):
        filas_series.append(("Autocorrelación del crecimiento del PIB", "Estados Unidos y modelo", "retardo %d" % (k + 1), round(datos[k], 3), "",
                             "FRED (GDPC1) y simulación propia", "modelo: %.3f (500 simulaciones de 200 trimestres)" % mod[k], "anx_rbc_autocorrelacion"))
    cifras.append(("Autocorrelación del crecimiento del PIB, datos 1950-2019, retardos 1 a 4", "; ".join("%.2f" % x for x in datos[:4]), "", "II.4"))
    cifras.append(("Autocorrelación del crecimiento en el modelo básico, retardos 1 a 4", "; ".join("%.2f" % x for x in mod[:4]), "", "II.4"))
    cuerpo = ("\\addplot[ybar, bar width=7pt, bar shift=-4pt, fill=black!70, draw=none] coordinates {%s};\n\\addlegendentry{datos de Estados Unidos, $1950$-$2019$}\n"
              "\\addplot[ybar, bar width=7pt, bar shift=4pt, fill=black!25, draw=none] coordinates {%s};\n\\addlegendentry{modelo básico del ciclo real}\n"
              "\\draw[black!40, thin] (axis cs:0.4,0) -- (axis cs:8.6,0);"
              % (" ".join("(%d,%.4f)" % (k + 1, datos[k]) for k in range(8)), " ".join("(%d,%.4f)" % (k + 1, mod[k]) for k in range(8))))
    fig = ("\\begin{tikzpicture}\n\\begin{axis}[width=14.2cm, height=4.2cm, scale only axis, %s,\n"
           "    xmin=0.4, xmax=8.6, xtick={1,...,8}, ymin=-0.15, ymax=0.4, ytick={-0.1,0,0.1,0.2,0.3,0.4}, xlabel={Retardo (trimestres)},\n"
           "    ylabel={Autocorrelación}, legend style={draw=none, fill=none, font=\\footnotesize, at={(0.98,0.98)}, anchor=north east}, legend cell align=left, area legend]\n%s\n\\end{axis}\n\\end{tikzpicture}"
           % (ESTILO, cuerpo))
    escribir("anx_rbc_autocorrelacion", fig, "Autocorrelaciones del crecimiento trimestral del PIB: datos de EE. UU. (1950-2019) y modelo básico del ciclo real (COGLEY y NASON, 1995b).")


# ---------------------------------------------------------------- A7 (07/11/2026): extensiones y coste de bienestar
# anx_rbc_gasto: el modelo del ciclo real con un segundo impulso, el gasto público (C + I + G = Y; G/Y = 0,2; g sigue un
# AR(1) con rho_g = 0,93 y sigma_g = 1,5 %, estimados con GCEC1 sobre una tendencia cuadrática, 1950-2019), como en
# CHRISTIANO y EICHENBAUM (1992). Coste de bienestar de LUCAS (1987, 2003): lambda = theta sigma^2 / 2 con el consumo real
# por habitante anual (PCECC96 / B230RC0A052NBEA) respecto a una tendencia lineal o de HODRICK-PRESCOTT con lambda 400.
GASTO = dict(s_g=0.20, rho_g=0.93, sigma_g=1.5)


def rbc_gasto_resolver(rho_z=RBC["rho"], rho_g=GASTO["rho_g"], s_g=GASTO["s_g"], eta=RBC["eta"], delta=RBC["delta"], d=RBC["d"], hbar=RBC["hbar"]):
    rbar = 1 / delta - 1
    s_i = d * eta / (rbar + d)
    s_c = 1 - s_i - s_g
    den = 1 / (1 - hbar) - (1 - eta)
    a = delta * (rbar + d)

    def mapas(ck, cz, cg, k, z, g):
        c = ck * k + cz * z + cg * g
        h = (z + eta * k - c) / den
        y = z + eta * k + (1 - eta) * h
        i = (y - s_c * c - s_g * g) / s_i
        return c, h, y, i, (1 - d) * k + d * i

    def resid(ck, cz, cg, k, z, g):
        c, h, y, i, kp = mapas(ck, cz, cg, k, z, g)
        ez, eg = rho_z * z, rho_g * g
        ec = ck * kp + cz * ez + cg * eg
        ey = ez + eta * kp + (1 - eta) * (ez + eta * kp - ec) / den
        return (ec - c) - a * (ey - kp)

    xs = np.array([0.0, 0.5, 1.0])
    raices = np.roots(np.polyfit(xs, [resid(x, 0, 0, 1, 0, 0) for x in xs], 2)).real
    ck = [x for x in raices if x > 0 and abs(mapas(x, 0, 0, 1, 0, 0)[4]) < 1][0]
    f0, f1 = resid(ck, 0, 0, 0, 1, 0), resid(ck, 1, 0, 0, 1, 0)
    cz = -f0 / (f1 - f0)
    f0, f1 = resid(ck, cz, 0, 0, 0, 1), resid(ck, cz, 1, 0, 0, 1)
    cg = -f0 / (f1 - f0)
    return dict(ck=ck, cz=cz, cg=cg, mapas=mapas, s_g=s_g, rbar=rbar, d=d)


def rbc_gasto_trayectoria(sol, z, g):
    salida = {v: np.zeros(len(z)) for v in ("y", "c", "h", "i", "w", "r")}
    k = 0.0
    for t in range(len(z)):
        c, h, y, i, kp = sol["mapas"](sol["ck"], sol["cz"], sol["cg"], k, z[t], g[t])
        for v, x in (("y", y), ("c", c), ("h", h), ("i", i), ("w", y - h)):
            salida[v][t] = x
        salida["r"][t] = 4 * (sol["rbar"] + sol["d"]) * (y - k)
        k = kp
    return salida


def con_datos_a7(carpeta, filas_series, cifras, sim):
    # ---- respuesta a un aumento del gasto público del 1 % del PIB (g = 1 / s_g en %), que se desvanece al ritmo rho_g
    sol = rbc_gasto_resolver()
    H = 40
    g = (100 * 0.01 / GASTO["s_g"]) * GASTO["rho_g"] ** np.arange(H + 1)
    irf = rbc_gasto_trayectoria(sol, np.zeros(H + 1), g)
    mult = irf["y"][0] / (GASTO["s_g"] * g[0])
    cifras.append(("Ciclo real con gasto: impacto de +1 % del PIB de gasto en producción, consumo, inversión, horas y salario",
                   "; ".join("%.2f" % irf[v][0] for v in ("y", "c", "i", "h", "w")) + "; multiplicador en el impacto %.2f" % mult, "%", "II.5"))
    for v, nom in (("y", "producción"), ("c", "consumo"), ("h", "horas"), ("w", "salario real")):
        for h_ in range(H + 1):
            filas_series.append(("Ciclo real: respuesta de %s a +1 %% del PIB de gasto público" % nom, "Modelo", "h = %d trimestres" % h_, round(float(irf[v][h_]), 4), "%",
                                 "simulación propia", "G/Y 0,2; rho_g 0,93", "anx_rbc_gasto"))
    # ---- momentos con las dos perturbaciones
    rng = np.random.default_rng(1992)
    acum = {}
    for _ in range(500):
        nz, ng = rng.normal(0, RBC["sigma"], 300), rng.normal(0, GASTO["sigma_g"], 300)
        z, gg = np.zeros(300), np.zeros(300)
        for t in range(300):
            z[t] = (RBC["rho"] * z[t - 1] if t else 0.0) + nz[t]
            gg[t] = (GASTO["rho_g"] * gg[t - 1] if t else 0.0) + ng[t]
        o = rbc_gasto_trayectoria(sol, z, gg)
        cic = {v: hp(o[v][100:])[0] for v in ("y", "h", "w", "c")}
        for k_, x in (("sy", cic["y"].std()), ("sh", cic["h"].std() / cic["y"].std()), ("chw", np.corrcoef(cic["h"], cic["w"])[0, 1]),
                      ("cw", np.corrcoef(cic["w"], cic["y"])[0, 1])):
            acum.setdefault(k_, []).append(x)
    m = {k_: float(np.mean(x)) for k_, x in acum.items()}
    cifras.append(("Ciclo real con tecnología y gasto: sigma_y; sigma_h/sigma_y; corr(h, w); corr(w, y)", "%.2f; %.2f; %.2f; %.2f" % (m["sy"], m["sh"], m["chw"], m["cw"]), "", "II.5"))
    sim.append(("Simulación", "Modelo del ciclo real con perturbaciones tecnológicas y del gasto público (G/Y 0,2; rho_g 0,93; sigma_g 1,5 %); 500 x 200 trimestres", "anx_rbc_gasto"))
    # proceso del gasto estimado con los datos (comprobación de la calibración)
    gd, yd = a_dict(leer(carpeta, "GCEC1")), a_dict(leer(carpeta, "GDPC1"))
    fs = sorted(f for f in gd if f in yd and "1950-01-01" <= f <= "2019-10-01")
    lg = np.array([math.log(gd[f]) for f in fs])
    tt = np.arange(len(lg))
    cgc = lg - np.polyval(np.polyfit(tt, lg, 2), tt)
    rho = float(np.dot(cgc[1:], cgc[:-1]) / np.dot(cgc[:-1], cgc[:-1]))
    cifras.append(("Gasto público real (GCEC1) 1950-2019 sobre tendencia cuadrática: rho y sigma de las innovaciones", "%.3f; %.2f" % (rho, 100 * float((cgc[1:] - rho * cgc[:-1]).std())), "%", "II.5"))

    def panel(nombre, lugar, titulo, v, ymin, ymax, ytick, xlab):
        cuerpo = ("\\addplot[black, thick] coordinates {%s};\n\\addplot[black!40, thin] coordinates {(0,0) (40,0)};"
                  % " ".join("(%d,%.4f)" % (h_, irf[v][h_]) for h_ in range(H + 1)))
        return ("\\begin{axis}[name=%s, at={%s}, anchor=north west, width=6.2cm, height=2.6cm, scale only axis, %s,\n"
                "    xmin=0, xmax=40, xtick={0,8,...,40}, ymin=%s, ymax=%s, ytick={%s}, %sylabel={\\%%}, title={%s}, title style={font=\\footnotesize}]\n%s\n\\end{axis}\n"
                % (nombre, lugar, ESTILO, ymin, ymax, ytick, "xlabel={Trimestres}, " if xlab else "", titulo, cuerpo))

    fig = "\\begin{tikzpicture}\n"
    fig += panel("a", "{(0,0)}", "(a) Producción", "y", -0.1, 0.4, "0,0.1,0.2,0.3,0.4", False)
    fig += panel("b", "{($(a.north east)+(1.6cm,0)$)}", "(b) Consumo", "c", -0.6, 0.1, "-0.6,-0.4,-0.2,0", False)
    fig += panel("c", "{($(a.south west)+(0,-1.4cm)$)}", "(c) Horas", "h", -0.1, 0.6, "0,0.2,0.4,0.6", True)
    fig += panel("d", "{($(c.north east)+(1.6cm,0)$)}", "(d) Salario real", "w", -0.3, 0.1, "-0.3,-0.2,-0.1,0,0.1", True)
    fig += "\\end{tikzpicture}"
    escribir("anx_rbc_gasto", fig, "Modelo del ciclo real: respuestas a un aumento del gasto público del 1 % del PIB (G/Y 0,2; rho_g 0,93), trabajo divisible.")

    # ---- coste de bienestar de LUCAS con el consumo real por habitante anual
    pce, pob = a_dict(leer(carpeta, "PCECC96")), a_dict(leer(carpeta, "B230RC0A052NBEA"))
    anual = {}
    for f, v in pce.items():
        anual.setdefault(int(f[:4]), []).append(v)
    anual = {a: sum(v) / len(v) for a, v in anual.items() if len(v) == 4}
    for a0, a1 in ((1947, 2001), (1950, 2019)):
        anos = [a for a in range(a0, a1 + 1) if a in anual and "%d-01-01" % a in pob]
        c = np.array([math.log(anual[a] / pob["%d-01-01" % a]) for a in anos])
        t = np.arange(len(c))
        s_lin = float((c - np.polyval(np.polyfit(t, c, 1), t)).std())
        s_hp = float(hp(c, 400.0)[0].std())
        cifras.append(("Coste de LUCAS %d-%d: sigma del consumo por habitante (tendencia lineal; HP 400)" % (a0, a1), "%.4f; %.4f" % (s_lin, s_hp), "", "II.6"))
        cifras.append(("Coste de LUCAS %d-%d: lambda (%% del consumo) con theta 1, 4 y 10 (lineal | HP 400)" % (a0, a1),
                       "%s | %s" % (", ".join("%.3f" % (50 * th * s_lin ** 2) for th in (1, 4, 10)), ", ".join("%.3f" % (50 * th * s_hp ** 2) for th in (1, 4, 10))), "%", "II.6"))


# ---------------------------------------------------------------- A8 (II.7-II.10): modelo neokeynesiano de tres ecuaciones
# IS dinámica, curva de PHILLIPS de CALVO y regla de TAYLOR, sin capital (Y = Z h); perturbaciones AR(1) resueltas por
# coeficientes indeterminados: con persistencia rho, brecha = (1 - delta rho) L x, inflación = kappa L x para un
# desplazamiento x del tipo natural (x = r^n - rbar) o x = -nu^i para la perturbación monetaria,
# con L = 1 / [(1 - delta rho)(theta (1 - rho) + phi_y) + kappa (phi_pi - rho)]. Unidades: % y puntos trimestrales (x 4 en anual).
NEK = dict(delta=0.99, theta=1.0, eF=2.0, xi=0.75, phi_pi=1.5, phi_y=0.125, rho_i=0.5, rho_z=0.9, M=0.8)


def nek_kappa(xi, p=NEK):
    return (1 - xi) * (1 - p["delta"] * xi) / xi * (p["theta"] + 1 / p["eF"])


def nek_L(rho, xi, p=NEK):
    k = nek_kappa(xi, p)
    return k, 1.0 / ((1 - p["delta"] * rho) * (p["theta"] * (1 - rho) + p["phi_y"]) + k * (p["phi_pi"] - rho))


def nek_monetaria(xi, H, tam=0.25, p=NEK):
    rho = p["rho_i"]
    k, L = nek_L(rho, xi, p)
    nu = tam * rho ** np.arange(H + 1)
    yt = -(1 - p["delta"] * rho) * L * nu
    pi = -k * L * nu
    i = p["phi_pi"] * pi + p["phi_y"] * yt + nu
    r = i - rho * pi                     # E_t pi_{t+1} = rho pi_t
    return dict(brecha=yt, inflacion=4 * pi, nominal=4 * i, real=4 * r)


def nek_tecnologia(H, tam=1.0, p=NEK):
    rho = p["rho_z"]
    k, L = nek_L(rho, p["xi"], p)
    z = tam * rho ** np.arange(H + 1)
    psi = (1 + 1 / p["eF"]) / (p["theta"] + 1 / p["eF"])   # producción natural = psi z (1 con utilidad logarítmica)
    yn = psi * z
    rn = p["theta"] * psi * (rho - 1) * z                   # tipo natural menos rbar: theta E_t(y^n_{t+1} - y^n_t)
    yt = (1 - p["delta"] * rho) * L * rn
    pi = k * L * rn
    y = yn + yt
    i = p["phi_pi"] * pi + p["phi_y"] * yt
    r = i - rho * pi
    return dict(y=y, yn=yn, h=y - z, hn=yn - z, brecha=yt, inflacion=4 * pi, real=4 * r, natural=4 * rn)


def nek_orientacion(K, M, tam=0.25, p=NEK):
    # efecto hoy de bajar el tipo real tam puntos (trimestrales) solo en el trimestre k, anunciado hoy; M descuenta las
    # expectativas en la IS y en la curva de PHILLIPS (M = 1: modelo básico)
    kap = nek_kappa(p["xi"], p)
    brecha, infl = [], []
    for k in range(K + 1):
        ys = [tam / p["theta"] * M ** (k - j) for j in range(k + 1)]   # brecha en t + j
        brecha.append(ys[0])
        infl.append(4 * sum((p["delta"] * M) ** j * kap * ys[j] for j in range(k + 1)))
    return np.array(brecha), np.array(infl)


def con_datos_a8(cifras, sim):
    def eje(nombre, lugar, titulo, series, ylab, ymin, ymax, ytick, xmax, xtick, xlab="", leyenda=None):
        cuerpo = []
        for estilo, ys, et in series:
            cuerpo.append("\\addplot[%s] coordinates {%s};" % (estilo, " ".join("(%d,%.4f)" % (h_, v) for h_, v in enumerate(ys))))
            if et:
                cuerpo.append("\\addlegendentry{%s}" % et)
        cuerpo.append("\\addplot[black!40, thin, forget plot] coordinates {(0,0) (%d,0)};" % xmax)
        ley = ("legend style={draw=none, fill=none, font=\\footnotesize, at={%s}, anchor=%s}, legend cell align=left, " % leyenda) if leyenda else ""
        return ("\\begin{axis}[name=%s, at={%s}, anchor=north west, width=6.2cm, height=2.6cm, scale only axis, %s,\n"
                "    yticklabel style={/pgf/number format/fixed, /pgf/number format/precision=2},\n"
                "    xmin=0, xmax=%d, xtick={%s}, ymin=%s, ymax=%s, ytick={%s}, %sylabel={%s},\n"
                "    %stitle={%s}, title style={font=\\footnotesize}]\n%s\n\\end{axis}\n"
                % (nombre, lugar, ESTILO, xmax, xtick, ymin, ymax, ytick, ("xlabel={%s}, " % xlab) if xlab else "", ylab, ley, titulo, "\n".join(cuerpo)))

    abajo_a = "{($(a.south west)+(0,-1.4cm)$)}"
    # ---- perturbación monetaria contractiva: 25 puntos básicos trimestrales (1 punto anual), persistencia 0,5
    H = 12
    m75, m50 = nek_monetaria(0.75, H), nek_monetaria(0.5, H)
    for et, m in (("xi 0,75", m75), ("xi 0,5", m50)):
        cifras.append(("Modelo neokeynesiano, perturbación monetaria de 1 punto anual (rho 0,5), %s: impacto en brecha, inflación, tipo nominal y tipo real" % et,
                       "%.3f; %.2f; %.2f; %.2f" % (m["brecha"][0], m["inflacion"][0], m["nominal"][0], m["real"][0]), "% y puntos anuales", "II.7"))
    cifras.append(("Modelo neokeynesiano: kappa con xi 0,75 y 0,5", "%.4f; %.4f" % (nek_kappa(0.75), nek_kappa(0.5)), "", "II.7"))
    fig = "\\begin{tikzpicture}\n"
    s = lambda v: [("black, thick", m75[v], None), ("black!60, dashed, thick", m50[v], None)]
    s_ley = [("black, thick", m75["brecha"], "precios que duran un año de media"), ("black!60, dashed, thick", m50["brecha"], "precios que duran medio año")]
    fig += eje("a", "{(0,0)}", "(a) Brecha de producción", s_ley, "\\%", -0.35, 0.05, "-0.3,-0.2,-0.1,0", H, "0,2,...,12", leyenda=("(0.98,0.03)", "south east"))
    fig += eje("b", "{($(a.north east)+(1.6cm,0)$)}", "(b) Inflación anual", s("inflacion"), "Puntos", -0.8, 0.1, "-0.8,-0.6,-0.4,-0.2,0", H, "0,2,...,12")
    fig += eje("c", abajo_a, "(c) Tipo de interés nominal anual", s("nominal"), "Puntos", -0.2, 0.5, "-0.2,0,0.2,0.4", H, "0,2,...,12", "Trimestres")
    fig += eje("d", "{($(c.north east)+(1.6cm,0)$)}", "(d) Tipo de interés real anual", s("real"), "Puntos", -0.05, 0.6, "0,0.2,0.4,0.6", H, "0,2,...,12", "Trimestres")
    fig += "\\end{tikzpicture}"
    escribir("anx_nek_monetaria", fig, "Modelo neokeynesiano de tres ecuaciones: respuestas a una perturbación monetaria contractiva de 1 punto anual (rho 0,5) con xi 0,75 y 0,5.")

    # ---- mejora tecnológica del 1 % con persistencia 0,9
    H = 16
    t = nek_tecnologia(H)
    cifras.append(("Modelo neokeynesiano, mejora tecnológica del 1 % (rho 0,9): impacto en producción, natural, brecha, horas, inflación, tipo real y natural",
                   "%.3f; %.3f; %.3f; %.3f; %.2f; %.2f; %.2f" % (t["y"][0], t["yn"][0], t["brecha"][0], t["h"][0], t["inflacion"][0], t["real"][0], t["natural"][0]),
                   "% y puntos anuales", "II.7"))
    fig = "\\begin{tikzpicture}\n"
    fig += eje("a", "{(0,0)}", "(a) Producción", [("black, thick", t["y"], "con precios rígidos"), ("black!60, dashed, thick", t["yn"], "natural (precios flexibles)")],
               "\\%", 0, 1.1, "0,0.25,0.5,0.75,1", H, "0,4,...,16", leyenda=("(0.98,0.97)", "north east"))
    fig += eje("b", "{($(a.north east)+(1.6cm,0)$)}", "(b) Horas", [("black, thick", t["h"], None), ("black!60, dashed, thick", t["hn"], None)],
               "\\%", -0.12, 0.02, "-0.1,-0.05,0", H, "0,4,...,16")
    fig += eje("c", abajo_a, "(c) Inflación anual", [("black, thick", t["inflacion"], None)], "Puntos", -0.6, 0.05, "-0.6,-0.4,-0.2,0", H, "0,4,...,16", "Trimestres")
    fig += eje("d", "{($(c.north east)+(1.6cm,0)$)}", "(d) Tipos de interés real y natural anuales",
               [("black, thick", t["real"], "real"), ("black!60, dashed, thick", t["natural"], "natural")],
               "Puntos", -0.45, 0.05, "-0.4,-0.3,-0.2,-0.1,0", H, "0,4,...,16", "Trimestres", leyenda=("(0.98,0.03)", "south east"))
    fig += "\\end{tikzpicture}"
    escribir("anx_nek_tecnologia", fig, "Modelo neokeynesiano de tres ecuaciones: respuestas a una mejora tecnológica del 1 % (rho 0,9), regla de TAYLOR con phi_pi 1,5 y phi_y 0,125.")

    # ---- enigma de la orientación futura: recorte de 1 punto anual del tipo real durante un trimestre, anunciado para el trimestre k
    K = 20
    b1, p1 = nek_orientacion(K, 1.0)
    bM, pM = nek_orientacion(K, NEK["M"])
    cifras.append(("Orientación futura (recorte de 1 punto anual del tipo real en el trimestre k): brecha e inflación anual hoy con k = 0, 4, 8 y 20, modelo básico | descuento M 0,8",
                   "; ".join("%.3f/%.2f" % (b1[k], p1[k]) for k in (0, 4, 8, 20)) + " | " + "; ".join("%.3f/%.2f" % (bM[k], pM[k]) for k in (0, 4, 8, 20)),
                   "% y puntos anuales", "II.10"))
    fig = "\\begin{tikzpicture}\n"
    fig += eje("a", "{(0,0)}", "(a) Brecha de producción hoy", [("black, thick", b1, "modelo básico"), ("black!60, dashed, thick", bM, "expectativas descontadas ($M=0{,}8$)")],
               "\\%", 0, 0.4, "0,0.1,0.2,0.3,0.4", K, "0,4,...,20", "Trimestre del recorte anunciado", leyenda=("(0.98,0.97)", "north east"))
    fig += eje("b", "{($(a.north east)+(1.6cm,0)$)}", "(b) Inflación anual hoy", [("black, thick", p1, None), ("black!60, dashed, thick", pM, None)],
               "Puntos", 0, 2.6, "0,0.5,1,1.5,2,2.5", K, "0,4,...,20", "Trimestre del recorte anunciado")
    fig += "\\end{tikzpicture}"
    escribir("anx_orientacion_futura", fig, "Enigma de la orientación futura: efecto hoy de un recorte de 1 punto anual del tipo real durante un trimestre, anunciado para dentro de k trimestres.")
    sim.append(("Simulación", "Modelo neokeynesiano de tres ecuaciones sin capital (delta 0,99; theta 1; elasticidad de FRISCH 2; xi 0,75 y 0,5; phi_pi 1,5; phi_y 0,125): "
                "perturbación monetaria (rho 0,5), mejora tecnológica (rho 0,9) y orientación futura con y sin descuento de las expectativas (M 0,8); soluciones analíticas",
                "anx_nek_monetaria, anx_nek_tecnologia y anx_orientacion_futura"))


# ---------------------------------------------------------------- A9 (III.1-III.4): garantías y apalancamiento
# Modelo básico de KIYOTAKI y MOORE (1997) linealizado: agricultores productivos con la restricción (1 + r) b_t <= q_{t+1} k_t
# y recolectores sin restricción cuya demanda de tierra fija el coste de uso u_t = q_t - q_{t+1}/(1 + r) = u(k_t),
# con elasticidad e de la oferta residual de tierra al coste de uso (u^ = k^/e). Una caída imprevista y transitoria de la
# productividad de los agricultores, D, en t: k^_t + u^_t = -D + ((1 + r)/r) q^_t (la pérdida de valor de la tierra que ya
# tienen reduce su patrimonio); después k^_{t+s} = (e/(1 + e)) k^_{t+s-1}; q^_t = c k^_t con c = r (1 + e)/(e ((1 + e)(1 + r) - e)).
# Resultado: q^_t = -D/e y k^_t = -(1 + 1/(r (1 + e))) D; sin la revalorización de las garantías, k^_t = -(e/(1 + e)) D.
KM = dict(r=0.05, e=2.0, D=1.0)

SERIES_A9 = {"BOGZ1FL664090005Q": "Intermediarios del mercado de valores (security brokers and dealers): activos financieros totales",
             "BOGZ1FL664190005Q": "Intermediarios del mercado de valores (security brokers and dealers): pasivos totales",
             "BOGZ1FL764090005Q": "Instituciones de depósito con licencia de EE. UU.: activos financieros totales",
             "BOGZ1FL764190005Q": "Instituciones de depósito con licencia de EE. UU.: pasivos totales"}


def descargar_a9(carpeta):
    import time
    for s in SERIES_A9:
        destino = os.path.join(carpeta, s + ".csv")
        if not os.path.exists(destino):
            urllib.request.urlretrieve(FRED + s, destino); time.sleep(0.3)


def km_lineal(H, revaloriza=True, p=KM):
    r, e, D = p["r"], p["e"], p["D"]
    c = r * (1 + e) / (e * ((1 + e) * (1 + r) - e))
    k0 = -(1 + 1 / (r * (1 + e))) * D if revaloriza else -(e / (1 + e)) * D
    k = k0 * (e / (1 + e)) ** np.arange(H + 1)
    return dict(k=k, q=c * k)


def con_datos_a9(carpeta, filas_series, cifras, sim):
    # ---- anx_garantias: tierra de los agricultores y precio de la tierra, con y sin la revalorización de las garantías
    H = 10
    con, sin = km_lineal(H, True), km_lineal(H, False)
    cifras.append(("KIYOTAKI-MOORE lineal (r 5 %, elasticidad 2, caída del 1 % de la productividad de los agricultores): tierra y precio en t, con | sin revalorización; persistencia",
                   "%.2f; %.3f | %.2f; %.3f; %.3f" % (con["k"][0], con["q"][0], sin["k"][0], sin["q"][0], KM["e"] / (1 + KM["e"])), "%", "III.3"))
    for et, d in (("con revalorización de las garantías", con), ("sin revalorización", sin)):
        for v, nom in (("k", "tierra de los agricultores"), ("q", "precio de la tierra")):
            for h_ in range(H + 1):
                filas_series.append(("KIYOTAKI-MOORE: %s (%s)" % (nom, et), "Modelo", "año %d" % h_, round(float(d[v][h_]), 4), "%",
                                     "simulación propia", "r 5 %; elasticidad 2; caída del 1 % en el año 0", "anx_garantias"))

    def eje(nombre, lugar, titulo, series, ylab, ymin, ymax, ytick, xlab="", leyenda=None):
        cuerpo = []
        for estilo, ys, et in series:
            cuerpo.append("\\addplot[%s] coordinates {%s};" % (estilo, " ".join("(%d,%.4f)" % (h_, v) for h_, v in enumerate(ys))))
            if et:
                cuerpo.append("\\addlegendentry{%s}" % et)
        cuerpo.append("\\addplot[black!40, thin, forget plot] coordinates {(0,0) (%d,0)};" % H)
        ley = ("legend style={draw=none, fill=none, font=\\footnotesize, at={%s}, anchor=%s}, legend cell align=left, " % leyenda) if leyenda else ""
        return ("\\begin{axis}[name=%s, at={%s}, anchor=north west, width=6.2cm, height=3.2cm, scale only axis, %s,\n"
                "    yticklabel style={/pgf/number format/fixed, /pgf/number format/precision=2},\n"
                "    xmin=0, xmax=%d, xtick={0,2,...,10}, ymin=%s, ymax=%s, ytick={%s}, %sylabel={%s},\n"
                "    %stitle={%s}, title style={font=\\footnotesize}]\n%s\n\\end{axis}\n"
                % (nombre, lugar, ESTILO, H, ymin, ymax, ytick, ("xlabel={%s}, " % xlab) if xlab else "", ylab, ley, titulo, "\n".join(cuerpo)))

    fig = "\\begin{tikzpicture}\n"
    fig += eje("a", "{(0,0)}", "(a) Tierra de los agricultores",
               [("black, thick", con["k"], "con la pérdida de valor de las garantías"), ("black!60, dashed, thick", sin["k"], "sin ella")],
               "\\%", -8.5, 0.5, "-8,-6,-4,-2,0", "Años", leyenda=("(0.98,0.03)", "south east"))
    fig += eje("b", "{($(a.north east)+(1.6cm,0)$)}", "(b) Precio de la tierra",
               [("black, thick", con["q"], None), ("black!60, dashed, thick", sin["q"], None)], "\\%", -0.55, 0.05, "-0.5,-0.4,-0.3,-0.2,-0.1,0", "Años")
    fig += "\\end{tikzpicture}"
    escribir("anx_garantias", fig, "Versión lineal del modelo básico de KIYOTAKI y MOORE (1997): caída transitoria del 1 % de la productividad de los agricultores, r 5 % anual, elasticidad 2.")
    sim.append(("Simulación", "Versión lineal del modelo básico de KIYOTAKI y MOORE (1997), solución analítica (r 5 %; elasticidad de la oferta residual de tierra al coste de uso 2); "
                "con y sin la revalorización de las garantías en el patrimonio de los agricultores", "anx_garantias"))

    # ---- anx_apalancamiento: crecimiento trimestral de los activos y del apalancamiento (activos / (activos - pasivos)), 1963-2026
    paneles, xy = [], {}
    for clave, (a, l, nombre) in (("b", ("BOGZ1FL664090005Q", "BOGZ1FL664190005Q", "intermediarios del mercado de valores")),
                                  ("c", ("BOGZ1FL764090005Q", "BOGZ1FL764190005Q", "instituciones de depósito"))):
        A, L = a_dict(leer(carpeta, a)), a_dict(leer(carpeta, l))
        fs = sorted(f for f in A if f in L and f >= "1963-01-01")
        act = np.array([A[f] for f in fs])
        pat = act - np.array([L[f] for f in fs])
        apal = act / pat
        ga, gl = 100 * np.diff(np.log(act)), 100 * np.diff(np.log(apal))
        pend, cte = np.polyfit(ga, gl, 1)
        xy[clave] = (ga, gl, pend, cte)
        cifras.append(("Apalancamiento de %s (Cuentas Financieras de la Reserva Federal, %s-%s): correlación y pendiente crecimiento activos-apalancamiento; apalancamiento medio, mínimo y máximo"
                       % (nombre, fs[1][:4], fs[-1][:4]), "%.2f; %.2f; %.1f; %.1f; %.1f" % (np.corrcoef(ga, gl)[0, 1], pend, apal.mean(), apal.min(), apal.max()), "", "III.4"))
        for i, f in enumerate(fs[1:]):
            filas_series.append(("Crecimiento trimestral de los activos de %s" % nombre, "Estados Unidos", f, round(float(ga[i]), 3), "% (log)",
                                 "Reserva Federal, Cuentas Financieras (FRED %s)" % a, "100 x diferencia del logaritmo", "anx_apalancamiento"))
            filas_series.append(("Crecimiento trimestral del apalancamiento de %s" % nombre, "Estados Unidos", f, round(float(gl[i]), 3), "% (log)",
                                 "Reserva Federal, Cuentas Financieras (FRED %s y %s)" % (a, l), "apalancamiento = activos / (activos - pasivos); 100 x diferencia del logaritmo",
                                 "anx_apalancamiento"))

    def nube(nombre, lugar, titulo, ga, gl, pend, cte, xmin, xmax, xtick, ymin, ymax, ytick, ylab):
        puntos = " ".join("(%.2f,%.2f)" % (x, y) for x, y in zip(ga, gl))
        return ("\\begin{axis}[name=%s, at={%s}, anchor=north west, width=6.2cm, height=5.2cm, scale only axis, %s,\n"
                "    xmin=%s, xmax=%s, xtick={%s}, ymin=%s, ymax=%s, ytick={%s}, xlabel={Crecimiento de los activos (\\%%)}, ylabel={%s},\n"
                "    title={%s}, title style={font=\\footnotesize}]\n"
                "\\addplot[only marks, mark=*, mark size=0.7pt, black!65] coordinates {%s};\n"
                "\\addplot[black, thick, domain=%s:%s] {%.4f*x+%.4f};\n"
                "\\addplot[black!35, thin] coordinates {(%s,0) (%s,0)};\n\\addplot[black!35, thin] coordinates {(0,%s) (0,%s)};\n\\end{axis}\n"
                % (nombre, lugar, ESTILO, xmin, xmax, xtick, ymin, ymax, ytick, ylab, titulo, puntos, xmin, xmax, pend, cte, xmin, xmax, ymin, ymax))

    fig = "\\begin{tikzpicture}\n"
    fig += nube("b", "{(0,0)}", "(a) Intermediarios del mercado de valores", *xy["b"], -40, 30, "-40,-30,...,30", -40, 30, "-40,-30,...,30",
                "Crecimiento del apalancamiento (\\%)")
    fig += nube("c", "{($(b.north east)+(1.6cm,0)$)}", "(b) Instituciones de depósito", *xy["c"], -4, 10, "-4,-2,...,10", -25, 35, "-20,-10,...,30", "")
    fig += "\\end{tikzpicture}"
    escribir("anx_apalancamiento", fig, "Crecimiento trimestral de los activos y del apalancamiento de los intermediarios del mercado de valores y de las instituciones de depósito de EE. UU., 1963-2026.")


# ---------------------------------------------------------------- A10 (III.5-III.7): crisis predecibles, precio del riesgo, recesiones financieras
# Base de JORDÀ, SCHULARICK y TAYLOR (macrohistory.net, R6: 18 economías avanzadas, 1870-2020), prima de los bonos en exceso de
# GILCHRIST y ZAKRAJŠEK (Reserva Federal, FEDS Notes) e índice nacional de condiciones financieras de la Reserva Federal de Chicago.
JST_URL = "https://www.macrohistory.net/app/download/9834512569/JSTdatasetR6.xlsx"
EBP_URL = "https://www.federalreserve.gov/econres/notes/feds-notes/ebp_csv.csv"
NFCI_URL = "https://www.chicagofed.org/-/media/publications/nfci/nfci-data-series-csv.csv"
GUERRAS = set(range(1914, 1920)) | set(range(1939, 1948))


def descargar_a10(carpeta):
    for nombre, url in (("JSTdatasetR6.xlsx", JST_URL), ("ebp_csv.csv", EBP_URL), ("NFCI_chicago.csv", NFCI_URL)):
        destino = os.path.join(carpeta, nombre)
        if not os.path.exists(destino):
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with open(destino, "wb") as f:
                f.write(urllib.request.urlopen(req, timeout=180).read())


def leer_xlsx_simple(ruta):  # primera hoja de un .xlsx sin openpyxl (zip + XML): cabecera y filas como diccionarios
    import zipfile, re
    import xml.etree.ElementTree as ET
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

    def col(ref):
        n = 0
        for c in re.match(r"[A-Z]+", ref).group(0):
            n = n * 26 + ord(c) - 64
        return n - 1
    z = zipfile.ZipFile(ruta)
    comp = ["".join(t.text or "" for t in si.findall(".//m:t", ns)) for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", ns)]
    filas = []
    for row in ET.fromstring(z.read("xl/worksheets/sheet1.xml")).find("m:sheetData", ns).findall("m:row", ns):
        fila = {}
        for c in row.findall("m:c", ns):
            v = c.find("m:v", ns)
            if v is None:
                continue
            if c.get("t") == "s":
                fila[col(c.get("r"))] = comp[int(v.text)]
            else:
                try:
                    fila[col(c.get("r"))] = float(v.text)
                except ValueError:
                    fila[col(c.get("r"))] = v.text
        filas.append(fila)
    cab = [filas[0].get(i) for i in range(max(filas[0]) + 1)]
    return cab, [{cab[i]: f.get(i) for i in range(len(cab))} for f in filas[1:]]


def cuantil_lineal(y, M, tau):  # regresión por cuantiles como programa lineal
    from scipy.optimize import linprog
    n, k = M.shape
    c = np.r_[np.zeros(k), tau * np.ones(n), (1 - tau) * np.ones(n)]
    A = np.hstack([M, np.eye(n), -np.eye(n)])
    return linprog(c, A_eq=A, b_eq=y, bounds=[(None, None)] * k + [(0, None)] * (2 * n), method="highs").x[:k]


def con_datos_a10(carpeta, filas_series, cifras, sim):
    _, jst = leer_xlsx_simple(os.path.join(carpeta, "JSTdatasetR6.xlsx"))
    por = {}
    for d in jst:
        por.setdefault(d["country"], {})[int(d["year"])] = d

    def val(p, a, v):
        x = por[p].get(a, {}).get(v)
        return x if isinstance(x, float) else None

    # ---- anx_crisis_prediccion: probabilidad de una crisis bancaria en los tres años siguientes según el auge previo (1950-2016)
    resultados = {}
    for ini in (1870, 1950):
        obs = []
        for p in por:
            for a in range(ini, 2017):
                if any(x in GUERRAS for x in range(a - 3, a + 4)):
                    continue
                v = [val(p, a, "tloans"), val(p, a - 3, "tloans"), val(p, a, "gdp"), val(p, a - 3, "gdp"),
                     val(p, a, "hpnom"), val(p, a - 3, "hpnom"), val(p, a, "cpi"), val(p, a - 3, "cpi")]
                futuro = [val(p, a + k, "crisisJST") for k in (1, 2, 3)]
                if None in v or None in futuro or any(val(p, a - k, "crisisJST") == 1.0 for k in (0, 1, 2)):
                    continue
                dc = 100 * (v[0] / v[2] - v[1] / v[3])
                dh = 100 * (math.log(v[4] / v[6]) - math.log(v[5] / v[7]))
                obs.append((dc, dh, 1.0 if 1.0 in futuro else 0.0))
        F = np.array(obs)
        uc, uh = np.percentile(F[:, 0], 80), np.percentile(F[:, 1], 80)
        ac, ah = F[:, 0] >= uc, F[:, 1] >= uh
        grupos = [("sin auge", ~ac & ~ah), ("solo crédito", ac & ~ah), ("solo vivienda", ~ac & ah), ("crédito y vivienda", ac & ah)]
        resultados[ini] = {"todas": 100 * F[:, 2].mean(), "n": len(F), "uc": uc, "uh": uh}
        for nombre, m in grupos:
            resultados[ini][nombre] = (100 * F[m, 2].mean(), int(m.sum()), int(F[m, 2].sum()))
        cifras.append(("JST %d-2016: probabilidad de crisis en 3 años (todas; sin auge; solo crédito; solo vivienda; los dos) y n; umbrales del quinto superior" % ini,
                       "%.1f; " % resultados[ini]["todas"] + "; ".join("%.1f (n %d, %d)" % resultados[ini][g] for g, _ in grupos)
                       + "; n total %d; umbrales %.1f pp y %.1f %%" % (len(F), uc, uh), "%", "III.5"))
        for g, _ in grupos:
            filas_series.append(("Probabilidad de crisis bancaria en los tres años siguientes (%s)" % g, "18 economías avanzadas", "%d-2016" % ini,
                                 round(resultados[ini][g][0], 2), "%", "JORDÀ, SCHULARICK y TAYLOR, base R6",
                                 "auge = quinto superior del aumento en 3 años del crédito/PIB o del precio real de la vivienda", "anx_crisis_prediccion"))
    r = resultados[1950]
    barras = [("sin auge", 1), ("solo crédito", 2), ("solo vivienda", 3), ("crédito y vivienda", 4)]
    fig = ("\\begin{tikzpicture}\n\\begin{axis}[width=11cm, height=4.6cm, scale only axis, %s,\n"
           "    ybar, bar width=1.5cm, xmin=0.4, xmax=4.6, xtick={1,2,3,4}, ymin=0, ymax=45, ytick={0,10,...,40},\n"
           "    xticklabels={{Sin auge}, {Auge del crédito}, {Auge del precio\\\\ de la vivienda}, {Auge de los dos}},\n"
           "    xticklabel style={align=center, text width=2.6cm}, ylabel={Probabilidad de crisis (\\%%)},\n"
           "    nodes near coords, nodes near coords style={font=\\footnotesize, /pgf/number format/fixed, /pgf/number format/fixed zerofill, /pgf/number format/precision=1, /pgf/number format/use comma}]\n"
           "\\addplot[fill=black!30, draw=black] coordinates {%s};\n"
           "\\begin{pgfonlayer}{axis background}\\draw[dashed, black!70] (axis cs:0.4,%.2f) -- (axis cs:4.6,%.2f);\\end{pgfonlayer}\n"
           "\\node[font=\\footnotesize, anchor=north west, align=left] at (rel axis cs:0.01,0.98) {Línea discontinua: todas las observaciones ($%s$\\,\\%%)};\n\\end{axis}\n\\end{tikzpicture}"
           % (ESTILO, " ".join("(%d,%.1f)" % (x, r[g][0]) for g, x in barras), r["todas"], r["todas"], ("%.1f" % r["todas"]).replace(".", "{,}")))
    escribir("anx_crisis_prediccion", fig, "Probabilidad de una crisis bancaria en los tres años siguientes según el auge previo del crédito y del precio de la vivienda, JST 1950-2016.")

    # ---- anx_recesiones_financieras: PIB real por habitante tras los picos de las recesiones normales y financieras
    picos = []
    for p in por:
        for a in sorted(por[p]):
            y0, ym, yp = val(p, a, "rgdpbarro"), val(p, a - 1, "rgdpbarro"), val(p, a + 1, "rgdpbarro")
            if None in (y0, ym, yp) or not (y0 > ym and yp < y0) or any((a + h) in GUERRAS for h in range(6)) or a > 2015:
                continue
            camino = [val(p, a + h, "rgdpbarro") for h in range(6)]
            if None in camino:
                continue
            picos.append((p, a, any(val(p, a + k, "crisisJST") == 1.0 for k in (-2, -1, 0, 1, 2)), [100 * math.log(c / y0) for c in camino]))
    medias = {}
    for desde in (1870, 1950):
        for tipo in (False, True):
            sel = np.array([c for (_, a, f, c) in picos if f == tipo and a >= desde])
            medias[(desde, tipo)] = (sel.mean(0), len(sel))
            et = "financieras" if tipo else "normales"
            cifras.append(("JST: PIB real por habitante tras el pico de las recesiones %s desde %d (años 0-5, %% respecto al pico) y número" % (et, desde),
                           "; ".join("%.2f" % x for x in sel.mean(0)) + "; n %d" % len(sel), "%", "III.7"))
            for h in range(6):
                filas_series.append(("PIB real por habitante tras el pico de las recesiones %s (desde %d)" % (et, desde), "18 economías avanzadas",
                                     "año %d" % h, round(float(sel.mean(0)[h]), 3), "% respecto al pico", "JORDÀ, SCHULARICK y TAYLOR, base R6 (rgdpbarro, crisisJST)",
                                     "pico = máximo local anual; financiera si empieza una crisis bancaria entre dos años antes y dos después; sin guerras mundiales",
                                     "anx_recesiones_financieras"))

    def tray(nombre, lugar, titulo, desde, ymin, ymax, ytick, ylab, leyenda):
        cuerpo = ["\\addplot[black, thick, mark=*, mark size=1.2pt] coordinates {%s};" % " ".join("(%d,%.3f)" % (h, v) for h, v in enumerate(medias[(desde, False)][0])),
                  "\\addplot[black!60, dashed, thick, mark=square*, mark size=1.2pt] coordinates {%s};" % " ".join("(%d,%.3f)" % (h, v) for h, v in enumerate(medias[(desde, True)][0]))]
        if leyenda:
            cuerpo[0] += "\n\\addlegendentry{recesiones normales}"
            cuerpo[1] += "\n\\addlegendentry{recesiones con crisis financiera}"
        cuerpo.append("\\addplot[black!40, thin, forget plot] coordinates {(0,0) (5,0)};")
        return ("\\begin{axis}[name=%s, at={%s}, anchor=north west, width=6.2cm, height=3.6cm, scale only axis, %s,\n"
                "    yticklabel style={/pgf/number format/fixed}, xmin=0, xmax=5, xtick={0,1,...,5}, ymin=%s, ymax=%s, ytick={%s},\n"
                "    xlabel={Años desde el pico}, ylabel={%s}, title={%s}, title style={font=\\footnotesize},\n"
                "    legend style={draw=none, fill=none, font=\\footnotesize, at={(0.02,0.98)}, anchor=north west}, legend cell align=left]\n%s\n\\end{axis}\n"
                % (nombre, lugar, ESTILO, ymin, ymax, ytick, ylab, titulo, "\n".join(cuerpo)))
    fig = "\\begin{tikzpicture}\n"
    fig += tray("a", "{(0,0)}", "(a) 1870-2015, sin las guerras mundiales", 1870, -4, 6, "-4,-2,...,6", "\\% respecto al pico", True)
    fig += tray("b", "{($(a.north east)+(1.6cm,0)$)}", "(b) 1950-2015", 1950, -4, 9, "-4,-2,...,8", "", False)
    fig += "\\end{tikzpicture}"
    escribir("anx_recesiones_financieras", fig, "PIB real por habitante tras los picos de las recesiones normales y de las que acompañan a una crisis bancaria, JST.")

    # ---- anx_ebp: diferencial de GILCHRIST-ZAKRAJŠEK y prima de los bonos en exceso, mensual, con las recesiones del NBER
    ebp = []
    with open(os.path.join(carpeta, "ebp_csv.csv"), encoding="utf-8") as f:
        for fila in list(csv.reader(f))[1:]:
            ebp.append((fila[0], float(fila[1]), float(fila[2])))
    xe = np.array([decimal(f) for f, _, _ in ebp])
    gz, pe = np.array([g for _, g, _ in ebp]), np.array([e for _, _, e in ebp])
    recm = {decimal(f): v for f, v in leer(carpeta, "USREC")}
    xm = [x for x in sorted(recm) if x >= xe[0] - 1]
    rec_m = tramos(xm, [recm[x] for x in xm], 1 / 12.0)
    i_gz, i_pe = int(np.argmax(gz)), int(np.argmax(pe))
    en_rec = np.array([recm.get(x, 0.0) >= 0.5 for x in xe])
    cifras.append(("GZ y prima en exceso (mensual, %s a %s): máximos y fechas; medias en recesión y en expansión" % (ebp[0][0][:7], ebp[-1][0][:7]),
                   "GZ %.2f (%s); prima %.2f (%s); GZ %.2f / %.2f; prima %.2f / %.2f" % (gz[i_gz], ebp[i_gz][0][:7], pe[i_pe], ebp[i_pe][0][:7],
                                                                              gz[en_rec].mean(), gz[~en_rec].mean(), pe[en_rec].mean(), pe[~en_rec].mean()), "puntos", "III.6"))
    for (f, g, e) in ebp:
        filas_series.append(("Diferencial de crédito de GILCHRIST y ZAKRAJŠEK", "Estados Unidos", f, round(g, 3), "puntos porcentuales",
                             "Reserva Federal, FEDS Notes (ebp_csv.csv)", "nivel", "anx_ebp"))
        filas_series.append(("Prima de los bonos en exceso", "Estados Unidos", f, round(e, 3), "puntos porcentuales",
                             "Reserva Federal, FEDS Notes (ebp_csv.csv)", "nivel", "anx_ebp"))
    ymax = math.ceil(gz.max() + 0.5)
    cuerpo = (sombras([r_ for r_ in rec_m if r_[1] >= xe[0]], 0) + "\n\\addplot[black, thick] coordinates {%s};\n\\addlegendentry{diferencial de crédito}\n"
              "\\addplot[black!60, thin] coordinates {%s};\n\\addlegendentry{prima en exceso}\n\\addplot[black!40, thin, forget plot] coordinates {(1972,0) (2027,0)};"
              % (coords(xe, gz, 2), coords(xe, pe, 2)))
    fig = ("\\begin{tikzpicture}\n\\begin{axis}[width=14.5cm, height=4.8cm, scale only axis, %s,\n"
           "    ymin=-2, ymax=%d, ytick={-2,0,...,%d}, xmin=1972, xmax=2027, xtick={1975,1980,...,2025}, ylabel={Puntos porcentuales},\n"
           "    legend style={draw=none, fill=none, font=\\footnotesize, at={(0.99,0.98)}, anchor=north east}, legend cell align=left]\n%s\n\\end{axis}\n\\end{tikzpicture}"
           % (ESTILO, ymax, ymax, cuerpo))
    escribir("anx_ebp", fig, "Diferencial de crédito de GILCHRIST y ZAKRAJŠEK y prima de los bonos en exceso (Reserva Federal), mensual, con las recesiones del NBER sombreadas.")

    # ---- anx_crecimiento_riesgo: cuantiles del crecimiento del PIB en los cuatro trimestres siguientes frente al NFCI
    nf = {}
    with open(os.path.join(carpeta, "NFCI_chicago.csv"), encoding="utf-8") as f:
        for fila in list(csv.reader(f))[1:]:
            m_, d_, a_ = fila[0].split("/")
            nf.setdefault((int(a_), (int(m_) - 1) // 3), []).append(float(fila[1]))
    nf = {k: sum(v) / len(v) for k, v in nf.items()}
    pib = {}
    for f, v in leer(carpeta, "GDPC1"):
        pib[(int(f[:4]), (int(f[5:7]) - 1) // 3)] = v

    def mas(k, h):
        t = k[0] * 4 + k[1] + h
        return (t // 4, t % 4)
    ks = [k for k in sorted(nf) if k in pib and mas(k, 4) in pib]
    X = np.array([nf[k] for k in ks])
    Y = np.array([100 * math.log(pib[mas(k, 4)] / pib[k]) for k in ks])
    M = np.c_[np.ones(len(X)), X]
    coef = {tau: cuantil_lineal(Y, M, tau) for tau in (0.05, 0.5, 0.95)}
    cifras.append(("Crecimiento en riesgo (NFCI medio del trimestre t frente al crecimiento del PIB real de t a t+4, %dT%d-%dT%d, n %d): constante y pendiente de los cuantiles 5, 50 y 95"
                   % (ks[0][0], ks[0][1] + 1, ks[-1][0], ks[-1][1] + 1, len(ks)),
                   "; ".join("%.2f, %.2f" % tuple(coef[t]) for t in (0.05, 0.5, 0.95)), "puntos", "III.7"))
    for k, x, y in zip(ks, X, Y):
        filas_series.append(("Índice de condiciones financieras (NFCI, media trimestral) y crecimiento del PIB real en los cuatro trimestres siguientes", "Estados Unidos",
                             "%dT%d" % (k[0], k[1] + 1), round(float(x), 3), "índice", "Reserva Federal de Chicago (NFCI) y FRED (GDPC1)",
                             "crecimiento siguiente = %.3f %%" % y, "anx_crecimiento_riesgo"))
    lineas = ""
    for tau, estilo, et in ((0.05, "black, very thick", "cuantil del $5$\\,\\%%"), (0.5, "black!60, thick, dashed", "mediana"), (0.95, "black!60, thick, dotted", "cuantil del $95$\\,\\%%")):
        lineas += "\\addplot[%s, domain=-1.2:5] {%.4f+%.4f*x};\n\\addlegendentry{%s}\n" % (estilo, coef[tau][0], coef[tau][1], et.replace("%%", "%"))
    fig = ("\\begin{tikzpicture}\n\\begin{axis}[width=11cm, height=6cm, scale only axis, %s,\n"
           "    xmin=-1.2, xmax=5, xtick={-1,0,...,5}, ymin=-10, ymax=20, ytick={-10,-5,...,15},\n"
           "    xlabel={Índice de condiciones financieras de la Reserva Federal de Chicago (trimestre $t$)},\n"
           "    ylabel={Crecimiento del PIB de $t$ a $t+4$ (\\%%)},\n"
           "    legend style={draw=none, fill=none, font=\\footnotesize, at={(0.02,0.98)}, anchor=north west}, legend cell align=left]\n"
           "\\addplot[only marks, mark=*, mark size=0.8pt, black!45, forget plot] coordinates {%s};\n%s"
           "\\addplot[black!40, thin, forget plot] coordinates {(-1.2,0) (5,0)};\n\\end{axis}\n\\end{tikzpicture}"
           % (ESTILO, " ".join("(%.3f,%.2f)" % (x, y) for x, y in zip(X, Y)), lineas))
    escribir("anx_crecimiento_riesgo", fig, "Crecimiento en riesgo: regresiones por cuantiles del crecimiento del PIB de EE. UU. en los cuatro trimestres siguientes sobre el NFCI.")
    sim.append(("Cálculo", "JST R6: probabilidad de crisis según el auge previo y recesiones normales y financieras; GILCHRIST-ZAKRAJŠEK; regresiones por cuantiles con el NFCI",
                "anx_crisis_prediccion, anx_recesiones_financieras, anx_ebp y anx_crecimiento_riesgo"))


# ---------------------------------------------------------------- A11 (III.8-III.10): oleadas de crisis bancarias (JST)
def con_datos_a11(carpeta, filas_series, cifras, sim):
    _, jst = leer_xlsx_simple(os.path.join(carpeta, "JSTdatasetR6.xlsx"))
    cuenta = {a: 0 for a in range(1870, 2021)}
    for d in jst:
        if d.get("crisisJST") == 1.0:
            cuenta[int(d["year"])] += 1
    for a in sorted(cuenta):
        filas_series.append(("Número de economías que empiezan una crisis bancaria sistémica", "18 economías avanzadas", str(a), cuenta[a], "economías",
                             "JORDÀ, SCHULARICK y TAYLOR, base R6 (crisisJST)", "suma por año", "anx_olas_crisis"))
    olas = (("1890-1893", 1890, 1893), ("1907-1908", 1907, 1908), ("1920-1922", 1920, 1922), ("1929-1931", 1929, 1931), ("1990-1992", 1990, 1992), ("2007-2008", 2007, 2008))
    cifras.append(("JST: crisis bancarias sistémicas 1870-2020 (total, años con crisis, máximo anual) y por oleadas; crisis entre 1940 y 1969",
                   "%d; %d años; máximo %d (%d); " % (sum(cuenta.values()), sum(1 for v in cuenta.values() if v), max(cuenta.values()), max(cuenta, key=cuenta.get))
                   + "; ".join("%s: %d" % (n, sum(cuenta[a] for a in range(i, f + 1))) for n, i, f in olas)
                   + "; 1940-1969: %d" % sum(cuenta[a] for a in range(1940, 1970)), "crisis", "III.10"))
    marcas = "\n".join("\\node[font=\\footnotesize, anchor=south] at (axis cs:%d,%d) {$%d$};" % (a, cuenta[a] + 0.2, a) for a in (1890, 1907, 1921, 1931, 1991, 2008))
    fig = ("\\begin{tikzpicture}\n\\begin{axis}[width=14.5cm, height=4.6cm, scale only axis, %s,\n"
           "    xmin=1868, xmax=2022, xtick={1870,1890,...,2010}, ymin=0, ymax=13, ytick={0,2,...,12}, ylabel={Economías que entran en crisis}]\n"
           "\\addplot[ycomb, black, line width=1.6pt] coordinates {%s};\n%s\n\\end{axis}\n\\end{tikzpicture}"
           % (ESTILO, " ".join("(%d,%d)" % (a, v) for a, v in sorted(cuenta.items()) if v), marcas))
    escribir("anx_olas_crisis", fig, "Número de las 18 economías de la base JST que empiezan una crisis bancaria sistémica cada año, 1870-2020.")
    sim.append(("Cálculo", "JST R6: número de economías que empiezan una crisis bancaria cada año", "anx_olas_crisis"))


# ---------------------------------------------------------------- A12 (IV.1-IV.2): figuras sintéticas de los ciclos endógenos
def sinteticas_a12(filas_series, cifras, sim):
    # ---- anx_schumpeter: esquema de los tres ciclos (Kitchin 40 meses, Juglar 10 años, Kondratieff 60 años; amplitudes ilustrativas)
    t = np.linspace(0, 60, 1201)
    comp = {"Kitchin": 0.5 * np.sin(2 * math.pi * t / (40 / 12.0)), "Juglar": 1.0 * np.sin(2 * math.pi * t / 10.0), "Kondratieff": 2.0 * np.sin(2 * math.pi * t / 60.0)}
    suma = comp["Kitchin"] + comp["Juglar"] + comp["Kondratieff"]

    def eje(nombre, lugar, titulo, cuerpo, xlab=""):
        return ("\\begin{axis}[name=%s, at={%s}, anchor=north west, width=14.5cm, height=2.6cm, scale only axis, %s,\n"
                "    xmin=0, xmax=60, ymin=-3.8, ymax=3.8, xtick=\\empty, ytick=\\empty, title={%s}, title style={font=\\footnotesize},\n"
                "    xlabel={%s}, xlabel style={at={(1,0)}, anchor=north east},\n"
                "    legend style={draw=none, fill=none, font=\\footnotesize, at={(0.99,0.99)}, anchor=north east}, legend columns=3, legend cell align=left]\n%s\n\\end{axis}\n"
                % (nombre, lugar, ESTILO, titulo, xlab, cuerpo))
    c1 = ("\\addplot[black!45, thin] coordinates {%s};\n\\addlegendentry{Kitchin ($40$ meses)}\n"
          "\\addplot[black!70, thick, dashed] coordinates {%s};\n\\addlegendentry{Juglar ($10$ años)}\n"
          "\\addplot[black, very thick] coordinates {%s};\n\\addlegendentry{Kondratieff ($60$ años)}\n"
          "\\addplot[black!30, thin, forget plot] coordinates {(0,0) (60,0)};"
          % (coords(t[::4], comp["Kitchin"][::4]), coords(t[::4], comp["Juglar"][::4]), coords(t[::4], comp["Kondratieff"][::4])))
    c2 = ("\\addplot[black, thick] coordinates {%s};\n\\addplot[black!30, thin, forget plot] coordinates {(0,0) (60,0)};" % coords(t[::4], suma[::4]))
    fig = "\\begin{tikzpicture}\n" + eje("a", "{(0,0)}", "(a) Los tres ciclos", c1) + eje("b", "{($(a.south west)+(0,-1.2cm)$)}", "(b) Su suma", c2, "Tiempo") + "\\end{tikzpicture}"
    escribir("anx_schumpeter", fig, "Esquema de los tres ciclos de SCHUMPETER (1939): tres Kitchin en un Juglar y seis Juglar en un Kondratieff; amplitudes ilustrativas.")
    sim.append(("Sintética", "Suma de tres sinusoides de 40 meses, 10 años y 60 años con amplitudes 0,5, 1 y 2", "anx_schumpeter"))

    # ---- anx_multiplicador_acelerador: regiones de SAMUELSON (1939) en el plano (v, alfa) y tres trayectorias con alfa = 0,8
    v_ = np.linspace(0.02, 4, 300)
    osc = 4 * v_ / (1 + v_) ** 2
    est = [(v, 1 / v) for v in v_ if 1 / v <= 1.0]
    a = 0.8
    tray = {}
    for v in (0.25, 1.0, 1.5):
        y = [0.0, 0.0]                         # desviaciones respecto al equilibrio inicial; el gasto sube 1 desde t = 1
        for k in range(2, 26):
            y.append(a * (1 + v) * y[-1] - a * v * y[-2] + 1.0)
        tray[v] = y[1:]
    cifras.append(("Multiplicador-acelerador (alfa 0,8): nuevo equilibrio y desviación en t = 5, 10 y 20 con v = 0,25, 1 y 1,5",
                   "equilibrio %.1f; " % (1 / (1 - a)) + "; ".join("v %.2f: %.2f, %.2f, %.2f" % (v, tray[v][5], tray[v][10], tray[v][20]) for v in (0.25, 1.0, 1.5)), "", "IV.2"))
    pa = ("\\addplot[black, thick] coordinates {%s};\n\\addplot[black, thick, dashed] coordinates {%s};\n"
          "\\node[font=\\footnotesize] at (axis cs:0.12,0.93) {A};\n"
          "\\node[font=\\footnotesize] at (axis cs:1.0,0.3) {B};\n"
          "\\node[font=\\footnotesize] at (axis cs:2.3,0.65) {C};\n"
          "\\node[font=\\footnotesize] at (axis cs:3.3,0.9) {D};\n"
          "\\node[font=\\footnotesize, anchor=south west] at (axis cs:3.3,0.31) {$\\alpha v=1$};\n"
          "\\node[font=\\footnotesize, anchor=north east] at (axis cs:3.98,0.62) {$\\alpha(1+v)^2=4v$};\n"
          "\\addplot[only marks, mark=*, mark size=1.6pt] coordinates {(0.25,0.8) (1,0.8) (1.5,0.8)};"
          % (coords(v_, osc), " ".join("(%.4f,%.4f)" % p for p in est)))
    ejes_a = ("\\begin{axis}[name=a, at={(0,0)}, anchor=north west, width=6.2cm, height=4.4cm, scale only axis, %s,\n"
              "    yticklabel style={/pgf/number format/fixed}, xmin=0, xmax=4, xtick={0,1,...,4}, ymin=0, ymax=1.02, ytick={0,0.25,0.5,0.75,1},\n"
              "    xlabel={Acelerador, $v$}, ylabel={Propensión a consumir, $\\alpha$}, title={(a) Regiones}, title style={font=\\footnotesize}]\n%s\n\\end{axis}\n" % (ESTILO, pa))
    pb = []
    for v, estilo, et in ((0.25, "black!45, thick", "$v=0{,}25$"), (1.0, "black, thick", "$v=1$"), (1.5, "black, thick, dashed", "$v=1{,}5$")):
        pb.append("\\addplot[%s, mark=*, mark size=0.9pt] coordinates {%s};\n\\addlegendentry{%s}" % (estilo, " ".join("(%d,%.3f)" % (k, y) for k, y in enumerate(tray[v]) if k <= 20), et))
    pb.append("\\addplot[black!40, thin, dotted, forget plot] coordinates {(0,5) (20,5)};")
    ejes_b = ("\\begin{axis}[name=b, at={($(a.north east)+(1.6cm,0)$)}, anchor=north west, width=6.2cm, height=4.4cm, scale only axis, %s,\n"
              "    xmin=0, xmax=20, xtick={0,5,...,20}, ymin=-16, ymax=22, ytick={-15,-10,...,20},\n"
              "    xlabel={Periodos}, ylabel={Desviación de la renta}, title={(b) Trayectorias con $\\alpha=0{,}8$}, title style={font=\\footnotesize},\n"
              "    legend style={draw=none, fill=none, font=\\footnotesize, at={(0.02,0.02)}, anchor=south west}, legend cell align=left, clip=true]\n%s\n\\end{axis}\n"
              % (ESTILO, "\n".join(pb)))
    clave = ("\\node[font=\\scriptsize, anchor=north] at ([yshift=-4pt]current bounding box.south) {A: convergencia monótona\\quad "
             "B: oscilaciones amortiguadas\\quad C: oscilaciones explosivas\\quad D: crecimiento explosivo};\n")
    escribir("anx_multiplicador_acelerador", "\\begin{tikzpicture}\n" + ejes_a + ejes_b + clave + "\\end{tikzpicture}",
             "Multiplicador-acelerador de SAMUELSON (1939): regiones de la dinámica según la propensión a consumir y el acelerador, y trayectorias tras un aumento permanente del gasto.")
    sim.append(("Sintética", "Y_t = alfa(1+v)Y_(t-1) - alfa v Y_(t-2) + G con alfa 0,8 y v 0,25, 1 y 1,5", "anx_multiplicador_acelerador"))

    # ---- anx_goodwin: ciclo de GOODWIN (1967) con parámetros ilustrativos (participación de los salarios u, tasa de empleo e)
    gq, n, sig, gam, rho = 0.02, 0.01, 10.0, 0.43, 0.5   # productividad, población activa, capital/producto, curva de PHILLIPS lineal

    def deriv(x):
        u, e = x
        return np.array([u * (-gam - gq + rho * e), e * ((1 - u) / sig - (gq + n))])
    x, dt, caminos = np.array([0.70, 0.84]), 0.05, []
    for k in range(int(80 / dt) + 1):
        caminos.append((k * dt, x[0], x[1]))
        k1 = deriv(x); k2 = deriv(x + dt / 2 * k1); k3 = deriv(x + dt / 2 * k2); k4 = deriv(x + dt * k3)
        x = x + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    C = np.array(caminos)
    u_eq, e_eq = 1 - sig * (gq + n), (gam + gq) / rho
    cifras.append(("Ciclo de GOODWIN (parámetros ilustrativos): equilibrio de la participación salarial y del empleo; rangos de la órbita",
                   "u* %.2f, e* %.2f; u entre %.3f y %.3f; e entre %.3f y %.3f" % (u_eq, e_eq, C[:, 1].min(), C[:, 1].max(), C[:, 2].min(), C[:, 2].max()), "", "IV.2"))
    sel = C[::4]
    ga = ("\\begin{axis}[name=a, at={(0,0)}, anchor=north west, width=6.2cm, height=4.4cm, scale only axis, %s,\n"
          "    xtick=\\empty, ytick=\\empty, xlabel={Participación de los salarios}, ylabel={Tasa de empleo}, title={(a) Diagrama de fases}, title style={font=\\footnotesize}]\n"
          "\\addplot[black, thick] coordinates {%s};\n\\addplot[only marks, mark=*, mark size=1.4pt] coordinates {(%.4f,%.4f)};\n"
          "%s\n\\end{axis}\n"
          % (ESTILO, " ".join("(%.4f,%.4f)" % (u, e) for _, u, e in sel), u_eq, e_eq,
             "\n".join("\\draw[-{Stealth[length=2.6mm, width=2mm]}, very thick] (axis cs:%.4f,%.4f) -- (axis cs:%.4f,%.4f);"
                       % (sel[i][1], sel[i][2], sel[i + 6][1], sel[i + 6][2]) for i in (4, 92))))
    gb = ("\\begin{axis}[name=b, at={($(a.north east)+(1.6cm,0)$)}, anchor=north west, width=6.2cm, height=4.4cm, scale only axis, %s,\n"
          "    xmin=0, xmax=80, ymin=-0.2, ymax=0.32, xtick=\\empty, ytick=\\empty, xlabel={Tiempo}, title={(b) Las dos variables en el tiempo}, title style={font=\\footnotesize},\n"
          "    legend style={draw=none, fill=none, font=\\footnotesize, at={(0.5,0.98)}, anchor=north}, legend columns=2, legend cell align=left]\n"
          "\\addplot[black, thick] coordinates {%s};\n\\addlegendentry{participación de los salarios}\n"
          "\\addplot[black!55, thick, dashed] coordinates {%s};\n\\addlegendentry{tasa de empleo}\n\\end{axis}\n"
          % (ESTILO, " ".join("(%.2f,%.4f)" % (tt, (u - u_eq) / u_eq) for tt, u, _ in sel), " ".join("(%.2f,%.4f)" % (tt, (e - e_eq) / e_eq) for tt, _, e in sel)))
    escribir("anx_goodwin", "\\begin{tikzpicture}\n" + ga + gb + "\\end{tikzpicture}",
             "Ciclo de GOODWIN (1967) con parámetros ilustrativos: órbita cerrada de la participación de los salarios y la tasa de empleo, y su evolución en el tiempo.")
    sim.append(("Sintética", "Modelo de GOODWIN (1967) de depredador y presa con parámetros ilustrativos, integrado con RUNGE-KUTTA de orden 4", "anx_goodwin"))

    # ---- anx_kaldor: inversión en forma de S y ahorro lineal (KALDOR, 1940); parámetros ilustrativos
    ka, kb, kk, ks, kc, desplaza = 1.067, 3.0, 1.2, 0.4734, 0.2, 0.45

    def inv(y, d=0.0):
        return ka - d + kb / (1 + math.exp(-kk * (y - 5)))

    def aho(y):
        return ks * y + kc

    def raices(d):  # cortes de la inversión y el ahorro en [0, 10] por bisección
        malla = np.linspace(0.01, 10, 2000)
        f = [inv(y, d) - aho(y) for y in malla]
        sal = []
        for i in range(1, len(malla)):
            if f[i - 1] * f[i] < 0:
                lo, hi = malla[i - 1], malla[i]
                for _ in range(60):
                    me = (lo + hi) / 2
                    if (inv(lo, d) - aho(lo)) * (inv(me, d) - aho(me)) <= 0:
                        hi = me
                    else:
                        lo = me
                sal.append((lo + hi) / 2)
        return sal
    e0, e1 = raices(0.0), raices(desplaza)
    assert len(e0) == 3 and len(e1) == 1, (e0, e1)
    cifras.append(("KALDOR (ilustrativo): equilibrios antes y después de desplazar la inversión", "antes %s; después %s" % (
        ", ".join("%.2f" % y for y in e0), ", ".join("%.2f" % y for y in e1)), "renta", "IV.2"))
    f_inv = "%.3f+%.3f/(1+exp(-%.2f*(x-5)))" % (ka, kb, kk)
    f_inv2 = "%.3f+%.3f/(1+exp(-%.2f*(x-5)))" % (ka - desplaza, kb, kk)
    f_aho = "%.4f*x+%.2f" % (ks, kc)
    comun = ("width=5.4cm, height=4.4cm, scale only axis, %s, xmin=0, xmax=10, ymin=0, ymax=5.4, xtick=\\empty, ytick=\\empty,\n"
             "    xlabel={Renta}, ylabel={Inversión y ahorro}, title style={font=\\footnotesize}, clip=false" % ESTILO)
    ka_ = ("\\begin{axis}[name=a, at={(0,0)}, anchor=north west, %s, title={(a) Tres equilibrios}]\n"
           "\\addplot[black, thick, domain=0:10, samples=150] {%s};\n\\addplot[black!55, thick, dashed, domain=0:10, samples=2] {%s};\n"
           "\\node[font=\\footnotesize, anchor=west] at (axis cs:10,%.3f) {inversión};\n\\node[font=\\footnotesize, anchor=west] at (axis cs:10,%.3f) {ahorro};\n"
           % (comun, f_inv, f_aho, inv(10), aho(10)))
    for y, nom, lado in zip(e0, ("bajo", "inestable", "alto"), ("south east", "north west", "south east")):
        ka_ += "\\addplot[only marks, mark=*, mark size=1.5pt] coordinates {(%.3f,%.3f)};\n\\node[font=\\footnotesize, anchor=%s] at (axis cs:%.3f,%.3f) {%s};\n" % (
            y, aho(y), lado, y, aho(y), nom)
    flechas = [(0.3, e0[0] - 0.25), (e0[1] - 0.3, e0[0] + 0.3), (e0[1] + 0.3, e0[2] - 0.3), (9.8, e0[2] + 0.3)]
    ka_ += "".join("\\draw[-{Stealth[length=1.8mm]}, thick] (axis cs:%.3f,0.25) -- (axis cs:%.3f,0.25);\n" % (x0, x1) for x0, x1 in flechas)
    ka_ += "\\end{axis}\n"
    kb_ = ("\\begin{axis}[name=b, at={($(a.north east)+(2.4cm,0)$)}, anchor=north west, %s, title={(b) Tras acumular capital en el auge}]\n"
           "\\addplot[black!35, thick, domain=0:10, samples=150] {%s};\n\\addplot[black, thick, domain=0:10, samples=150] {%s};\n"
           "\\addplot[black!55, thick, dashed, domain=0:10, samples=2] {%s};\n"
           "\\node[font=\\footnotesize, anchor=west] at (axis cs:10,%.3f) {inversión};\n\\node[font=\\footnotesize, anchor=west] at (axis cs:10,%.3f) {ahorro};\n"
           "\\node[font=\\footnotesize, anchor=west, text=black!45] at (axis cs:10,%.3f) {inversión inicial};\n"
           "\\addplot[only marks, mark=o, mark size=1.5pt] coordinates {(%.3f,%.3f)};\n\\addplot[only marks, mark=*, mark size=1.5pt] coordinates {(%.3f,%.3f)};\n"
           "\\draw[-{Stealth[length=2.2mm]}, very thick] (axis cs:%.3f,0.25) -- (axis cs:%.3f,0.25);\n"
           "\\node[font=\\footnotesize, anchor=south] at (axis cs:%.3f,0.3) {caída de la renta};\n\\end{axis}\n"
           % (comun, f_inv, f_inv2, f_aho, inv(10, desplaza), aho(10), inv(10), e0[2], aho(e0[2]), e1[0], aho(e1[0]), e0[2], e1[0] + 0.15, (e0[2] + e1[0]) / 2))
    escribir("anx_kaldor", "\\begin{tikzpicture}\n" + ka_ + kb_ + "\\end{tikzpicture}",
             "Modelo de KALDOR (1940) con parámetros ilustrativos: inversión en forma de S y ahorro lineal; tres equilibrios y salto al equilibrio bajo cuando la acumulación de capital desplaza la inversión.")
    sim.append(("Sintética", "KALDOR (1940): inversión logística y ahorro lineal con parámetros ilustrativos; la inversión baja 0,45 al acumular capital", "anx_kaldor"))


# ---------------------------------------------------------------- A13 (IV.3-IV.5): caos, modelo de KEEN y cifras con datos
def sinteticas_a13(filas_series, cifras, sim):
    from scipy.integrate import solve_ivp
    # ---- anx_caos: ecuación logística de MAY (1976), x_(t+1) = theta x_t (1 - x_t)
    def tray(th, x0, n):
        xs = [x0]
        for _ in range(n):
            xs.append(th * xs[-1] * (1 - xs[-1]))
        return xs
    a1, a2 = tray(4.0, 0.3, 40), tray(4.0, 0.3001, 40)
    sep = next(t for t in range(41) if abs(a1[t] - a2[t]) > 0.1)
    cifras.append(("Ecuación logística con parámetro 4: primer periodo en que dos trayectorias que empiezan en 0,3 y 0,3001 difieren en más de 0,1",
                   "%d" % sep, "periodos", "IV.3"))
    puntos = set()
    for th in np.linspace(2.8, 4.0, 301):
        x = 0.5
        for _ in range(600):
            x = th * x * (1 - x)
        for _ in range(60):
            x = th * x * (1 - x)
            puntos.add((round(th, 3), round(x, 3)))
    pa = ("\\addplot[black, thick, mark=*, mark size=0.9pt] coordinates {%s};\n\\addlegendentry{$x_0=0{,}3$}\n"
          "\\addplot[black!50, thick, dashed, mark=o, mark size=0.9pt] coordinates {%s};\n\\addlegendentry{$x_0=0{,}3001$}"
          % (" ".join("(%d,%.4f)" % (t, v) for t, v in enumerate(a1)), " ".join("(%d,%.4f)" % (t, v) for t, v in enumerate(a2))))
    ca = ("\\begin{axis}[name=a, at={(0,0)}, anchor=north west, width=6.2cm, height=4.4cm, scale only axis, %s,\n"
          "    xmin=0, xmax=40, xtick={0,10,...,40}, ymin=0, ymax=1.25, ytick={0,0.5,1}, yticklabels={$0$,$0{,}5$,$1$},\n"
          "    xlabel={Periodos}, ylabel={$x_t$}, title={(a) Dos trayectorias con $\\vartheta=4$}, title style={font=\\footnotesize},\n"
          "    legend style={draw=none, fill=none, font=\\footnotesize, at={(0.5,0.99)}, anchor=north}, legend columns=2, legend cell align=left]\n%s\n\\end{axis}\n"
          % (ESTILO, pa))
    cb = ("\\begin{axis}[name=b, at={($(a.north east)+(1.6cm,0)$)}, anchor=north west, width=6.2cm, height=4.4cm, scale only axis, %s,\n"
          "    xmin=2.8, xmax=4, xtick={2.8,3,3.5699,4}, xticklabels={$2{,}8$,$3$,$3{,}57$,$4$}, ymin=0, ymax=1, ytick={0,0.5,1}, yticklabels={$0$,$0{,}5$,$1$},\n"
          "    xlabel={$\\vartheta$}, ylabel={Valores de $x_t$ a largo plazo}, title={(b) Diagrama de bifurcación}, title style={font=\\footnotesize}]\n"
          "\\addplot[only marks, mark=*, mark size=0.12pt, black] coordinates {%s};\n"
          "\\draw[black!40, dotted] (axis cs:3,0) -- (axis cs:3,1);\n\\draw[black!40, dotted] (axis cs:3.5699,0) -- (axis cs:3.5699,1);\n\\end{axis}\n"
          % (ESTILO, " ".join("(%.3f,%.3f)" % p for p in sorted(puntos))))
    escribir("anx_caos", "\\begin{tikzpicture}\n" + ca + cb + "\\end{tikzpicture}",
             "Ecuación logística de MAY (1976): sensibilidad a las condiciones iniciales con parámetro 4 y diagrama de bifurcación entre 2,8 y 4.")
    sim.append(("Sintética", "Ecuación logística x_(t+1) = theta x_t (1 - x_t): trayectorias con theta 4 desde 0,3 y 0,3001; bifurcación con 301 valores de theta entre 2,8 y 4 (600 iteraciones previas y 60 registradas)", "anx_caos"))

    # ---- anx_keen: modelo de KEEN (1995), GOODWIN con deuda, con parámetros ilustrativos
    al, be, de, nu, r = 0.025, 0.02, 0.01, 3.0, 0.03      # productividad, población activa, depreciación, capital/producto, tipo de interés
    f0, f1 = 0.04 / (1 - 0.04 ** 2), 0.04 ** 3 / (1 - 0.04 ** 2)   # curva de PHILLIPS: f1/(1 - empleo)^2 - f0
    k0, k1, k2 = -0.0065, math.exp(-5), 20.0              # inversión sobre la producción: k0 + k1 exp(k2 beneficio)

    def keen(t, x):
        w, l, d = x
        p = 1 - w - r * d
        k = k0 + k1 * math.exp(min(k2 * p, 50))
        return [w * (f1 / (1 - l) ** 2 - f0 - al), l * (k / nu - al - be - de), k - p - d * (k / nu - de)]

    def tope(t, x):
        return x[2] - 1000
    tope.terminal = True
    p1 = math.log((nu * (al + be + de) - k0) / k1) / k2
    l1 = 1 - math.sqrt(f1 / (al + f0))
    d1 = (k0 + k1 * math.exp(k2 * p1) - p1) / (al + be)
    casos = {}
    for d0 in (0.5, 2.0):
        s = solve_ivp(keen, (0, 180), [0.75, 0.75, d0], method="LSODA", rtol=1e-10, atol=1e-12, max_step=0.05, events=tope, dense_output=True)
        tt = np.arange(0, s.t[-1], 0.25)
        casos[d0] = (tt, s.sol(tt), s.t[-1])
    t_alta, Y_alta, fin_alta = casos[2.0]
    picos = sum(1 for i in range(1, len(t_alta) - 1) if Y_alta[1][i] > Y_alta[1][i - 1] and Y_alta[1][i] >= Y_alta[1][i + 1])
    t_baja, Y_baja, fin_baja = casos[0.5]
    cifras.append(("Modelo de KEEN (ilustrativo): equilibrio bueno (participación salarial, empleo, deuda/producción); deuda inicial 0,5: estado en el año 180; deuda inicial 2: año en que la deuda llega a 1.000 veces la producción y ciclos del empleo antes",
                   "equilibrio %.3f, %.3f, %.3f; baja: %.3f, %.3f, %.3f; alta: año %.1f, %d máximos del empleo" % (1 - p1 - r * d1, l1, d1, Y_baja[0][-1], Y_baja[1][-1], Y_baja[2][-1], fin_alta, picos), "", "IV.4"))
    paso = 2
    ka = ("\\begin{axis}[name=a, at={(0,0)}, anchor=north west, width=6.2cm, height=4.4cm, scale only axis, %s,\n"
          "    xmin=0, xmax=180, xtick={0,30,...,180}, ymin=0, ymax=1.2, ytick={0,0.5,1}, yticklabels={$0$,$0{,}5$,$1$},\n"
          "    xlabel={Años}, ylabel={Tasa de empleo}, title={(a) Empleo}, title style={font=\\footnotesize},\n"
          "    legend style={draw=none, fill=none, font=\\footnotesize, at={(0.5,0.99)}, anchor=north}, legend columns=2, legend cell align=left]\n"
          "\\addplot[black, thick] coordinates {%s};\n\\addlegendentry{deuda inicial baja}\n"
          "\\addplot[black!55, thick, dashed] coordinates {%s};\n\\addlegendentry{deuda inicial alta}\n\\end{axis}\n"
          % (ESTILO, " ".join("(%.2f,%.4f)" % (t, v) for t, v in zip(t_baja[::paso], Y_baja[1][::paso])),
             " ".join("(%.2f,%.4f)" % (t, v) for t, v in zip(t_alta[::paso], Y_alta[1][::paso]))))
    kb = ("\\begin{axis}[name=b, at={($(a.north east)+(1.6cm,0)$)}, anchor=north west, width=6.2cm, height=4.4cm, scale only axis, %s,\n"
          "    ymode=log, xmin=0, xmax=180, xtick={0,30,...,180}, ymin=0.05, ymax=1000, ytick={0.1,1,10,100,1000}, yticklabels={$0{,}1$,$1$,$10$,$100$,$1.000$},\n"
          "    xlabel={Años}, ylabel={Deuda sobre producción (escala logarítmica)}, title={(b) Deuda de las empresas}, title style={font=\\footnotesize}]\n"
          "\\addplot[black, thick] coordinates {%s};\n\\addplot[black!55, thick, dashed] coordinates {%s};\n\\end{axis}\n"
          % (ESTILO, " ".join("(%.2f,%.5f)" % (t, max(v, 1e-3)) for t, v in zip(t_baja[::paso], Y_baja[2][::paso])),
             " ".join("(%.2f,%.5f)" % (t, max(v, 1e-3)) for t, v in zip(t_alta[::paso], Y_alta[2][::paso]))))
    escribir("anx_keen", "\\begin{tikzpicture}\n" + ka + kb + "\\end{tikzpicture}",
             "Modelo de KEEN (1995) con parámetros ilustrativos: tasa de empleo y deuda de las empresas sobre la producción con una deuda inicial de 0,5 y de 2 veces la producción.")
    sim.append(("Sintética", "Modelo de KEEN (1995): participación salarial, empleo y deuda con curva de PHILLIPS f1/(1-l)^2 - f0, inversión -0,0065 + exp(-5) exp(20 beneficio), capital/producto 3, tipo 3 %, productividad 2,5 %, población 2 %, depreciación 1 %; LSODA; deuda inicial 0,5 y 2", "anx_keen"))


# ---------------------------------------------------------------- T14 (cuerpo, B1): figuras abstractas sobre una misma serie base
def cuerpo_b1(sim):
    T = np.arange(0, 121, 0.5)

    def tendencia(t):  # crecimiento de 0,3 por periodo que baja a 0,05 hacia t = 86 (transición suave)
        s = 1 / (1 + np.exp(-(t - 86) / 3.0))
        g = 0.3 * (1 - s) + 0.05 * s
        return np.cumsum(np.r_[0, (g[1:] + g[:-1]) / 2 * np.diff(t)])

    def amplitud(t):  # dos ciclos amplios y, entre ellos, una desaceleración sin caída
        return 6.0 - 5.0 / (1 + np.exp(-(t - 40) / 2.5)) + 4.5 / (1 + np.exp(-(t - 80) / 2.5))

    def ciclo(t):  # oscilación de 40 periodos, asimétrica: cae más deprisa de lo que sube
        th = 2 * math.pi * (t - 6) / 40.0
        return amplitud(t) * np.sin(th - 0.55 * np.sin(th))
    yg, c = tendencia(T), ciclo(T)
    y = yg + c
    dy, dc = np.gradient(y, T), np.gradient(c, T)

    def tramos(ind):
        out, ini = [], None
        for t, v in zip(T, ind):
            if v and ini is None:
                ini = t
            if not v and ini is not None:
                out.append((ini, t))
                ini = None
        return out
    rec, desc = tramos(dy < 0), tramos(dc < 0)

    def fondo(intervalos, color):
        return "\n".join("\\fill[%s] ({rel axis cs:0,0} -| {axis cs:%.2f,0}) rectangle ({rel axis cs:0,1} -| {axis cs:%.2f,0});" % (color, a, b) for a, b in intervalos)

    def xy(xs, ys):
        return " ".join("(%.2f,%.3f)" % (a, b) for a, b in zip(xs, ys))
    # ---- b1_fases: el ciclo clásico sobre el nivel
    iP, iV = int(np.argmin(abs(T - rec[0][0]))), int(np.argmin(abs(T - rec[0][1])))
    xr = (rec[1][0] + rec[1][1]) / 2
    f1 = ("\\begin{tikzpicture}\n\\begin{axis}[width=13cm, height=5.2cm, scale only axis, %s, xmin=0, xmax=120, xtick=\\empty, ytick=\\empty,\n"
          "    xlabel={Tiempo}, ylabel={Logaritmo de la producción}, clip=false]\n"
          "\\begin{pgfonlayer}{axis background}\n%s\n\\end{pgfonlayer}\n"
          "\\addplot[black!45, dashed] coordinates {%s};\n\\addplot[black, thick] coordinates {%s};\n"
          "\\node[font=\\footnotesize, anchor=south] at (axis cs:%.2f,%.3f) {pico};\n\\node[font=\\footnotesize, anchor=north east] at (axis cs:%.2f,%.3f) {valle};\n"
          "\\draw[<->, thick] (axis cs:%.2f,%.3f) -- (axis cs:%.2f,%.3f) node[midway, right=2pt, font=\\footnotesize] {$A$};\n"
          "\\draw[black!50, dotted] (axis cs:%.2f,%.3f) -- (axis cs:%.2f,%.3f);\n"
          "\\draw[<->, thick] (axis cs:%.2f,%.3f) -- (axis cs:%.2f,%.3f) node[midway, below, font=\\footnotesize] {$D$};\n"
          "\\node[font=\\footnotesize] at (axis cs:62,%.3f) {expansión};\n\\node[font=\\footnotesize, anchor=south] at (axis cs:%.2f,%.3f) {recesión};\n"
          "\\node[font=\\footnotesize, anchor=west, text=black!55] at (axis cs:120,%.3f) {tendencia};\n\\end{axis}\n\\end{tikzpicture}"
          % (ESTILO, fondo(rec, "black!12"), xy(T[::2], yg[::2]), xy(T[::2], y[::2]),
             T[iP], y[iP] + 0.6, T[iV] - 0.5, y[iV] - 0.3,
             T[iV] + 4, y[iP], T[iV] + 4, y[iV], T[iP], y[iP], T[iV] + 4, y[iP],
             T[iP], y[iV] - 5.0, T[iV], y[iV] - 5.0,
             float(np.interp(62, T, y)) + 5.0, xr, float(np.interp(xr, T, y)) + 4.0, yg[-1]))
    escribir("b1_fases", f1, "Cuerpo B1: fases del ciclo clásico sobre la serie base (pico, valle, amplitud A, duración D; recesiones sombreadas).")
    # ---- b1_crecimiento: la misma serie como desviación respecto a la tendencia
    f2 = ("\\begin{tikzpicture}\n\\begin{axis}[width=13cm, height=4.6cm, scale only axis, %s, xmin=0, xmax=120, xtick=\\empty, ytick=\\empty,\n"
          "    xlabel={Tiempo}, ylabel={Desviación respecto a la tendencia}, legend style={draw=none, fill=none, font=\\footnotesize, at={(0.5,1.02)}, anchor=south}, legend columns=2]\n"
          "\\begin{pgfonlayer}{axis background}\n%s\n%s\n\\end{pgfonlayer}\n"
          "\\addlegendimage{area legend, fill=black!10, draw=none}\\addlegendentry{fase descendente del ciclo de crecimiento}\n"
          "\\addlegendimage{area legend, fill=black!30, draw=none}\\addlegendentry{recesión clásica}\n"
          "\\addplot[black!40, thin, forget plot] coordinates {(0,0) (120,0)};\n\\addplot[black, thick, forget plot] coordinates {%s};\n"
          "\\end{axis}\n\\end{tikzpicture}" % (ESTILO, fondo(desc, "black!10"), fondo(rec, "black!30"), xy(T[::2], c[::2])))
    escribir("b1_crecimiento", f2, "Cuerpo B1: la serie base como desviación respecto a su tendencia; fases descendentes del ciclo de crecimiento y recesiones clásicas.")
    # ---- b1_tendencias: la tendencia elegida decide el ciclo
    lin = np.polyval(np.polyfit(T, y, 1), T)
    ta = ("\\begin{axis}[name=a, at={(0,0)}, anchor=north west, width=6.2cm, height=4.4cm, scale only axis, %s, xmin=0, xmax=120, xtick=\\empty, ytick=\\empty,\n"
          "    xlabel={Tiempo}, ylabel={Logaritmo de la producción}, title={(a) Dos tendencias}, title style={font=\\footnotesize},\n"
          "    legend style={draw=none, fill=none, font=\\footnotesize, at={(0.02,0.98)}, anchor=north west}, legend cell align=left]\n"
          "\\addplot[black, thick, forget plot] coordinates {%s};\n\\addplot[black!60, dashed, thick] coordinates {%s};\\addlegendentry{tendencia lineal}\n"
          "\\addplot[black!45, very thick] coordinates {%s};\\addlegendentry{tendencia flexible}\n\\end{axis}\n"
          % (ESTILO, xy(T[::2], y[::2]), xy(T[::2], lin[::2]), xy(T[::2], yg[::2])))
    tb = ("\\begin{axis}[name=b, at={($(a.north east)+(1.6cm,0)$)}, anchor=north west, width=6.2cm, height=4.4cm, scale only axis, %s, xmin=0, xmax=120, xtick=\\empty, ytick=\\empty,\n"
          "    xlabel={Tiempo}, ylabel={Ciclo}, title={(b) Dos ciclos}, title style={font=\\footnotesize},\n"
          "    legend style={draw=none, fill=none, font=\\footnotesize, at={(0.5,0.99)}, anchor=north}, legend cell align=left]\n"
          "\\addplot[black!40, thin, forget plot] coordinates {(0,0) (120,0)};\n"
          "\\addplot[black!60, dashed, thick] coordinates {%s};\\addlegendentry{con la tendencia lineal}\n"
          "\\addplot[black!45, very thick] coordinates {%s};\\addlegendentry{con la tendencia flexible}\n\\end{axis}\n"
          % (ESTILO, xy(T[::2], (y - lin)[::2]), xy(T[::2], c[::2])))
    escribir("b1_tendencias", "\\begin{tikzpicture}\n" + ta + tb + "\\end{tikzpicture}",
             "Cuerpo B1: la serie base con una tendencia lineal y otra flexible, y los dos ciclos que resultan.")
    # ---- b1_correlograma (N1, 09/11): función de correlación cruzada con la producción de tres variables tipo, sin datos
    # (sustituye a b1_volatilidad y b1_desfases, series sintéticas que el usuario rechazó por ad hoc)
    kk = np.linspace(-8, 8, 161)

    def campana(centro, altura):
        return altura * np.exp(-(kk - centro) ** 2 / (2 * 2.6 ** 2))
    coin, adel, retr = campana(0, 0.85), campana(-2.5, 0.70), campana(1.5, -0.80)
    fc = ("\\begin{tikzpicture}\n\\begin{axis}[width=11.5cm, height=5.2cm, scale only axis, %s, xmin=-8, xmax=8, ymin=-1.05, ymax=1.05,\n"
          "    xtick={0}, xticklabels={$0$}, ytick={0}, yticklabels={$0$}, clip=false,\n"
          "    xlabel={Adelanto ($k<0$) o retraso ($k>0$) de la variable, en trimestres}, ylabel={Correlación con la producción, $\\rho_k$}]\n"
          "\\addplot[black!40, thin] coordinates {(-8,0) (8,0)};\\addplot[black!40, thin] coordinates {(0,-1.05) (0,1.05)};\n"
          "\\addplot[black, thick] coordinates {%s};\n\\addplot[black!60, thick, dashed] coordinates {%s};\n\\addplot[black!45, very thick] coordinates {%s};\n"
          "\\addplot[only marks, mark=*, mark size=1.5pt] coordinates {(0,0.85) (-2.5,0.70) (1.5,-0.80)};\n"
          "\\draw[black!50, densely dotted] (axis cs:-2.5,0) -- (axis cs:-2.5,0.70);\\draw[black!50, densely dotted] (axis cs:1.5,0) -- (axis cs:1.5,-0.80);\n"
          "\\node[font=\\footnotesize, anchor=south west, align=left] at (axis cs:0.35,0.80) {procíclica y coincidente\\\\(consumo)};\n"
          "\\node[font=\\footnotesize, anchor=south east, align=right] at (axis cs:-2.9,0.66) {procíclica y adelantada\\\\(inversión residencial)};\n"
          "\\node[font=\\footnotesize, anchor=north west, align=left] at (axis cs:1.9,-0.74) {contracíclica y retrasada\\\\(tasa de paro)};\n"
          "\\end{axis}\n\\end{tikzpicture}" % (ESTILO, xy(kk[::2], coin[::2]), xy(kk[::2], adel[::2]), xy(kk[::2], retr[::2])))
    escribir("b1_correlograma", fc, "Cuerpo B1: función de correlación cruzada con la producción de tres variables tipo (procíclica y coincidente, procíclica y adelantada, contracíclica y retrasada), en versión abstracta.")
    sim.append(("Sintética", "Serie base del cuerpo (B1): tendencia con crecimiento 0,3 que baja a 0,05 hacia t = 86 y ciclo asimétrico de 40 periodos con amplitudes 6, 1 y 5,5; recesiones clásicas en %s y fases descendentes del ciclo de crecimiento en %s"
                % (", ".join("%.1f-%.1f" % r for r in rec), ", ".join("%.1f-%.1f" % r for r in desc)), "b1_fases, b1_crecimiento, b1_tendencias"))
    sim.append(("Sintética", "Correlograma abstracto del cuerpo (B1): campanas de anchura 2,6 trimestres; coincidente con 0,85 en k = 0, adelantada con 0,70 en k = -2,5 y contracíclica con -0,80 en k = 1,5",
                "b1_correlograma"))


# ---------------------------------------------------------------- T15 (cuerpo, B2, nueva macroeconomía clásica): figuras abstractas
def cuerpo_b2_nmc(sim):
    def xy(xs, ys):
        return " ".join("(%.2f,%.4f)" % (a, b) for a, b in zip(xs, ys))
    # ---- b2_lucas: oferta de LUCAS y demanda agregada en el plano de la producción y los precios
    psi, yg, Ep0, m0, dm = 1.0, 5.0, 5.0, 10.0, 2.0

    def oa(Ep, y):
        return Ep + (y - yg) / psi

    def da(m, y):
        return m - y
    y1 = (m0 + dm - Ep0 + yg / psi) / (1 + 1 / psi)
    E0, E1, E2 = (yg, Ep0), (y1, da(m0 + dm, y1)), (yg, Ep0 + dm)
    f = ("\\begin{tikzpicture}\n\\begin{axis}[width=10cm, height=6cm, scale only axis, %s, xmin=2.4, xmax=8.6, ymin=2.2, ymax=9.6, xtick={%.2f}, xticklabels={$y^g_t$}, ytick=\\empty,\n"
         "    xlabel={Producción, $y_t$}, ylabel={Nivel de precios, $p_t$}, clip=false]\n"
         "\\addplot[black!40, dashed] coordinates {(%.2f,2.2) (%.2f,9.6)};\n"
         "\\addplot[black, thick, domain=2.4:7.4, samples=2] {%.3f-x};\n\\addplot[black, thick, dashed, domain=2.4:7.4, samples=2] {%.3f-x};\n"
         "\\addplot[black!60, thick, domain=2.4:7.4, samples=2] {%.3f+(x-%.2f)/%.2f};\n\\addplot[black!60, thick, dotted, domain=2.4:5.6, samples=2] {%.3f+(x-%.2f)/%.2f};\n"
         "\\addplot[only marks, mark=*, mark size=1.6pt] coordinates {(%.3f,%.3f) (%.3f,%.3f) (%.3f,%.3f)};\n"
         "\\node[font=\\footnotesize, anchor=north east] at (axis cs:%.3f,%.3f) {$E_0$};\n\\node[font=\\footnotesize, anchor=west] at (axis cs:%.3f,%.3f) {$E_1$};\n\\node[font=\\footnotesize, anchor=east] at (axis cs:%.3f,%.3f) {$E_2$};\n"
         "\\node[font=\\footnotesize, anchor=west] at (axis cs:7.4,%.3f) {$DA_0$};\n\\node[font=\\footnotesize, anchor=west] at (axis cs:7.4,%.3f) {$DA_1$};\n"
         "\\node[font=\\footnotesize, anchor=west] at (axis cs:7.4,%.3f) {$OA_0$};\n\\node[font=\\footnotesize, anchor=west] at (axis cs:5.6,%.3f) {$OA_1$};\n"
         "\\node[font=\\footnotesize, anchor=south, text=black!55] at (axis cs:%.2f,9.6) {tendencia};\n\\end{axis}\n\\end{tikzpicture}"
         % (ESTILO, yg, yg, yg, m0, m0 + dm, Ep0, yg, psi, Ep0 + dm, yg, psi,
            E0[0], E0[1], E1[0], E1[1], E2[0], E2[1], E0[0] - 0.05, E0[1] - 0.05, E1[0] + 0.12, E1[1], E2[0] - 0.12, E2[1],
            da(m0, 7.4), da(m0 + dm, 7.4), oa(Ep0, 7.4), oa(Ep0 + dm, 5.6), yg))
    escribir("b2_lucas", f, "Cuerpo B2: oferta agregada de LUCAS y demanda agregada; relajación monetaria imprevista (E1) y prevista (E2).")
    # ---- b2_clasico (N2, 09/11): el ciclo real en la oferta y la demanda agregadas, misma base que b2_lucas
    # (sustituye a b2_rbc; el usuario pidió una representación más canónica, «una versión adaptada de la forma anterior»)
    y0, y1, mm, dmm = 5.0, 6.4, 10.0, 2.0
    C0, C1, C2 = (y0, mm - y0), (y1, mm - y1), (y0, mm + dmm - y0)
    fl = "-{Stealth[length=2mm]}, black!55, thick"
    f = ("\\begin{tikzpicture}\n\\begin{axis}[width=10cm, height=6cm, scale only axis, %s, xmin=2.4, xmax=8.6, ymin=2.2, ymax=9.6, xtick=\\empty, ytick=\\empty,\n"
         "    xlabel={Producción, $y_t$}, ylabel={Nivel de precios, $p_t$}, clip=false]\n"
         "\\addplot[black!60, thick] coordinates {(%.2f,2.2) (%.2f,9.6)};\n\\addplot[black!60, thick, dotted] coordinates {(%.2f,2.2) (%.2f,9.6)};\n"
         "\\addplot[black, thick, domain=2.4:7.4, samples=2] {%.3f-x};\n\\addplot[black, thick, dashed, domain=2.4:7.4, samples=2] {%.3f-x};\n"
         "\\addplot[only marks, mark=*, mark size=1.6pt] coordinates {(%.3f,%.3f) (%.3f,%.3f) (%.3f,%.3f)};\n"
         "\\draw[%s] (axis cs:%.2f,8.9) -- (axis cs:%.2f,8.9);\n\\draw[%s] (axis cs:7.0,%.2f) -- (axis cs:7.0,%.2f);\n"
         "\\node[font=\\footnotesize, anchor=north east] at (axis cs:%.3f,%.3f) {$E_0$};\n\\node[font=\\footnotesize, anchor=south west] at (axis cs:%.3f,%.3f) {$E_1$};\n\\node[font=\\footnotesize, anchor=east] at (axis cs:%.3f,%.3f) {$E_2$};\n"
         "\\node[font=\\footnotesize, anchor=west] at (axis cs:7.4,%.3f) {$DA_0$};\n\\node[font=\\footnotesize, anchor=west] at (axis cs:7.4,%.3f) {$DA_1$};\n"
         "\\node[font=\\footnotesize, anchor=south] at (axis cs:%.2f,9.6) {$OA_0$};\n\\node[font=\\footnotesize, anchor=south] at (axis cs:%.2f,9.6) {$OA_1$};\n"
         "\\end{axis}\n\\end{tikzpicture}"
         % (ESTILO, y0, y0, y1, y1, mm, mm + dmm, C0[0], C0[1], C1[0], C1[1], C2[0], C2[1],
            fl, y0 + 0.08, y1 - 0.08, fl, mm - 7.0 + 0.12, mm + dmm - 7.0 - 0.12,
            C0[0] - 0.05, C0[1] - 0.05, C1[0] + 0.05, C1[1] + 0.05, C2[0] - 0.12, C2[1],
            mm - 7.4, mm + dmm - 7.4, y0, y1))
    escribir("b2_clasico", f, "Cuerpo B2: el ciclo real en la oferta y la demanda agregadas: la mejora de la productividad desplaza la oferta vertical (E0 a E1: más producción y precios más bajos) y la relajación monetaria solo sube los precios (E0 a E2).")
    # ---- b2_trabajo: la mejora tecnológica desplaza la demanda de trabajo; dos ofertas de distinta elasticidad
    w0, h0, s = 5.0, 5.0, 1.6
    h_el = h0 + s / (0.9 + 0.25)
    w_el = w0 + 0.25 * (h_el - h0)
    h_ri = h0 + s / (0.9 + 3.0)
    w_ri = w0 + 3.0 * (h_ri - h0)
    f = ("\\begin{tikzpicture}\n\\begin{axis}[width=10cm, height=6cm, scale only axis, %s, xmin=2, xmax=9.2, ymin=1.5, ymax=9.8, xtick=\\empty, ytick=\\empty,\n"
         "    xlabel={Horas, $h_t$}, ylabel={Salario real, $w_t$}, clip=false]\n"
         "\\addplot[black, thick, domain=2.2:8.4, samples=2] {%.3f-0.9*(x-%.2f)};\n\\addplot[black, thick, dashed, domain=2.2:8.4, samples=2] {%.3f-0.9*(x-%.2f)};\n"
         "\\addplot[black!60, thick, domain=2.4:8.6, samples=2] {%.3f+0.25*(x-%.2f)};\n\\addplot[black!45, very thick, domain=3.6:6.4, samples=2] {%.3f+3*(x-%.2f)};\n"
         "\\addplot[only marks, mark=*, mark size=1.6pt] coordinates {(%.3f,%.3f) (%.3f,%.3f) (%.3f,%.3f)};\n"
         "\\node[font=\\footnotesize, anchor=north east] at (axis cs:%.3f,%.3f) {$E_0$};\n\\node[font=\\footnotesize, anchor=north west] at (axis cs:%.3f,%.3f) {$E_1$};\n\\node[font=\\footnotesize, anchor=south east] at (axis cs:%.3f,%.3f) {$E_2$};\n"
         "\\node[font=\\footnotesize, anchor=west] at (axis cs:8.4,%.3f) {demanda};\n\\node[font=\\footnotesize, anchor=west] at (axis cs:8.4,%.3f) {demanda tras la mejora};\n"
         "\\node[font=\\footnotesize, anchor=west] at (axis cs:8.6,%.3f) {oferta muy elástica};\n\\node[font=\\footnotesize, anchor=south] at (axis cs:6.4,%.3f) {oferta poco elástica};\n"
         "\\end{axis}\n\\end{tikzpicture}"
         % (ESTILO, w0, h0, w0 + s, h0, w0, h0, w0, h0, h0, w0, h_el, w_el, h_ri, w_ri,
            h0 - 0.05, w0 - 0.05, h_el + 0.05, w_el - 0.05, h_ri - 0.08, w_ri + 0.05,
            w0 - 0.9 * (8.4 - h0), w0 + s - 0.9 * (8.4 - h0), w0 + 0.25 * (8.6 - h0), w0 + 3 * (6.4 - h0)))
    escribir("b2_trabajo", f, "Cuerpo B2: una mejora tecnológica desplaza la demanda de trabajo; con una oferta muy elástica suben sobre todo las horas (E1) y con una poco elástica, el salario (E2).")
    sim.append(("Sintética", "Cuerpo B2 (NMC): oferta de LUCAS con pendiente 1 y demanda y = m - p; oferta clásica vertical que la mejora de la productividad lleva de 5 a 6,4 y demanda con m de 10 a 12; mercado de trabajo con demanda de pendiente -0,9 y ofertas de pendiente 0,25 y 3",
                "b2_lucas, b2_clasico, b2_trabajo"))


# ---------------------------------------------------------------- T16 (cuerpo, B2, nueva economía keynesiana): figuras abstractas
def cuerpo_b2_nek(sim):
    def xy(xs, ys):
        return " ".join("(%.2f,%.4f)" % (a, b) for a, b in zip(xs, ys))
    a, b = 0.6, 1.2          # pendientes de la curva de PHILLIPS y de la demanda agregada en el aspa (ilustrativas)

    # ---- b2_aspa: (a) relajación monetaria, (b) mejora de la productividad (baja el tipo natural)
    def aspa(nombre, lugar, titulo, desp, ylab, etiqueta):
        x1 = desp / (a + b)
        y1 = a * x1
        lo, hi = max(-1.9, (desp - 1.95) / b), min(1.9, (desp + 1.95) / b)
        return ("\\begin{axis}[name=%s, at={%s}, anchor=north west, width=6cm, height=5cm, scale only axis, %s, xmin=-2, xmax=2, ymin=-2, ymax=2, xtick={0}, xticklabels={$0$}, ytick={0}, yticklabels={$0$},\n"
                "    xlabel={Brecha de producción, $\\tilde y_t$}, %s title={%s}, title style={font=\\footnotesize}, clip=false]\n"
                "\\addplot[black!30, thin] coordinates {(-2,0) (2,0)};\\addplot[black!30, thin] coordinates {(0,-2) (0,2)};\n"
                "\\addplot[black!60, thick, domain=-1.9:1.9, samples=2] {%.3f*x};\n"
                "\\addplot[black, thick, domain=-1.3:1.3, samples=2] {-%.3f*x};\n\\addplot[black, thick, dashed, domain=%.3f:%.3f, samples=2] {-%.3f*x%+.3f};\n"
                "\\addplot[only marks, mark=*, mark size=1.6pt] coordinates {(0,0) (%.3f,%.3f)};\n"
                "\\node[font=\\footnotesize, anchor=%s] at (axis cs:-0.03,-0.05) {$E_0$};\n\\node[font=\\footnotesize, anchor=%s] at (axis cs:%.3f,%.3f) {$%s$};\n"
                "\\node[font=\\footnotesize, anchor=west] at (axis cs:1.9,%.3f) {$CP$};\n\\node[font=\\footnotesize, anchor=north] at (axis cs:1.3,%.3f) {$DA_0$};\n\\node[font=\\footnotesize, anchor=%s] at (axis cs:%.3f,%.3f) {$DA_1$};\n"
                "\\end{axis}\n"
                % (nombre, lugar, ESTILO, ylab, titulo, a, b, lo, hi, b, desp,
                   x1, y1, "north east" if desp > 0 else "south west", "south west" if desp > 0 else "north east", x1 + (0.05 if desp > 0 else -0.05), y1, etiqueta,
                   a * 1.9, -b * 1.3, "west" if desp > 0 else "north", hi, -b * hi + desp))
    escribir("b2_aspa", "\\begin{tikzpicture}\n" + aspa("a", "{(0,0)}", "(a) Relajación monetaria", 1.4, "ylabel={Inflación, $\\pi_t$},", "E_1")
             + aspa("b", "{($(a.north east)+(1.8cm,0)$)}", "(b) Mejora de la productividad", -1.4, "", "E_2") + "\\end{tikzpicture}",
             "Cuerpo B2: aspa del modelo neokeynesiano (curva de PHILLIPS y demanda agregada) ante una relajación monetaria y una mejora de la productividad que baja el tipo natural.")
    # ---- b2_nek: respuestas dinámicas (funciones de la A8, calibración NEK)
    H = 16
    t = np.arange(H + 1)
    m = nek_monetaria(NEK["xi"], H, tam=-0.25)
    z = nek_tecnologia(H)
    pa = ("\\begin{axis}[name=a, at={(0,0)}, anchor=north west, width=6.2cm, height=4.2cm, scale only axis, %s, xmin=0, xmax=16, xtick=\\empty, ytick=\\empty, ymin=-0.75, ymax=0.55,\n"
          "    xlabel={Trimestres}, ylabel={Desviación}, title={(a) Relajación monetaria}, title style={font=\\footnotesize},\n"
          "    legend style={draw=none, fill=none, font=\\footnotesize, at={(0.98,0.98)}, anchor=north east}, legend cell align=left]\n"
          "\\addplot[black!40, thin, forget plot] coordinates {(0,0) (16,0)};\n"
          "\\addplot[black, thick] coordinates {%s};\\addlegendentry{brecha}\n\\addplot[black!45, very thick, dashed] coordinates {%s};\\addlegendentry{tipo de interés real}\n\\end{axis}\n"
          % (ESTILO, xy(t, m["brecha"]), xy(t, m["real"])))
    pb = ("\\begin{axis}[name=b, at={($(a.north east)+(1.6cm,0)$)}, anchor=north west, width=6.2cm, height=4.2cm, scale only axis, %s, xmin=0, xmax=16, xtick=\\empty, ytick=\\empty, ymin=-0.35, ymax=1.25,\n"
          "    xlabel={Trimestres}, title={(b) Mejora de la productividad}, title style={font=\\footnotesize},\n"
          "    legend style={draw=none, fill=none, font=\\footnotesize, at={(0.98,0.98)}, anchor=north east}, legend cell align=left]\n"
          "\\addplot[black!40, thin, forget plot] coordinates {(0,0) (16,0)};\n"
          "\\addplot[black!50, thick, dotted] coordinates {%s};\\addlegendentry{producción natural}\n\\addplot[black, thick] coordinates {%s};\\addlegendentry{producción}\n"
          "\\addplot[black!45, very thick] coordinates {%s};\\addlegendentry{horas}\n\\end{axis}\n"
          % (ESTILO, xy(t, z["yn"]), xy(t, z["y"]), xy(t, z["h"])))
    escribir("b2_nek", "\\begin{tikzpicture}\n" + pa + pb + "\\end{tikzpicture}",
             "Cuerpo B2: respuestas del modelo neokeynesiano de tres ecuaciones (calibración de la A8) a una relajación monetaria y a una mejora de la productividad.")
    # ---- b2_costes: perturbación de costes en el aspa
    c = 1.2
    x3, y3 = -c / (a + b), a * (-c / (a + b)) + c
    f = ("\\begin{tikzpicture}\n\\begin{axis}[width=7cm, height=5.4cm, scale only axis, %s, xmin=-2, xmax=2, ymin=-2, ymax=2.6, xtick={0}, xticklabels={$0$}, ytick={0}, yticklabels={$0$},\n"
         "    xlabel={Brecha de producción, $\\tilde y_t$}, ylabel={Inflación, $\\pi_t$}, clip=false]\n"
         "\\addplot[black!30, thin] coordinates {(-2,0) (2,0)};\\addplot[black!30, thin] coordinates {(0,-2) (0,2.6)};\n"
         "\\addplot[black!60, thick, domain=-1.9:1.9, samples=2] {%.3f*x};\n\\addplot[black!60, thick, dashed, domain=-1.9:1.0, samples=2] {%.3f*x%+.3f};\n"
         "\\addplot[black, thick, domain=-1.5:1.5, samples=2] {-%.3f*x};\n"
         "\\addplot[only marks, mark=*, mark size=1.6pt] coordinates {(0,0) (%.3f,%.3f)};\n"
         "\\node[font=\\footnotesize, anchor=north east] at (axis cs:-0.03,-0.05) {$E_0$};\n\\node[font=\\footnotesize, anchor=south east] at (axis cs:%.3f,%.3f) {$E_3$};\n"
         "\\node[font=\\footnotesize, anchor=west] at (axis cs:1.9,%.3f) {$CP_0$};\n\\node[font=\\footnotesize, anchor=west] at (axis cs:1.0,%.3f) {$CP_1$};\n\\node[font=\\footnotesize, anchor=west] at (axis cs:1.5,%.3f) {$DA$};\n"
         "\\end{axis}\n\\end{tikzpicture}" % (ESTILO, a, a, c, b, x3, y3, x3 - 0.05, y3 + 0.05, a * 1.9, a * 1.0 + c, -b * 1.5))
    escribir("b2_costes", f, "Cuerpo B2: una perturbación de costes desplaza la curva de PHILLIPS hacia arriba: más inflación y menos producción.")
    # ---- b2_coincidencia (N3, 09/11): divina coincidencia en el aspa: la mejora baja el tipo natural (DA0 a DA1, E2)
    # y el banco central, al bajar su tipo con el natural, devuelve la demanda a DA0 (E0)
    dd, pf = -1.4, 0.6
    x2, y2 = dd / (a + b), a * dd / (a + b)
    fl = "-{Stealth[length=2.2mm]}, black!55, thick"
    f = ("\\begin{tikzpicture}\n\\begin{axis}[width=7cm, height=5.4cm, scale only axis, %s, xmin=-2, xmax=2, ymin=-2, ymax=2, xtick={0}, xticklabels={$0$}, ytick={0}, yticklabels={$0$},\n"
         "    xlabel={Brecha de producción, $\\tilde y_t$}, ylabel={Inflación, $\\pi_t$}, clip=false]\n"
         "\\addplot[black!30, thin] coordinates {(-2,0) (2,0)};\\addplot[black!30, thin] coordinates {(0,-2) (0,2)};\n"
         "\\addplot[black!60, thick, domain=-1.9:1.9, samples=2] {%.3f*x};\n"
         "\\addplot[black, thick, domain=-1.5:1.5, samples=2] {-%.3f*x};\n\\addplot[black, thick, dashed, domain=-1.9:0.25, samples=2] {-%.3f*x%+.3f};\n"
         "\\addplot[only marks, mark=*, mark size=1.6pt] coordinates {(0,0) (%.3f,%.3f)};\n"
         "\\draw[%s] (axis cs:%.3f,%.2f) -- (axis cs:%.3f,%.2f);\n"
         "\\node[font=\\footnotesize, anchor=south] at (axis cs:0.06,0.14) {$E_0$};\n\\node[font=\\footnotesize, anchor=north east] at (axis cs:%.3f,%.3f) {$E_2$};\n"
         "\\node[font=\\footnotesize, anchor=west] at (axis cs:1.9,%.3f) {$CP$};\n\\node[font=\\footnotesize, anchor=west] at (axis cs:1.5,%.3f) {$DA_0$};\n\\node[font=\\footnotesize, anchor=west] at (axis cs:0.25,%.3f) {$DA_1$};\n"
         "\\end{axis}\n\\end{tikzpicture}"
         % (ESTILO, a, b, b, dd, x2, y2, fl, (dd - pf) / b + 0.07, pf, -pf / b - 0.07, pf, x2 - 0.04, y2 - 0.04, a * 1.9, -b * 1.5, -b * 0.25 + dd))
    escribir("b2_coincidencia", f, "Cuerpo B2: divina coincidencia; la mejora de la productividad baja el tipo natural y desplaza la demanda (E2) y el banco central, al bajar su tipo con el natural, la devuelve a DA0 (E0).")
    sim.append(("Sintética", "Cuerpo B2 (NEK): aspa con pendientes 0,6 (CP) y -1,2 (DA) y desplazamientos de 1,4; respuestas del modelo de tres ecuaciones con la calibración de la A8 (relajación de un punto anual con persistencia 0,5; mejora del 1 % con persistencia 0,9); perturbación de costes de 1,2",
                "b2_aspa, b2_nek, b2_costes, b2_coincidencia"))


def cuerpo_b3(sim):
    def xy(xs, ys):
        return " ".join("(%.2f,%.4f)" % (a, b) for a, b in zip(xs, ys))
    flecha = "-{Stealth[length=2.4mm]}, thick"

    # ---- b3_ciclos: ciclo financiero (largo y amplio) y ciclo económico (corto), con las crisis en los picos financieros
    T = np.linspace(0, 60, 601)
    fin = 3.0 * np.sin(2 * math.pi * (T - 8.5) / 18.0)
    dfin = np.gradient(fin, T)
    eco = np.sin(2 * math.pi * T / 7.0) - 0.9 * np.clip(-dfin, 0, None) / np.abs(dfin).max() * 1.6   # recesiones más hondas en la contracción financiera
    picos = [T[i] for i in range(1, 600) if fin[i] > fin[i - 1] and fin[i] >= fin[i + 1]]
    f = ("\\begin{tikzpicture}\n\\begin{axis}[width=13cm, height=4.8cm, scale only axis, %s, xmin=0, xmax=60, ymin=-4.6, ymax=4.6, xtick=\\empty, ytick=\\empty,\n"
         "    xlabel={Tiempo}, ylabel={Desviación respecto a la tendencia},\n"
         "    legend style={draw=none, fill=none, font=\\footnotesize, at={(0.5,1.02)}, anchor=south}, legend columns=3]\n"
         "\\addplot[black!40, thin, forget plot] coordinates {(0,0) (60,0)};\n"
         "\\addplot[black, very thick] coordinates {%s};\\addlegendentry{ciclo financiero}\n"
         "\\addplot[black!50, thick] coordinates {%s};\\addlegendentry{ciclo económico}\n"
         "\\addplot[only marks, mark=triangle*, mark size=3pt, black] coordinates {%s};\\addlegendentry{crisis bancaria}\n"
         "\\end{axis}\n\\end{tikzpicture}" % (ESTILO, xy(T[::3], fin[::3]), xy(T[::3], eco[::3]), " ".join("(%.2f,3.550)" % p for p in picos)))
    escribir("b3_ciclos", f, "Cuerpo B3: ciclo financiero (periodo 18, amplitud 3) y ciclo económico (periodo 7, amplitud 1, con recesiones más hondas en la contracción financiera); crisis en los picos financieros.")

    # ---- b3_espiral: bucle de amplificación financiera
    cajas = [("pre", "Caen los precios\\\\de los activos", "(0,1.9)"),
             ("pat", "Caen el patrimonio de los\\\\prestatarios y el valor\\\\de sus garantías", "(4.2,0)"),
             ("cre", "Se encarece y se\\\\restringe el crédito", "(0,-1.9)"), ("gas", "Caen la inversión\\\\y el gasto", "(-4.2,0)")]
    f = "\\begin{tikzpicture}[font=\\footnotesize, caja/.style={draw, rounded corners=2pt, align=center, inner sep=4pt, minimum width=3.2cm, minimum height=1.1cm}]\n"
    for n, txt, pos in cajas:
        f += "\\node[caja] (%s) at %s {%s};\n" % (n, pos, txt)
    f += ("\\node[caja, fill=black!8] (per) at (0,3.75) {Una perturbación: cae la\\\\productividad o sube el tipo de interés};\n"
          "\\node[caja, fill=black!8] (int) at (4.2,-3.4) {Los intermediarios pierden\\\\capital y prestan menos};\n"
          "\\draw[%s] (per) -- (pre);\n\\draw[%s] (pre.east) to[out=0, in=90] (pat.north);\n\\draw[%s] (pat.south) to[out=270, in=0] (cre.east);\n"
          "\\draw[%s] (cre.west) to[out=180, in=270] (gas.south);\n\\draw[%s] (gas.north) to[out=90, in=180] (pre.west);\n"
          "\\draw[%s, dashed] (pat.south east) to[out=300, in=90] (int.north);\n\\draw[%s, dashed] (int.west) to[out=180, in=300] (cre.south);\n"
          "\\end{tikzpicture}" % ((flecha,) * 7))
    escribir("b3_espiral", f, "Cuerpo B3: espiral de amplificación financiera (precios de los activos, patrimonio y garantías, crédito, gasto) y capital de los intermediarios.")

    # ---- b3_recesiones: sendas estilizadas tras el pico, con y sin crisis financiera (medias de la A10, 1870-2015, anexo III.7)
    x = np.array([0, 1, 2, 3, 4, 5.0])
    normal = np.array([0, -2.04, -0.33, 1.52, 3.12, 4.61])
    finan = np.array([0, -2.73, -2.45, -1.31, 0.18, 1.52])
    xs = np.linspace(0, 5, 101)
    f = ("\\begin{tikzpicture}\n\\begin{axis}[width=10cm, height=5cm, scale only axis, %s, xmin=0, xmax=5, ymin=-3.4, ymax=5.4, xtick={0}, xticklabels={pico}, ytick={0}, yticklabels={$0$},\n"
         "    xlabel={Años desde el pico}, ylabel={Producción respecto al pico},\n"
         "    legend style={draw=none, fill=none, font=\\footnotesize, at={(0.02,0.98)}, anchor=north west}, legend cell align=left]\n"
         "\\addplot[black!40, thin, forget plot] coordinates {(0,0) (5,0)};\n"
         "\\addplot[black, thick] coordinates {%s};\\addlegendentry{recesión sin crisis financiera}\n"
         "\\addplot[black, very thick, dashed] coordinates {%s};\\addlegendentry{recesión con crisis financiera}\n"
         "\\end{axis}\n\\end{tikzpicture}" % (ESTILO, xy(xs, np.polyval(np.polyfit(x, normal, 4), xs)), xy(xs, np.polyval(np.polyfit(x, finan, 4), xs))))
    escribir("b3_recesiones", f, "Cuerpo B3: sendas estilizadas (polinomio de grado 4) de la producción por habitante tras el pico de las recesiones normales y financieras (medias de la A10).")

    # ---- b3_riesgo: distribución del crecimiento futuro con condiciones financieras holgadas y tensas (normales asimétricas ilustrativas)
    erf = np.vectorize(math.erf)
    g = np.linspace(-11, 9, 801)

    def asim(loc, esc, a):
        z = (g - loc) / esc
        return 2 / esc * np.exp(-z ** 2 / 2) / math.sqrt(2 * math.pi) * 0.5 * (1 + erf(a * z / math.sqrt(2)))

    def cuantil(d, q):
        return g[np.searchsorted(np.cumsum(d) * (g[1] - g[0]), q)]
    d1, d2 = asim(2.6, 1.6, 0.0), asim(4.4, 4.0, -2.5)
    q1, q2 = cuantil(d1, 0.05), cuantil(d2, 0.05)
    f = ("\\begin{tikzpicture}\n\\begin{axis}[width=10cm, height=5cm, scale only axis, %s, xmin=-11, xmax=9, ymin=0, ymax=0.3, xtick={0}, xticklabels={$0$}, ytick=\\empty,\n"
         "    xlabel={Crecimiento de la producción en el año siguiente}, ylabel={Densidad},\n"
         "    legend style={draw=none, fill=none, font=\\footnotesize, at={(0.02,0.98)}, anchor=north west}, legend cell align=left]\n"
         "\\addplot[black!45, very thick] coordinates {%s};\\addlegendentry{condiciones financieras holgadas}\n"
         "\\addplot[black, thick, dashed] coordinates {%s};\\addlegendentry{condiciones financieras tensas}\n"
         "\\draw[black!45, thin] (axis cs:%.2f,0) -- (axis cs:%.2f,0.13);\\draw[black, thin] (axis cs:%.2f,0) -- (axis cs:%.2f,0.05);\n"
         "\\node[font=\\footnotesize, anchor=south east, align=center, inner sep=1pt] at (axis cs:%.2f,0.13) {cuantil del\\\\$5\\%%$};\n"
         "\\node[font=\\footnotesize, anchor=south, align=center] at (axis cs:%.2f,0.05) {cuantil del\\\\$5\\%%$};\n"
         "\\end{axis}\n\\end{tikzpicture}" % (ESTILO, xy(g[::4], d1[::4]), xy(g[::4], d2[::4]), q1, q1, q2, q2, q1, q2))
    escribir("b3_riesgo", f, "Cuerpo B3: crecimiento en riesgo; con condiciones tensas el cuantil del 5 %% baja mucho (de %.2f a %.2f), la mediana poco (de %.2f a %.2f) y el del 95 %% no baja (de %.2f a %.2f)."
             % (q1, q2, cuantil(d1, 0.5), cuantil(d2, 0.5), cuantil(d1, 0.95), cuantil(d2, 0.95)))

    # ---- b3_global: transmisión del ciclo financiero global
    f = ("\\begin{tikzpicture}[font=\\footnotesize, caja/.style={draw, rounded corners=2pt, align=center, inner sep=4pt, text width=3.1cm, minimum height=1.4cm}]\n"
         "\\node[caja, fill=black!8] (a) at (0,0) {Política monetaria\\\\de Estados Unidos};\n"
         "\\node[caja] (b) at (4.1,0) {Apetito global por el\\\\riesgo y valor del dólar};\n"
         "\\node[caja] (c) at (8.2,0) {Flujos de capital, crédito\\\\y precios de los activos\\\\en el resto del mundo};\n"
         "\\node[caja] (d) at (12.3,0) {Ciclos financieros\\\\nacionales sincronizados};\n"
         "\\draw[%s] (a) -- (b);\\draw[%s] (b) -- (c);\\draw[%s] (c) -- (d);\n"
         "\\end{tikzpicture}" % ((flecha,) * 3))
    escribir("b3_global", f, "Cuerpo B3: transmisión del ciclo financiero global desde la política monetaria de Estados Unidos.")
    sim.append(("Sintética", "Cuerpo B3 (ciclo financiero): ciclos sinusoidales de periodo 18 (financiero, amplitud 3) y 7 (económico, amplitud 1, más hondo en la contracción financiera); "
                "sendas tras el pico ajustadas con un polinomio de grado 4 a las medias de la A10 (1870-2015); normales asimétricas (2,6; 1,6; 0) y (4,4; 4,0; -2,5) para las condiciones holgadas y tensas; esquemas",
                "b3_ciclos, b3_espiral, b3_recesiones, b3_riesgo, b3_global"))


def con_datos_a13(carpeta, filas_series, cifras):
    # ---- colas gruesas: asimetría y curtosis del crecimiento trimestral del PIB real de EE. UU.
    pib = {f: v for f, v in leer(carpeta, "GDPC1")}
    fechas = sorted(pib)
    crec = [(fechas[i], 100 * (math.log(pib[fechas[i]]) - math.log(pib[fechas[i - 1]]))) for i in range(1, len(fechas))]
    for desde, hasta in (("1947-04-01", "2019-10-01"), ("1985-01-01", "2019-10-01")):
        s = np.array([v for f, v in crec if desde <= f <= hasta])
        z = (s - s.mean()) / s.std()
        cifras.append(("Crecimiento trimestral del PIB real de EE. UU. (100 x diferencia del logaritmo), %s a %s: observaciones, asimetría y curtosis" % (desde[:7], hasta[:7]),
                       "%d; %.2f; %.2f" % (len(s), float(np.mean(z ** 3)), float(np.mean(z ** 4))), "", "IV.5"))
    # ---- pico espectral: espectro autorregresivo de orden 12 de las horas por habitante y del paro, 1948T1-2019T4
    horas = {f: v for f, v in leer(carpeta, "HOANBS")}
    pob = dict(trimestral(leer(carpeta, "CNP16OV")))
    paro = dict(trimestral(leer(carpeta, "UNRATE")))
    claves = ["%d-%02d-01" % (a, m) for a in range(1948, 2020) for m in (1, 4, 7, 10)]
    series_esp = {"horas por habitante": np.array([100 * math.log(horas[k] / pob[k]) for k in claves]),
                  "paro": np.array([paro[k] for k in claves])}

    def paso_alto(x, corte):
        x = x - x.mean()
        F = np.fft.rfft(x)
        fr = np.fft.rfftfreq(len(x))
        F[0] = 0
        F[(fr > 0) & (fr < 1.0 / corte)] = 0
        return np.fft.irfft(F, len(x))

    def maximo_ar(x, p=12):
        x = x - x.mean()
        X = np.column_stack([x[p - j - 1:len(x) - j - 1] for j in range(p)])
        b = np.linalg.lstsq(X, x[p:], rcond=None)[0]
        per = np.arange(6, 121, 1.0)
        dens = [1 / abs(1 - sum(b[j] * np.exp(-1j * 2 * math.pi / q * (j + 1)) for j in range(p))) ** 2 for q in per]
        return per[int(np.argmax(dens))]
    textos = []
    for nombre, x in series_esp.items():
        textos.append("%s: en niveles %.0f; sin oscilaciones de más de 100 trimestres %.0f" % (nombre, maximo_ar(x), maximo_ar(paso_alto(x, 100))))
    cifras.append(("Periodo (trimestres, entre 6 y 120) de máxima densidad del espectro autorregresivo de orden 12, EE. UU. 1948T1-2019T4 (120 = sigue creciendo hacia las frecuencias bajas)",
                   "; ".join(textos), "trimestres", "IV.3"))


def main():
    carpeta = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
    descargar(carpeta)
    descargar_a2(carpeta)
    descargar_a3(carpeta)
    descargar_a4(carpeta)
    descargar_a9(carpeta)
    descargar_a10(carpeta)
    series, cifras, sint, momentos = [], [], [], []
    sinteticas(sint)
    sinteticas_a4(sint)
    con_datos(carpeta, series, cifras)
    con_datos_a2(carpeta, series, cifras, momentos)
    con_datos_a3(carpeta, series, cifras)
    con_datos_a4(carpeta, series, cifras)
    con_datos_a5(carpeta, series, cifras, momentos, sint)
    con_datos_a6(carpeta, series, cifras)
    con_datos_a7(carpeta, series, cifras, sint)
    con_datos_a8(cifras, sint)
    con_datos_a9(carpeta, series, cifras, sint)
    con_datos_a10(carpeta, series, cifras, sint)
    con_datos_a11(carpeta, series, cifras, sint)
    sinteticas_a12(series, cifras, sint)
    sinteticas_a13(series, cifras, sint)
    con_datos_a13(carpeta, series, cifras)
    cuerpo_b1(sint)
    cuerpo_b2_nmc(sint)
    cuerpo_b2_nek(sint)
    cuerpo_b3(sint)
    leeme = [["Libro de datos del tema 3.A.42 (Teorías de los ciclos económicos)"],
             ["Generado por Code/libro_y_figuras.py el %s con los datos de FRED descargados ese día." % FECHA_DESCARGA],
             ["Hojas: Fuentes (series y su origen), Series (formato largo: serie, país, fecha, valor, unidad, fuente, tratamiento, figura),"],
             ["Cronologías (picos y valles del NBER, de la AEE y del CEPR), Cifras_citadas (las que da el texto) y Simulaciones."],
             ["Tratamientos: nivel; ciclo HP con lambda 1600; ciclo HAMILTON con h 8 y p 4; ciclo BAXTER-KING con banda de 6 a 32 trimestres y K 12;"],
             ["todos los ciclos sobre 100 x logaritmo del PIB real (desviación en porcentaje)."],
             ["A3 (I.7 e I.8): VAR recursivo de EE. UU. (PIB, deflactor, materias primas, tipo de los fondos federales; 4 retardos; 1965T3-1995T3 y 1965T1-2007T4;"],
             ["bandas del 90% por remuestreo de los residuos, 1.000 réplicas), proyección local recursiva con errores de NEWEY y WEST, probit de la recesión"],
             ["dentro de doce meses sobre la pendiente (bono a diez años menos letras a tres meses en rendimiento equivalente), estimado con 1959-2018, y regla de SAHM."],
             ["A4 (II.1 y II.2): simulaciones de SLUTSKY y FRISCH (hoja Simulaciones) y réplica de LUCAS (1973) y BALL, MANKIW y ROMER (1988) con el PIB"],
             ["nominal y real del Banco Mundial: por país, y_t = a + b t + tau Dx_t + c y_(t-1) con 100 x log, 1960-2019, países con al menos 41 años seguidos."],
             ["A5 (II.3): modelo básico del ciclo real log-linealizado (trabajo divisible e indivisible), respuestas a la PTF y momentos de 500 simulaciones con HP."],
             ["A6 (II.4): VAR de largo plazo de GALÍ (1999) y autocorrelaciones del crecimiento del PIB. A7 (II.5 y II.6): ciclo real con gasto público y coste de LUCAS."],
             ["A8 (II.7-II.10): modelo neokeynesiano de tres ecuaciones con soluciones analíticas (perturbación monetaria, mejora tecnológica, orientación futura)."],
             ["A9 (III.1-III.4): versión lineal de KIYOTAKI y MOORE (1997) y apalancamiento de los intermediarios con las Cuentas Financieras de la Reserva Federal."],
             ["A10 (III.5-III.7): base JST R6 (crisis tras auges y recesiones financieras), prima de GILCHRIST y ZAKRAJŠEK y regresiones por cuantiles con el NFCI."],
             ["A11 (III.10): oleadas de crisis bancarias sistémicas en las 18 economías de la base JST, 1870-2020."],
             ["A12 (IV.1 y IV.2): figuras sintéticas (tres ciclos de SCHUMPETER, multiplicador-acelerador de SAMUELSON, ciclo de GOODWIN y equilibrios de KALDOR con parámetros ilustrativos)."],
             ["A13 (IV.3-IV.5): ecuación logística (caos y bifurcación), modelo de KEEN con parámetros ilustrativos, curtosis del crecimiento del PIB y espectro de las horas y del paro."],
             ["T14 (cuerpo, bloque 1): figuras abstractas b1_fases, b1_crecimiento y b1_tendencias sobre una misma serie base sintética (hoja Simulaciones); N1 (09/11): b1_volatilidad y b1_desfases, sustituidas por b1_correlograma (correlación cruzada abstracta)."],
             ["T15 (cuerpo, bloque 2, nueva macroeconomía clásica): figuras abstractas b2_lucas y b2_trabajo; N2 (09/11): b2_impulsos, retirada, y b2_rbc, sustituida por b2_clasico (oferta vertical y demanda de la teoría cuantitativa)."],
             ["T16 (cuerpo, bloque 2, nueva economía keynesiana): figuras abstractas b2_aspa, b2_nek (con el modelo de tres ecuaciones de la A8) y b2_costes; N3 (09/11): b2_coincidencia (divina coincidencia en el aspa)."],
             ["T17 (cuerpo, bloque 3, ciclo financiero): figuras abstractas b3_ciclos, b3_espiral, b3_recesiones (estilizada a partir de las medias de la A10), b3_riesgo y b3_global."]]
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
    for s, nombre in SERIES_A2.items():
        fuentes.append([s, nombre, "Estados Unidos", "ver FRED", "trimestral o mensual (media trimestral)", "FRED, Banco de la Reserva Federal de San Luis", FRED + s, FECHA_DESCARGA])
    fuentes.append(["ALFRED GDPC1", "Ediciones del PIB real de EE. UU., diciembre de 1991-2019", "Estados Unidos", "miles de millones de dólares encadenados de cada edición",
                    "trimestral", "ALFRED, Banco de la Reserva Federal de San Luis", "https://alfred.stlouisfed.org/series?seid=GDPC1", FECHA_DESCARGA])
    for s, nombre in BANCO_MUNDIAL.items():
        fuentes.append([s, nombre, "Todos los países (sin agregados regionales)", "moneda nacional", "anual", "Banco Mundial, Indicadores del Desarrollo Mundial",
                        "https://api.worldbank.org/v2/country/all/indicator/%s?format=json" % s, "07/11/2026"])
    fuentes.append(["CNP16OV", "Población civil no institucional de 16 años o más", "Estados Unidos", "miles de personas", "mensual (media trimestral)",
                    "FRED, Banco de la Reserva Federal de San Luis (BLS)", FRED + "CNP16OV", "07/11/2026"])
    fuentes.append(["B230RC0A052NBEA", "Población de EE. UU. (media anual)", "Estados Unidos", "miles de personas", "anual",
                    "FRED, Banco de la Reserva Federal de San Luis (BEA)", FRED + "B230RC0A052NBEA", "07/11/2026"])
    for s, nombre in SERIES_A3.items():
        fuentes.append([s, nombre, "Estados Unidos", "ver FRED", "mensual (media trimestral en el VAR)", "FRED, Banco de la Reserva Federal de San Luis", FRED + s, FECHA_DESCARGA])
    for s, nombre in SERIES_A9.items():
        fuentes.append([s, nombre, "Estados Unidos", "millones de dólares", "trimestral (saldo a fin de trimestre)",
                        "Reserva Federal, Cuentas Financieras (Z.1), en FRED", FRED + s, "08/11/2026"])
    fuentes.append(["JST R6", "Base macrohistórica de JORDÀ, SCHULARICK y TAYLOR (crédito, PIB, precios, vivienda, crisis bancarias)", "18 economías avanzadas",
                    "varias", "anual, 1870-2020", "macrohistory.net", JST_URL, "08/11/2026"])
    fuentes.append(["ebp_csv", "Diferencial de crédito de GILCHRIST y ZAKRAJŠEK y prima de los bonos en exceso", "Estados Unidos", "puntos porcentuales",
                    "mensual", "Reserva Federal, FEDS Notes", EBP_URL, "08/11/2026"])
    fuentes.append(["NFCI", "Índice nacional de condiciones financieras", "Estados Unidos", "índice (0 = media, valores positivos = más tensión)",
                    "semanal (media trimestral)", "Reserva Federal de Chicago", NFCI_URL, "08/11/2026"])
    for nombre, consulta in EUROSTAT.items():
        fuentes.append(["Eurostat " + consulta.split("?")[0], nombre, "España y zona del euro", "CLV10_MEUR, PD10_EUR, THS_PER o THS_HW", "trimestral",
                        "Eurostat", "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/" + consulta, FECHA_DESCARGA])
    for b, nombre in (("WS_TC", "Crédito total al sector privado no financiero"), ("WS_CREDIT_GAP", "Brechas de crédito sobre el PIB"),
                      ("WS_SPP", "Precios de la vivienda seleccionados")):
        fuentes.append(["BPI " + b, nombre, "España y Estados Unidos", "porcentaje del PIB o índice 2010 = 100", "trimestral",
                        "Banco de Pagos Internacionales", "https://data.bis.org/static/bulk/%s_csv_flat.zip" % b, FECHA_DESCARGA])
    cif = [["Cifra", "Valor", "Unidad", "Apartado"]] + [list(c) for c in cifras]
    simul = [["Simulación", "Descripción", "Figura"]] + [list(s) for s in sint]
    mom = [["País", "Variable", "Estadístico", "Valor", "Muestra", "Filtro"]] + [list(m) for m in momentos]
    escribir_xlsx(os.path.join(TEMA, "Code", "datos_3A42.xlsx"),
                  [("Léeme", leeme), ("Fuentes", fuentes), ("Series", filas), ("Cronologías", cron), ("Cifras_citadas", cif), ("Momentos", mom),
                   ("Simulaciones", simul)])
    for c in cifras:
        print("%-75s %s %s" % (c[0], c[1], c[2]))


if __name__ == "__main__":
    main()
