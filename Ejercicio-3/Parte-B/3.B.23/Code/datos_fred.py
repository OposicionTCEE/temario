"""Datos de FRED (Banco de la Reserva Federal de San Luis) para las figuras del 3.B.23.

Fuente: FRED (https://fred.stlouisfed.org), serie A794RX0Q048SBEA: gasto real en consumo personal por habitante de
Estados Unidos (dólares encadenados de 2017, trimestral, desestacionalizado), del Bureau of Economic Analysis.
Descargada el 02/11/2026 y guardada sin tocar en Code/datos/; si falta, se descarga de nuevo (la versión nueva puede
traer datos revisados).
"""
import csv
import math
import urllib.request
from pathlib import Path

DATOS = Path(__file__).resolve().parent / "datos"
CONSUMO = "A794RX0Q048SBEA"
URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"


def fichero(serie):
    ruta = DATOS / f"FRED_{serie}.csv"
    if not ruta.exists():
        DATOS.mkdir(exist_ok=True)
        peticion = urllib.request.Request(URL.format(serie), headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(peticion, timeout=60) as r:
            ruta.write_bytes(r.read())
    return ruta


def trimestres(serie=CONSUMO):
    """Lista de (fecha aaaa-mm-dd, valor) tal como la publica FRED."""
    with open(fichero(serie), encoding="utf-8") as f:
        filas = list(csv.reader(f))[1:]
    return [(fecha, float(valor)) for fecha, valor in filas if valor not in ("", ".")]


def crecimiento_anual(desde, hasta, serie=CONSUMO):
    """Crecimiento logarítmico anual, en %, de la media de los cuatro trimestres de cada año (años completos)."""
    por_año = {}
    for fecha, valor in trimestres(serie):
        por_año.setdefault(int(fecha[:4]), []).append(valor)
    media = {a: sum(v) / 4 for a, v in por_año.items() if len(v) == 4}
    return {a: 100 * math.log(media[a] / media[a - 1]) for a in range(desde, hasta + 1) if a in media and a - 1 in media}


def crecimiento_cuarto_trimestre(desde, hasta, serie=CONSUMO):
    """Crecimiento logarítmico, en %, del cuarto trimestre de cada año respecto del cuarto trimestre del anterior."""
    cuarto = {int(fecha[:4]): valor for fecha, valor in trimestres(serie) if fecha[5:7] == "10"}
    return {a: 100 * math.log(cuarto[a] / cuarto[a - 1]) for a in range(desde, hasta + 1) if a in cuarto and a - 1 in cuarto}
