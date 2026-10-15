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
    'MERCOSUR': {
        'organos': {
            'cmc': (4.45, 4.95, 4.0, 'intergub', 'Consejo del Mercado Común', 'ministros; decide por consenso', False),
            'gmc': (1.75, 3.55, 3.3, 'intergub', 'Grupo Mercado Común', 'órgano ejecutivo', False),
            'ccm': (7.15, 3.55, 3.3, 'intergub', 'Comisión de Comercio', 'política comercial común', False),
            'est': (4.45, 2.15, 8.8, 'estados', 'Estados parte (incorporan las normas)', '', False),
            'tpr': (1.55, 0.7, 3.0, 'judicial', 'Tribunal Permanente', 'de Revisión', False),
            'par': (3.95, 0.7, 1.7, 'parlamento', 'Parlasur', 'consultivo', True),
            'foc': (5.95, 0.7, 2.0, 'financiero', 'FOCEM', 'convergencia', False),
            'sec': (8.0, 0.7, 1.9, 'tecnico', 'Secretaría', 'Montevideo', False),
        },
        'marcos': [],
        'flechas': [('cmc', 'gmc.north', 'directrices', 'o', 'sloped, above'), ('cmc', 'ccm.north', '', 'o'),
                    ('cmc', 'cmc|-est.north', 'normas', 'o', 'right'), ('tpr', 'tpr|-est.south', 'laudos', 'c', 'right'),
                    ('foc', 'foc|-est.south', 'financia', 'a', 'right')],
        'grados': [(3, 2), (3, 2), (3, 1), (3, 2), (2, 1), (1, 1), (2, 2)],
    },
    'CEFTA': {
        'organos': {
            'cm': (2.6, 4.95, 4.4, 'intergub', 'Comité Mixto', 'ministros; por consenso', False),
            'ue': (7.75, 4.95, 2.3, 'financiero', 'Comisión Europea', '', False),
            'sub': (4.7, 3.55, 3.0, 'tecnico', 'Subcomités y grupos', 'de trabajo', False),
            'sec': (7.75, 3.55, 2.3, 'tecnico', 'Secretaría', 'Bruselas', False),
            'est': (4.45, 2.15, 8.8, 'estados', 'Partes del CEFTA', '', False),
            'dif': (4.45, 0.7, 4.0, 'judicial', 'Solución de diferencias', 'protocolo en ratificación', True),
        },
        'marcos': [],
        'flechas': [('cm', 'sub.north', 'encarga', 'o', 'sloped, above'), ('ue', 'sec', 'financia', 'a', 'right'),
                    ('cm', 'cm|-est.north', 'decisiones', 'o', 'left'),
                    ('dif', 'dif|-est.south', 'arbitraje', 'c', 'right')],
        'grados': [(3, 2), (0, 0), (3, 1), (2, 1), (0, 0), (0, 0), (1, 1)],
    },
    'AfCFTA': {
        'organos': {
            'asa': (4.45, 4.95, 4.4, 'intergub', 'Asamblea de la Unión Africana', 'jefes de Estado', False),
            'min': (1.75, 3.55, 3.3, 'intergub', 'Consejo de Ministros', 'de Comercio', False),
            'sec': (7.15, 3.55, 3.3, 'tecnico', 'Secretaría', 'Acra', False),
            'est': (4.45, 2.15, 8.8, 'estados', 'Estados parte y ocho comunidades económicas regionales', '', False),
            'osd': (2.2, 0.7, 3.4, 'judicial', 'Órgano de Solución', 'de Diferencias', False),
            'pap': (6.7, 0.7, 3.4, 'financiero', 'PAPSS', 'pagos en monedas locales', False),
        },
        'marcos': [],
        'flechas': [('asa', 'min.north', 'orienta', 'o', 'sloped, above'), ('sec', 'min', 'coordina', 'a', 'above'),
                    ('min', 'min|-est.north', 'decisiones', 'o', 'right'), ('osd', 'osd|-est.south', 'resuelve', 'c', 'right'),
                    ('pap', 'pap|-est.south', 'liquida', 'a', 'right')],
        'grados': [(3, 1), (3, 0), (3, 1), (3, 0), (3, 1), (1, 1), (2, 1)],
    },
    'PAFTA': {
        'organos': {
            'ces': (4.45, 4.95, 4.4, 'intergub', 'Consejo Económico y Social', 'Liga Árabe; decide por consenso', False),
            'com': (1.75, 3.55, 3.3, 'tecnico', 'Comités', 'de seguimiento', False),
            'sg': (7.15, 3.55, 3.3, 'tecnico', 'Secretaría General', 'de la Liga, El Cairo', False),
            'est': (4.45, 2.15, 8.8, 'estados', 'Estados parte', '', False),
            'fma': (2.2, 0.7, 3.4, 'financiero', 'Fondo Monetario Árabe', 'Abu Dabi', False),
            'dif': (6.7, 0.7, 3.4, 'judicial', 'Solución de diferencias', 'sin mecanismo eficaz', True),
        },
        'marcos': [],
        'flechas': [('ces', 'com.north', 'encarga', 'o', 'sloped, above'), ('sg', 'ces', 'apoyo', 'a', 'sloped, above'),
                    ('ces', 'ces|-est.north', 'decisiones', 'o', 'right'), ('fma', 'fma|-est.south', 'financia', 'a', 'right')],
        'grados': [(3, 2), (3, 0), (2, 1), (2, 0), (1, 0), (0, 0), (3, 1)],
    },
    'ASEAN': {
        'organos': {
            'cum': (4.45, 4.95, 4.0, 'intergub', 'Cumbre de la ASEAN', 'jefes de Estado; por consenso', False),
            'cc': (1.75, 3.55, 3.3, 'intergub', 'Consejo de Coordinación', 'ministros de Exteriores', False),
            'tres': (7.15, 3.55, 3.3, 'intergub', 'Tres Consejos', 'de la Comunidad', False),
            'est': (4.45, 2.15, 8.8, 'estados', 'Estados miembros (no injerencia)', '', False),
            'sec': (1.1, 0.7, 2.15, 'tecnico', 'Secretaría', 'Yakarta', False),
            'aipa': (3.35, 0.7, 2.15, 'parlamento', 'Asamblea', 'Interparlamentaria', True),
            'dif': (5.6, 0.7, 2.15, 'judicial', 'Diferencias', 'protocolo de 2004', True),
            'cmi': (7.85, 0.7, 2.15, 'financiero', 'Chiang Mai', 'con China, Japón, Corea', False),
        },
        'marcos': [],
        'flechas': [('cum', 'cc.north', 'orienta', 'o', 'sloped, above'), ('cum', 'tres.north', '', 'o'),
                    ('cum', 'cum|-est.north', 'decide', 'o', 'right'), ('sec', 'sec|-est.south', 'apoyo', 'a', 'right'),
                    ('dif', 'dif|-est.south', '', 'c'), ('cmi', 'cmi|-est.south', 'liquidez', 'a', 'right')],
        'grados': [(3, 2), (0, 0), (2, 1), (1, 1), (1, 1), (0, 0), (2, 2)],
    },
    'CCG': {
        'organos': {
            'sup': (4.45, 4.95, 4.0, 'intergub', 'Consejo Supremo', 'jefes de Estado; unanimidad', False),
            'min': (1.75, 3.55, 3.3, 'intergub', 'Consejo Ministerial', 'ministros de Exteriores', False),
            'sg': (7.15, 3.55, 3.3, 'tecnico', 'Secretaría General', 'Riad', False),
            'est': (4.45, 2.15, 8.8, 'estados', 'Estados miembros', '', False),
            'dif': (1.1, 0.7, 2.15, 'judicial', 'Comisión', 'de Controversias', True),
            'cons': (3.35, 0.7, 2.15, 'parlamento', 'Comisión', 'Consultiva', True),
            'mon': (5.6, 0.7, 2.15, 'financiero', 'Consejo', 'Monetario (4)', True),
            'esc': (7.85, 0.7, 2.15, 'intergub', 'Escudo de', 'la Península', False),
        },
        'marcos': [],
        'flechas': [('sup', 'min.north', 'orienta', 'o', 'sloped, above'), ('sg', 'min', 'prepara', 'a', 'above'),
                    ('sup', 'sup|-est.north', 'decide', 'o', 'right'), ('dif', 'dif|-est.south', '', 'c'),
                    ('mon', 'mon|-est.south', '', 'a'), ('esc', 'esc|-est.south', 'defensa', 'a', 'right')],
        'grados': [(3, 2), (3, 2), (3, 2), (3, 2), (3, 1), (0, 0), (3, 2)],
    },
    'RCEP': {
        'organos': {
            'min': (2.6, 4.95, 4.4, 'intergub', 'Reunión de Ministros', 'por consenso', False),
            'sec': (7.75, 4.95, 2.3, 'tecnico', 'Secretaría', 'pequeña', False),
            'cc': (2.6, 3.55, 4.4, 'intergub', 'Comité Conjunto', 'altos funcionarios', False),
            'sub': (7.75, 3.55, 2.3, 'tecnico', 'Subcomités', 'cuatro', False),
            'est': (4.45, 2.15, 8.8, 'estados', 'Partes (diez de la ASEAN y cinco socios)', '', False),
            'pan': (4.45, 0.7, 4.0, 'judicial', 'Paneles', 'solución de diferencias', False),
        },
        'marcos': [],
        'flechas': [('min', 'cc', 'orienta', 'o', 'right'), ('cc', 'sub', 'encarga', 'o', 'above'), ('sec', 'min', 'apoyo', 'a', 'above'),
                    ('cc', 'cc|-est.north', 'aplica', 'o', 'right'), ('pan', 'pan|-est.south', 'resuelven', 'c', 'right')],
        'grados': [(2, 1), (0, 0), (1, 1), (1, 1), (0, 0), (0, 0), (0, 0)],
    },
    'CPTPP': {
        'organos': {
            'com': (4.45, 4.95, 4.2, 'intergub', 'Comisión del CPTPP', 'ministros; por consenso', False),
            'cmt': (1.75, 3.55, 3.3, 'tecnico', 'Comités', 'y grupos de trabajo', False),
            'dep': (7.15, 3.55, 3.3, 'tecnico', 'Depositario', 'Nueva Zelanda', False),
            'est': (4.45, 2.15, 8.8, 'estados', 'Partes (doce)', '', False),
            'pan': (1.6, 0.7, 2.9, 'judicial', 'Paneles', 'entre Estados', False),
            'isds': (4.45, 0.7, 2.4, 'judicial', 'Arbitraje', 'de inversiones', True),
            'lab': (7.3, 0.7, 2.9, 'judicial', 'Consultas', 'laborales y ambientales', False),
        },
        'marcos': [],
        'flechas': [('com', 'cmt.north', 'supervisa', 'o', 'sloped, above'), ('com', 'com|-est.north', 'interpreta y admite', 'o', 'right'),
                    ('pan', 'pan|-est.south', 'resuelven', 'c', 'right'), ('isds', 'isds|-est.south', '', 'c'),
                    ('lab', 'lab|-est.south', '', 'c')],
        'grados': [(3, 2), (0, 0), (3, 2), (1, 1), (0, 0), (0, 0), (0, 0)],
    },
    'UEE': {
        'organos': {
            'sup': (4.45, 4.95, 4.4, 'intergub', 'Consejo Económico Supremo', 'jefes de Estado; consenso', False),
            'int': (1.75, 3.55, 3.3, 'intergub', 'Consejo Intergubernamental', 'primeros ministros', False),
            'com': (7.15, 3.55, 3.3, 'supra', 'Comisión Económica', 'Moscú', False),
            'est': (4.45, 2.15, 8.8, 'estados', 'Estados miembros', '', False),
            'tri': (2.2, 0.7, 3.4, 'judicial', 'Tribunal', 'Minsk', True),
            'ban': (6.7, 0.7, 3.4, 'financiero', 'Banco Euroasiático', 'de Desarrollo, Almaty', False),
        },
        'marcos': [],
        'flechas': [('sup', 'int.north', 'orienta', 'o', 'sloped, above'), ('sup', 'com.north', '', 'o'),
                    ('int', 'int|-est.north', '', 'o'), ('com', 'com|-est.north', 'decisiones', 'o', 'left'),
                    ('tri', 'tri|-est.south', 'sentencias', 'c', 'right'), ('ban', 'ban|-est.south', 'financia', 'a', 'right')],
        'grados': [(3, 2), (3, 2), (3, 1), (3, 3), (2, 1), (2, 1), (0, 0)],
    },
}


def rgb(nombre, c):
    return '\\definecolor{%s}{RGB}{%d,%d,%d}' % (nombre, *c)


def main(clave):
    g = GOBERNANZA[clave]
    # los colores, dentro del tikzpicture: fuera, cada salto de línea añade un espacio a la izquierda de la figura
    o = [f'% Generado por Code/gobernanza.py ({clave}).', '\\begin{tikzpicture}[font=\\sffamily\\footnotesize]']
    for t, (borde, relleno, _) in TIPOS.items():
        o += ['  ' + rgb(f'b{t}', borde), '  ' + rgb(f'f{t}', relleno)]
    # (a) organigrama
    alto_a = max([m[3] for m in g['marcos']] + [v[1] + 0.45 for v in g['organos'].values()])
    o.append(f'  \\node[anchor=south west, font=\\sffamily\\small, inner sep=0pt] at (0,{alto_a + 0.25:.2f}) {{(a) Gobernanza}};')
    for i, (x0, y0, x1, y1, rotulo) in enumerate(g['marcos']):
        o.append(f'  \\draw[black!45, line width=0.5pt, {"densely dashed" if i else ""}, rounded corners=3pt] ({x0},{y0}) rectangle ({x1},{y1});')
        o.append(f'  \\node[anchor=north east, inner sep=2.5pt, font=\\sffamily\\footnotesize\\bfseries, text=black!60] at ({x1},{y1}) {{{rotulo}}};')
    usados = []
    for k, (x, y, ancho, tipo, nombre, linea2, disc) in g['organos'].items():
        usados.append(tipo)
        estilo = ', densely dashed' if disc else ''
        o.append(f'  \\node[draw=b{tipo}, fill=f{tipo}, line width=0.7pt{estilo}, rounded corners=2pt, align=center, '
                 f'minimum width={ancho}cm, text width={ancho - 0.1:.2f}cm, inner sep=2pt] ({k}) at ({x},{y}) '
                 f'{{\\textbf{{{nombre}}}' + (f'\\\\[-1pt]{{\\color{{black!70}}{linea2}}}' if linea2 else '') + '};')
    estilos = {'o': 'black!75, line width=0.7pt', 'a': 'black!55, line width=0.6pt', 'c': 'black!55, line width=0.6pt, densely dashed'}
    for a, b, rot, e, *lado in g['flechas']:
        # rótulo a la derecha de las flechas verticales, encima de las horizontales y a lo largo de las oblicuas
        def punto(n):
            if '|-' in n:   # 'a|-b.ancla': la x de a con la y de b
                return punto(n.split('|-')[0])[0], punto(n.split('|-')[1])[1]
            return tuple(map(float, n.split(','))) if ',' in n else g['organos'][n.split('.')[0]][:2]
        (xa, ya), (xb_, yb) = punto(a), punto(b)
        pos = lado[0] if lado else ('right' if abs(xa - xb_) < 0.3 else ('above' if abs(ya - yb) < 0.3 else 'sloped, above'))
        a = f'{a}' if '|-' not in a else a
        b = f'{b.split("|-")[0]}.south |- {b.split("|-")[1]}' if '|-' in b else b
        o.append(f'  \\draw[-{{Stealth[length=4pt]}}, {estilos[e]}] ({a}) -- ({b}) '
                 f'node[midway, {pos}, inner sep=1.5pt, font=\\sffamily\\footnotesize\\itshape, text=black!75] {{{rot}}};')
    # (b) vertientes y grado
    xb, xl = 9.45, 12.75       # inicio del panel y del primer grado
    paso_x, paso_y = 0.92, 0.62
    ytop = alto_a - 0.55
    o.append(f'  \\node[anchor=south west, font=\\sffamily\\small, inner sep=0pt] at ({xb},{alto_a + 0.25:.2f}) {{(b) Vertientes y grado}};')
    for j, gr in enumerate(GRADOS):
        o.append(f'  \\node[anchor=base, inner sep=1pt, text=black!70] at ({xl + j * paso_x:.2f},{ytop + 0.32:.2f}) {{{gr}}};')
        o.append(f'  \\draw[black!12, line width=0.3pt] ({xl + j * paso_x:.2f},{ytop + 0.22:.2f}) -- '
                 f'({xl + j * paso_x:.2f},{ytop - (len(VERTIENTES) - 1) * paso_y - 0.25:.2f});')
    for i, (nombre, (prev, alc)) in enumerate(zip(VERTIENTES, g['grados'])):
        y = ytop - i * paso_y
        o.append(f'  \\node[anchor=east, inner sep=1pt] at ({xl - 0.3:.2f},{y:.2f}) {{{nombre}}};')
        o.append(f'  \\draw[black!20, line width=0.4pt] ({xl:.2f},{y:.2f}) -- ({xl + 3 * paso_x:.2f},{y:.2f});')
        if prev != alc:
            o.append(f'  \\draw[bintergub!60, line width=2.2pt] ({xl + alc * paso_x:.2f},{y:.2f}) -- ({xl + prev * paso_x:.2f},{y:.2f});')
        o.append(f'  \\draw[bintergub, fill=white, line width=0.9pt] ({xl + prev * paso_x:.2f},{y:.2f}) circle (3.6pt);')
        o.append(f'  \\fill[bintergub] ({xl + alc * paso_x:.2f},{y:.2f}) circle (2.4pt);')
    yl = ytop - (len(VERTIENTES) - 1) * paso_y - 0.65
    o.append(f'  \\draw[bintergub, fill=white, line width=0.9pt] ({xb + 0.15:.2f},{yl:.2f}) circle (3.6pt);')
    o.append(f'  \\node[anchor=west, inner sep=1pt] at ({xb + 0.35:.2f},{yl:.2f}) {{previsto en los tratados}};')
    o.append(f'  \\fill[bintergub] ({xb + 3.75:.2f},{yl:.2f}) circle (2.4pt);')
    o.append(f'  \\node[anchor=west, inner sep=1pt] at ({xb + 3.95:.2f},{yl:.2f}) {{alcanzado (2026)}};')
    # leyenda de colores del organigrama, debajo de todo, en filas de tres para no pasar de 16 cm
    entradas = [(f'draw=b{t}, fill=f{t}', TIPOS[t][2]) for t in TIPOS if t in usados and TIPOS[t][2]]
    entradas.append(('draw=black!60, densely dashed', 'competencias limitadas'))
    y0 = min([m[1] for m in g['marcos']] + [v[1] - 0.45 for v in g['organos'].values()]) - 0.45
    for n, (estilo, texto) in enumerate(entradas):
        x, y = (n % 3) * 5.45, y0 - (n // 3) * 0.45
        o.append(f'  \\node[{estilo}, line width=0.6pt, minimum width=0.42cm, minimum height=0.26cm, inner sep=0pt, '
                 f'anchor=west] at ({x:.2f},{y:.2f}) {{}};')
        o.append(f'  \\node[anchor=west, inner sep=1pt] at ({x + 0.5:.2f},{y:.2f}) {{{texto}}};')
    o.append('\\end{tikzpicture}')
    destino = Path(__file__).resolve().parent.parent / 'Img' / f'{clave}_gobernanza.tikz'
    destino.write_text('\n'.join(o) + '\n', encoding='utf-8')
    print('Escrito', destino)


if __name__ == '__main__':
    main(sys.argv[1])
