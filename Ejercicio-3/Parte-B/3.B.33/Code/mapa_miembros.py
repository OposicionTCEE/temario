#!/usr/bin/env python3
"""Genera Img/OMC_miembros.tikz: mapa del mundo con los miembros y observadores de la OMC.

Fuentes (descargarlas antes en una carpeta cualquiera y pasar su ruta):
  - ne_110m_admin_0_countries.geojson: contornos de Natural Earth 1:110m (dominio público),
    https://github.com/nvkelso/natural-earth-vector/tree/master/geojson
  - country_data.js: estado de cada país en la web de la OMC (mbrstatus MBR/OBS/OTH),
    https://www.wto.org/library/groupings/country_data.js (consultado el 12/10/2026: 166 miembros, 22 observadores).

Uso, desde la carpeta del tema:
  python3 Code/mapa_miembros.py RUTA/ne_110m_admin_0_countries.geojson RUTA/country_data.js
  bash Code/generar_figura.sh OMC_miembros
Proyección equirectangular, sin la Antártida. A esta escala no aparecen los microestados
(Singapur, Malta, Hong Kong, Macao, las islas del Caribe y del Pacífico...).
"""
import json
import re
import sys
from pathlib import Path

ANCHO_CM = 16.0          # anchura del mapa
LAT_MIN, LAT_MAX = -56.0, 84.0
ESC = ANCHO_CM / 360.0   # cm por grado

# Códigos de Natural Earth (ADM0_A3) que la OMC escribe de otra forma o que se asignan a otro país.
EQUIVALENCIAS = {
    'ROU': 'ROM',  # Rumanía
    'TWN': 'CHT',  # Taipéi Chino (territorio aduanero distinto)
    'SDS': 'SSD',  # Sudán del Sur
    'SOL': 'SOM',  # Somalilandia, parte de Somalia
    'CYN': 'CYP',  # norte de Chipre, parte de Chipre
    'FLK': 'GBR', 'ATF': 'FRA', 'NCL': 'FRA', 'PRI': 'USA',  # territorios
}
EXCLUIR = {'ATA'}  # Antártida
ESTILO = {'MBR': 'omcMiembro', 'OBS': 'omcObservador', 'OTH': 'omcOtro', None: 'omcOtro'}


def estados(ruta_js):
    texto = Path(ruta_js).read_text(encoding='latin-1')
    filas = re.findall(r'code:"([A-Z0-9]+)".*?mbrstatus: "([A-Z]+)"', texto)
    return dict(filas)


def anillo(coords):
    puntos, previo = [], None
    for lon, lat in coords:
        lat = max(LAT_MIN, min(LAT_MAX, lat))
        p = (round((lon + 180) * ESC, 2), round((lat - LAT_MIN) * ESC, 2))
        if p != previo:
            puntos.append(p)
            previo = p
    if len(puntos) < 3:
        return None
    return ' -- '.join(f'({x},{y})' for x, y in puntos) + ' -- cycle'


def main(ruta_geojson, ruta_js):
    estado = estados(ruta_js)
    cuenta = {'MBR': 0, 'OBS': 0}
    caminos = []
    for f in json.load(open(ruta_geojson))['features']:
        codigo = f['properties']['ADM0_A3']
        if codigo in EXCLUIR:
            continue
        st = estado.get(EQUIVALENCIAS.get(codigo, codigo))
        geom = f['geometry']
        poligonos = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
        trozos = [a for a in (anillo(p[0]) for p in poligonos) if a]
        if trozos:
            caminos.append(f'  \\fill[{ESTILO[st]}] ' + ' '.join(trozos) + ';')
    alto = round((LAT_MAX - LAT_MIN) * ESC, 2)
    for st in estado.values():
        if st in cuenta:
            cuenta[st] += 1
    salida = [
        f'% Generado por Code/mapa_miembros.py: {cuenta["MBR"]} miembros y {cuenta["OBS"]} observadores (web de la OMC).',
        '\\definecolor{omcMiembro}{RGB}{46,125,90}',
        '\\definecolor{omcObservador}{RGB}{230,170,40}',
        '\\definecolor{omcOtro}{RGB}{200,200,200}',
        '\\begin{tikzpicture}[line join=round]',
        '  \\tikzset{omcMiembro/.style={fill=omcMiembro, draw=white, line width=0.15pt},',
        '           omcObservador/.style={fill=omcObservador, draw=white, line width=0.15pt},',
        '           omcOtro/.style={fill=omcOtro, draw=white, line width=0.15pt}}',
        *caminos,
        '  % Leyenda',
        f'  \\begin{{scope}}[shift={{(0.3,0.25)}}, font=\\footnotesize]',
        '    \\fill[omcMiembro] (0,1.0) rectangle ++(0.35,0.22); \\node[anchor=west] at (0.4,1.11) {Miembros (' + str(cuenta['MBR']) + ')};',
        '    \\fill[omcObservador] (0,0.6) rectangle ++(0.35,0.22); \\node[anchor=west] at (0.4,0.71) {Observadores (' + str(cuenta['OBS']) + ')};',
        '    \\fill[omcOtro] (0,0.2) rectangle ++(0.35,0.22); \\node[anchor=west] at (0.4,0.31) {Ni miembros ni observadores};',
        '  \\end{scope}',
        f'  \\path (0,0) rectangle ({ANCHO_CM},{alto});',
        '\\end{tikzpicture}',
    ]
    destino = Path(__file__).resolve().parent.parent / 'Img' / 'OMC_miembros.tikz'
    destino.write_text('\n'.join(salida) + '\n', encoding='utf-8')
    print(f'Escrito {destino} ({len(caminos)} países; {cuenta})')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
