#!/usr/bin/env python3
"""Genera Img/<CLAVE>_gobernanza.tikz: (a) organigrama de gobernanza y (b) vertientes de la integración y su grado.

Formato común del tema (nota de \\modificaciones, 14/10/2026):
(a) organigrama mínimo: órganos (nombre y, debajo, quiénes lo forman o qué tipo de órgano es), marcos que los agrupan y
    flechas con la relación (quién orienta, decide, apoya o controla). El color indica la naturaleza del órgano; el borde
    discontinuo, que sus competencias son limitadas o no las reconocen todos los miembros. Sin resumir lo que hace cada
    órgano: eso está en el texto.
(b) siete vertientes, cada una en cuatro grados (nada, bajo, parcial, pleno): el círculo hueco es lo previsto en los
    tratados vigentes y el relleno lo alcanzado en octubre de 2026. Es una valoración propia a partir del texto del tema.
Letra de 8 puntos (\\footnotesize), ancho total de 16 cm.
Uso, desde la carpeta del tema:
  python3 Code/gobernanza.py MCCA
  bash Code/generar_figura.sh MCCA_gobernanza
"""
import sys
from pathlib import Path

TIPOS = {   # naturaleza del órgano: (borde, relleno, texto de la leyenda)
    'intergub': ((30, 75, 135), (218, 232, 246), 'intergubernamental'),
    'supra': ((175, 55, 45), (247, 220, 212), 'supranacional'),
    'tecnico': ((105, 105, 105), (236, 236, 236), 'técnico o administrativo'),
    'judicial': ((105, 65, 140), (233, 223, 242), 'judicial o arbitral'),
    'parlamento': ((55, 125, 65), (223, 238, 214), 'parlamentario o consultivo'),
    'financiero': ((185, 125, 20), (252, 236, 206), 'financiero o monetario'),
    'estados': ((70, 70, 70), (255, 255, 255), ''),   # los Estados miembros, destinatarios de las normas (sin leyenda)
}
VERTIENTES = ['Libre comercio interno', 'Arancel exterior común', 'Servicios e inversión', 'Movilidad de personas',
              'Macro y moneda', 'Supranacionalidad', 'Política y seguridad']
GRADOS = ['Nada', 'Bajo', 'Parcial', 'Pleno']

GOBERNANZA = {
    'MCCA': {
        # órgano: (x, y, ancho, tipo, nombre, segunda línea, discontinuo)
        'organos': {
            'pres': (4.45, 4.6, 3.8, 'intergub', 'Reunión de Presidentes', 'órgano supremo', False),
            'parl': (1.3, 3.45, 2.5, 'parlamento', 'Parlamento', 'Centroamericano', True),
            'corte': (7.5, 3.5, 2.8, 'judicial', 'Corte de Justicia', 'Centroamericana', True),
            'contro': (1.3, 1.55, 2.2, 'judicial', 'Controversias', 'arbitraje', False),
            'comieco': (4.45, 1.55, 3.0, 'intergub', 'COMIECO', 'ministros de Economía', False),
            'sieca': (7.9, 1.55, 1.75, 'tecnico', 'SIECA', 'secretaría', False),
            'sg': (1.5, 0.0, 2.8, 'tecnico', 'Secretaría General', 'del SICA, vacante', True),
            'bcie': (4.45, 0.0, 2.4, 'financiero', 'BCIE', 'banco regional', False),
            'cmca': (7.4, 0.0, 2.8, 'financiero', 'Consejo Monetario', 'bancos centrales', False),
        },
        # marcos: (izquierda, abajo, derecha, arriba, rótulo); el rótulo va arriba a la derecha
        'marcos': [(0.0, -0.55, 8.95, 5.35, 'SICA'), (0.1, 0.85, 8.85, 2.65, 'Subsistema económico')],
        # flechas: (desde, hasta, rótulo, estilo): desde y hasta son órganos (con ancla opcional, 'pres.west') o
        # coordenadas 'x,y'; estilo 'o' = orienta o decide, 'a' = apoyo, 'c' = control o consulta
        'flechas': [('pres', 'comieco', 'directrices', 'o'), ('sieca', 'comieco', 'apoyo', 'a'),
                    ('parl.north', 'pres.west', 'recomienda', 'c'), ('corte', '7.5,2.65', 'jurisdicción', 'c', 'left')],
        # vertientes: (previsto, alcanzado), de 0 (nada) a 3 (pleno)
        'grados': [(3, 3), (3, 2), (3, 2), (3, 1), (3, 1), (2, 1), (2, 1)],
    },
    'CAN': {
        'organos': {
            'pres': (4.45, 4.95, 3.6, 'intergub', 'Consejo Presidencial', 'órgano supremo', False),
            'min': (1.6, 3.55, 3.2, 'intergub', 'Consejo de Ministros', 'de Exteriores', False),
            'com': (4.75, 3.55, 2.5, 'intergub', 'Comisión', 'de los gobiernos', False),
            'sg': (7.55, 3.55, 2.7, 'supra', 'Secretaría General', 'Lima', False),
            'est': (4.45, 2.15, 8.8, 'estados', 'Estados miembros', '', False),
            'tri': (1.6, 0.7, 3.2, 'judicial', 'Tribunal de Justicia', 'Quito', False),
            'parl': (4.75, 0.7, 2.6, 'parlamento', 'Parlamento', 'Andino', True),
            'caf': (7.55, 0.7, 2.7, 'financiero', 'CAF', 'banco de desarrollo', False),
        },
        'marcos': [],
        'flechas': [('pres', 'min.north', 'directrices', 'o', 'sloped, above'), ('pres', 'com.north', '', 'o'),
                    ('min', 'min|-est.north', 'Decisiones', 'o', 'left'), ('com', 'com|-est.north', 'Decisiones', 'o', 'left'),
                    ('sg', 'sg|-est.north', 'incumplimiento', 'c', 'left'), ('tri', 'tri|-est.south', 'sentencias', 'c', 'left'),
                    ('caf', 'caf|-est.south', 'financia', 'a', 'right')],
        'grados': [(3, 3), (3, 0), (3, 2), (3, 3), (2, 1), (3, 2), (2, 1)],
    },
    'NAFTA': {   # USMCA
        'organos': {
            'com': (4.45, 4.95, 4.2, 'intergub', 'Comisión de Libre Comercio', 'ministros de los tres países', False),
            'sec': (1.6, 3.55, 3.0, 'tecnico', 'Secretariado', 'secciones nacionales', False),
            'cmt': (7.3, 3.55, 3.1, 'tecnico', 'Comités y grupos', 'de trabajo', False),
            'est': (4.45, 2.15, 8.8, 'estados', 'Estados miembros', '', False),
            'pan': (1.1, 0.7, 2.15, 'judicial', 'Paneles', 'entre Estados', False),
            'bin': (3.35, 0.7, 2.15, 'judicial', 'Paneles', 'binacionales', False),
            'lab': (5.6, 0.7, 2.15, 'judicial', 'Mecanismo', 'laboral', False),
            'isds': (7.85, 0.7, 2.15, 'judicial', 'Arbitraje', 'de inversiones', True),
        },
        'marcos': [],
        'flechas': [('sec', 'com', 'apoyo', 'a', 'sloped, above'), ('com', 'cmt', 'supervisa', 'o', 'sloped, above'),
                    ('com', 'com|-est.north', 'interpreta', 'o', 'right'),
                    ('pan', 'pan|-est.south', 'resuelven', 'c', 'right'), ('bin', 'bin|-est.south', '', 'c'),
                    ('lab', 'lab|-est.south', '', 'c'), ('isds', 'isds|-est.south', '', 'c')],
        'grados': [(3, 3), (0, 0), (3, 3), (1, 1), (1, 1), (1, 1), (1, 1)],
    },
    'EFTA': {
        'organos': {
            'con': (2.25, 5.05, 3.7, 'intergub', 'Consejo de la EFTA', 'embajadores y ministros', False),
            'sec': (6.75, 5.05, 3.4, 'tecnico', 'Secretaría', 'Ginebra y Bruselas', False),
            'cm': (1.7, 3.05, 3.2, 'intergub', 'Comité Mixto del EEE', 'UE y EEE-EFTA', False),
            'esa': (4.85, 3.05, 2.8, 'supra', 'Órgano de Vigilancia', 'de la AELC', False),
            'tri': (7.65, 3.05, 2.4, 'judicial', 'Tribunal', 'de la AELC', False),
            'est': (4.45, 1.4, 8.6, 'estados', 'Islandia, Liechtenstein y Noruega', '', False),
            'sui': (4.45, -0.2, 8.8, 'intergub', 'Suiza y la UE: unos veinte comités mixtos', 'acuerdos bilaterales', False),
        },
        'marcos': [(0.0, 4.45, 8.95, 5.9, 'EFTA'), (0.0, 0.95, 8.95, 4.05, 'EEE (sin Suiza)')],
        'flechas': [('sec', 'con', 'apoyo', 'a'), ('cm', 'cm|-est.north', 'incorpora normas', 'o', 'right'),
                    ('esa', 'esa|-est.north', 'vigila', 'c', 'right'), ('tri', 'tri|-est.north', 'resuelve', 'c', 'right')],
        'grados': [(2, 2), (0, 0), (3, 2), (3, 3), (0, 0), (2, 2), (0, 0)],
    },
}
