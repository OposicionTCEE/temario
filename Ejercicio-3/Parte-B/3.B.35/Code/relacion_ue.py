#!/usr/bin/env python3
"""Peso mutuo entre la UE y cada proceso de integración del tema (2023), para los párrafos «Relación con la UE»
(nota del usuario, 15/10/2026: qué finalidad motiva la asociación de la UE con cada bloque, y demostrarlo).

  Peso del bloque para la UE: exportaciones más importaciones de mercancías de los 27 con los miembros del bloque,
      en % de su comercio con fuera de la UE (WITS, lo que declaran los Estados miembros).
  Peso de la UE para el bloque: las mismas cifras en % del comercio total de mercancías de los miembros del bloque
      (exportaciones e importaciones de WDI, TX.VAL.MRCH.CD.WT y TM.VAL.MRCH.CD.WT). Aproximado: la UE declara sus
      importaciones CIF y WDI las exportaciones del bloque FOB.
Escribe la hoja UE_peso_mutuo en Code/datos/tablas_figuras.xlsx.
Uso, desde la carpeta del tema:  /ruta/a/python-con-openpyxl Code/relacion_ue.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import datos_comercio as dc  # noqa: E402
import datos_wits as dw  # noqa: E402
import indicadores_bloque as ib  # noqa: E402

ANIO = 2023
BLOQUES = [   # (nombre, miembros); Liechtenstein y Kosovo no figuran como socios en WITS
    ('MCCA (con Panamá)', ['GTM', 'SLV', 'HND', 'NIC', 'CRI', 'PAN']),
    ('CAN', ['BOL', 'COL', 'ECU', 'PER']),
    ('EFTA', ['CHE', 'NOR', 'ISL']),
    ('NAFTA/USMCA', ['USA', 'CAN', 'MEX']),
    ('MERCOSUR', ['ARG', 'BRA', 'PRY', 'URY']),
    ('CEFTA', ['ALB', 'BIH', 'MKD', 'MNE', 'SRB', 'MDA']),
    ('AfCFTA', dc.GRUPOS['AFCFTA'][0]),
    ('PAFTA', dc.GRUPOS['PAFTA'][0]),
    ('ASEAN', dc.GRUPOS['ASEAN'][0]),
    ('CCG', ['SAU', 'ARE', 'KWT', 'QAT', 'BHR', 'OMN']),
    ('RCEP', dc.GRUPOS['RCEP'][0]),
    ('CPTPP', dc.GRUPOS['CPTPP'][0]),
    ('UEE', dc.GRUPOS['UEE'][0]),
    ('EE. UU. (referencia)', ['USA']),
    ('China (referencia)', ['CHN']),
    ('Reino Unido (referencia)', ['GBR']),
]


def main():
    dw.descarga([('comercio', p, ANIO, f, 'Total') for p in dc.UE27 for f in ('X', 'M')])
    X, M = dw.tabla('comercio', 'X', 'Total'), dw.tabla('comercio', 'M', 'Total')
    w = ib.wdi()
    ue = set(dc.UE27)

    def extra(t):
        return sum(t[(p, ANIO)]['WLD'] - sum(v for s, v in t[(p, ANIO)].items() if s in ue) for p in dc.UE27)
    ex, em = extra(X), extra(M)
    filas = []
    for nombre, miembros in BLOQUES:
        x = sum(X[(p, ANIO)].get(s, 0.0) for p in dc.UE27 for s in miembros)
        m = sum(M[(p, ANIO)].get(s, 0.0) for p in dc.UE27 for s in miembros)
        tx = sum(w.get((s, 'TX.VAL.MRCH.CD.WT', ANIO)) or w.get((s, 'TX.VAL.MRCH.CD.WT', ANIO - 1)) or 0 for s in miembros)
        tm = sum(w.get((s, 'TM.VAL.MRCH.CD.WT', ANIO)) or w.get((s, 'TM.VAL.MRCH.CD.WT', ANIO - 1)) or 0 for s in miembros)
        filas.append((ANIO, nombre, round(100 * (x + m) / (ex + em), 2), round(100 * x / ex, 2), round(100 * m / em, 2),
                      round(100 * (x + m) / (tx + tm), 1), round(x / 1e9, 1), round(m / 1e9, 1)))
        print(f'{nombre:26s} bloque para la UE {filas[-1][2]:5.1f} %   UE para el bloque {filas[-1][5]:5.1f} %')
    try:
        ib.hoja('UE_peso_mutuo', f'Peso mutuo entre la UE y cada proceso de integración, comercio de mercancías, {ANIO}',
                'WITS (Banco Mundial): exportaciones e importaciones declaradas por los 27 Estados miembros con cada socio; Banco Mundial '
                '(WDI): exportaciones e importaciones totales de mercancías de los miembros de cada bloque. Peso para la UE = comercio '
                'con el bloque / comercio con fuera de la UE; peso para el bloque = comercio con la UE / comercio total del bloque '
                '(aproximado: importaciones de la UE CIF, exportaciones del bloque FOB). Cálculo propio (Code/relacion_ue.py).',
                ['Año', 'Bloque', 'El bloque en el comercio exterior de la UE (%)', 'En las exportaciones de la UE (%)',
                 'En las importaciones de la UE (%)', 'La UE en el comercio del bloque (%)', 'Exportaciones de la UE (miles de millones de USD)',
                 'Importaciones de la UE (miles de millones de USD)'], filas)
    except ImportError:
        print('Falta openpyxl: no se escribe la tabla')


if __name__ == '__main__':
    main()
