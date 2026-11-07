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


# ---------------------------------------------------------------- A3 (07/11/2026): identificación y predicción
# Figuras: anx_var_monetario (VAR recursivo de EE. UU. a la manera de CHRISTIANO, EICHENBAUM y EVANS, 1999),
# anx_proyeccion_local (proyección local del PIB, JORDÀ 2005, frente al VAR) y anx_senales_recesion (probit de la
# pendiente de la curva, ESTRELLA y MISHKIN 1998, y regla de SAHM con los datos de cada momento). Fuentes adicionales de
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
                                 "elaboración propia con FRED (GS10, TB3MS, USREC)", "pendiente %.2f; probit estimado con 1959-2018 (recesiones hasta 2019)" % pend[f], "anx_senales_recesion"))
    for f in sorted(sahm):
        filas_series.append(("Indicador de SAHM con los datos de cada momento", "Estados Unidos", f, sahm[f], "puntos", "FRED (SAHMREALTIME)", "", "anx_senales_recesion"))
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
    fig = "\\begin{tikzpicture}\n"
    fig += ("\\begin{axis}[name=a, at={(0,0)}, anchor=north west, width=14.2cm, height=3.6cm, scale only axis, %s,\n"
            "    xmin=1959, xmax=2027, xtick={1960,1965,...,2025}, ymin=0, ymax=100, ytick={0,25,50,75,100}, ylabel={Porcentaje},\n"
            "    title={(a) Probabilidad de recesión dentro de doce meses según la pendiente de la curva}, title style={font=\\footnotesize}]\n%s\n\\end{axis}\n" % (ESTILO, cuerpo_a))
    fig += ("\\begin{axis}[name=b, at={($(a.south west)+(0,-1.5cm)$)}, anchor=north west, width=14.2cm, height=3.6cm, scale only axis, %s,\n"
            "    xmin=1959, xmax=2027, xtick={1960,1965,...,2025}, ymin=-0.5, ymax=3, ytick={0,0.5,1,2,3}, ylabel={Puntos},\n"
            "    title={(b) Regla de SAHM con los datos de cada momento}, title style={font=\\footnotesize}]\n%s\n\\end{axis}\n" % (ESTILO, cuerpo_b))
    fig += "\\end{tikzpicture}"
    escribir("anx_senales_recesion", fig, "EE. UU.: probabilidad de recesión a doce meses de un probit sobre la pendiente (10 años menos 3 meses), estimado con 1959-2018, y regla de SAHM en tiempo real.")


def main():
    carpeta = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
    descargar(carpeta)
    descargar_a2(carpeta)
    descargar_a3(carpeta)
    series, cifras, sint, momentos = [], [], [], []
    sinteticas(sint)
    con_datos(carpeta, series, cifras)
    con_datos_a2(carpeta, series, cifras, momentos)
    con_datos_a3(carpeta, series, cifras)
    leeme = [["Libro de datos del tema 3.A.42 (Teorías de los ciclos económicos)"],
             ["Generado por Code/libro_y_figuras.py el %s con los datos de FRED descargados ese día." % FECHA_DESCARGA],
             ["Hojas: Fuentes (series y su origen), Series (formato largo: serie, país, fecha, valor, unidad, fuente, tratamiento, figura),"],
             ["Cronologías (picos y valles del NBER, de la AEE y del CEPR), Cifras_citadas (las que da el texto) y Simulaciones."],
             ["Tratamientos: nivel; ciclo HP con lambda 1600; ciclo HAMILTON con h 8 y p 4; ciclo BAXTER-KING con banda de 6 a 32 trimestres y K 12;"],
             ["todos los ciclos sobre 100 x logaritmo del PIB real (desviación en porcentaje)."],
             ["A3 (I.7 e I.8): VAR recursivo de EE. UU. (PIB, deflactor, materias primas, tipo de los fondos federales; 4 retardos; 1965T3-1995T3 y 1965T1-2007T4;"],
             ["bandas del 90% por remuestreo de los residuos, 1.000 réplicas), proyección local recursiva con errores de NEWEY y WEST, probit de la recesión"],
             ["dentro de doce meses sobre la pendiente (bono a diez años menos letras a tres meses en rendimiento equivalente), estimado con 1959-2018, y regla de SAHM."]]
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
    for s, nombre in SERIES_A3.items():
        fuentes.append([s, nombre, "Estados Unidos", "ver FRED", "mensual (media trimestral en el VAR)", "FRED, Banco de la Reserva Federal de San Luis", FRED + s, "07/11/2026"])
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
