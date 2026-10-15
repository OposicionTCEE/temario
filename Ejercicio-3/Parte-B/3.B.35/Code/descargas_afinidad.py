#!/usr/bin/env python3
"""Lista de descargas de WITS para las figuras económicas del bloque de afinidad (CEFTA, AfCFTA, PAFTA).

  CEFTA:  exportaciones e importaciones totales por socio, 2006-2023 (peso de la UE frente a los socios del CEFTA).
  PAFTA:  exportaciones totales y de combustibles por socio, 1998-2023 (comercio árabe sin petróleo); exportaciones por grupos
          de la CUCI (alimentos, materias primas agrícolas, combustibles, minerales y metales, manufacturas) en 2005 y 2023.
  AfCFTA: exportaciones totales y de manufacturas por socio en 2000, 2005, 2010, 2015, 2019 y 2023; exportaciones por grupos
          de la CUCI en 2000 y 2023 (dependencia de las materias primas); exportaciones e importaciones por secciones del SA
          de las doce mayores economías en 2023 (complementariedad aproximada); aranceles aplicados y de nación más
          favorecida por socio, con las importaciones para ponderar, 2019-2022.
Uso, desde la carpeta del tema:  python3 Code/descargas_afinidad.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import datos_comercio as dc  # noqa: E402
import datos_wits as dw  # noqa: E402

GRUPOS_CUCI = ['Food', 'AgrRaw', 'Fuels', 'OresMtls', 'manuf']
SECCIONES_SA = ['01-05_Animal', '06-15_Vegetable', '16-24_FoodProd', '25-26_Minerals', '27-27_Fuels', '28-38_Chemicals',
                '39-40_PlastiRub', '41-43_HidesSkin', '44-49_Wood', '50-63_TextCloth', '64-67_Footwear', '68-71_StoneGlas',
                '72-83_Metals', '84-85_MachElec', '86-89_Transport', '90-99_Miscellan']
AFRICA_GRANDES = ['NGA', 'ZAF', 'EGY', 'DZA', 'MAR', 'KEN', 'ETH', 'GHA', 'CIV', 'AGO', 'TZA', 'TUN']


def tareas():
    t = []
    for p in dc.GRUPOS['CEFTA'][0]:
        for a in range(2006, 2024):
            t += [('comercio', p, a, 'X', 'Total'), ('comercio', p, a, 'M', 'Total')]
    for p in dc.GRUPOS['PAFTA'][0]:
        for a in range(1998, 2024):
            t += [('comercio', p, a, 'X', 'Total'), ('comercio', p, a, 'X', 'Fuels')]
        for a in (2005, 2023):
            t += [('comercio', p, a, 'X', g) for g in GRUPOS_CUCI]
    africa = dc.GRUPOS['AFCFTA'][0]
    for p in africa:
        for a in (2000, 2005, 2010, 2015, 2019, 2023):
            t += [('comercio', p, a, 'X', 'Total'), ('comercio', p, a, 'X', 'manuf')]
        for a in (2000, 2023):
            t += [('comercio', p, a, 'X', g) for g in GRUPOS_CUCI]
        for a in (2019, 2020, 2021, 2022):
            t += [('arancel', p, a, 'AHS', 'Total'), ('arancel', p, a, 'MFN', 'Total'), ('comercio', p, a, 'M', 'Total')]
    for p in AFRICA_GRANDES:
        t += [('comercio', p, 2023, f, s) for f in ('X', 'M') for s in SECCIONES_SA]
    return t


if __name__ == '__main__':
    dw.descarga(tareas())
