"""Datos de Robert J. SHILLER (bolsa de Estados Unidos desde 1871) para la figura del CAPE del 3.B.23.

Fuente: Robert J. Shiller, Online Data (https://shillerdata.com/), fichero ie_data.xls, hoja Data, guardado por su autor
el 05/10/2026 y descargado el 02/11/2026: datos mensuales de enero de 1871 a octubre de 2026 (los de octubre de 2026,
con el cierre del día 2 y el IPC estimado). La hoja se guarda tal cual, en CSV, en Code/datos/Shiller_ie_data.csv, con
la fecha como aaaamm. Si falta, `python3 Code/datos_shiller.py` la descarga y la convierte de nuevo, para lo que hace
falta el paquete xlrd (la versión nueva puede traer datos revisados); el resto del código solo lee el CSV.
Columnas: índice S&P compuesto (P, media mensual de los cierres diarios), dividendo (D) y beneficio (E) por acción de
los últimos doce meses, IPC, tipo a
diez años, precio y dividendo reales, precio real con los dividendos reinvertidos (Real Total Return Price), beneficio
real y CAPE (precio real entre la media del beneficio real de los diez años anteriores), entre otras.
"""
import csv
import urllib.request
from pathlib import Path

DATOS = Path(__file__).resolve().parent / "datos"
CSV = DATOS / "Shiller_ie_data.csv"
PAGINA = "https://shillerdata.com/"
URL = ("https://img1.wsimg.com/blobby/go/e5e77e0b-59d1-44d9-ab25-4763ac982e53/downloads/"
       "1449043e-a1ed-4e2e-8e9c-7b9a2a064493/ie_data.xls")
COLUMNAS = ["Date", "P", "D", "E", "CPI", "Date Fraction", "Rate GS10", "Real Price", "Real Dividend",
            "Real Total Return Price", "Real Earnings", "Real TR Scaled Earnings", "CAPE", "", "TR CAPE", "",
            "Excess CAPE Yield", "Monthly Total Bond Returns", "Real Total Bond Returns",
            "10 Year Annualized Stock Real Return", "10 Year Annualized Bonds Real Return",
            "Real 10 Year Excess Annualized Returns"]


def convertir(xls, destino=CSV):
    """Pasa la hoja Data del fichero de SHILLER a CSV, sin tocar los datos (las celdas NA quedan vacías)."""
    import xlrd
    hoja = xlrd.open_workbook(str(xls)).sheet_by_name("Data")
    if [str(hoja.cell_value(7, j)).strip() for j in (0, 1, 12)] != ["Date", "P", "CAPE"]:
        raise ValueError("la hoja Data no tiene la estructura esperada")
    with open(destino, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Mes"] + [c for c in COLUMNAS[1:] if c])
        for i in range(8, hoja.nrows):
            fecha = hoja.cell_value(i, 0)
            if not isinstance(fecha, float):
                continue  # notas al pie de la hoja
            anio = int(fecha)
            mes = round((fecha - anio) * 100)
            fila = [hoja.cell_value(i, j) for j in range(1, hoja.ncols) if COLUMNAS[j]]
            w.writerow([f"{anio}{mes:02d}"] + ["" if v in ("", "NA") else v for v in fila])


def fichero():
    if not CSV.exists():
        DATOS.mkdir(exist_ok=True)
        xls = DATOS / "ie_data.xls"
        with urllib.request.urlopen(URL) as r:
            xls.write_bytes(r.read())
        convertir(xls)
        xls.unlink()
    return CSV


def mensual():
    """Meses (aaaamm) y series mensuales: precio, dividendo y beneficio reales, rentabilidad total real y CAPE."""
    import numpy as np
    with open(fichero(), encoding="utf-8") as f:
        filas = list(csv.DictReader(f))

    def serie(nombre):
        return np.array([float(fl[nombre]) if fl[nombre] else np.nan for fl in filas])

    return dict(meses=np.array([int(fl["Mes"]) for fl in filas]), precio=serie("Real Price"),
                dividendo=serie("Real Dividend"), total=serie("Real Total Return Price"),
                beneficio=serie("Real Earnings"), cape=serie("CAPE"))


if __name__ == "__main__":
    print(fichero())
