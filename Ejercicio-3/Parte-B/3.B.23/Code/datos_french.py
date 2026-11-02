"""Datos de la biblioteca de Kenneth R. FRENCH para las figuras del 3.B.23.

Fuente: Kenneth R. French Data Library (https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html),
ficheros creados con la base de datos de CRSP de septiembre de 2026 y descargados el 02/11/2026. Se guardan sin tocar
en Code/datos/ y, si falta alguno, se descarga de nuevo (la versión nueva puede traer datos revisados).
Rentabilidades mensuales en %, carteras ponderadas por su valor; -99,99 y -999 son datos que faltan.
"""
import io
import urllib.request
import zipfile
from pathlib import Path

import numpy as np

DATOS = Path(__file__).resolve().parent / "datos"
URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/{}_CSV.zip"
FACTORES = "F-F_Research_Data_Factors"
BETA = "Portfolios_Formed_on_BETA"
BM = "Portfolios_Formed_on_BE-ME"


def fichero(nombre):
    ruta = DATOS / f"{nombre}.csv"
    if not ruta.exists():
        DATOS.mkdir(exist_ok=True)
        with urllib.request.urlopen(URL.format(nombre)) as r:
            z = zipfile.ZipFile(io.BytesIO(r.read()))
        miembro = next(n for n in z.namelist() if n.lower() == f"{nombre.lower()}.csv")
        ruta.write_bytes(z.read(miembro))
    return ruta


def seccion(nombre, marca):
    """Meses (aaaamm), nombres de columna y matriz de la primera sección mensual tras la línea que contiene `marca`.

    La marca puede ser el título de la sección («Value Weighted Returns -- Monthly») o la propia cabecera («,Mkt-RF»).
    """
    lineas = fichero(nombre).read_text(encoding="latin-1").splitlines()
    i = next(k for k, l in enumerate(lineas) if marca in l)
    if not lineas[i].startswith(","):
        i += 1
    columnas = [c.strip() for c in lineas[i].split(",")[1:] if c.strip()]
    meses, filas = [], []
    for l in lineas[i + 1:]:
        partes = [p.strip() for p in l.split(",")]
        if len(partes[0]) != 6 or not partes[0].isdigit():
            break
        meses.append(int(partes[0]))
        filas.append([float(x) for x in partes[1:len(columnas) + 1]])
    matriz = np.array(filas)
    matriz[matriz <= -99.99] = np.nan
    return np.array(meses), columnas, matriz


def excesos(nombre, marca, columnas, desde, hasta):
    """Rentabilidades en exceso del letra del Tesoro a un mes (en %) de las carteras pedidas y del mercado."""
    mf, cf, f = seccion(FACTORES, ",Mkt-RF")
    mp, cp, p = seccion(nombre, marca)
    meses = np.array([m for m in mp if desde <= m <= hasta and m in set(mf)])
    fi = np.searchsorted(mf, meses)
    pi = np.searchsorted(mp, meses)
    rf = f[fi, cf.index("RF")]
    mercado = f[fi, cf.index("Mkt-RF")]
    carteras = np.column_stack([p[pi, cp.index(c)] for c in columnas]) - rf[:, None]
    return meses, carteras, mercado, rf
