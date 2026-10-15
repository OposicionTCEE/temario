#!/usr/bin/env python3
"""Lista de descargas de WITS para las figuras económicas del bloque geoestratégico (ASEAN, CCG, RCEP, UEE).

  ASEAN: exportaciones por socio según la fase de elaboración de la UNCTAD (materias primas, bienes intermedios, de consumo
         y de capital) y totales, 2000-2023 (Fábrica Asia); aranceles aplicados y de nación más favorecida por socio, con
         las importaciones para ponderar, 2000-2023 (margen de preferencia).
  RCEP:  exportaciones e importaciones totales por socio de los quince miembros en 2000-2001 y 2021-2023 (peso de China y
         de Japón en su comercio); aranceles aplicados y NMF de China, Japón y Corea por socio, 2018-2023 (enlaces nuevos).
  UEE:   exportaciones totales por socio de los Estados de la UE-27 y de Armenia, Kazajistán y Kirguistán, 2019-2024
         (desvío por sanciones).
El comercio intrarregional de la UEE (exportaciones bilaterales, 1996-2012) lo descarga Code/datos_comercio.py.
Uso, desde la carpeta del tema:  python3 Code/descargas_geoestrategicas.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import datos_comercio as dc  # noqa: E402
import datos_wits as dw  # noqa: E402

FASES = ['UNCTAD-SoP1', 'UNCTAD-SoP2', 'UNCTAD-SoP3', 'UNCTAD-SoP4']   # materias primas, intermedios, consumo, capital
ASEAN10 = [p for p in dc.GRUPOS['ASEAN'][0] if p != 'TLS']
CAUCASO_ASIA = ['ARM', 'KAZ', 'KGZ']


def tareas():
    t = []
    for p in ASEAN10:
        for a in range(2000, 2024):
            t += [('comercio', p, a, 'X', g) for g in ['Total'] + FASES]
            t += [('arancel', p, a, 'AHS', 'Total'), ('arancel', p, a, 'MFN', 'Total'), ('comercio', p, a, 'M', 'Total')]
    for p in dc.GRUPOS['RCEP'][0]:
        for a in (2000, 2001, 2021, 2022, 2023):
            t += [('comercio', p, a, 'X', 'Total'), ('comercio', p, a, 'M', 'Total')]
    for p in ('CHN', 'JPN', 'KOR'):
        for a in range(2018, 2024):
            t += [('arancel', p, a, 'AHS', 'Total'), ('arancel', p, a, 'MFN', 'Total'), ('comercio', p, a, 'M', 'Total')]
    for p in dc.UE27 + CAUCASO_ASIA:
        for a in range(2019, 2025):
            t.append(('comercio', p, a, 'X', 'Total'))
    return t


if __name__ == '__main__':
    dw.descarga(tareas())
