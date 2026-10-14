#!/usr/bin/env python3
"""Escribe la hoja Cifras_citadas de Code/datos_3B35.xlsx: cada dato numérico del tema con su fuente.

Se amplía a medida que se trabajan los acuerdos. Uso, desde la carpeta del tema (con openpyxl):
  /tmp/v/bin/python Code/cifras_citadas.py
"""
from pathlib import Path

XLSX = Path(__file__).resolve().parent / 'datos_3B35.xlsx'

# (acuerdo, dato, valor, unidad, año, fuente, enlace)
CIFRAS = [
    ('MCCA', 'Exportaciones intrarregionales / totales', 7, '%', 1960,
     'Encyclopedia of business in today\'s world (SAGE), entrada Central American Common Market',
     'https://sk.sagepub.com/ency/edvol/embed/businesstoday/chpt/central-american-common-market'),
    ('MCCA', 'Exportaciones intrarregionales / totales', 26.2, '%', 1970,
     'Cálculo propio con UN Comtrade (hoja MCCA_intrarregional)', 'https://comtradeapi.un.org'),
    ('MCCA', 'Exportaciones intrarregionales / totales (mínimo)', 10.7, '%', 1986,
     'Cálculo propio con UN Comtrade (hoja MCCA_intrarregional)', 'https://comtradeapi.un.org'),
    ('MCCA', 'Exportaciones intrarregionales / totales', 25.4, '%', 2023,
     'Cálculo propio con WITS (hoja MCCA_intrarregional)', 'https://wits.worldbank.org'),
    ('MCCA', 'Comercio El Salvador-Honduras', 0, 'USD', '1970-1980',
     'UN Comtrade (hoja Exportaciones_bilaterales)', 'https://comtradeapi.un.org'),
    ('MCCA', 'Mercancías en libre circulación en la unión aduanera Guatemala-Honduras', 85, '%', 'c. 2018',
     'Ministerio de Economía de Guatemala, Integración profunda (documento informativo)',
     'https://www.mineco.gob.gt/images/que_hacer/integracion/nuevo/INFO_INTEGRACION_PROFUNDA.pdf'),
    ('MCCA', 'Comercio de bienes UE-Centroamérica', 8.7, 'miles de millones EUR', 2012,
     'Servicio Europeo de Acción Exterior (2024)', 'https://www.eeas.europa.eu/node/441072_en'),
    ('MCCA', 'Comercio de bienes UE-Centroamérica', 22, 'miles de millones EUR', 2023,
     'Servicio Europeo de Acción Exterior (2024)', 'https://www.eeas.europa.eu/node/441072_en'),
    ('DR-CAFTA', 'Puesto como mercado de exportación de EE. UU. en América Latina (tras México y Brasil)', 3, 'puesto', 2008,
     'International Trade Administration, Office of Industry Analysis',
     'https://legacy.trade.gov/mas/ian/tradeagreements/fta/tg_ian_002419.asp'),
    ('MCCA', 'Exportaciones intrarregionales / totales', 17.9, '%', 1965,
     'Cálculo propio con UN Comtrade (hoja MCCA_intrarregional)', 'https://comtradeapi.un.org'),
    ('MCCA', 'Valor de las exportaciones intrarregionales', 1134.6, 'millones USD', 1980,
     'Cálculo propio con UN Comtrade (hoja MCCA_intrarregional)', 'https://comtradeapi.un.org'),
    ('MCCA', 'Valor de las exportaciones intrarregionales', 413.3, 'millones USD', 1986,
     'Cálculo propio con UN Comtrade (hoja MCCA_intrarregional)', 'https://comtradeapi.un.org'),
    ('MCCA', 'Valor de las exportaciones intrarregionales', 13554.2, 'millones USD', 2023,
     'Cálculo propio con WITS (hoja MCCA_intrarregional)', 'https://wits.worldbank.org'),
    ('MCCA', 'Exportaciones a Centroamérica / totales: El Salvador', 47.4, '%', 2023, 'Cálculo propio con WITS', 'https://wits.worldbank.org'),
    ('MCCA', 'Exportaciones a Centroamérica / totales: Guatemala', 36.0, '%', 2023, 'Cálculo propio con WITS', 'https://wits.worldbank.org'),
    ('MCCA', 'Exportaciones a Centroamérica / totales: Honduras', 20.3, '%', 2023, 'Cálculo propio con WITS', 'https://wits.worldbank.org'),
    ('MCCA', 'Exportaciones a Centroamérica / totales: Nicaragua', 17.0, '%', 2023, 'Cálculo propio con WITS', 'https://wits.worldbank.org'),
    ('MCCA', 'Exportaciones a Centroamérica / totales: Costa Rica', 14.6, '%', 2023, 'Cálculo propio con WITS', 'https://wits.worldbank.org'),
    ('CAN', 'Exportaciones intrarregionales / totales', 3.0, '%', 1969, 'Cálculo propio con UN Comtrade y WITS (hoja CAN_intrarregional)', 'https://comtradeapi.un.org'),
    ('CAN', 'Exportaciones intrarregionales / totales', 6.0, '%', 1976, 'Cálculo propio con UN Comtrade y WITS (hoja CAN_intrarregional)', 'https://comtradeapi.un.org'),
    ('CAN', 'Exportaciones intrarregionales / totales (mínimo)', 2.6, '%', 1985, 'Cálculo propio con UN Comtrade y WITS (hoja CAN_intrarregional)', 'https://comtradeapi.un.org'),
    ('CAN', 'Exportaciones intrarregionales / totales (máximo)', 13.9, '%', 1998, 'Cálculo propio con UN Comtrade y WITS (hoja CAN_intrarregional)', 'https://comtradeapi.un.org'),
    ('CAN', 'Exportaciones intrarregionales / totales', 6.0, '%', 2023, 'Cálculo propio con UN Comtrade y WITS (hoja CAN_intrarregional)', 'https://wits.worldbank.org'),
    ('CAN', 'Valor de las exportaciones intrarregionales (con Venezuela)', 9714.7, 'millones USD', 2006, 'Cálculo propio con UN Comtrade y WITS (hoja CAN_intrarregional)', 'https://wits.worldbank.org'),
    ('CAN', 'Valor de las exportaciones intrarregionales (sin Venezuela)', 5935.4, 'millones USD', 2007, 'Cálculo propio con UN Comtrade y WITS (hoja CAN_intrarregional)', 'https://wits.worldbank.org'),
    ('CAN', 'Valor de las exportaciones intrarregionales (máximo)', 11110.1, 'millones USD', 2012, 'Cálculo propio con UN Comtrade y WITS (hoja CAN_intrarregional)', 'https://wits.worldbank.org'),
    ('CAN', 'Exportaciones intracomunitarias (dato oficial CAN)', 9152, 'millones USD', 2024,
     'Comunidad Andina, citada por La Cámara (2025)', 'https://lacamara.pe/can-exportaciones-logran-us-165-000-millones-en-2024-con-aumento-del-5-5/'),
    ('CAN', 'Peso del bloque en sus exportaciones (dato oficial CAN)', 5.5, '%', 2024,
     'Comunidad Andina, citada por La Cámara (2025)', 'https://lacamara.pe/can-exportaciones-logran-us-165-000-millones-en-2024-con-aumento-del-5-5/'),
    ('CAN', 'Manufacturas en las exportaciones intracomunitarias', 82.9, '%', 2024,
     'Comunidad Andina, citada por La Cámara (2025)', 'https://lacamara.pe/can-exportaciones-logran-us-165-000-millones-en-2024-con-aumento-del-5-5/'),
    ('CAN', 'Destinos de las exportaciones por miembro', None, '%', 2023, 'Cálculo propio con WITS (hoja CAN_destinos_2023)', 'https://wits.worldbank.org'),
    ('MERCOSUR', 'Exportaciones intrarregionales / totales', 9.4, '%', 1970, 'Cálculo propio con UN Comtrade (hoja MERCOSUR_intrarregional)', 'https://comtradeapi.un.org'),
    ('MERCOSUR', 'Exportaciones intrarregionales / totales (mínimo)', 5.5, '%', 1985, 'Cálculo propio con UN Comtrade (hoja MERCOSUR_intrarregional)', 'https://comtradeapi.un.org'),
    ('MERCOSUR', 'Exportaciones intrarregionales / totales', 8.9, '%', 1990, 'Cálculo propio con UN Comtrade (hoja MERCOSUR_intrarregional)', 'https://comtradeapi.un.org'),
    ('MERCOSUR', 'Exportaciones intrarregionales / totales (máximo)', 25.0, '%', 1998, 'Cálculo propio con WITS (hoja MERCOSUR_intrarregional)', 'https://wits.worldbank.org'),
    ('MERCOSUR', 'Exportaciones intrarregionales / totales', 12.8, '%', 2002, 'Cálculo propio con WITS (hoja MERCOSUR_intrarregional)', 'https://wits.worldbank.org'),
    ('MERCOSUR', 'Exportaciones intrarregionales / totales', 11.3, '%', 2023, 'Cálculo propio con WITS (hoja MERCOSUR_intrarregional)', 'https://wits.worldbank.org'),
    ('MERCOSUR', 'Destinos de las exportaciones por miembro (PRY 64 %, URY 27 %, ARG 22 %, BRA 7 % al bloque; BRA 31 % a China)', None, '%', 2023, 'Cálculo propio con WITS (hoja MERCOSUR_destinos_2023)', 'https://wits.worldbank.org'),
    ('NAFTA', 'Exportaciones intrarregionales / totales', 35.5, '%', 1981, 'Cálculo propio con UN Comtrade (hoja NAFTA_intrarregional)', 'https://comtradeapi.un.org'),
    ('NAFTA', 'Exportaciones intrarregionales / totales', 41.0, '%', 1989, 'Cálculo propio con UN Comtrade (hoja NAFTA_intrarregional)', 'https://comtradeapi.un.org'),
    ('NAFTA', 'Exportaciones intrarregionales / totales', 48.2, '%', 1994, 'Cálculo propio con UN Comtrade (hoja NAFTA_intrarregional)', 'https://comtradeapi.un.org'),
    ('NAFTA', 'Exportaciones intrarregionales / totales (máximo)', 56.1, '%', 2004, 'Cálculo propio con WITS (hoja NAFTA_intrarregional)', 'https://wits.worldbank.org'),
    ('NAFTA', 'Exportaciones intrarregionales / totales', 48.0, '%', 2009, 'Cálculo propio con WITS (hoja NAFTA_intrarregional)', 'https://wits.worldbank.org'),
    ('NAFTA', 'Exportaciones intrarregionales / totales', 50.8, '%', 2023, 'Cálculo propio con WITS (hoja NAFTA_intrarregional)', 'https://wits.worldbank.org'),
    ('NAFTA', 'Exportaciones de México a EE. UU. / totales', 80.0, '%', 2023, 'Cálculo propio con WITS (hoja Exportaciones_bilaterales)', 'https://wits.worldbank.org'),
    ('NAFTA', 'Exportaciones de Canadá a EE. UU. / totales', 77.3, '%', 2023, 'Cálculo propio con WITS', 'https://wits.worldbank.org'),
    ('NAFTA', 'Exportaciones de EE. UU. a Canadá / totales', 17.5, '%', 2023, 'Cálculo propio con WITS', 'https://wits.worldbank.org'),
    ('NAFTA', 'Exportaciones de EE. UU. a México / totales', 16.0, '%', 2023, 'Cálculo propio con WITS', 'https://wits.worldbank.org'),
    ('NAFTA', 'Importaciones de EE. UU. desde México', 480.1, 'miles de millones USD', 2023, 'WITS (hoja USA_importaciones)', 'https://wits.worldbank.org'),
    ('NAFTA', 'Importaciones de EE. UU. desde China', 448.0, 'miles de millones USD', 2023, 'WITS (hoja USA_importaciones)', 'https://wits.worldbank.org'),
    ('NAFTA', 'Importaciones de EE. UU. desde Canadá', 429.6, 'miles de millones USD', 2023, 'WITS (hoja USA_importaciones)', 'https://wits.worldbank.org'),
    ('NAFTA', 'Cuota de México en la producción de vehículos de Norteamérica', 8.8, '%', 1999, 'OICA (hoja NAFTA_vehiculos)', 'https://www.oica.net/category/production-statistics/1999-statistics'),
    ('NAFTA', 'Cuota de México en la producción de vehículos de Norteamérica', 26.2, '%', 2024, 'OICA vía statbase.org (hoja NAFTA_vehiculos)', 'https://statbase.org/datasets/road-transportation/motor-vehicle-production/'),
    ('NAFTA', 'Efecto del NAFTA en el bienestar de México / EE. UU. / Canadá', '1,31 / 0,08 / -0,06', '%', 2015, 'Caliendo y Parro (2015)', 'https://www.nber.org/papers/w18508'),
    ('NAFTA', 'Efecto estimado del USMCA en el PIB real de EE. UU.', 0.35, '%', 2019, 'USITC (2019)', 'https://www.usitc.gov/press_room/news_release/2019/er0418ll1087.htm'),
    ('EFTA', 'Exportaciones intrarregionales / totales (Islandia, Noruega y Suiza)', 0.46, '%', 2023, 'Cálculo propio con WITS (destinos.csv)', 'https://wits.worldbank.org'),
    ('EFTA', 'Exportaciones a la UE-27 / totales: Noruega', 67.5, '%', 2023, 'Cálculo propio con WITS (hoja EFTA_destinos_2023)', 'https://wits.worldbank.org'),
    ('EFTA', 'Exportaciones a la UE-27 / totales: Islandia', 63.1, '%', 2023, 'Cálculo propio con WITS (hoja EFTA_destinos_2023)', 'https://wits.worldbank.org'),
    ('EFTA', 'Exportaciones a la UE-27 / totales: Suiza', 40.0, '%', 2023, 'Cálculo propio con WITS (hoja EFTA_destinos_2023)', 'https://wits.worldbank.org'),
    ('EFTA', 'Exportaciones a Reino Unido / totales: Noruega', 19.0, '%', 2023, 'Cálculo propio con WITS (hoja EFTA_destinos_2023)', 'https://wits.worldbank.org'),
    ('EFTA', 'Referéndum de Islandia sobre reanudar la negociación con la UE: votos en contra', 52.8, '%', 2026,
     'LIGA.net (2026)', 'https://news.liga.net/en/world/news/iceland-voted-against-resuming-eu-accession-negotiations-in-a-referendum'),
    ('CAN', 'Tasa de seguridad de Ecuador sobre importaciones colombianas (inicial)', 30, '%', 2026,
     'Portafolio (2026)', 'https://www.portafolio.co/negocios/comercio/de-30-a-50-la-cronologia-de-la-guerra-comercial-que-enfrenta-a-colombia-y-ecuador-489248'),
    ('CEFTA', 'Exportaciones intrarregionales / totales (sin Kosovo)', 15.1, '%', 2007, 'Cálculo propio con WITS (hoja CEFTA_intrarregional)', 'https://wits.worldbank.org'),
    ('CEFTA', 'Exportaciones intrarregionales / totales (sin Kosovo; mínimo)', 13.2, '%', 2017, 'Cálculo propio con WITS (hoja CEFTA_intrarregional)', 'https://wits.worldbank.org'),
    ('CEFTA', 'Exportaciones intrarregionales / totales (sin Kosovo)', 15.1, '%', 2023, 'Cálculo propio con WITS (hoja CEFTA_intrarregional)', 'https://wits.worldbank.org'),
    ('CEFTA', 'Valor de las exportaciones intrarregionales (sin Kosovo)', 8.8, 'miles de millones USD', 2023, 'Cálculo propio con WITS (hoja CEFTA_intrarregional)', 'https://wits.worldbank.org'),
    ('CEFTA', 'Peso de Serbia en las exportaciones intrarregionales', 54.3, '%', 2023, 'Cálculo propio con WITS (Exportaciones_bilaterales)', 'https://wits.worldbank.org'),
    ('CEFTA', 'Destinos de las exportaciones por miembro (UE-27: MKD 79 %, BIH 73 %, ALB 72 %, MDA 65 %, SRB 63 %, MNE 36 %; bloque: MNE 45 %)', None, '%', 2023, 'Cálculo propio con WITS (hoja CEFTA_destinos_2023)', 'https://wits.worldbank.org'),
    ('CEFTA', 'Presupuesto de la Secretaría del CEFTA', 4.57, 'millones EUR', 2026, 'Conclusiones ministeriales del Comité Mixto, 2 de diciembre de 2025', 'https://cefta.int/wp-content/uploads/2025/12/Ministerial-conclusions_2-December-2025.pdf'),
    ('CEFTA', 'Subvención de la UE a la Secretaría (de 9,25 millones en total)', 7, 'millones EUR', '2025-2028', 'Conclusiones ministeriales del Comité Mixto, 2 de diciembre de 2025', 'https://cefta.int/wp-content/uploads/2025/12/Ministerial-conclusions_2-December-2025.pdf'),
    ('CEFTA', 'Mecanismo de Reforma y Crecimiento para los Balcanes occidentales (2 mil millones en subvenciones y 4 mil millones en préstamos)', 6, 'miles de millones EUR', '2024-2027', 'Comisión Europea, Plan de Crecimiento para los Balcanes occidentales', 'https://enlargement.ec.europa.eu/enlargement-policy/growth-plan-western-balkans_en'),
    ('CEFTA', 'Capítulos de adhesión cerrados provisionalmente por Montenegro', 21, 'capítulos', 2026, 'New Union Post (12/10/2026)', 'https://newunionpost.eu/2026/10/12/montenegro-eu-accession-negotiations-2/'),
    ('AfCFTA', 'Exportaciones intraafricanas / totales (países que declaran)', 11.8, '%', 1996, 'Cálculo propio con WITS (hoja AFCFTA_intrarregional)', 'https://wits.worldbank.org'),
    ('AfCFTA', 'Exportaciones intraafricanas / totales (países que declaran; 40 de 53)', 20.0, '%', 2023, 'Cálculo propio con WITS (hoja AFCFTA_intrarregional)', 'https://wits.worldbank.org'),
    ('ASEAN', 'Exportaciones intrarregionales / totales', 22.1, '%', 2023, 'Cálculo propio con WITS (hoja ASEAN_intrarregional)', 'https://wits.worldbank.org'),
    ('UE-27', 'Exportaciones intrarregionales / totales', 59.7, '%', 2023, 'Cálculo propio con WITS (hoja UE27_intrarregional)', 'https://wits.worldbank.org'),
    ('AfCFTA', 'Ratificaciones (de 54 signatarios)', 50, 'países', 2026, 'tralac (2026)', 'https://www.tralac.org/resources/afcfta-negotiations-timeline.html'),
    ('AfCFTA', 'Participantes al cierre de la fase de comercio guiado', 39, 'países', 2025, 'tralac (2026)', 'https://www.tralac.org/resources/afcfta-negotiations-timeline.html'),
    ('AfCFTA', 'Ratificaciones del Protocolo de libre circulación de personas (de 15 necesarias)', 4, 'países', 2025, 'Ghana News Agency (2025)', 'https://gna.org.gh/2025/03/stakeholders-dialogues-progress-on-ratifying-aus-free-movement-of-persons-protocol/'),
    ('AfCFTA', 'Aumento de las exportaciones de África en 2035 con más IED (intraafricanas: 109 %)', 32, '%', 2022, 'Banco Mundial (2022)', 'https://www.worldbank.org/en/topic/trade/publication/making-the-most-of-the-african-continental-free-trade-area'),
]


def main():
    from openpyxl import Workbook, load_workbook
    wb = load_workbook(XLSX) if XLSX.exists() else Workbook()
    if wb.sheetnames == ['Sheet']:
        del wb['Sheet']
    if 'Cifras_citadas' in wb.sheetnames:
        del wb['Cifras_citadas']
    ws = wb.create_sheet('Cifras_citadas', 0)
    ws.append(['Cifras citadas en el tema 3.B.35, con su fuente'])
    ws.append([])
    ws.append(['Acuerdo', 'Dato', 'Valor', 'Unidad', 'Año', 'Fuente', 'Enlace'])
    for fila in CIFRAS:
        ws.append(list(fila))
    wb.save(XLSX)
    print('Hoja Cifras_citadas escrita en', XLSX)


if __name__ == '__main__':
    main()
