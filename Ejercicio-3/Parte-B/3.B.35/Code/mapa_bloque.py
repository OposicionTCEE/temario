#!/usr/bin/env python3
"""Genera Img/Mapa_<bloque>.tikz: mapa del mundo con los procesos de un bloque y, debajo, su línea del tiempo.

Fuente de los contornos (descargarla antes en una carpeta cualquiera y pasar su ruta):
  - ne_50m_admin_0_countries.geojson: Natural Earth 1:50m (dominio público),
    https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson
Miembros y fechas: ver el diccionario BLOQUES (comprobados en octubre de 2026; fuentes en el pie de cada figura).

Uso, desde la carpeta del tema:
  python3 Code/mapa_bloque.py RUTA/ne_50m_admin_0_countries.geojson economico
  bash Code/generar_figura.sh Mapa_economico
Proyección equirectangular, sin la Antártida. Los países pequeños se ven en los recuadros ampliados o con un círculo.
"""
import json
import sys
from pathlib import Path

ANCHO_CM = 16.0
LAT_MIN, LAT_MAX = -56.0, 84.0
ESC = ANCHO_CM / 360.0
GRIS, BORDE = (214, 214, 214), 'white'

# Línea del tiempo: años y posición horizontal
T0, T1 = 1945, 2026
TX0, TX1 = 3.45, 15.85           # cm: el eje empieza tras la columna de etiquetas
PASO_FILA = 0.82                # cm entre filas

BLOQUES = {
    'economico': {
        'grupos': [  # clave, nombre, color RGB, miembros (códigos ADM0_A3 de Natural Earth)
            ('mcca', 'MCCA', (200, 76, 58), ['GTM', 'SLV', 'HND', 'NIC', 'CRI']),
            ('pan', 'Panamá', (238, 165, 145), ['PAN']),
            ('can', 'CAN', (233, 160, 40), ['BOL', 'COL', 'ECU', 'PER']),
            ('efta', 'EFTA', (110, 165, 215), ['ISL', 'LIE', 'NOR', 'CHE']),
            ('nafta', 'NAFTA/USMCA', (30, 75, 135), ['USA', 'MEX', 'CAN', 'PRI']),
        ],
        'rayado': ('DR-CAFTA', ['USA', 'PRI', 'DOM', 'CRI', 'SLV', 'GTM', 'HND', 'NIC']),
        'recuadros': [
            {'titulo': 'Centroamérica y Caribe', 'lon': (-93.0, -59.0), 'lat': (6.5, 21.5),
             'pos': (0.25, 0.25), 'ancho': 4.0, 'esquina_mapa': 'south west'},
        ],
        'circulos': [  # lon, lat, radio (cm), grupo, texto, (lon, lat) del texto
            (8.9, 46.9, 0.14, 'efta', 'Suiza y Liechtenstein', (-14.0, 40.5)),
        ],
        'notas_mapa': [  # texto en una zona vacía del mapa (lon, lat)
            ((-31.0, -38.0), 'pan', 'Panamá: subsistema económico desde 2013'),
            ((-31.0, -45.5), 'rayado', 'DR-CAFTA (EE.\\,UU., Centroamérica y Rep. Dominicana)'),
        ],
        'filas': [
            # (etiqueta, grupo o None, año de inicio de la barra o None, [(año, texto, 'a'rriba/'b'ajo)], tramos [(desde, hasta, grupo)])
            ('CEPAL', None, None, [(1948, 'CEPAL', 'a'), (1960, 'ALALC', 'b'), (1980, 'ALADI', 'a'),
                                    (1994, 'regionalismo abierto', 'b')], []),
            ('MCCA', 'mcca', 1960, [(1960, 'Tratado de Managua', 'a'), (1969, 'guerra El Salvador-Honduras', 'b'),
                                    (1991, 'SICA', 'a'), (2006, 'DR-CAFTA', 'b'), (2013, 'Panamá', 'a')], []),
            ('CAN', 'can', 1969, [(1969, 'Acuerdo de Cartagena', 'a'), (1976, 'sale Chile', 'b'),
                                  (1995, 'AEC; 1996 CAN', 'a'), (2006, 'sale Venezuela', 'b')], []),
            ('EFTA', 'efta', 1960, [(1960, 'Convenio de Estocolmo', 'a'), (1973, 'salen Reino Unido y Dinamarca', 'b'),
                                    (1994, 'EEE', 'a'), (2001, 'Convenio de Vaduz', 'b')], []),
            ('NAFTA/USMCA', 'nafta', 1989, [(1989, 'Canadá-EE.\\,UU.', 'a'), (1994, 'NAFTA', 'b'),
                                            (2020, 'USMCA', 'a'), (2026, 'EE.\\,UU. no lo renueva', 'be')], []),
        ],
        'tipos': [  # corchete a la izquierda: (texto, primera fila, última fila)
            ('Regionalismo\\\\cerrado', 1, 2),
            ('Sin cesión de\\\\soberanía', 3, 4),
        ],
    },
    'afinidad': {
        'grupos': [  # orden: los posteriores prevalecen (PAFTA sobre AfCFTA en el norte de África)
            ('afcfta', 'AfCFTA', (60, 140, 90), ['@AFRICA']),
            ('afsin', 'AfCFTA, sin ratificar', (160, 205, 170), ['BEN', 'SSD']),
            ('pafta', 'Zona Pan-Árabe', (150, 90, 160), ['DZA', 'BHR', 'EGY', 'IRQ', 'KWT', 'LBN', 'LBY', 'MAR', 'OMN',
                                                       'PSX', 'QAT', 'SAU', 'SDN', 'SYR', 'TUN', 'ARE', 'JOR', 'YEM']),
            ('mercosur', 'MERCOSUR', (30, 75, 135), ['ARG', 'BRA', 'PRY', 'URY']),
            ('bol', 'Bolivia', (120, 160, 210), ['BOL']),
            ('ven', 'Venezuela', (200, 210, 225), ['VEN']),
            ('cefta', 'CEFTA', (200, 76, 58), ['ALB', 'BIH', 'KOS', 'MKD', 'MDA', 'MNE', 'SRB']),
        ],
        'excluir': ['ERI'],   # único miembro de la Unión Africana que no ha firmado el AfCFTA
        'rayado': ('también en el AfCFTA', ['DZA', 'EGY', 'LBY', 'MAR', 'SDN', 'TUN']),
        'recuadros': [
            {'titulo': 'Balcanes occidentales y Moldavia', 'lon': (13.0, 30.5), 'lat': (39.3, 48.6),
             'pos': (6.35, 0.25), 'ancho': 2.15, 'esquina_mapa': 'south west'},
        ],
        'circulos': [],
        'notas_mapa': [
            ((62.0, -36.0), 'bol', 'Bolivia: miembro desde 2024, en adaptación'),
            ((62.0, -40.5), 'ven', 'Venezuela: suspendida desde 2016'),
            ((62.0, -45.0), 'afsin', 'AfCFTA: firmado, sin ratificar'),
            ((62.0, -49.5), 'rayado', 'Zona Pan-Árabe también en el AfCFTA'),
        ],
        'filas': [
            ('MERCOSUR', 'mercosur', 1991, [(1985, 'Foz de Iguazú', 'aw'), (1991, 'Asunción', 'b'), (1994, 'Ouro Preto', 'a'),
                                           (1998, 'Ushuaia', 'b'), (2012, 'entra Venezuela', 'a'),
                                           (2016, 'suspende a Venezuela', 'b'), (2026, 'acuerdo con la UE', 'ae')], []),
            ('CEFTA', 'cefta', 1992, [(1992, 'Cracovia', 'a'), (2004, 'primeras salidas a la UE', 'b'),
                                      (2006, 'CEFTA 2006', 'a'), (2013, 'sale Croacia', 'b')], []),
            ('AfCFTA', 'afcfta', 2018, [(2012, 'decisión de la UA', 'ae'), (2018, 'Kigali', 'b'), (2019, 'en vigor', 'aw'),
                                        (2021, 'empieza el comercio', 'bw')], []),
            ('Zona Pan-Árabe', 'pafta', 1998, [(1997, 'programa ejecutivo', 'ae'), (1998, 'en vigor', 'b'),
                                                 (2005, 'liberalización completa', 'aw')], []),
        ],
        'tipos': [
            ('Régimen\\\\político', 0, 1),
            ('Identidad\\\\panregional', 2, 3),
        ],
    },
}


def xy(lon, lat):
    lat = max(LAT_MIN, min(LAT_MAX, lat))
    return (lon + 180) * ESC, (lat - LAT_MIN) * ESC


def camino(coords, f):
    puntos, previo = [], None
    for lon, lat in coords:
        x, y = f(lon, lat)
        p = (round(x, 2), round(y, 2))
        if p != previo:
            puntos.append(p)
            previo = p
    if len(puntos) < 3:
        return None
    return ' -- '.join(f'({x},{y})' for x, y in puntos) + ' -- cycle'


def poligonos(geom):
    return geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]


def caja(geom):
    lons = [p[0] for pol in poligonos(geom) for p in pol[0]]
    lats = [p[1] for pol in poligonos(geom) for p in pol[0]]
    return min(lons), max(lons), min(lats), max(lats)


def color(nombre, rgb):
    return '\\definecolor{%s}{RGB}{%d,%d,%d}' % (nombre, *rgb)


def tx(anio):
    return TX0 + (anio - T0) / (T1 - T0) * (TX1 - TX0)


def main(ruta_geojson, clave):
    B = BLOQUES[clave]
    paises = [f for f in json.load(open(ruta_geojson))['features'] if f['properties']['ADM0_A3'] != 'ATA']
    estilo = {}
    africa = [p['properties']['ADM0_A3'] for p in paises if p['properties'].get('CONTINENT') == 'Africa']
    for g, _, _, miembros in B['grupos']:   # los grupos posteriores prevalecen sobre los anteriores
        for m in (africa if miembros == ['@AFRICA'] else miembros):
            if m not in B.get('excluir', []):
                estilo[m] = g
    rayados = set(B['rayado'][1]) if B.get('rayado') else set()

    out = [f'% Generado por Code/mapa_bloque.py ({clave}) con Natural Earth 1:50m.',
           color('gris', GRIS)]
    out += [color('c' + g, rgb) for g, _, rgb, _ in B['grupos']]
    out += ['\\begin{tikzpicture}[line join=round, font=\\sffamily]',
            '  \\tikzset{pais/.style={draw=white, line width=0.12pt},',
            '           raya/.style={pattern={Lines[angle=45, distance=1.6pt, line width=0.35pt]}, pattern color=black!70}}']

    def dibuja(f, filtro=None):
        lineas = []
        for p in paises:
            cod = p['properties']['ADM0_A3']
            if filtro and not filtro(p):
                continue
            trozos = [c for c in (camino(pol[0], f) for pol in poligonos(p['geometry'])) if c]
            if not trozos:
                continue
            col = 'c' + estilo[cod] if cod in estilo else 'gris'
            lineas.append(f'  \\fill[pais, fill={col}] ' + ' '.join(trozos) + ';')
            if cod in rayados:
                lineas.append('  \\fill[raya] ' + ' '.join(trozos) + ';')
        return lineas

    # Mapa del mundo
    out += dibuja(xy)
    alto = round((LAT_MAX - LAT_MIN) * ESC, 2)

    # Círculos para países pequeños
    for lon, lat, r, g, texto, (tl, tla) in B.get('circulos', []):
        x, y = xy(lon, lat)
        x2, y2 = xy(tl, tla)
        out.append(f'  \\draw[c{g}!80!black, line width=0.6pt] ({x:.2f},{y:.2f}) circle ({r});')
        out.append(f'  \\draw[c{g}!80!black, line width=0.3pt] ({x - r:.2f},{y:.2f}) -- ({x2:.2f},{y2:.2f});')
        out.append(f'  \\node[anchor=east, font=\\sffamily\\tiny, inner sep=1pt] at ({x2:.2f},{y2:.2f}) {{{texto}}};')

    # Recuadros ampliados
    for R in B.get('recuadros', []):
        (l0, l1), (a0, a1) = R['lon'], R['lat']
        px, py = R['pos']
        s = R['ancho'] / (l1 - l0)
        w, h = R['ancho'], (a1 - a0) * s

        def f(lon, lat, l0=l0, a0=a0, px=px, py=py, s=s):
            return px + (lon - l0) * s, py + (lat - a0) * s

        def dentro(p, l0=l0, l1=l1, a0=a0, a1=a1):
            x0, x1, y0, y1 = caja(p['geometry'])
            return x1 >= l0 - 1 and x0 <= l1 + 1 and y1 >= a0 - 1 and y0 <= a1 + 1

        mx0, my0 = xy(l0, a0)
        mx1, my1 = xy(l1, a1)
        out.append(f'  \\draw[black!60, line width=0.3pt, densely dashed] ({mx0:.2f},{my0:.2f}) rectangle ({mx1:.2f},{my1:.2f});')
        out.append(f'  \\draw[black!60, line width=0.3pt, densely dashed] ({mx0:.2f},{my0:.2f}) -- ({px + w:.2f},{py + h:.2f});')
        out.append(f'  \\fill[white] ({px:.2f},{py:.2f}) rectangle ({px + w:.2f},{py + h:.2f});')
        out.append(f'  \\begin{{scope}}\\clip ({px:.2f},{py:.2f}) rectangle ({px + w:.2f},{py + h:.2f});')
        out += dibuja(f, dentro)
        out.append('  \\end{scope}')
        out.append(f'  \\draw[black!60, line width=0.4pt] ({px:.2f},{py:.2f}) rectangle ({px + w:.2f},{py + h:.2f});')
        out.append(f'  \\node[anchor=south west, font=\\sffamily\\tiny, inner sep=1pt] at ({px:.2f},{py + h + 0.02:.2f}) {{{R["titulo"]}}};')

    # Notas dentro del mapa (zonas vacías)
    for (lon, lat), g, texto in B.get('notas_mapa', []):
        x, y = xy(lon, lat)
        if g == 'rayado':
            out.append(f'  \\fill[gris] ({x:.2f},{y - 0.09:.2f}) rectangle ++(0.32,0.18); \\fill[raya] ({x:.2f},{y - 0.09:.2f}) rectangle ++(0.32,0.18);')
        else:
            out.append(f'  \\fill[c{g}] ({x:.2f},{y - 0.09:.2f}) rectangle ++(0.32,0.18);')
        out.append(f'  \\node[anchor=west, font=\\sffamily\\tiny, inner sep=1pt] at ({x + 0.36:.2f},{y:.2f}) {{{texto}}};')
    out.append(f'  \\path (0,0) rectangle ({ANCHO_CM},{alto});')

    # Línea del tiempo
    filas = B['filas']
    y0 = -0.75
    ys = [y0 - i * PASO_FILA for i in range(len(filas))]
    yeje = ys[-1] - 0.62
    for d in range(1950, 2030, 10):
        out.append(f'  \\draw[black!12, line width=0.3pt] ({tx(d):.2f},{y0 + 0.4:.2f}) -- ({tx(d):.2f},{yeje:.2f});')
    out.append(f'  \\draw[black!70, line width=0.5pt, -{{Stealth[length=4pt]}}] ({TX0:.2f},{yeje:.2f}) -- ({TX1 + 0.12:.2f},{yeje:.2f});')
    for d in range(1950, 2030, 10):
        out.append(f'  \\draw[black!70, line width=0.5pt] ({tx(d):.2f},{yeje:.2f}) -- ++(0,-0.07) node[below, font=\\sffamily\\scriptsize, inner sep=1.5pt] {{{d}}};')
    for (etq, g, inicio, hitos, _), y in zip(filas, ys):
        col = f'c{g}' if g else 'black!45'
        out.append(f'  \\node[anchor=east, font=\\sffamily\\scriptsize\\bfseries, text={col if g else "black!60"}] at ({TX0 - 0.1:.2f},{y:.2f}) {{{etq}}};')
        if inicio is None:
            out.append(f'  \\draw[black!35, line width=0.6pt, dotted] ({TX0:.2f},{y:.2f}) -- ({TX1:.2f},{y:.2f});')
        else:
            out.append(f'  \\draw[{col}, line width=3.2pt, line cap=round] ({tx(inicio):.2f},{y:.2f}) -- ({tx(T1):.2f},{y:.2f});')
        for anio, texto, lado in hitos:
            x = tx(anio)
            out.append(f'  \\fill[white] ({x:.2f},{y:.2f}) circle (1.15pt); \\draw[{col}!70!black, line width=0.45pt] ({x:.2f},{y:.2f}) circle (1.15pt);')
            ancla, dy = {'a': ('south', 0.07), 'b': ('north', -0.07), 'ae': ('south east', 0.07), 'be': ('north east', -0.07)}[lado]
            if lado.endswith('e'):
                x += 0.08
            out.append(f'  \\node[anchor={ancla}, font=\\sffamily\\tiny, inner sep=0.8pt] at ({x:.2f},{y + dy:.2f}) {{{anio} {texto}}};')
    for texto, a, b in B.get('tipos', []):
        ya, yb = ys[a] + 0.22, ys[b] - 0.22
        out.append(f'  \\draw[black!55, line width=0.4pt] (1.32,{ya:.2f}) -- (1.22,{ya:.2f}) -- (1.22,{yb:.2f}) -- (1.32,{yb:.2f});')
        out.append(f'  \\node[anchor=east, align=right, font=\\sffamily\\tiny\\itshape, text=black!70] at (1.15,{(ya + yb) / 2:.2f}) {{{texto}}};')
    out.append('\\end{tikzpicture}')

    nombre = 'Mapa_' + clave
    destino = Path(__file__).resolve().parent.parent / 'Img' / f'{nombre}.tikz'
    destino.write_text('\n'.join(out) + '\n', encoding='utf-8')
    print(f'Escrito {destino} ({destino.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
