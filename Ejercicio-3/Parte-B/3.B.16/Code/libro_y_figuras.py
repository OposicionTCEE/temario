# -*- coding: utf-8 -*-
# Libro de datos del tema 3.B.16 (Code/datos_3B16.xlsx) y figuras calculadas del anexo de evidencia.
# A7 (07/11/2026): II.1 simetría (ciclos, amplitud, perturbaciones a la manera de BAYOUMI y EICHENGREEN, estructuras
# productivas) y II.2 ajuste (réplica de BLANCHARD y KATZ con los estados de EE. UU.; dispersión y persistencia del paro).
# Fuentes: Banco Mundial (Indicadores del Desarrollo Mundial): NY.GDP.MKTP.KN (PIB a precios constantes, moneda nacional),
# NY.GDP.MKTP.CN (PIB a precios corrientes, moneda nacional), NY.GDP.MKTP.KD (PIB a precios constantes, dólares de 2015);
# Eurostat: nama_10_a10 (valor añadido bruto por ramas, millones de euros corrientes), une_rt_a (tasa de paro, 15-74 años);
# FRED (Banco de la Reserva Federal de San Luis, con datos del BLS): {ST}NAN (empleo asalariado no agrario por estado, sin
# desestacionalizar), {ST}UR (tasa de paro por estado), LBSSA{FIPS} (tasa de actividad por estado), UNRATE y CIVPART.
# Uso, desde la carpeta del tema:  python3 -I Code/libro_y_figuras.py [carpeta con las descargas]
#   Sin carpeta, descarga en una carpeta temporal. Después, para cada figura:  bash Code/generar_figura.sh <nombre>

import csv, json, math, os, sys, tempfile, time, urllib.request

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

sys.path.insert(0, "/Users/marceloortega/TCEE/main/herramientas")
from xlsx_simple import escribir_xlsx

TEMA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(TEMA, "Img")
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="
WB = "https://api.worldbank.org/v2/country/%s/indicator/%s?format=json&per_page=20000&date=1960:2024"
EST = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
FECHA_DESCARGA = "07/11/2026"

# Países: once miembros fundadores de la zona del euro con datos largos (sin Luxemburgo) y tres de la Unión que no la adoptaron.
EURO = ["DEU", "FRA", "ITA", "ESP", "NLD", "BEL", "AUT", "FIN", "PRT", "IRL", "GRC"]
FUERA = ["GBR", "SWE", "DNK"]
NOMBRE = {"DEU": "Alemania", "FRA": "Francia", "ITA": "Italia", "ESP": "España", "NLD": "Países Bajos", "BEL": "Bélgica",
          "AUT": "Austria", "FIN": "Finlandia", "PRT": "Portugal", "IRL": "Irlanda", "GRC": "Grecia", "GBR": "Reino Unido",
          "SWE": "Suecia", "DNK": "Dinamarca"}
ISO2 = {"DEU": "DE", "FRA": "FR", "ITA": "IT", "ESP": "ES", "NLD": "NL", "BEL": "BE", "AUT": "AT", "FIN": "FI", "PRT": "PT",
        "IRL": "IE", "GRC": "EL", "GBR": "UK", "SWE": "SE", "DNK": "DK"}
WB_SERIES = {"NY.GDP.MKTP.KN": "PIB a precios constantes, moneda nacional",
             "NY.GDP.MKTP.CN": "PIB a precios corrientes, moneda nacional",
             "NY.GDP.MKTP.KD": "PIB a precios constantes, dólares de 2015"}
ESTADOS = {"AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08", "CT": "09", "DE": "10", "DC": "11",
           "FL": "12", "GA": "13", "HI": "15", "ID": "16", "IL": "17", "IN": "18", "IA": "19", "KS": "20", "KY": "21",
           "LA": "22", "ME": "23", "MD": "24", "MA": "25", "MI": "26", "MN": "27", "MS": "28", "MO": "29", "MT": "30",
           "NE": "31", "NV": "32", "NH": "33", "NJ": "34", "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39",
           "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45", "SD": "46", "TN": "47", "TX": "48", "UT": "49",
           "VT": "50", "VA": "51", "WA": "53", "WV": "54", "WI": "55", "WY": "56"}
WB_PARO = "SL.UEM.TOTL.ZS"  # tasa de paro, estimación armonizada de la OIT, desde 1991
WB_A8 = {"SP.POP.TOTL": "Población total", "NY.GDP.PCAP.KD": "PIB por habitante a precios constantes, dólares de 2015"}
GEO = "&".join("geo=" + ISO2[p] for p in EURO)
EUROSTAT = {"a10.json": "nama_10_a10?unit=CP_MEUR&na_item=B1G&" + GEO,
            "cuentas.json": "nasa_10_nf_tr?unit=CP_MEUR&sector=S1&direct=PAID&na_item=B1GQ&na_item=B5G&na_item=B6G&na_item=P3&" + GEO,
            "deflactor.json": "nama_10_gdp?unit=PD15_EUR&na_item=B1GQ&" + GEO,
            "precios.json": "prc_ppp_ind?na_item=PLI_EU27_2020&ppp_cat=A01&" + GEO,
            "clu.json": "nama_10_lp_ulc?unit=I15&na_item=NULC_PER&" + GEO}
# A9: tipos de la deuda pública a diez años (OCDE, en FRED), euríbor a tres meses, HICP de España y de la zona del euro (FRED),
# inflación de cinco países con tipos de cambio rígidos y balanza por cuenta corriente (Banco Mundial), saldos TARGET (BCE).
TIPOS_10 = {p: "IRLTLT01%sM156N" % ("GR" if p == "GRC" else ISO2[p]) for p in EURO}
FRED_A9 = dict({TIPOS_10[p]: "Tipo de interés de la deuda pública a diez años, " + NOMBRE[p] for p in EURO},
               IR3TIB01EZM156N="Tipo de interés interbancario a tres meses de la zona del euro",
               CP0000ESM086NEST="Índice armonizado de precios de consumo de España",
               CP0000EZCCM086NEST="Índice armonizado de precios de consumo de la zona del euro (composición cambiante)")
RIGIDOS = {"BGR": ("Bulgaria", "caja de conversión", 1997), "EST": ("Estonia", "caja de conversión", 1992),
           "LTU": ("Lituania", "caja de conversión", 1994), "ECU": ("Ecuador", "dolarización", 2000), "SLV": ("El Salvador", "dolarización", 2001)}
WB_A9 = {"FP.CPI.TOTL.ZG": "Inflación de los precios de consumo", "BN.CAB.XOKA.GD.ZS": "Saldo de la balanza por cuenta corriente, porcentaje del PIB"}
TARGET = ["DE", "NL", "LU", "FI", "FR", "IT", "ES", "GR", "PT", "IE"]
ECB = "https://data-api.ecb.europa.eu/service/data/TGB/M.%s.N.A094T.U2.EUR.E?format=csvdata"
SECTORES = ["A", "BDE", "C", "F", "G-I", "J", "K", "L", "M_N", "O-Q", "R-U"]
LAMBDA_ANUAL = 6.25  # RAVN y UHLIG (2002)
RETARDOS_BE, RETARDOS_BK, HORIZONTE = 2, 2, 10


# ---------------------------------------------------------------- descargas y lectura
def bajar(url, destino, pausa=0.25):
    if not os.path.exists(destino):
        urllib.request.urlretrieve(url, destino)
        time.sleep(pausa)


def descargar(carpeta):
    for s in list(WB_SERIES) + [WB_PARO]:
        bajar(WB % (";".join(EURO + FUERA), s), os.path.join(carpeta, "wb_" + s + ".json"))
    for s in WB_A8:
        bajar(WB % (";".join(EURO + FUERA + ["USA"]), s), os.path.join(carpeta, "wb_" + s + ".json"))
    for s in WB_A9:
        bajar((WB % (";".join(EURO + list(RIGIDOS)), s)).replace("1960:2024", "1985:2024"), os.path.join(carpeta, "wb_" + s + ".json"))
    for s in FRED_A9:
        bajar(FRED + s, os.path.join(carpeta, s + ".csv"))
    for c in TARGET:
        bajar(ECB % c, os.path.join(carpeta, "tgb_" + c + ".csv"))
    for st, fips in ESTADOS.items():
        for s in (st + "NAN", st + "UR", "LBSSA" + fips):
            bajar(FRED + s, os.path.join(carpeta, s + ".csv"))
    for s in ("UNRATE", "CIVPART"):
        bajar(FRED + s, os.path.join(carpeta, s + ".csv"))
    for nombre, consulta in EUROSTAT.items():
        bajar(EST + consulta + "&format=JSON&lang=EN", os.path.join(carpeta, nombre))


def leer_wb(carpeta, serie):
    d = json.load(open(os.path.join(carpeta, "wb_" + serie + ".json"), encoding="utf-8"))
    salida = {}
    for x in d[1]:
        if x["value"] is not None:
            salida.setdefault(x["countryiso3code"], {})[int(x["date"])] = float(x["value"])
    return salida


def leer_fred_anual(carpeta, serie, desde, hasta):  # media anual de los meses; solo años completos
    acum = {}
    with open(os.path.join(carpeta, serie + ".csv"), encoding="utf-8") as f:
        lector = csv.reader(f)
        next(lector)
        for fecha, valor in lector:
            if valor not in (".", ""):
                acum.setdefault(int(fecha[:4]), []).append(float(valor))
    return {a: sum(v) / len(v) for a, v in acum.items() if len(v) == 12 and desde <= a <= hasta}


def leer_eurostat_anual(ruta, **sel):
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
            salida[int(t)] = float(v)
    return salida


# ---------------------------------------------------------------- herramientas
def hp(y, lam=LAMBDA_ANUAL):
    n = len(y)
    d = sparse.diags([np.ones(n - 2), -2 * np.ones(n - 2), np.ones(n - 2)], [0, 1, 2], shape=(n - 2, n))
    tendencia = spsolve((sparse.eye(n) + lam * d.T @ d).tocsc(), y)
    return y - tendencia


def corr(a, b):
    return float(np.corrcoef(a, b)[0, 1])


def svar_bq(X, p=RETARDOS_BE):
    """VAR(p) con constante y tendencia lineal en (crecimiento, inflación) e identificación de BLANCHARD y QUAH: la segunda
    perturbación (demanda) no afecta a la producción a largo plazo. La tendencia recoge la desinflación de 1970-2019: sin
    ella, la perturbación de oferta sube los precios a largo plazo en 12 de los 14 países y la de demanda baja la producción
    en el impacto en 9, contra lo que predice el modelo de oferta y demanda agregadas. Devuelve las perturbaciones
    estructurales normalizadas (T-p x 2), las respuestas acumuladas [h, variable, perturbación] y la matriz de impacto G."""
    Y = X[p:]
    Z = np.hstack([np.ones((len(Y), 1)), np.arange(len(Y)).reshape(-1, 1) / 10.0] + [X[p - j:len(X) - j] for j in range(1, p + 1)])
    B = np.linalg.lstsq(Z, Y, rcond=None)[0]
    E = Y - Z @ B
    S = E.T @ E / (len(Y) - Z.shape[1])
    Phi = [B[2 + 2 * (j - 1):2 + 2 * j].T for j in range(1, p + 1)]
    C1 = np.linalg.inv(np.eye(2) - sum(Phi))
    G = np.linalg.inv(C1) @ np.linalg.cholesky(C1 @ S @ C1.T)  # efecto a largo plazo triangular inferior con diagonal positiva
    eps = E @ np.linalg.inv(G).T
    Psi = [np.eye(2)]
    for h in range(1, HORIZONTE + 1):
        Psi.append(sum(Phi[j] @ Psi[h - 1 - j] for j in range(min(p, h))))
    R = np.cumsum(np.array([P @ G for P in Psi]), axis=0)  # niveles (logaritmo de la producción y de los precios)
    return eps, R, G


# ---------------------------------------------------------------- II.1 simetría
def simetria(carpeta, series, cifras):
    kn, cn, kd = (leer_wb(carpeta, s) for s in WB_SERIES)
    anios = list(range(1970, 2020))
    for p in EURO + FUERA:
        for a in anios:
            series.append(("PIB real (moneda nacional constante)", NOMBRE[p], a, kn[p][a], "moneda nacional constante", "Banco Mundial NY.GDP.MKTP.KN", "nivel", "anx2_correlaciones; anx2_amplitud; anx2_bayoumi"))
            series.append(("PIB nominal (moneda nacional corriente)", NOMBRE[p], a, cn[p][a], "moneda nacional corriente", "Banco Mundial NY.GDP.MKTP.CN", "nivel; el deflactor es el cociente con el PIB real", "anx2_bayoumi"))
            series.append(("PIB real (dólares de 2015)", NOMBRE[p], a, kd[p][a], "dólares constantes de 2015", "Banco Mundial NY.GDP.MKTP.KD", "nivel; pondera los agregados", "anx2_correlaciones; anx2_amplitud"))
    ciclo = {p: hp(100 * np.log([kn[p][a] for a in anios])) for p in EURO + FUERA}
    total = np.array([sum(kd[p][a] for p in EURO) for a in anios])
    ciclo["EA11"] = hp(100 * np.log(total))
    resto = {p: hp(100 * np.log(total - np.array([kd[p][a] for a in anios]))) for p in EURO}
    i1, i2 = anios.index(1971), anios.index(1998) + 1
    j1, j2 = anios.index(1999), anios.index(2019) + 1
    res = {}
    for p in EURO + FUERA:
        ref = resto[p] if p in EURO else ciclo["EA11"]
        r1 = corr(ciclo[p][i1:i2], ref[i1:i2])
        r2 = corr(ciclo[p][j1:j2], ref[j1:j2])
        amp = float(np.std(ciclo[p][j1:j2]) / np.std(ciclo["EA11"][j1:j2]))
        res[p] = (r1, r2, amp)
        cifras.append(("Correlación del ciclo con el resto de la zona, 1971-1998, " + NOMBRE[p], round(r1, 2), "coeficiente", "II.1.1"))
        cifras.append(("Correlación del ciclo con el resto de la zona, 1999-2019, " + NOMBRE[p], round(r2, 2), "coeficiente", "II.1.1"))
        cifras.append(("Amplitud del ciclo respecto a la zona, 1999-2019, " + NOMBRE[p], round(amp, 2), "cociente de desviaciones típicas", "II.1.2"))
    for nombre, grupo in (("zona del euro", EURO), ("fuera de la zona", FUERA)):
        m1 = float(np.mean([res[p][0] for p in grupo])); m2 = float(np.mean([res[p][1] for p in grupo]))
        cifras.append(("Correlación media, 1971-1998, " + nombre, round(m1, 2), "coeficiente", "II.1.1"))
        cifras.append(("Correlación media, 1999-2019, " + nombre, round(m2, 2), "coeficiente", "II.1.1"))
    # BAYOUMI y EICHENGREEN: VAR(2) en crecimiento e inflación del deflactor, 1971-2019 (estimación 1973-2019).
    be, shocks = {}, {}
    for p in EURO + FUERA:
        y = 100 * np.diff(np.log([kn[p][a] for a in anios]))
        pr = 100 * np.diff(np.log([cn[p][a] / kn[p][a] for a in anios]))
        eps, R, G = svar_bq(np.column_stack([y, pr]))
        shocks[p] = eps  # años 1973-2019
        be[p] = R
    t = list(range(1973, 2020))
    k1, k2, k3 = t.index(1998) + 1, t.index(1999), t.index(2019) + 1
    corr_be = {}
    for p in EURO + FUERA:
        if p == "DEU":
            continue
        o1 = corr(shocks[p][:k1, 0], shocks["DEU"][:k1, 0]); d1 = corr(shocks[p][:k1, 1], shocks["DEU"][:k1, 1])
        o2 = corr(shocks[p][k2:k3, 0], shocks["DEU"][k2:k3, 0]); d2 = corr(shocks[p][k2:k3, 1], shocks["DEU"][k2:k3, 1])
        corr_be[p] = (o1, d1, o2, d2)
        for nom, v, per in (("oferta", o1, "1973-1998"), ("demanda", d1, "1973-1998"), ("oferta", o2, "1999-2019"), ("demanda", d2, "1999-2019")):
            cifras.append(("Correlación con Alemania de las perturbaciones de %s, %s, %s" % (nom, per, NOMBRE[p]), round(v, 2), "coeficiente", "II.1.3"))
    for nombre, grupo in (("zona del euro", [p for p in EURO if p != "DEU"]), ("fuera de la zona", FUERA)):
        for k, nom in ((0, "oferta 1973-1998"), (1, "demanda 1973-1998"), (2, "oferta 1999-2019"), (3, "demanda 1999-2019")):
            cifras.append(("Correlación media con Alemania, %s, %s" % (nom, nombre), round(float(np.mean([corr_be[p][k] for p in grupo])), 2), "coeficiente", "II.1.3"))
    return res, corr_be, be


def estructuras(carpeta, series, cifras):
    ruta = os.path.join(carpeta, "a10.json")
    datos = {}
    for p in EURO:
        g = ISO2[p]
        for n in ["TOTAL", "A", "B-E", "C", "F", "G-I", "J", "K", "L", "M_N", "O-Q", "R-U"]:
            datos[(p, n)] = leer_eurostat_anual(ruta, geo=g, nace_r2=n, unit="CP_MEUR", na_item="B1G", freq="A")
    def cuotas(p, a):
        v = {"A": datos[(p, "A")][a], "BDE": datos[(p, "B-E")][a] - datos[(p, "C")][a], "C": datos[(p, "C")][a]}
        for n in ["F", "G-I", "J", "K", "L", "M_N", "O-Q", "R-U"]:
            v[n] = datos[(p, n)][a]
        return v
    res = {}
    for a in (1995, 2023):
        niveles = {p: cuotas(p, a) for p in EURO}
        for p in EURO:
            for n in SECTORES:
                series.append(("Valor añadido bruto por ramas (NACE " + n + ")", NOMBRE[p], a, niveles[p][n], "millones de euros corrientes", "Eurostat nama_10_a10", "nivel; BDE = B-E menos C", "anx2_krugman"))
        for p in EURO:
            propio = niveles[p]; tot = sum(propio.values())
            otros = {n: sum(niveles[q][n] for q in EURO if q != p) for n in SECTORES}; tot_o = sum(otros.values())
            k = sum(abs(propio[n] / tot - otros[n] / tot_o) for n in SECTORES)
            res.setdefault(p, {})[a] = k
            cifras.append(("Índice de especialización de KRUGMAN frente al resto de la zona, %d, %s" % (a, NOMBRE[p]), round(k, 3), "índice (0 a 2)", "II.1.4"))
    for a in (1995, 2023):
        cifras.append(("Índice de KRUGMAN medio, %d" % a, round(float(np.mean([res[p][a] for p in EURO])), 3), "índice (0 a 2)", "II.1.4"))
    for p in EURO:
        cifras.append(("Peso de la industria manufacturera en el valor añadido, 1995 y 2023, " + NOMBRE[p],
                       "%.1f y %.1f" % tuple(100 * datos[(p, "C")][a] / sum(cuotas(p, a).values()) for a in (1995, 2023)), "porcentaje", "II.1.4"))
    return res


# ---------------------------------------------------------------- II.2 ajuste
def blanchard_katz(carpeta, series, cifras):
    desde, hasta = 1976, 2019
    emp = {st: leer_fred_anual(carpeta, st + "NAN", desde, hasta) for st in ESTADOS}
    par = {st: leer_fred_anual(carpeta, st + "UR", desde, hasta) for st in ESTADOS}
    act = {st: leer_fred_anual(carpeta, "LBSSA" + f, desde, hasta) for st, f in ESTADOS.items()}
    u_us = leer_fred_anual(carpeta, "UNRATE", desde, hasta)
    p_us = leer_fred_anual(carpeta, "CIVPART", desde, hasta)
    anios = list(range(desde, hasta + 1))
    e_us = np.array([sum(emp[st][a] for st in ESTADOS) for a in anios])
    for st in ESTADOS:
        for a in anios:
            series.append(("Empleo asalariado no agrario (media anual)", st, a, emp[st][a], "miles de personas", "FRED " + st + "NAN (BLS)", "media de los doce meses", "anx2_bk"))
            series.append(("Tasa de paro (media anual)", st, a, par[st][a], "porcentaje", "FRED " + st + "UR (BLS)", "media de los doce meses", "anx2_bk; anx2_dispersion"))
            series.append(("Tasa de actividad (media anual)", st, a, act[st][a], "porcentaje", "FRED LBSSA" + ESTADOS[st] + " (BLS)", "media de los doce meses", "anx2_bk"))
    # variables relativas a la nación, en 100 x logaritmos
    Xe, Xl, Xp, ids = [], [], [], []
    for st in ESTADOS:
        e = 100 * (np.log([emp[st][a] for a in anios]) - np.log(e_us))
        le = 100 * (np.log([1 - par[st][a] / 100 for a in anios]) - np.log([1 - u_us[a] / 100 for a in anios]))
        lp = 100 * (np.log([act[st][a] / 100 for a in anios]) - np.log([p_us[a] / 100 for a in anios]))
        Xe.append(np.diff(e)); Xl.append(le[1:]); Xp.append(lp[1:])  # años 1977-2019
    # regresiones agrupadas con efectos fijos por estado (desviaciones respecto a la media de cada estado)
    def apilar(dep, regs):
        Y, Z = [], []
        for i in range(len(ESTADOS)):
            y = dep[i]; cols = [r[i] for r in regs]
            y = y - y.mean(); cols = [c - c.mean() for c in cols]
            Y.append(y); Z.append(np.column_stack(cols))
        return np.concatenate(Y), np.vstack(Z)
    p = RETARDOS_BK
    T = len(Xe[0])  # 43 años, 1977-2019
    def r(serie, k):  # retardo k sobre la muestra t = p..T-1
        return [s[p - k:T - k] for s in serie]
    regs_e = [r(Xe, 1), r(Xe, 2), r(Xl, 1), r(Xl, 2), r(Xp, 1), r(Xp, 2)]
    regs_lp = [r(Xe, 0), r(Xe, 1), r(Xe, 2), r(Xl, 1), r(Xl, 2), r(Xp, 1), r(Xp, 2)]
    ye, Ze = apilar(r(Xe, 0), regs_e)
    yl, Zl = apilar(r(Xl, 0), regs_lp)
    yp, Zp = apilar(r(Xp, 0), regs_lp)
    be = np.linalg.lstsq(Ze, ye, rcond=None)[0]
    bl = np.linalg.lstsq(Zl, yl, rcond=None)[0]
    bp = np.linalg.lstsq(Zp, yp, rcond=None)[0]
    # respuestas a una caída del 1 % del empleo relativo
    H = HORIZONTE
    de, le, lp = np.zeros(H + 1 + p), np.zeros(H + 1 + p), np.zeros(H + 1 + p)
    for h in range(H + 1):
        t = h + p
        de[t] = (-1.0 if h == 0 else 0.0) + be @ [de[t - 1], de[t - 2], le[t - 1], le[t - 2], lp[t - 1], lp[t - 2]]
        le[t] = bl @ [de[t], de[t - 1], de[t - 2], le[t - 1], le[t - 2], lp[t - 1], lp[t - 2]]
        lp[t] = bp @ [de[t], de[t - 1], de[t - 2], le[t - 1], le[t - 2], lp[t - 1], lp[t - 2]]
    de, le, lp = de[p:], le[p:], lp[p:]
    empleo = np.cumsum(de)
    paro = -le          # puntos de la tasa de paro (aproximación de 100 x log(1 - u))
    actividad = lp      # 100 x log de la tasa de actividad
    poblacion = empleo - le - lp  # 100 x log de la población en edad de trabajar: migración
    for h in range(H + 1):
        for nombre, v in (("empleo", empleo[h]), ("tasa de paro", paro[h]), ("tasa de actividad", actividad[h]), ("población en edad de trabajar", poblacion[h])):
            series.append(("Respuesta de " + nombre + " a una caída del 1 % del empleo relativo", "Estados de EE. UU. (agrupados)", h, float(v),
                           "100 x log o puntos", "estimación propia", "VAR agrupado de BLANCHARD y KATZ, 2 retardos, 1979-2019", "anx2_bk"))
    pico = int(np.argmax(paro))
    vida = next((h for h in range(pico, H + 1) if paro[h] <= paro[pico] / 2), None)
    p_media = float(np.mean([p_us[a] for a in anios]))
    act_pp = actividad * p_media / 100
    minimo = int(np.argmin(act_pp))
    for nombre, v in (("Empleo relativo, mínimo (porcentaje)", float(np.min(empleo))), ("Año del mínimo del empleo", int(np.argmin(empleo))),
                      ("Empleo relativo a los 10 años (porcentaje)", empleo[H]), ("Tasa de paro en el impacto (puntos)", paro[0]), ("Tasa de paro máxima (puntos)", paro[pico]),
                      ("Año del máximo de la tasa de paro", pico), ("Años hasta que el paro cae a la mitad de su máximo", vida),
                      ("Tasa de paro a los 5 años (puntos)", paro[5]), ("Tasa de paro a los 10 años (puntos)", paro[H]),
                      ("Tasa de actividad en el impacto (puntos)", act_pp[0]), ("Tasa de actividad, mínimo (puntos)", act_pp[minimo]), ("Año del mínimo de la tasa de actividad", minimo),
                      ("Tasa de actividad a los 10 años (puntos)", act_pp[H]),
                      ("Población en edad de trabajar en el impacto (porcentaje)", poblacion[0]), ("Población en edad de trabajar a los 5 años (porcentaje)", poblacion[5]),
                      ("Población en edad de trabajar a los 10 años (porcentaje)", poblacion[H]),
                      ("Parte del ajuste del empleo hecha por migración a los 10 años", poblacion[H] / empleo[H]), ("Tasa de actividad media de EE. UU., 1976-2019", p_media)):
        cifras.append(("BLANCHARD y KATZ, réplica propia: " + nombre, None if v is None else round(float(v), 3), "puntos, porcentaje o años", "II.2.1"))
    return empleo, paro, actividad, poblacion, p_media


def dispersion(carpeta, series, cifras):
    desde, hasta = 1991, 2024
    wb = leer_wb(carpeta, WB_PARO)
    ue = {p: wb[p] for p in EURO}
    us = {st: leer_fred_anual(carpeta, st + "UR", desde, hasta) for st in ESTADOS}
    anios = list(range(desde, hasta + 1))
    for p in EURO:
        for a in anios:
            series.append(("Tasa de paro (estimación armonizada de la OIT)", NOMBRE[p], a, ue[p][a], "porcentaje de la población activa", "Banco Mundial " + WB_PARO, "nivel", "anx2_dispersion"))
    disp_ea = [float(np.std([ue[p][a] for p in EURO])) for a in anios]
    disp_us = [float(np.std([us[st][a] for st in ESTADOS])) for a in anios]
    for a, x, y in zip(anios, disp_ea, disp_us):
        series.append(("Desviación típica de la tasa de paro entre países", "Zona del euro (11)", a, x, "puntos", "Banco Mundial " + WB_PARO, "desviación típica sin ponderar", "anx2_dispersion"))
        series.append(("Desviación típica de la tasa de paro entre estados", "EE. UU. (51)", a, y, "puntos", "FRED {ST}UR", "desviación típica sin ponderar", "anx2_dispersion"))
    def persistencia(datos, unidades):
        X, Y = [], []
        for u in unidades:
            dev = np.array([datos[u][a] - np.mean([datos[v][a] for v in unidades]) for a in anios])
            x, y = dev[:-1] - dev[:-1].mean(), dev[1:] - dev[1:].mean()
            X.append(x); Y.append(y)
        X, Y = np.concatenate(X), np.concatenate(Y)
        rho = float(X @ Y / (X @ X))
        return rho, math.log(0.5) / math.log(rho)
    r_ea, v_ea = persistencia(ue, EURO)
    r_us, v_us = persistencia(us, list(ESTADOS))
    for nombre, v in (("Desviación típica entre países de la zona, 2007", disp_ea[anios.index(2007)]), ("Desviación típica entre países de la zona, 2013", disp_ea[anios.index(2013)]),
                      ("Desviación típica entre países de la zona, 2024", disp_ea[-1]), ("Desviación típica entre estados de EE. UU., 2007", disp_us[anios.index(2007)]),
                      ("Desviación típica entre estados de EE. UU., 2010", disp_us[anios.index(2010)]), ("Desviación típica entre estados de EE. UU., 2024", disp_us[-1]),
                      ("Persistencia anual del paro relativo, zona del euro", r_ea), ("Vida media del paro relativo, zona del euro (años)", v_ea),
                      ("Persistencia anual del paro relativo, EE. UU.", r_us), ("Vida media del paro relativo, EE. UU. (años)", v_us)):
        cifras.append((nombre + ", 1991-2024", round(v, 2), "puntos, coeficiente o años", "II.2.2"))
    return anios, disp_ea, disp_us


# ---------------------------------------------------------------- II.3 reparto del riesgo (A8)
def reparto(carpeta, series, cifras):
    """Descomposición de ASDRUBALI, SØRENSEN y YOSHA (1996) para los once miembros: PIB -> renta nacional bruta (B5G)
    -> renta nacional disponible bruta (B6G) -> consumo final (P3), en términos reales por habitante (deflactor del PIB
    y población del Banco Mundial). Coeficientes de MCO agrupados con efectos fijos de año; suman uno."""
    ruta = os.path.join(carpeta, "cuentas.json")
    defl = {p: leer_eurostat_anual(os.path.join(carpeta, "deflactor.json"), geo=ISO2[p], unit="PD15_EUR", na_item="B1GQ", freq="A") for p in EURO}
    pob = leer_wb(carpeta, "SP.POP.TOTL")
    datos = {}
    for p in EURO:
        for n in ("B1GQ", "B5G", "B6G", "P3"):
            datos[(p, n)] = leer_eurostat_anual(ruta, geo=ISO2[p], na_item=n, unit="CP_MEUR", sector="S1", direct="PAID", freq="A")
    anios = list(range(1995, 2020))
    nombres = {"B1GQ": "PIB", "B5G": "Renta nacional bruta", "B6G": "Renta nacional disponible bruta", "P3": "Consumo final"}
    reales = {}
    for p in EURO:
        for n in ("B1GQ", "B5G", "B6G", "P3"):
            v = [datos[(p, n)][a] / (defl[p][a] / 100) / pob[p][a] * 1e6 for a in anios]
            reales[(p, n)] = np.array(v)
            for a, x in zip(anios, v):
                series.append((nombres[n] + " real por habitante", NOMBRE[p], a, x, "euros de 2015 por habitante", "Eurostat nasa_10_nf_tr y nama_10_gdp; Banco Mundial SP.POP.TOTL",
                               "precios corrientes / deflactor del PIB / población", "anx2_reparto"))
    def coeficientes(paises, a0, a1):
        i0, i1 = anios.index(a0), anios.index(a1)  # diferencias de a0 a a1 (a0 es el primer año con diferencia)
        d = {}
        for p in paises:
            for n in ("B1GQ", "B5G", "B6G", "P3"):
                d[(p, n)] = 100 * np.diff(np.log(reales[(p, n)]))[i0 - 1:i1]
        comp = {"K": lambda p: d[(p, "B1GQ")] - d[(p, "B5G")], "F": lambda p: d[(p, "B5G")] - d[(p, "B6G")],
                "C": lambda p: d[(p, "B6G")] - d[(p, "P3")], "U": lambda p: d[(p, "P3")]}
        X = np.array([d[(p, "B1GQ")] for p in paises]); X = X - X.mean(axis=0)  # efectos fijos de año
        res = {}
        for k, f in comp.items():
            Y = np.array([f(p) for p in paises]); Y = Y - Y.mean(axis=0)
            res[k] = float((X * Y).sum() / (X * X).sum())
        return res
    resultados = {}
    sin_irlanda = [p for p in EURO if p != "IRL"]
    for etiqueta, paises, a0, a1 in (("1996-2019, once países", EURO, 1996, 2019), ("1996-2019, sin Irlanda", sin_irlanda, 1996, 2019),
                                     ("1999-2008, sin Irlanda", sin_irlanda, 1999, 2008), ("2009-2019, sin Irlanda", sin_irlanda, 2009, 2019)):
        r = coeficientes(paises, a0, a1)
        resultados[etiqueta] = r
        for k, nom in (("K", "mercados de capitales"), ("F", "transferencias internacionales"), ("C", "crédito y ahorro"), ("U", "sin alisar")):
            cifras.append(("Reparto del riesgo, %s: %s" % (etiqueta, nom), round(100 * r[k], 1), "porcentaje de la perturbación del PIB", "II.3.2"))
    return resultados


# ---------------------------------------------------------------- II.4 precios y crecimiento (A8)
def precios(carpeta, series, cifras):
    pli = {p: leer_eurostat_anual(os.path.join(carpeta, "precios.json"), geo=ISO2[p], na_item="PLI_EU27_2020", ppp_cat="A01", freq="A") for p in EURO}
    anios = list(range(1995, 2025))
    for p in EURO:
        for a in anios:
            series.append(("Nivel de precios del consumo individual efectivo", NOMBRE[p], a, pli[p][a], "índice, UE-27 = 100", "Eurostat prc_ppp_ind (A01)", "nivel", "anx2_precios"))
    cv, cv_sin = [], []
    for a in anios:
        v = np.array([pli[p][a] for p in EURO])
        w = np.array([pli[p][a] for p in EURO if p != "IRL"])
        cv.append(float(100 * v.std() / v.mean())); cv_sin.append(float(100 * w.std() / w.mean()))
        series.append(("Coeficiente de variación de los niveles de precios", "Zona del euro (11)", a, cv[-1], "porcentaje", "Eurostat prc_ppp_ind (A01)", "desviación típica / media, sin ponderar", "anx2_precios"))
        series.append(("Coeficiente de variación de los niveles de precios", "Zona del euro sin Irlanda (10)", a, cv_sin[-1], "porcentaje", "Eurostat prc_ppp_ind (A01)", "desviación típica / media, sin ponderar", "anx2_precios"))
    for a in (1995, 1999, 2008, 2013, 2024):
        cifras.append(("Coeficiente de variación de los niveles de precios del consumo, zona del euro, %d" % a, round(cv[anios.index(a)], 1), "porcentaje", "II.4.2"))
        cifras.append(("Coeficiente de variación de los niveles de precios del consumo, sin Irlanda, %d" % a, round(cv_sin[anios.index(a)], 1), "porcentaje", "II.4.2"))
    for p in ("PRT", "GRC", "ESP", "IRL", "DEU", "FRA", "ITA", "NLD", "BEL", "AUT", "FIN"):
        cifras.append(("Nivel de precios del consumo, 1995, 1999 y 2024 (UE-27 = 100), " + NOMBRE[p], "%.0f, %.0f y %.0f" % (pli[p][1995], pli[p][1999], pli[p][2024]), "índice", "II.4.2"))
    return anios, cv, cv_sin


def crecimiento(carpeta, series, cifras):
    kd = leer_wb(carpeta, "NY.GDP.MKTP.KD")
    pob = leer_wb(carpeta, "SP.POP.TOTL")
    pc = leer_wb(carpeta, "NY.GDP.PCAP.KD")
    anios = list(range(1995, 2025))
    def agregado(grupo):
        return [sum(kd[p][a] for p in grupo) / sum(pob[p][a] for p in grupo) for a in anios]
    curvas = {"Zona del euro (once países)": agregado(EURO), "Estados Unidos": [pc["USA"][a] for a in anios],
              "Reino Unido, Suecia y Dinamarca": agregado(FUERA)}
    base = anios.index(1999)
    indices = {k: [100 * x / v[base] for x in v] for k, v in curvas.items()}
    for k, v in indices.items():
        for a, x in zip(anios, v):
            series.append(("PIB real por habitante, índice 1999 = 100", k, a, x, "índice", "Banco Mundial NY.GDP.MKTP.KD, SP.POP.TOTL y NY.GDP.PCAP.KD", "agregado = suma del PIB / suma de la población", "anx2_crecimiento"))
        for a in (2008, 2019, 2024):
            cifras.append(("PIB real por habitante, %d (1999 = 100), %s" % (a, k), round(v[anios.index(a)], 1), "índice", "II.4.3"))
    for p in EURO + FUERA:
        g = 100 * (kd[p][2019] / pob[p][2019]) / (kd[p][1999] / pob[p][1999]) - 100
        cifras.append(("Crecimiento acumulado del PIB real por habitante, 1999-2019, " + NOMBRE[p], round(g, 1), "porcentaje", "II.4.3"))
    return anios, indices


# ---------------------------------------------------------------- II.5 credibilidad y tipos (A9)
def leer_fred_mensual(carpeta, serie):  # {(año, mes): valor}
    salida = {}
    with open(os.path.join(carpeta, serie + ".csv"), encoding="utf-8") as f:
        lector = csv.reader(f)
        next(lector)
        for fecha, valor in lector:
            if valor not in (".", ""):
                salida[(int(fecha[:4]), int(fecha[5:7]))] = float(valor)
    return salida


def meses(desde, hasta):
    a, m = desde
    while (a, m) <= hasta:
        yield (a, m)
        a, m = (a + 1, 1) if m == 12 else (a, m + 1)


def credibilidad(carpeta, series, cifras):
    tipos = {p: leer_fred_mensual(carpeta, TIPOS_10[p]) for p in EURO}
    dif = {p: {k: v - tipos["DEU"][k] for k, v in tipos[p].items() if k in tipos["DEU"]} for p in EURO if p != "DEU"}
    for p in dif:
        for (a, m), v in sorted(dif[p].items()):
            if a >= 1993:
                series.append(("Diferencial de la deuda a diez años frente a Alemania", NOMBRE[p], "%d-%02d" % (a, m), v, "puntos porcentuales", "FRED " + TIPOS_10[p] + " menos " + TIPOS_10["DEU"] + " (OCDE)", "diferencia de tipos mensuales", "anx2_diferenciales"))
    def media(p, a):
        v = [dif[p][(a, m)] for m in range(1, 13) if (a, m) in dif[p]]
        return sum(v) / len(v) if len(v) == 12 else None
    for p in dif:
        for a in (1995, 1998, 2007):
            x = media(p, a)
            if x is not None:
                cifras.append(("Diferencial medio frente a Alemania, %d, %s" % (a, NOMBRE[p]), round(x, 2), "puntos", "II.5.1"))
        crisis = {k: v for k, v in dif[p].items() if 2009 <= k[0] <= 2013}
        k = max(crisis, key=crisis.get)
        cifras.append(("Diferencial máximo frente a Alemania, 2009-2013, %s (%d-%02d)" % (NOMBRE[p], k[0], k[1]), round(crisis[k], 2), "puntos", "II.5.1"))
        for k in ((2012, 7), (2012, 12), (2013, 12), (2019, 12), (2026, 8)):
            if k in dif[p]:
                cifras.append(("Diferencial frente a Alemania, %d-%02d, %s" % (k[0], k[1], NOMBRE[p]), round(dif[p][k], 2), "puntos", "II.5.1"))
    infl = leer_wb(carpeta, "FP.CPI.TOTL.ZG")
    tabla = {}
    for c, (nombre, regimen, a0) in RIGIDOS.items():
        fila = [infl[c].get(a) for a in (a0 - 1, a0, a0 + 2, a0 + 5)]
        tabla[c] = fila
        cifras.append(("Inflación con %s (%d), %s: año anterior, año de adopción, dos y cinco años después" % (regimen, a0, nombre),
                       ", ".join("n. d." if x is None else "%.1f" % x for x in fila), "porcentaje", "II.5.2"))
        for a in range(a0 - 3, a0 + 6):
            if a in infl[c]:
                series.append(("Inflación de los precios de consumo", nombre, a, infl[c][a], "porcentaje", "Banco Mundial FP.CPI.TOTL.ZG", "tasa anual", "cuadro de II.5.2"))
    return dif, tabla


# ---------------------------------------------------------------- II.6 desequilibrios y fragilidad (A9)
def desequilibrios(carpeta, series, cifras):
    # tipos reales: euríbor a tres meses (media anual) menos la inflación de cada país, 1999-2007
    eur = leer_fred_mensual(carpeta, "IR3TIB01EZM156N")
    infl = leer_wb(carpeta, "FP.CPI.TOTL.ZG")
    euribor = {a: sum(eur[(a, m)] for m in range(1, 13)) / 12 for a in range(1999, 2008)}
    reales = {p: float(np.mean([euribor[a] - infl[p][a] for a in range(1999, 2008)])) for p in EURO}
    for p in EURO:
        cifras.append(("Tipo de interés real a corto plazo medio, 1999-2007, " + NOMBRE[p], round(reales[p], 2), "porcentaje", "II.6.1"))
        for a in range(1999, 2008):
            series.append(("Tipo real a corto plazo (euríbor a tres meses menos inflación)", NOMBRE[p], a, euribor[a] - infl[p][a], "porcentaje", "FRED IR3TIB01EZM156N y Banco Mundial FP.CPI.TOTL.ZG", "media anual del tipo menos inflación anual", "anx2_tipos_reales"))
    # costes laborales unitarios nominales relativos a la media geométrica de los once, 1999 = 100
    clu = {p: leer_eurostat_anual(os.path.join(carpeta, "clu.json"), geo=ISO2[p], unit="I15", na_item="NULC_PER", freq="A") for p in EURO}
    anios = list(range(1995, 2025))
    media = {a: math.exp(np.mean([math.log(clu[p][a]) for p in EURO])) for a in anios}
    rel = {p: [100 * (clu[p][a] / media[a]) / (clu[p][1999] / media[1999]) for a in anios] for p in EURO}
    for p in EURO:
        for a, x in zip(anios, rel[p]):
            series.append(("Coste laboral unitario nominal relativo a la media de la zona", NOMBRE[p], a, x, "índice, 1999 = 100", "Eurostat nama_10_lp_ulc (NULC_PER, I15)", "cociente con la media geométrica de los once", "anx2_clu_real"))
        maximo = max(range(len(anios)), key=lambda i: rel[p][i]) if p != "DEU" else min(range(len(anios)), key=lambda i: rel[p][i])
        cifras.append(("CLU relativo, 2008, extremo 1999-2024 y 2024 (1999 = 100), %s" % NOMBRE[p], "%.1f; %.1f en %d; %.1f" % (rel[p][anios.index(2008)], rel[p][maximo], anios[maximo], rel[p][-1]), "índice", "II.6.2"))
    # cuenta corriente
    cc = leer_wb(carpeta, "BN.CAB.XOKA.GD.ZS")
    for p in EURO:
        for a in range(1995, 2025):
            if a in cc[p]:
                series.append(("Saldo por cuenta corriente", NOMBRE[p], a, cc[p][a], "porcentaje del PIB", "Banco Mundial BN.CAB.XOKA.GD.ZS", "nivel", "anx2_cuenta_corriente"))
        for a in (1999, 2007, 2008, 2013, 2019, 2024):
            if a in cc[p]:
                cifras.append(("Saldo por cuenta corriente, %d, %s" % (a, NOMBRE[p]), round(cc[p][a], 1), "porcentaje del PIB", "II.6.2"))
    # saldos TARGET (fin de mes, millones de euros)
    tgb = {}
    for c in TARGET:
        with open(os.path.join(carpeta, "tgb_" + c + ".csv"), encoding="utf-8") as f:
            lector = csv.DictReader(f)
            tgb[c] = {(int(r["TIME_PERIOD"][:4]), int(r["TIME_PERIOD"][5:7])): float(r["OBS_VALUE"]) / 1000 for r in lector if r["OBS_VALUE"]}
        for (a, m), v in sorted(tgb[c].items()):
            series.append(("Saldo TARGET a fin de mes", c, "%d-%02d" % (a, m), v, "miles de millones de euros", "BCE, TGB.M." + c + ".N.A094T.U2.EUR.E", "nivel", "anx2_target"))
        for k in ((2008, 6), (2012, 8), (2014, 12), (2022, 8)):
            if k in tgb[c]:
                cifras.append(("Saldo TARGET, %d-%02d, %s" % (k[0], k[1], c), round(tgb[c][k], 0), "miles de millones de euros", "II.6.3"))
        ultimo = max(tgb[c])
        cifras.append(("Saldo TARGET, último dato (%d-%02d), %s" % (ultimo[0], ultimo[1], c), round(tgb[c][ultimo], 0), "miles de millones de euros", "II.6.3"))
    # inflación armonizada de España y de la zona, tasa interanual mensual, y su diferencia
    es, ea = leer_fred_mensual(carpeta, "CP0000ESM086NEST"), leer_fred_mensual(carpeta, "CP0000EZCCM086NEST")
    difi = {}
    for k in sorted(es):
        k0 = (k[0] - 1, k[1])
        if k0 in es and k in ea and k0 in ea:
            pe, pa = 100 * (es[k] / es[k0] - 1), 100 * (ea[k] / ea[k0] - 1)
            difi[k] = (pe, pa, pe - pa)
            series.append(("Inflación armonizada interanual y diferencial", "España - zona del euro", "%d-%02d" % k, pe - pa, "puntos", "FRED CP0000ESM086NEST y CP0000EZCCM086NEST (Eurostat)", "tasa interanual de España menos la de la zona", "anx2_inflacion_espana"))
    def media_dif(a0, a1):
        v = [d[2] for k, d in difi.items() if a0 <= k[0] <= a1]
        return sum(v) / len(v)
    for a0, a1 in ((1999, 2007), (2009, 2016), (2017, 2019), (2021, 2024)):
        cifras.append(("Diferencial de inflación de España con la zona, media %d-%d" % (a0, a1), round(media_dif(a0, a1), 2), "puntos", "II.6.4"))
    for k in ((2026, 4), max(difi)):
        cifras.append(("Inflación de España y de la zona y diferencial, %d-%02d" % k, "%.1f; %.1f; %.1f" % difi[k], "porcentaje y puntos", "II.6.4"))
    return reales, (anios, rel), cc, tgb, difi


# ---------------------------------------------------------------- figuras (TikZ simple, escala de grises, \footnotesize)
def num(x, dec=1):  # cifra con coma decimal en modo matemático
    s = ("%." + str(dec) + "f") % x
    return "$" + s.replace("-", "-").replace(".", "{,}") + "$"


def escribir(nombre, cuerpo, comentario):
    texto = ("% " + nombre + ": " + comentario + "\n% Generada por Code/libro_y_figuras.py; PDF con: bash Code/generar_figura.sh "
             + nombre + "\n\\begin{tikzpicture}[font=\\footnotesize, >={Stealth[length=2mm]}]\n" + cuerpo + "\\end{tikzpicture}\n")
    with open(os.path.join(IMG, nombre + ".tikz"), "w", encoding="utf-8") as f:
        f.write(texto)


def eje_x(x0, x1, ticks, esc, etiqueta, y=0.0, dec=1, desde=0.0):
    c = "  \\draw[->] (%.3f,%.3f) -- (%.3f,%.3f);\n" % (x0, y, x1, y)
    for t in ticks:
        x = (t - desde) * esc
        c += "  \\draw (%.3f,%.3f) -- (%.3f,%.3f) node[below] {%s};\n" % (x, y + 0.06, x, y - 0.06, num(t, dec) if dec >= 0 else "$%d$" % t)
    c += "  \\node[below=12pt] at (%.3f,%.3f) {%s};\n" % ((x0 + x1) / 2, y, etiqueta)
    return c


def fig_correlaciones(res):
    orden = sorted(EURO, key=lambda p: -res[p][1]) + sorted(FUERA, key=lambda p: -res[p][1])
    esc, dy, c = 9.0, 0.42, ""
    ys = {}
    for i, p in enumerate(orden):
        ys[p] = -(i * dy + (0.35 if p in FUERA else 0.0))
    fondo = min(ys.values()) - 0.45
    for t in [0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        c += "  \\draw[black!12] (%.3f,0.3) -- (%.3f,%.3f);\n" % (t * esc, t * esc, fondo)
    for p in orden:
        y = ys[p]; a, b = res[p][0] * esc, res[p][1] * esc
        c += "  \\node[anchor=east] at (-0.15,%.3f) {%s};\n" % (y, NOMBRE[p])
        c += "  \\draw[black!45, thick] (%.3f,%.3f) -- (%.3f,%.3f);\n" % (a, y, b, y)
        c += "  \\draw[black!80, fill=white] (%.3f,%.3f) circle (2.1pt);\n" % (a, y)
        c += "  \\fill[black!85] (%.3f,%.3f) circle (2.1pt);\n" % (b, y)
    ye = ys[orden[len(EURO) - 1]]; yf = ys[orden[len(EURO)]]
    c += "  \\draw[black!40, densely dashed] (-2.6,%.3f) -- (%.3f,%.3f);\n" % ((ye + yf) / 2, esc, (ye + yf) / 2)
    c += "  \\node[anchor=west, black!60] at (%.3f,%.3f) {zona del euro};\n" % (esc + 0.1, ys[orden[0]])
    c += "  \\node[anchor=west, black!60] at (%.3f,%.3f) {fuera de la zona};\n" % (esc + 0.1, yf)
    c += eje_x(0, esc + 0.3, [0, 0.2, 0.4, 0.6, 0.8, 1.0], esc, "correlación del ciclo con el resto de la zona del euro", y=fondo)
    c += "  \\draw[black!80, fill=white] (1.2,0.75) circle (2.1pt) node[right=3pt, black] {$1971$-$1998$};\n"
    c += "  \\fill[black!85] (4.2,0.75) circle (2.1pt) node[right=3pt, black] {$1999$-$2019$};\n"
    escribir("anx2_correlaciones", c, "correlación del ciclo (HP, lambda 6,25) de cada país con el resto de la zona del euro, 1971-1998 y 1999-2019 (anexo II.1.1)")


def dispersion_puntos(puntos, desp, esc_x, esc_y, x0, y0):
    c = ""
    for p, (x, y) in puntos.items():
        X, Y = (x - x0) * esc_x, (y - y0) * esc_y
        c += "  \\fill[black!85] (%.3f,%.3f) circle (1.9pt);\n" % (X, Y)
        pos = desp.get(p, "above right")
        c += "  \\node[%s=1pt, font=\\scriptsize] at (%.3f,%.3f) {%s};\n" % (pos, X, Y, ISO2[p])
    return c


DESP_BE1 = {"AUT": "above left", "ITA": "above right", "PRT": "below", "NLD": "above"}
DESP_BE2 = {"BEL": "above left", "SWE": "above", "ESP": "below right", "GBR": "left", "NLD": "above right"}


def fig_amplitud(res):
    x0, x1, y0, y1 = 0.0, 1.0, 0.0, 3.2
    ex, ey = 10.0, 1.9
    c = "  \\draw[black!40, densely dashed] (0,%.3f) -- (%.3f,%.3f);\n" % ((1 - y0) * ey, (x1 - x0) * ex, (1 - y0) * ey)
    c += "  \\node[above right, black!60, font=\\scriptsize] at (0.05,%.3f) {amplitud igual a la de la zona};\n" % ((1 - y0) * ey)
    fuera = {p: (res[p][1], res[p][2]) for p in EURO + FUERA if res[p][1] < 0.85}
    c += dispersion_puntos(fuera, {}, ex, ey, x0, y0)
    # los países con correlación alta forman un grupo apretado: sus etiquetas van en una columna a la derecha, con guías
    grupo = sorted([p for p in EURO + FUERA if res[p][1] >= 0.85], key=lambda p: -res[p][2])
    centro = np.mean([res[p][2] * ey for p in grupo]); paso = 0.36
    for i, p in enumerate(grupo):
        X, Y = res[p][1] * ex, res[p][2] * ey
        yl = centro + paso * (len(grupo) - 1) / 2 - i * paso
        c += "  \\draw[black!35] (%.3f,%.3f) -- (%.3f,%.3f);\n" % (X, Y, 10.45, yl)
        c += "  \\fill[black!85] (%.3f,%.3f) circle (1.9pt);\n" % (X, Y)
        c += "  \\node[anchor=west, font=\\scriptsize] at (%.3f,%.3f) {%s};\n" % (10.45, yl, ISO2[p])
    c += eje_x(0, (x1 - x0) * ex + 0.3, [0, 0.2, 0.4, 0.6, 0.8, 1.0], ex, "correlación del ciclo con el resto de la zona, $1999$-$2019$")
    c += "  \\draw[->] (0,0) -- (0,%.3f) node[above] {amplitud relativa del ciclo};\n" % ((y1 - y0) * ey + 0.2)
    for t in [0, 1, 2, 3]:
        c += "  \\draw (0.06,%.3f) -- (-0.06,%.3f) node[left] {$%d$};\n" % ((t - y0) * ey, (t - y0) * ey, t)
    escribir("anx2_amplitud", c, "correlación del ciclo con el resto de la zona y amplitud relativa (desviación típica del ciclo del país entre la de la zona), 1999-2019 (anexo II.1.2)")


def fig_bayoumi(corr_be):
    x0, x1, y0, y1 = -0.2, 0.9, -0.1, 0.7
    ex, ey = 5.6, 5.6
    c = ""
    for k, (titulo, desp, dx) in enumerate(((r"(a) $1973$-$1998$", DESP_BE1, 0.0), (r"(b) $1999$-$2019$", DESP_BE2, 7.9))):
        c += "  \\begin{scope}[xshift=%.2fcm]\n" % dx
        c += "  \\node[anchor=base] at (%.3f,%.3f) {%s};\n" % ((x1 - x0) * ex / 2, (y1 - y0) * ey + 0.55, titulo)
        c += "  \\draw[black!25] (%.3f,0) -- (%.3f,%.3f);\n" % ((0 - x0) * ex, (0 - x0) * ex, (y1 - y0) * ey)
        c += "  \\draw[black!25] (0,%.3f) -- (%.3f,%.3f);\n" % ((0 - y0) * ey, (x1 - x0) * ex, (0 - y0) * ey)
        pts = {p: (v[0], v[1]) if k == 0 else (v[2], v[3]) for p, v in corr_be.items()}
        c += dispersion_puntos(pts, desp, ex, ey, x0, y0)
        c += "  \\draw[->] (0,0) -- (%.3f,0);\n" % ((x1 - x0) * ex + 0.2)
        for t in [-0.2, 0, 0.2, 0.4, 0.6, 0.8]:
            c += "  \\draw (%.3f,0.06) -- (%.3f,-0.06) node[below] {%s};\n" % ((t - x0) * ex, (t - x0) * ex, num(t))
        c += "  \\node[below=12pt] at (%.3f,0) {perturbaciones de oferta};\n" % ((x1 - x0) * ex / 2)
        c += "  \\draw[->] (0,0) -- (0,%.3f);\n" % ((y1 - y0) * ey + 0.2)
        for t in [0, 0.2, 0.4, 0.6]:
            c += "  \\draw (0.06,%.3f) -- (-0.06,%.3f) node[left] {%s};\n" % ((t - y0) * ey, (t - y0) * ey, num(t))
        c += "  \\node[rotate=90] at (-1.05,%.3f) {perturbaciones de demanda};\n" % ((y1 - y0) * ey / 2)
        c += "  \\end{scope}\n"
    escribir("anx2_bayoumi", c, "correlación con Alemania de las perturbaciones de oferta y de demanda identificadas a la manera de BAYOUMI y EICHENGREEN (1993), 1973-1998 y 1999-2019 (anexo II.1.3)")


def fig_krugman(krug):
    orden = sorted(EURO, key=lambda p: -krug[p][2023])
    esc, dy, c = 13.0, 0.42, ""
    ys = {p: -i * dy for i, p in enumerate(orden)}
    fondo = min(ys.values()) - 0.45
    for t in [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]:
        c += "  \\draw[black!12] (%.3f,0.3) -- (%.3f,%.3f);\n" % (t * esc, t * esc, fondo)
    for p in orden:
        y = ys[p]; a, b = krug[p][1995] * esc, krug[p][2023] * esc
        c += "  \\node[anchor=east] at (-0.15,%.3f) {%s};\n" % (y, NOMBRE[p])
        c += "  \\draw[black!45, thick] (%.3f,%.3f) -- (%.3f,%.3f);\n" % (a, y, b, y)
        c += "  \\draw[black!80, fill=white] (%.3f,%.3f) circle (2.1pt);\n" % (a, y)
        c += "  \\fill[black!85] (%.3f,%.3f) circle (2.1pt);\n" % (b, y)
    c += eje_x(0, 0.6 * esc + 0.3, [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6], esc, "índice de especialización de KRUGMAN frente al resto de la zona", y=fondo)
    c += "  \\draw[black!80, fill=white] (1.2,0.75) circle (2.1pt) node[right=3pt, black] {$1995$};\n"
    c += "  \\fill[black!85] (3.4,0.75) circle (2.1pt) node[right=3pt, black] {$2023$};\n"
    escribir("anx2_krugman", c, "índice de especialización de KRUGMAN (suma de las diferencias absolutas de cuotas de valor añadido en once ramas) de cada país frente al resto de la zona, 1995 y 2023 (anexo II.1.4)")


def linea(xs, ys, ex, ey, x0, y0, estilo):
    return "  \\draw[%s] %s;\n" % (estilo, " -- ".join("(%.3f,%.3f)" % ((x - x0) * ex, (y - y0) * ey) for x, y in zip(xs, ys)))


def fig_bk(bk):
    empleo, paro, actividad, poblacion = bk[:4]
    actividad = actividad * bk[4] / 100  # de 100 x log de la tasa de actividad a puntos de la tasa, con la tasa media nacional
    h = list(range(HORIZONTE + 1))
    c = ""
    # (a) niveles: empleo y población en edad de trabajar
    ex, ey, y0 = 0.56, 1.85, -2.5
    fin = 10 * ex
    c += "  \\node[anchor=base] at (%.3f,%.3f) {(a) Empleo y población};\n" % (fin / 2, (0.2 - y0) * ey + 0.45)
    c += "  \\draw[black!30] (0,%.3f) -- (%.3f,%.3f);\n" % ((0 - y0) * ey, fin, (0 - y0) * ey)
    c += linea(h, empleo, ex, ey, 0, y0, "black!85, thick")
    c += linea(h, poblacion, ex, ey, 0, y0, "black!55, thick, dashed")
    c += "  \\node[anchor=west, font=\\scriptsize] at (%.3f,%.3f) {empleo};\n" % (fin + 0.1, (empleo[-1] - y0) * ey - 0.12)
    c += "  \\node[anchor=west, font=\\scriptsize, black!70] at (%.3f,%.3f) {población};\n" % (fin + 0.1, (poblacion[-1] - y0) * ey + 0.12)
    c += "  \\draw[->] (0,0) -- (%.3f,0);\n  \\draw[->] (0,0) -- (0,%.3f);\n" % (fin + 0.3, (0.2 - y0) * ey + 0.2)
    for t in [0, 2, 4, 6, 8, 10]:
        c += "  \\draw (%.3f,0.06) -- (%.3f,-0.06) node[below] {$%d$};\n" % (t * ex, t * ex, t)
    c += "  \\node[below=12pt] at (%.3f,0) {años};\n" % (fin / 2)
    for t in [-2, -1.5, -1, -0.5, 0]:
        c += "  \\draw (0.06,%.3f) -- (-0.06,%.3f) node[left] {%s};\n" % ((t - y0) * ey, (t - y0) * ey, num(t))
    c += "  \\node[rotate=90] at (-1.15,%.3f) {desviación, en porcentaje};\n" % ((0.2 - y0) * ey / 2)
    # (b) tasas: paro y actividad
    dx, ey2, yb = 8.3, 6.25, -0.4
    c += "  \\begin{scope}[xshift=%.2fcm]\n" % dx
    c += "  \\node[anchor=base] at (%.3f,%.3f) {(b) Tasas de paro y de actividad};\n" % (fin / 2, (0.4 - yb) * ey2 + 0.45)
    c += "  \\draw[black!30] (0,%.3f) -- (%.3f,%.3f);\n" % ((0 - yb) * ey2, fin, (0 - yb) * ey2)
    c += linea(h, paro, ex, ey2, 0, yb, "black!85, thick")
    c += linea(h, actividad, ex, ey2, 0, yb, "black!55, thick, dashed")
    c += "  \\node[anchor=south west, font=\\scriptsize] at (%.3f,%.3f) {tasa de paro};\n" % (1 * ex + 0.05, (paro[1] - yb) * ey2 + 0.02)
    c += "  \\node[anchor=north west, font=\\scriptsize, black!70] at (%.3f,%.3f) {tasa de actividad};\n" % (4 * ex, (actividad[4] - yb) * ey2 - 0.05)
    c += "  \\draw[->] (0,0) -- (%.3f,0);\n  \\draw[->] (0,0) -- (0,%.3f);\n" % (fin + 0.3, (0.4 - yb) * ey2 + 0.2)
    for t in [0, 2, 4, 6, 8, 10]:
        c += "  \\draw (%.3f,0.06) -- (%.3f,-0.06) node[below] {$%d$};\n" % (t * ex, t * ex, t)
    c += "  \\node[below=12pt] at (%.3f,0) {años};\n" % (fin / 2)
    for t in [-0.4, -0.2, 0, 0.2, 0.4]:
        c += "  \\draw (0.06,%.3f) -- (-0.06,%.3f) node[left] {%s};\n" % ((t - yb) * ey2, (t - yb) * ey2, num(t))
    c += "  \\node[rotate=90] at (-1.15,%.3f) {desviación, en puntos};\n" % ((0.4 - yb) * ey2 / 2)
    c += "  \\end{scope}\n"
    escribir("anx2_bk", c, "respuesta de un estado de EE. UU. a una caída del 1 % de su empleo relativo, VAR agrupado de BLANCHARD y KATZ (1992), réplica propia con 51 estados, 1979-2019 (anexo II.2.1)")


def fig_dispersion(disp):
    anios, ea, us = disp
    ex, ey, x0 = 0.33, 0.62, 1991
    c = linea(anios, ea, ex, ey, x0, 0, "black!85, thick")
    c += linea(anios, us, ex, ey, x0, 0, "black!55, thick, dashed")
    i13 = anios.index(2013)
    c += "  \\node[anchor=south, font=\\scriptsize] at (%.3f,%.3f) {zona del euro (once países)};\n" % ((2013 - x0) * ex, ea[i13] * ey + 0.05)
    i10 = anios.index(2010)
    c += "  \\node[anchor=north, font=\\scriptsize, black!70] at (%.3f,%.3f) {EE. UU. ($51$ estados)};\n" % ((1997 - x0) * ex, us[anios.index(1997)] * ey - 0.12)
    c += "  \\draw[->] (0,0) -- (%.3f,0);\n  \\draw[->] (0,0) -- (0,%.3f) node[above] {desviación típica de la tasa de paro, en puntos};\n" % ((2024 - x0) * ex + 0.4, 8 * ey + 0.3)
    for t in [1991, 1995, 2000, 2005, 2010, 2015, 2020, 2024]:
        c += "  \\draw (%.3f,0.06) -- (%.3f,-0.06) node[below] {$%d$};\n" % ((t - x0) * ex, (t - x0) * ex, t)
    for t in [0, 2, 4, 6, 8]:
        c += "  \\draw (0.06,%.3f) -- (-0.06,%.3f) node[left] {$%d$};\n" % (t * ey, t * ey, t)
    escribir("anx2_dispersion", c, "desviación típica sin ponderar de la tasa de paro entre los once países de la zona del euro y entre los 51 estados de EE. UU., 1991-2024 (anexo II.2.2)")


def fig_reparto(rr):
    """Barras apiladas: canales del reparto del riesgo en los estados de EE. UU. (ASDRUBALI et al., 1996) y en la zona del euro."""
    filas = [("Estados de EE. UU., $1963$-$1990$", {"K": 0.39, "F": 0.13, "C": 0.23, "U": 0.25}),
             ("Zona del euro, $1999$-$2008$", rr["1999-2008, sin Irlanda"]),
             ("Zona del euro, $2009$-$2019$", rr["2009-2019, sin Irlanda"])]
    ancho, alto, dy = 10.0, 0.55, 0.95
    estilos = {"K": "fill=black!70", "F": "fill=black!45", "C": "fill=black!20", "U": "fill=white"}
    texto = {"K": "white", "F": "white", "C": "black", "U": "black"}
    c = ""
    for i, (nombre, r) in enumerate(filas):
        y = -i * dy
        c += "  \\node[anchor=east] at (-0.15,%.3f) {%s};\n" % (y, nombre)
        x = 0.0
        for k in ("K", "F", "C", "U"):
            v = max(r[k], 0.0)
            if v <= 0.0005:
                continue
            w = v * ancho
            c += "  \\draw[black!70, %s] (%.3f,%.3f) rectangle (%.3f,%.3f);\n" % (estilos[k], x, y - alto / 2, x + w, y + alto / 2)
            if w > 0.75:
                c += "  \\node[%s, font=\\scriptsize] at (%.3f,%.3f) {%s};\n" % (texto[k], x + w / 2, y, "$%d\\%%$" % round(100 * r[k]))
            x += w
    fondo = -(len(filas) - 1) * dy - alto / 2 - 0.15
    c += "  \\draw (0,%.3f) -- (%.3f,%.3f);\n" % (fondo, ancho, fondo)
    for t in (0, 25, 50, 75, 100):
        c += "  \\draw (%.3f,%.3f) -- (%.3f,%.3f) node[below] {$%d$};\n" % (t / 100 * ancho, fondo + 0.06, t / 100 * ancho, fondo - 0.06, t)
    c += "  \\node[below=12pt] at (%.3f,%.3f) {porcentaje de una perturbación del producto};\n" % (ancho / 2, fondo)
    ley = [("K", "mercados de capitales"), ("F", "presupuesto federal o transferencias"), ("C", "crédito y ahorro"), ("U", "sin alisar")]
    xs = [0.0, 2.75, 7.0, 9.3]
    for (k, nombre), x in zip(ley, xs):
        c += "  \\draw[black!70, %s] (%.3f,0.62) rectangle (%.3f,0.88);\n" % (estilos[k], x, x + 0.35)
        c += "  \\node[anchor=west, font=\\scriptsize] at (%.3f,0.75) {%s};\n" % (x + 0.42, nombre)
    escribir("anx2_reparto", c, "canales del reparto del riesgo: estados de EE. UU. (ASDRUBALI, SØRENSEN y YOSHA, 1996) y zona del euro sin Irlanda (cálculo propio) (anexo II.3.2)")


def fig_precios(pr):
    anios, cv, cv_sin = pr
    ex, ey, x0 = 0.36, 0.25, 1995
    c = "  \\draw[black!40, densely dotted] (%.3f,0) -- (%.3f,%.3f);\n" % ((1999 - x0) * ex, (1999 - x0) * ex, 20 * ey)
    c += "  \\node[anchor=south, font=\\scriptsize, black!60] at (%.3f,%.3f) {euro};\n" % ((1999 - x0) * ex, 20 * ey)
    c += linea(anios, cv, ex, ey, x0, 0, "black!85, thick")
    c += linea(anios, cv_sin, ex, ey, x0, 0, "black!55, thick, dashed")
    c += "  \\node[anchor=west, font=\\scriptsize] at (%.3f,%.3f) {once países};\n" % ((2024 - x0) * ex + 0.1, cv[-1] * ey + 0.12)
    c += "  \\node[anchor=west, font=\\scriptsize, black!70] at (%.3f,%.3f) {sin Irlanda};\n" % ((2024 - x0) * ex + 0.1, cv_sin[-1] * ey - 0.12)
    c += "  \\draw[->] (0,0) -- (%.3f,0);\n  \\draw[->] (0,0) -- (0,%.3f) node[above] {coeficiente de variación de los niveles de precios, en porcentaje};\n" % ((2024 - x0) * ex + 0.4, 20 * ey + 0.3)
    for t in (1995, 2000, 2005, 2010, 2015, 2020, 2024):
        c += "  \\draw (%.3f,0.06) -- (%.3f,-0.06) node[below] {$%d$};\n" % ((t - x0) * ex, (t - x0) * ex, t)
    for t in (0, 5, 10, 15, 20):
        c += "  \\draw (0.06,%.3f) -- (-0.06,%.3f) node[left] {$%d$};\n" % (t * ey, t * ey, t)
    escribir("anx2_precios", c, "dispersión de los niveles de precios del consumo individual efectivo entre los miembros de la zona del euro, 1995-2024 (anexo II.4.2)")


def fig_crecimiento(cr):
    anios, indices = cr
    ex, ey, x0, y0 = 0.34, 0.085, 1995, 85
    estilos = {"Zona del euro (once países)": "black!85, thick", "Estados Unidos": "black!55, thick, dashed",
               "Reino Unido, Suecia y Dinamarca": "black!45, thick, densely dotted"}
    c = "  \\draw[black!30] (%.3f,%.3f) -- (%.3f,%.3f);\n" % (0, (100 - y0) * ey, (2024 - x0) * ex, (100 - y0) * ey)
    for nombre, v in indices.items():
        c += linea(anios, v, ex, ey, x0, y0, estilos[nombre])
    etiquetas = {"Zona del euro (once países)": "zona del euro", "Estados Unidos": "EE. UU.", "Reino Unido, Suecia y Dinamarca": "Reino Unido, Suecia y Dinamarca"}
    finales = sorted(((v[-1], n) for n, v in indices.items()), reverse=True)
    ultimo = None
    for valor, n in finales:
        y = (valor - y0) * ey
        if ultimo is not None and ultimo - y < 0.33:
            y = ultimo - 0.33
        c += "  \\node[anchor=west, font=\\scriptsize] at (%.3f,%.3f) {%s};\n" % ((2024 - x0) * ex + 0.1, y, etiquetas[n])
        ultimo = y
    c += "  \\draw[->] (0,0) -- (%.3f,0);\n  \\draw[->] (0,0) -- (0,%.3f) node[above] {PIB real por habitante, $1999=100$};\n" % ((2024 - x0) * ex + 0.4, (145 - y0) * ey + 0.3)
    for t in (1995, 2000, 2005, 2010, 2015, 2020, 2024):
        c += "  \\draw (%.3f,0.06) -- (%.3f,-0.06) node[below] {$%d$};\n" % ((t - x0) * ex, (t - x0) * ex, t)
    for t in (90, 100, 110, 120, 130, 140):
        c += "  \\draw (0.06,%.3f) -- (-0.06,%.3f) node[left] {$%d$};\n" % ((t - y0) * ey, (t - y0) * ey, t)
    escribir("anx2_crecimiento", c, "PIB real por habitante de la zona del euro (once países), EE. UU. y Reino Unido, Suecia y Dinamarca, 1995-2024, 1999 = 100 (anexo II.4.3)")


def mensual_x(k, x0):  # (año, mes) -> años decimales desde x0
    return k[0] + (k[1] - 1) / 12.0 - x0


def marca_vertical(x, alto, texto, ex, x0, lado="right"):
    X = (x - x0) * ex
    return ("  \\draw[black!35, densely dotted] (%.3f,0) -- (%.3f,%.3f);\n" % (X, X, alto)
            + "  \\node[anchor=north %s, font=\\scriptsize, black!60, align=%s] at (%.3f,%.3f) {%s};\n"
            % ("west" if lado == "right" else "east", "left" if lado == "right" else "right", X + (0.05 if lado == "right" else -0.05), alto, texto))


def ejes_tiempo(x0, x1, ex, ticks_x, y0, y1, ey, ticks_y, titulo_y, fmt_y="$%d$"):
    c = "  \\draw[->] (0,%.3f) -- (%.3f,%.3f);\n" % ((0 - y0) * ey if y0 < 0 else 0, (x1 - x0) * ex + 0.3, (0 - y0) * ey if y0 < 0 else 0)
    c += "  \\draw[->] (0,0) -- (0,%.3f) node[above] {%s};\n" % ((y1 - y0) * ey + 0.25, titulo_y)
    base = 0.0
    for t in ticks_x:
        c += "  \\draw (%.3f,%.3f) -- (%.3f,%.3f);\n  \\node[below] at (%.3f,0) {$%d$};\n" % ((t - x0) * ex, base + 0.06, (t - x0) * ex, base - 0.06, (t - x0) * ex, t)
    for t in ticks_y:
        c += "  \\draw (0.06,%.3f) -- (-0.06,%.3f) node[left] {%s};\n" % ((t - y0) * ey, (t - y0) * ey, fmt_y % t if "%" in fmt_y else num(t))
    return c


def fig_diferenciales(dif):
    x0, x1, ex, y0, y1, ey, tope = 1993, 2026.75, 0.42, 0, 13, 0.5, 13.0
    estilos = {"GRC": "black!90, thick", "PRT": "black!55, thick, dashed", "ITA": "black!80", "ESP": "black!45, thick, densely dotted", "FRA": "black!35"}
    c = ""
    for p in ("FRA", "ESP", "ITA", "PRT", "GRC"):
        tramo, trozos = [], []
        for k in sorted(dif[p]):
            if k[0] < 1993:
                continue
            v = min(dif[p][k], tope)
            tramo.append("(%.3f,%.3f)" % (mensual_x(k, x0) * ex, (v - y0) * ey))
        c += "  \\draw[%s] %s;\n" % (estilos[p], " -- ".join(tramo))
    c += marca_vertical(1999, tope * ey + 0.1, "euro", ex, x0)
    c += marca_vertical(2012 + 6 / 12, tope * ey + 0.1, "OMT", ex, x0)
    c += marca_vertical(2022 + 6 / 12, tope * ey + 0.1, "TPI", ex, x0)
    c += "  \\node[anchor=east, font=\\scriptsize] at (%.3f,%.3f) {Grecia};\n" % ((2012.0 - x0) * ex - 0.25, (tope - 0.4) * ey)
    c += "  \\node[anchor=west, font=\\scriptsize, black!70] at (%.3f,%.3f) {Portugal};\n" % ((2012.1 - x0) * ex + 0.15, 11.6 * ey)
    c += "  \\node[anchor=south, font=\\scriptsize] at (%.3f,%.3f) {Italia};\n" % ((1995.3 - x0) * ex, 6.35 * ey)
    c += "  \\node[anchor=north west, font=\\scriptsize, black!60] at (%.3f,%.3f) {España};\n" % ((1996.4 - x0) * ex, 3.6 * ey)
    c += "  \\node[anchor=south, font=\\scriptsize, black!55] at (%.3f,%.3f) {Francia};\n" % ((2025.0 - x0) * ex, 1.3 * ey)
    c += ejes_tiempo(x0, x1, ex, [1995, 2000, 2005, 2010, 2015, 2020, 2025], y0, y1, ey, [0, 2, 4, 6, 8, 10, 12],
                     "diferencial frente a Alemania, en puntos porcentuales")
    escribir("anx2_diferenciales", c, "diferencial del tipo de la deuda pública a diez años frente a Alemania, 1993-2026, mensual; Grecia cortada en 13 puntos (máximo de 27,4 en febrero de 2012) (anexo II.5.1)")


def fig_tipos_reales(reales):
    orden = sorted(EURO, key=lambda p: reales[p])
    esc, dy, x0 = 4.0, 0.42, -0.75
    c = ""
    ys = {p: -i * dy for i, p in enumerate(orden)}
    fondo = min(ys.values()) - 0.45
    for t in (-0.5, 0, 0.5, 1.0, 1.5, 2.0):
        c += "  \\draw[%s] (%.3f,0.3) -- (%.3f,%.3f);\n" % ("black!45" if t == 0 else "black!12", (t - x0) * esc, (t - x0) * esc, fondo)
    for p in orden:
        y = ys[p]
        c += "  \\node[anchor=east] at (-0.15,%.3f) {%s};\n" % (y, NOMBRE[p])
        c += "  \\fill[black!%d] (%.3f,%.3f) rectangle (%.3f,%.3f);\n" % (70 if reales[p] < 0.5 else 35, (0 - x0) * esc, y - 0.13, (reales[p] - x0) * esc, y + 0.13)
    c += eje_x(0, (2.0 - x0) * esc + 0.3, [-0.5, 0, 0.5, 1.0, 1.5, 2.0], esc, "tipo de interés real a corto plazo, media de $1999$-$2007$, en porcentaje", y=fondo, desde=x0)
    escribir("anx2_tipos_reales", c, "tipo de interés real a corto plazo (euríbor a tres meses menos la inflación de cada país), media de 1999-2007 (anexo II.6.1)")


def etiquetas_finales(valores, x, ey, y0, separacion=0.32):
    """Etiquetas al final de las líneas, separadas si se solapan: lista de (valor, texto, color)."""
    c, ultimo = "", None
    for v, texto, color in sorted(valores, key=lambda t: -t[0]):
        y = (v - y0) * ey
        if ultimo is not None and ultimo - y < separacion:
            y = ultimo - separacion
        c += "  \\node[anchor=west, font=\\scriptsize, %s] at (%.3f,%.3f) {%s};\n" % (color, x, y, texto)
        ultimo = y
    return c


def fig_clu_real(datos):
    anios, rel = datos
    x0, x1, ex, y0, y1, ey = 1995, 2024, 0.36, 80, 120, 0.13
    estilos = {"DEU": "black!90, thick", "ESP": "black!55, thick, dashed", "GRC": "black!80", "ITA": "black!45, thick, densely dotted", "PRT": "black!30, thick"}
    c = "  \\draw[black!30] (0,%.3f) -- (%.3f,%.3f);\n" % ((100 - y0) * ey, (x1 - x0) * ex, (100 - y0) * ey)
    for p in ("PRT", "ITA", "GRC", "ESP", "DEU"):
        c += linea(anios, rel[p], ex, ey, x0, y0, estilos[p])
    c += marca_vertical(1999, (y1 - y0) * ey + 0.1, "euro", ex, x0)
    c += marca_vertical(2008, (y1 - y0) * ey + 0.1, "crisis", ex, x0)
    c += etiquetas_finales([(rel[p][-1], NOMBRE[p], "black") for p in ("DEU", "ESP", "GRC", "ITA", "PRT")], (x1 - x0) * ex + 0.1, ey, y0)
    c += ejes_tiempo(x0, x1, ex, [1995, 2000, 2005, 2010, 2015, 2020, 2024], y0, y1, ey, [80, 90, 100, 110, 120],
                     "coste laboral unitario relativo a la media de la zona, $1999=100$")
    escribir("anx2_clu_real", c, "coste laboral unitario nominal de cada país relativo a la media geométrica de los once miembros, 1995-2024, 1999 = 100 (anexo II.6.2)")


def fig_cuenta_corriente(cc):
    x0, x1, ex, y0, y1, ey = 1995, 2024, 0.36, -16, 10, 0.2
    estilos = {"DEU": "black!90, thick", "NLD": "black!40", "ESP": "black!55, thick, dashed", "PRT": "black!30, thick", "GRC": "black!80", "ITA": "black!45, thick, densely dotted"}
    c = "  \\draw[black!45] (0,%.3f) -- (%.3f,%.3f);\n" % ((0 - y0) * ey, (x1 - x0) * ex, (0 - y0) * ey)
    for p in ("NLD", "ITA", "PRT", "ESP", "GRC", "DEU"):
        a = [x for x in range(1995, 2025) if x in cc[p]]
        c += linea(a, [cc[p][x] for x in a], ex, ey, x0, y0, estilos[p])
    rotulos = {"GRC": (2008, -0.35, "Grecia"), "PRT": (2008.2, 0.35, "Portugal"), "ESP": (2006.4, -0.35, "España")}
    for p, (a, dy, texto) in rotulos.items():
        c += "  \\node[anchor=%s, font=\\scriptsize] at (%.3f,%.3f) {%s};\n" % ("north" if dy < 0 else "south", (a - x0) * ex, (cc[p][int(a)] - y0) * ey + dy, texto)
    c += etiquetas_finales([(cc["NLD"][2024], "Países Bajos", "black!60"), (cc["DEU"][2024], "Alemania", "black"), (cc["ITA"][2024], "Italia", "black!60")], (x1 - x0) * ex + 0.1, ey, y0)
    c += marca_vertical(1999, (y1 - y0) * ey + 0.1, "euro", ex, x0)
    c += ejes_tiempo(x0, x1, ex, [1995, 2000, 2005, 2010, 2015, 2020, 2024], y0, y1, ey, [-15, -10, -5, 0, 5, 10],
                     "saldo por cuenta corriente, en porcentaje del PIB")
    escribir("anx2_cuenta_corriente", c, "saldo de la balanza por cuenta corriente en porcentaje del PIB, 1995-2024 (anexo II.6.2)")


def fig_target(tgb):
    x0, x1, ex, y0, y1, ey = 2008, 2026.75, 0.62, -800, 1400, 0.0026
    estilos = {"DE": "black!90, thick", "IT": "black!45, thick, densely dotted", "ES": "black!55, thick, dashed", "GR": "black!70"}
    nombres = {"DE": "Alemania", "IT": "Italia", "ES": "España", "GR": "Grecia"}
    c = "  \\draw[black!45] (0,%.3f) -- (%.3f,%.3f);\n" % ((0 - y0) * ey, (x1 - x0) * ex, (0 - y0) * ey)
    for p in ("GR", "IT", "ES", "DE"):
        ks = sorted(tgb[p])
        c += "  \\draw[%s] %s;\n" % (estilos[p], " -- ".join("(%.3f,%.3f)" % (mensual_x(k, x0) * ex, (tgb[p][k] - y0) * ey) for k in ks))
    ultimo = max(tgb["DE"])
    c += etiquetas_finales([(tgb[p][max(tgb[p])], nombres[p], "black") for p in ("DE", "IT", "ES", "GR")], mensual_x(ultimo, x0) * ex + 0.1, ey, y0)
    c += marca_vertical(2012 + 6 / 12, (y1 - y0) * ey + 0.1, "OMT", ex, x0)
    c += marca_vertical(2015 + 2 / 12, (y1 - y0) * ey + 0.1, "compras de deuda", ex, x0)
    c += "  \\draw[->] (0,%.3f) -- (%.3f,%.3f);\n" % ((0 - y0) * ey, (x1 - x0) * ex + 0.3, (0 - y0) * ey)
    c += "  \\draw[->] (0,0) -- (0,%.3f) node[above] {saldo TARGET, en miles de millones de euros};\n" % ((y1 - y0) * ey + 0.25)
    for t in (2008, 2010, 2012, 2014, 2016, 2018, 2020, 2022, 2024, 2026):
        c += "  \\draw (%.3f,0.06) -- (%.3f,-0.06) node[below] {$%d$};\n" % ((t - x0) * ex, (t - x0) * ex, t)
    for t in (-800, -400, 0, 400, 800, 1200):
        c += "  \\draw (0.06,%.3f) -- (-0.06,%.3f) node[left] {$%d$};\n" % ((t - y0) * ey, (t - y0) * ey, t)
    escribir("anx2_target", c, "saldos TARGET de los bancos centrales de Alemania, Italia, España y Grecia frente al Eurosistema, fin de mes, 2008-2026 (anexo II.6.3)")


def fig_inflacion_espana(difi):
    x0, x1, ex, y0, y1, ey = 1997, 2026.75, 0.42, -2.5, 3, 0.9
    ks = sorted(difi)
    c = "  \\draw[black!45] (0,%.3f) -- (%.3f,%.3f);\n" % ((0 - y0) * ey, (x1 - x0) * ex, (0 - y0) * ey)
    c += "  \\draw[black!85, thick] %s;\n" % " -- ".join("(%.3f,%.3f)" % (mensual_x(k, x0) * ex, (difi[k][2] - y0) * ey) for k in ks)
    c += marca_vertical(1999, (y1 - y0) * ey + 0.1, "euro", ex, x0)
    c += marca_vertical(2008 + 8 / 12, (y1 - y0) * ey + 0.1, "crisis", ex, x0)
    c += "  \\draw[->] (0,0) -- (%.3f,0);\n" % ((x1 - x0) * ex + 0.3)
    c += "  \\draw[->] (0,0) -- (0,%.3f) node[above] {inflación de España menos la de la zona del euro, en puntos};\n" % ((y1 - y0) * ey + 0.25)
    for t in (2000, 2005, 2010, 2015, 2020, 2025):
        c += "  \\draw (%.3f,0.06) -- (%.3f,-0.06) node[below] {$%d$};\n" % ((t - x0) * ex, (t - x0) * ex, t)
    for t in (-2, -1, 0, 1, 2, 3):
        c += "  \\draw (0.06,%.3f) -- (-0.06,%.3f) node[left] {$%d$};\n" % ((t - y0) * ey, (t - y0) * ey, t)
    escribir("anx2_inflacion_espana", c, "diferencia entre la inflación armonizada interanual de España y la de la zona del euro, mensual, 1997-2026 (anexo II.6.4)")


def main():
    carpeta = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
    descargar(carpeta)
    series, cifras = [], []
    res, corr_be, be = simetria(carpeta, series, cifras)
    krug = estructuras(carpeta, series, cifras)
    bk = blanchard_katz(carpeta, series, cifras)
    disp = dispersion(carpeta, series, cifras)
    rr = reparto(carpeta, series, cifras)
    pr = precios(carpeta, series, cifras)
    cr = crecimiento(carpeta, series, cifras)
    cred = credibilidad(carpeta, series, cifras)
    deseq = desequilibrios(carpeta, series, cifras)
    fig_correlaciones(res)
    fig_amplitud(res)
    fig_bayoumi(corr_be)
    fig_krugman(krug)
    fig_bk(bk)
    fig_dispersion(disp)
    fig_reparto(rr)
    fig_precios(pr)
    fig_crecimiento(cr)
    leeme = [["Libro de datos del tema 3.B.16 (Teoría de la integración monetaria)"],
             ["Generado por Code/libro_y_figuras.py el %s con los datos descargados ese día del Banco Mundial, de Eurostat y de FRED." % FECHA_DESCARGA],
             ["Hojas: Fuentes (series y su origen), Series (formato largo: serie, país o estado, año u horizonte, valor, unidad, fuente, tratamiento, figura)"],
             ["y Cifras_citadas (las que da el texto del anexo de evidencia, con su apartado)."],
             ["II.1.1-II.1.2: ciclo = componente cíclico del filtro de HODRICK y PRESCOTT con lambda 6,25 (RAVN y UHLIG, 2002) sobre 100 x log del PIB real, 1970-2019;"],
             ["el agregado de la zona suma el PIB en dólares de 2015 de once países (sin Luxemburgo); para cada miembro, el resto de la zona excluye al propio país."],
             ["II.1.3: VAR(2) por país en crecimiento del PIB real e inflación del deflactor (100 x diferencias logarítmicas), con constante y tendencia lineal, 1973-2019;"],
             ["identificación de BLANCHARD y QUAH: la perturbación de demanda no afecta a la producción a largo plazo; correlaciones con las de Alemania."],
             ["II.1.4: índice de KRUGMAN = suma de las diferencias absolutas entre las cuotas del país y del resto de la zona en once ramas (NACE A, BDE, C, F, G-I, J, K, L, M_N, O-Q, R-U)."],
             ["II.2.1: VAR agrupado con efectos fijos por estado, 2 retardos, 1979-2019, en el crecimiento del empleo relativo, el log de la tasa de empleo relativa y el log"],
             ["de la tasa de actividad relativa (estado menos nación), como BLANCHARD y KATZ (1992); el empleo entra el primero y afecta en el mismo año a las otras dos."],
             ["II.2.2: desviación típica sin ponderar de las tasas de paro; persistencia = coeficiente de un AR(1) agrupado de la desviación respecto a la media"],
             ["sin ponderar de cada año, con efectos fijos, 1991-2024; vida media = log 0,5 / log del coeficiente."],
             ["II.3.2: descomposición de ASDRUBALI, SØRENSEN y YOSHA (1996): PIB (B1GQ) -> renta nacional bruta (B5G) -> renta nacional disponible bruta (B6G)"],
             ["-> consumo final (P3) del total de la economía (S1), en euros de 2015 por habitante (deflactor del PIB de nama_10_gdp y población del Banco Mundial);"],
             ["coeficientes de MCO agrupados con efectos fijos de año (suman uno); sin Irlanda en la versión principal, porque los beneficios de sus multinacionales"],
             ["separan el PIB de la renta nacional y dominan la estimación."],
             ["II.4.2: coeficiente de variación (desviación típica / media, sin ponderar) de los niveles de precios del consumo individual efectivo (UE-27 = 100)."],
             ["II.4.3: PIB real por habitante de los agregados = suma del PIB en dólares de 2015 / suma de la población; EE. UU., serie NY.GDP.PCAP.KD."]]
    fuentes = [["Código", "Serie", "Ámbito", "Unidad", "Frecuencia", "Institución", "Enlace", "Descarga"]]
    for s, nombre in list(WB_SERIES.items()) + [(WB_PARO, "Tasa de paro, estimación armonizada de la OIT")]:
        fuentes.append([s, nombre, ", ".join(NOMBRE[p] for p in EURO + FUERA), "ver serie", "anual", "Banco Mundial, Indicadores del Desarrollo Mundial",
                        WB % (";".join(EURO + FUERA), s), FECHA_DESCARGA])
    for s, nombre in WB_A8.items():
        fuentes.append([s, nombre, ", ".join(NOMBRE[p] for p in EURO + FUERA) + ", Estados Unidos", "ver serie", "anual", "Banco Mundial, Indicadores del Desarrollo Mundial",
                        WB % (";".join(EURO + FUERA + ["USA"]), s), FECHA_DESCARGA])
    descripcion = {"a10.json": ("Eurostat nama_10_a10", "Valor añadido bruto por ramas", "millones de euros corrientes"),
                   "cuentas.json": ("Eurostat nasa_10_nf_tr", "PIB, renta nacional bruta, renta nacional disponible bruta y consumo final del total de la economía", "millones de euros corrientes"),
                   "deflactor.json": ("Eurostat nama_10_gdp", "Deflactor del PIB", "índice 2015 = 100"),
                   "precios.json": ("Eurostat prc_ppp_ind", "Niveles de precios del consumo individual efectivo", "índice, UE-27 = 100"),
                   "clu.json": ("Eurostat nama_10_lp_ulc", "Coste laboral unitario nominal por persona ocupada", "índice 2015 = 100")}
    for nombre, consulta in EUROSTAT.items():
        codigo, serie, unidad = descripcion[nombre]
        fuentes.append([codigo, serie, ", ".join(NOMBRE[p] for p in EURO), unidad, "anual", "Eurostat", EST + consulta, FECHA_DESCARGA])
    for st, fips in ESTADOS.items():
        for s, nombre, unidad in ((st + "NAN", "Empleo asalariado no agrario, sin desestacionalizar", "miles de personas"),
                                  (st + "UR", "Tasa de paro, desestacionalizada", "porcentaje"),
                                  ("LBSSA" + fips, "Tasa de actividad, desestacionalizada", "porcentaje")):
            fuentes.append([s, nombre, st, unidad, "mensual (media anual)", "FRED, Banco de la Reserva Federal de San Luis (BLS)", FRED + s, FECHA_DESCARGA])
    for s, nombre in (("UNRATE", "Tasa de paro de EE. UU."), ("CIVPART", "Tasa de actividad de EE. UU.")):
        fuentes.append([s, nombre, "Estados Unidos", "porcentaje", "mensual (media anual)", "FRED, Banco de la Reserva Federal de San Luis (BLS)", FRED + s, FECHA_DESCARGA])
    filas = [["Serie", "Ámbito", "Año u horizonte", "Valor", "Unidad", "Fuente", "Tratamiento", "Figura"]] + [list(f) for f in series]
    cif = [["Cifra", "Valor", "Unidad", "Apartado"]] + [list(c) for c in cifras]
    escribir_xlsx(os.path.join(TEMA, "Code", "datos_3B16.xlsx"), [("Léeme", leeme), ("Fuentes", fuentes), ("Series", filas), ("Cifras_citadas", cif)])
    for c in cifras:
        print("%-100s %s %s" % (c[0], c[1], c[2]))


if __name__ == "__main__":
    main()
