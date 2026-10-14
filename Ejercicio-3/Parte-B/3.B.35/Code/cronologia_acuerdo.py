#!/usr/bin/env python3
"""Genera Img/<CLAVE>_cronologia.tikz: cronología de un acuerdo en el formato común del tema.

Formato (nota de \\modificaciones, 14/10/2026): etapas sombreadas con su nombre arriba (el color indica el tipo de
etapa, igual en todos los acuerdos), encima las estrategias que agrupan varias etapas, un carril de contexto (hechos
externos, en gris y cursiva) y los carriles del propio acuerdo. Cada hito es (año, texto) o (año, texto, lado), con
lado 'a' (encima) o 'b' (debajo); si no se indica, va donde quede más bajo. Las etiquetas se apilan solas en niveles
para no solaparse. Letra de 8 puntos (\\footnotesize), ancho total de 16 cm.
Fechas comprobadas en octubre de 2026 (fuentes en el pie de cada figura y en la bibliografía del tema).
Uso, desde la carpeta del tema:
  python3 Code/cronologia_acuerdo.py MCCA
  bash Code/generar_figura.sh MCCA_cronologia
"""
import sys
from pathlib import Path

X0, X1 = 2.75, 15.95        # cm del eje temporal (a la izquierda, los nombres de los carriles)
CM_POR_CARACTER = 0.142     # ancho medio de un carácter de 8 puntos en sans serif
NIVEL = 0.34                # alto de cada nivel de etiquetas
SEP = 0.16                  # distancia del carril al primer nivel

# Tipos de etapa: el mismo color significa lo mismo en todas las cronologías
ETAPAS = {
    'origen': (236, 236, 236),         # gestación y negociación
    'impulso': (223, 238, 214),        # avance o auge
    'crisis': (247, 220, 212),         # crisis, conflicto o estancamiento
    'relanzamiento': (218, 232, 246),  # refundación o reforma
    'terceros': (252, 236, 206),       # acuerdos con terceros, geometría variable
}
CONTEXTO = (115, 115, 115)

CRONOLOGIAS = {
    'MCCA': {
        'eje': (1950, 2027, range(1950, 2030, 10)),
        'estrategias': [(1951, 1990, 'Regionalismo cerrado'), (1990, 2027, 'Regionalismo abierto')],
        'etapas': [(1951, 1960, 'origen', 'Gestación'), (1960, 1969, 'impulso', 'Auge'),
                   (1969, 1990, 'crisis', 'Crisis y guerras'), (1990, 2004, 'relanzamiento', 'Relanzamiento'),
                   (2004, 2027, 'terceros', 'Acuerdos con terceros')],
        # sin carril de instituciones (las enseña la figura de gobernanza; el usuario lo pidió el 14/10/2026)
        'contexto': [
            (1969, 'guerra El Salvador-Honduras'), (1979, 'revolución sandinista'), (1982, 'crisis de la deuda'),
            (1984, 'Iniciativa de la Cuenca del Caribe'), (1987, 'paz de Esquipulas'), (2025, 'aranceles de EE.\\,UU.')],
        'carriles': [
            ('Miembros', (120, 120, 120), [
                (1960, 'Guatemala, El Salvador, Honduras, Nicaragua'), (1963, 'Costa Rica'),
                (1971, 'Honduras se retira de hecho'), (2013, 'Panamá'),
                (2024, 'Nicaragua deja el SICA')]),
            ('Comercio', (233, 160, 40), [
                (1958, 'Tratado Multilateral'), (1960, 'Tratado General de Managua'),
                (2002, 'servicios e inversión'), (2006, 'DR-CAFTA'), (2013, 'Acuerdo con la UE'),
                (2017, 'unión aduanera Guatemala-Honduras'), (2018, 'se suma El Salvador')]),
        ],
    },
    'CAN': {   # sustituye a la cronología normativa de Code/cronologia_bloque.py (sin carril de instituciones)
        'eje': (1965, 2027, range(1970, 2030, 10)),
        'estrategias': [(1969, 1987, 'Regionalismo cerrado'), (1987, 2027, 'Regionalismo abierto')],
        'etapas': [(1969, 1980, 'impulso', 'Auge'), (1980, 1987, 'crisis', 'Crisis'),
                   (1987, 1998, 'relanzamiento', 'Relanzamiento'),
                   (1998, 2027, 'terceros', 'Divergencia y acuerdos con terceros')],
        'contexto': [
            (1973, 'golpe de Estado en Chile'), (1982, 'crisis de la deuda'), (2003, 'auge de las materias primas'),
            (2006, 'Colombia y Perú firman TLC con EE.\\,UU.'), (2011, 'Alianza del Pacífico'), (2024, 'puerto de Chancay')],
        'carriles': [
            ('Miembros', (120, 120, 120), [
                (1969, 'Bolivia, Chile, Colombia, Ecuador, Perú'), (1973, 'entra Venezuela'), (1976, 'sale Chile'),
                (1992, 'Perú se suspende'), (2006, 'sale Venezuela'), (2024, 'Bolivia, también en MERCOSUR')]),
            ('Comercio', (233, 160, 40), [
                (1969, 'zona de libre comercio en etapas'), (1993, 'zona de libre comercio plena'),
                (1995, 'arancel exterior común'), (2007, 'se permite no aplicarlo'), (2015, 'queda sin efecto'),
                (2026, 'guerra arancelaria Colombia-Ecuador')]),
            ('Inversión\\\\extranjera', (200, 76, 58), [
                (1970, 'Decisión 24: control del capital extranjero'), (1987, 'Decisión 220: flexibiliza'),
                (1991, 'Decisión 291: trato nacional')]),
        ],
    },
    'NAFTA': {
        'eje': (1980, 2027, range(1980, 2030, 10)),
        'etapas': [(1982, 1994, 'origen', 'Apertura y negociación'), (1994, 2001, 'impulso', 'Auge'),
                   (2001, 2017, 'crisis', 'Competencia de China'), (2017, 2027, 'relanzamiento', 'Renegociación')],
        'contexto': [
            (1982, 'crisis de la deuda'), (1986, 'México entra en el GATT'), (1994, 'crisis del peso'),
            (2001, 'China entra en la OMC'), (2008, 'crisis financiera'), (2017, 'Trump abre la renegociación'),
            (2025, 'aranceles de EE.\\,UU.')],
        'carriles': [
            ('Miembros', (120, 120, 120), [(1989, 'Canadá y EE.\\,UU. (CUSFTA)'), (1994, 'se suma México')]),
            ('Comercio', (233, 160, 40), [
                (1992, 'firma del NAFTA'), (1994, 'entra en vigor'), (2008, 'fin de la desgravación'),
                (2018, 'firma del USMCA'), (2020, 'entra en vigor el USMCA'), (2023, 'reglas de origen del automóvil plenas'),
                (2026, 'revisión: EE.\\,UU. no lo renueva')]),
        ],
    },
    'EFTA': {   # sin carril de miembros: las entradas y salidas están en EFTA_arquitectura (valoración)
        'eje': (1955, 2027, range(1960, 2030, 10)),
        'etapas': [(1956, 1960, 'origen', 'Origen'), (1960, 1973, 'impulso', 'Alternativa a la CEE'),
                   (1973, 1994, 'crisis', 'Vaciamiento'), (1994, 2027, 'relanzamiento', 'EEE y vía bilateral suiza')],
        'contexto': [
            (1957, 'Tratados de Roma'), (1973, 'primera ampliación de la CEE'), (1986, 'Acta Única Europea'),
            (1993, 'mercado único'), (2004, 'ampliación al Este'), (2020, 'Brexit')],
        'carriles': [
            ('Convenio\\\\y terceros', (233, 160, 40), [
                (1960, 'Convenio de Estocolmo'), (1966, 'libre comercio industrial'), (2001, 'Convenio de Vaduz'),
                (2025, 'acuerdo con la India en vigor')]),
            ('Relación\\\\con la UE', (30, 75, 135), [
                (1972, 'acuerdos de libre comercio con la CEE'), (1984, 'Declaración de Luxemburgo'),
                (1992, 'Suiza rechaza el EEE'), (1994, 'EEE en vigor'), (1999, 'Bilaterales I'),
                (2021, 'Suiza abandona el acuerdo marco'), (2026, 'Bilaterales III; Islandia no reanuda')]),
        ],
    },
}
