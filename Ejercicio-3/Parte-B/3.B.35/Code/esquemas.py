#!/usr/bin/env python3
"""Genera Img/Esquema_<bloque>.tikz: el esquema de una página de cada bloque, para el anexo «Material de estudio: Esquemas».

Formato acordado con el usuario (15/10/2026, nota magenta del anexo):
- arriba, la cadena del bloque: tesis -> justificación -> medios (los dos tipos del bloque, con sus acuerdos);
- debajo, una fila por acuerdo, agrupadas por tipo: objetivo -> cómo se construyó (escala de BALASSA, hitos y quién decide)
  -> resultado y por qué (con una miniatura del indicador clave) -> qué busca la UE -> ¿confirma la tesis del bloque?;
- al pie, el balance del bloque y el glosario.
Sin título ni fuente (GUIA_TEMAS §4), una página, letra de 8 puntos como mínimo y sin tiempos de cante (elección del usuario).
Todo sale del cuerpo del tema; lo que no está en él lleva etiqueta naranja (primera pasada).
Colores de los acuerdos: los de los mapas de bloque (Code/mapa_bloque.py).

Uso, desde la carpeta del tema:  python3 Code/esquemas.py economico && bash Code/generar_figura.sh Esquema_economico
"""
import sys
from pathlib import Path

TEMA = Path(__file__).resolve().parent.parent

W = 15.94                                 # cm: ancho del texto menos el grosor de los bordes
COLS = [2.6, 3.2, 3.9, 2.6, 2.44]          # objetivo, cómo, resultado, UE, tesis
GAP = 0.3                                 # cm entre casillas (con una flecha)
CABECERAS = ['Objetivo', 'Cómo se construyó', 'Resultado y por qué', '¿Qué busca la UE?', '¿Confirma la tesis?']
ESCALA = ['ZLC', 'UA', 'MC']              # grados de BALASSA que se dibujan
PROB = r'\textcolor{orange}{\textsuperscript{[Probable]}}'

BLOQUES = {
    'economico': {
        'titulo': 'Lógica económica: ¿regionalismo abierto o cerrado?',
        'tesis': r'La finalidad dominante es \textbf{económica}: ampliar el mercado para ganar eficiencia, escala o credibilidad',
        'justificacion': (r'\textbf{Estáticas}: creación de comercio $>$ desviación (VINER, 1950)\\'
                          r'\textbf{Dinámicas}: escala, competencia, inversión\\'
                          r'\textbf{Vecinos} = socios naturales $\Rightarrow$ poca desviación (WONNACOTT y LUTZ, 1989; KRUGMAN, 1991)\\'
                          r'\textbf{Credibilidad}: un tratado ata las reformas (FERNÁNDEZ y PORTES, 1998)'),
        'medios': [
            ('A', r'\textbf{Regionalismo cerrado} (CEPAL): industrializar tras un AEC, a menor coste '
                  r'(COOPER y MASSELL, 1965) $\to$ MCCA, CAN'),
            ('B', r'\textbf{Sin cesión de soberanía}: libre comercio sin AEC ni órganos supranacionales; precio: reglas de origen '
                  r'$\to$ EFTA, NAFTA'),
        ],
        'grupos': [
            ('A', 'Regionalismo cerrado, reconvertido en abierto en los años noventa', [
                {'nombre': 'MCCA', 'anio': '1960', 'color': (200, 76, 58), 'alto': 2.75,
                 'objetivo': 'Industrializar cinco economías de café y banano: mercado protegido y reparto de industrias',
                 'escala': {'ZLC': 'a', 'UA': 'p', 'MC': 'v'},
                 'como': (r'Managua 1960 $\to$ guerra (1969) $\to$ SICA 1991: regionalismo abierto\\'
                          r'Intergubernamental, sin órgano que haga cumplir'),
                 'grafico': ('linea', [(1965, 18, 'l'), (1970, 26, 'a'), (1986, 11, 'b'), (2023, 25, 'a')]),
                 'resultado': (r'Cuota alta, de manufacturas, pero concentradas en Guatemala y El Salvador $\Rightarrow$ '
                               r'\textbf{conflicto distributivo}'),
                 'ue': r'\textbf{Afinidad}: acuerdo con la región en bloque, ligado a la democracia; $0{,}4\%$ del comercio de la UE',
                 'tesis': r'\textbf{Sí} crea comercio y escala. \textbf{No} reparte: sin compensación, la industria va al más avanzado'},
                {'nombre': 'CAN', 'anio': '1969', 'color': (233, 160, 40), 'alto': 2.75,
                 'objetivo': 'Lo mismo, con más ambición: programación industrial, control de la IED y negociar en bloque',
                 'escala': {'ZLC': 'a', 'UA': 'x', 'MC': 'v'},
                 'como': (r'Cartagena 1969 $\to$ ZLC 1993; AEC 1995, sin efecto en 2015\\'
                          r'La más \textbf{supranacional} de América Latina (Tribunal)'),
                 'grafico': ('linea', [(1969, 3, 'a'), (1976, 6, 'a'), (1985, 2.6, 'b'), (1998, 13.9, 'a'), (2023, 6, 'a')]),
                 'resultado': (r'Cuota baja y en caída: economías \textbf{competidoras}, que venden materias primas fuera '
                               r'(complementariedad: con China $27$, entre socios $18$)'),
                 'ue': r'\textbf{Económica}: acuerdo solo comercial con Colombia, Perú y Ecuador, no con el bloque',
                 'tesis': r'\textbf{No}: sin complementariedad no hay mercado regional, ni con las instituciones más fuertes'},
            ]),
            ('B', 'Integración de mercados sin cesión de soberanía', [
                {'nombre': 'EFTA', 'anio': '1960', 'color': (110, 165, 215), 'alto': 2.55,
                 'objetivo': 'Respuesta defensiva a la CEE: libre comercio industrial sin ceder soberanía',
                 'escala': {'ZLC': 'a', 'UA': None, 'MC': None},
                 'como': (r'Estocolmo 1960 $\to$ se vacía hacia la CEE (efecto dominó) $\to$ EEE 1994; Suiza, bilaterales\\'
                          r'Intergubernamental'),
                 'grafico': ('barras', [('a la UE', 63, r'$51$-$63\%$'), ('a los socios', 1, r'$<1\%$')]),
                 'resultado': r'Su mercado es la UE, no los socios; la protección agraria frena la adhesión',
                 'ue': r'\textbf{Económica con afinidad}: $9{,}6\%$ del comercio de la UE; el EEE les da su mercado interior sin voto',
                 'tesis': r'Como \textbf{alternativa} a la CEE, fracasó; como \textbf{antesala}, funcionó'},
                {'nombre': 'NAFTA', 'anio': '1994; USMCA, 2020', 'color': (30, 75, 135), 'alto': 2.75,
                 'objetivo': r'México: anclar sus reformas; EE.\,UU.: integración profunda; Canadá: no quedarse fuera',
                 'escala': {'ZLC': 'a', 'UA': None, 'MC': None},
                 'como': (r'USMCA 2020: origen del automóvil, cláusula China $\to$ 2026: EE.\,UU. no prorroga\\'
                          r'Intergubernamental, con paneles'),
                 'grafico': ('linea', [(1981, 35.5, 'l'), (1994, 48, 'b'), (2003, 56, 'a'), (2023, 50.8, 'a')]),
                 'resultado': (r'Radios en torno a EE.\,UU.; cadena del automóvil. México \textbf{no converge} '
                               r'($40\% \to 29\%$ del PIB per cápita de EE.\,UU.)'),
                 'ue': r'\textbf{Económica}: $19\%$ del comercio de la UE, más que la UE para ellos; desde 2025, diversificar',
                 'tesis': r'\textbf{Sí} en comercio y cadenas; \textbf{no} en convergencia. Desde 2025, también geoestratégico'},
            ]),
        ],
        'balance': (r'Hay comercio cuando los socios son complementarios o se anclan a un mercado grande (UE, EE.\,UU.), no cuando '
                    r'venden lo mismo; y ningún acuerdo reparte por sí solo las ganancias' + PROB),
        'glosario': (r'ZLC: zona de libre comercio; UA: unión aduanera; MC: mercado común (grados de BALASSA). AEC: arancel exterior común. '
                     r'IED: inversión extranjera directa. EEE: Espacio Económico Europeo. Línea: cuota intrarregional (exportaciones a '
                     r'los socios sobre el total, \%), escala propia en cada fila; barras: destino de las exportaciones, 2023.'),
    },
}

def color(nombre, c):
    return r'\definecolor{%s}{RGB}{%d,%d,%d}%%' % (nombre, *c)


def texto(x, y, ancho, contenido, extra=''):
    return (f'  \\node[anchor=north west, text width={ancho:.2f}cm, align=left, inner sep=0pt{extra}] '
            f'at ({x:.2f},{y:.2f}) {{{contenido}}};')


def escala(x, y, grados, c):
    """Escala de BALASSA: círculo hueco = previsto; relleno = alcanzado; medio = en parte; aspa = abandonado; gris = no previsto."""
    o, paso = [], 0.92
    o.append(f'  \\draw[black!25, line width=0.5pt] ({x:.2f},{y:.2f}) -- ({x + paso * (len(ESCALA) - 1):.2f},{y:.2f});')
    for i, g in enumerate(ESCALA):
        xi, est = x + i * paso, grados.get(g)
        if est is None:
            o.append(f'  \\fill[black!25] ({xi:.2f},{y:.2f}) circle (1.3pt);')
            o.append(f'  \\node[anchor=west, inner sep=1.5pt, text=black!40, fill={c}!7] at ({xi + 0.1:.2f},{y:.2f}) {{{g}}};')
            continue
        o.append(f'  \\draw[{c}, fill=white, line width=0.8pt] ({xi:.2f},{y:.2f}) circle (3.3pt);')
        if est == 'a':
            o.append(f'  \\fill[{c}] ({xi:.2f},{y:.2f}) circle (2.1pt);')
        elif est == 'p':
            o.append(f'  \\fill[{c}] ({xi:.2f},{y:.2f}) ++(0,2.1pt) arc (90:270:2.1pt) -- cycle;')
        elif est == 'x':
            o.append(f'  \\draw[{c}, line width=0.8pt] ({xi:.2f},{y:.2f}) ++(-2.3pt,-2.3pt) -- ++(4.6pt,4.6pt) '
                     f'++(-4.6pt,0) -- ++(4.6pt,-4.6pt);')
        o.append(f'  \\node[anchor=west, inner sep=1.5pt, fill={c}!7] at ({xi + 0.12:.2f},{y:.2f}) {{{g}}};')
    return o


def grafico(x0, x1, ytop, g, c):
    """Miniatura en lo alto de la casilla de resultado: línea (años bajo el eje, en los extremos) o barras horizontales.
    En la línea, cada punto lleva su valor arriba (a), abajo (b) o a la izquierda (l)."""
    o, tipo, datos = [], g[0], g[1]
    if tipo == 'linea':
        a0, a1 = datos[0][0], datos[-1][0]
        vmax = max(v for _, v, _ in datos)
        xa, xb = x0 + (0.65 if datos[0][2] == 'l' else 0.35), x1 - 0.3
        yb, alto = ytop - 0.72, 0.38
        pts = [(xa + (a - a0) / (a1 - a0) * (xb - xa), yb + v / vmax * alto, v, p) for a, v, p in datos]
        o.append(f'  \\draw[black!30, line width=0.4pt] ({xa:.2f},{yb:.2f}) -- ({xb:.2f},{yb:.2f});')
        o.append(f'  \\node[anchor=north, inner sep=1pt, text=black!55] at ({xa:.2f},{yb - 0.02:.2f}) {{{a0}}};')
        o.append(f'  \\node[anchor=north, inner sep=1pt, text=black!55] at ({xb:.2f},{yb - 0.02:.2f}) {{{a1}}};')
        o.append(f'  \\draw[{c}, line width=0.9pt] ' + ' -- '.join(f'({px:.2f},{py:.2f})' for px, py, _, _ in pts) + ';')
        for px, py, v, p in pts:
            et = f'{v:g}'.replace('.', '{,}')
            pos = {'a': 'above', 'b': 'below', 'l': 'left'}[p]
            o.append(f'  \\fill[{c}] ({px:.2f},{py:.2f}) circle (1.2pt);')
            o.append(f'  \\node[{pos}, inner sep=1pt] at ({px:.2f},{py:.2f}) {{${et}$}};')
        return o, 1.08
    if tipo == 'barras':
        vmax = max(v for _, v, _ in datos)
        xa, largo = x0 + 1.5, (x1 - x0) - 2.45
        for i, (et, v, txt) in enumerate(datos):
            y = ytop - 0.27 - i * 0.34
            o.append(f'  \\node[anchor=east, inner sep=1pt] at ({xa - 0.05:.2f},{y:.2f}) {{{et}}};')
            o.append(f'  \\fill[{c}] ({xa:.2f},{y - 0.1:.2f}) rectangle ({xa + max(v / vmax * largo, 0.04):.2f},{y + 0.1:.2f});')
            o.append(f'  \\node[anchor=west, inner sep=1pt] at ({xa + max(v / vmax * largo, 0.04) + 0.05:.2f},{y:.2f}) {{{txt}}};')
        return o, 0.15 + 0.34 * len(datos) + 0.1
    raise ValueError(tipo)


def main(clave):
    B = BLOQUES[clave]
    o = [f'% Esquema de una página del bloque «{B["titulo"]}», para el anexo «Material de estudio: Esquemas».',
         '% Generado por Code/esquemas.py (no editar a mano). Generar el PDF con: bash Code/generar_figura.sh Esquema_' + clave,
         color('eGri', (110, 110, 110))]
    acuerdos = [a for _, _, lista in B['grupos'] for a in lista]
    for i, a in enumerate(acuerdos):
        o.append(color(f'eA{i}', a['color']))
    o += [r'\begin{tikzpicture}[font=\footnotesize, x=1cm, y=1cm,',
          r'    every node/.append style={execute at begin node={\hyphenpenalty=10000\exhyphenpenalty=10000}},',
          r'    flecha/.style={-{Latex[length=1.5mm]}, line width=0.6pt, black!55}]']

    # --- Rótulo del bloque y cadena: tesis -> justificación -> medios ---
    o.append(f'  \\node[anchor=south west, inner sep=0pt, font=\\small\\bfseries, text=eGri] at (0,0) {{{B["titulo"]}}};')
    y0, h0 = -0.2, B.get('alto_cabeza', 2.9)
    xs = [(0.0, 2.9), (3.25, 9.55), (9.9, W)]
    for (xa, xb), cab, cont in [(xs[0], 'Tesis', B['tesis']), (xs[1], 'Justificación', B['justificacion'])]:
        o.append(f'  \\draw[eGri, fill=eGri!8, line width=0.6pt, rounded corners=2pt] ({xa:.2f},{y0:.2f}) rectangle ({xb:.2f},{y0 - h0:.2f});')
        o.append(texto(xa + 0.1, y0 - 0.1, xb - xa - 0.2, f'\\textbf{{\\small {cab}}}\\\\[1pt] {cont}'))
    xa, xb = xs[2]
    o.append(texto(xa + 0.02, y0 - 0.02, xb - xa, r'\textbf{\small Medios: dos estrategias}', ', text=eGri'))
    hm = (h0 - 0.42 - 0.15) / 2
    for i, (letra, cont) in enumerate(B['medios']):
        ya = y0 - 0.42 - i * (hm + 0.15)
        o.append(f'  \\draw[eGri, fill=white, line width=0.6pt, rounded corners=2pt] ({xa:.2f},{ya:.2f}) rectangle ({xb:.2f},{ya - hm:.2f});')
        o.append(f'  \\node[anchor=north west, fill=eGri, text=white, font=\\small\\bfseries, inner sep=2pt, rounded corners=1pt] '
                 f'at ({xa + 0.08:.2f},{ya - 0.08:.2f}) {{{letra}}};')
        o.append(texto(xa + 0.55, ya - 0.08, xb - xa - 0.65, cont))
    ym = y0 - h0 / 2
    o.append(f'  \\draw[flecha] ({xs[0][1] + 0.03:.2f},{ym:.2f}) -- ({xs[1][0] - 0.03:.2f},{ym:.2f});')
    o.append(f'  \\draw[flecha] ({xs[1][1] + 0.03:.2f},{ym:.2f}) -- ({xs[2][0] - 0.03:.2f},{ym:.2f});')

    # --- Cabeceras de las columnas ---
    xcol, x = [], 0.0
    for w in COLS:
        xcol.append((x, x + w))
        x += w + GAP
    y = y0 - h0 - 0.35
    for i, ((xa, xb), cab) in enumerate(zip(xcol, CABECERAS)):
        o.append(f'  \\node[anchor=south, inner sep=1pt, font=\\footnotesize\\bfseries, text=eGri] at ({(xa + xb) / 2:.2f},{y - 0.3:.2f}) {{{cab}}};')
        if i < len(xcol) - 1:
            o.append(f'  \\draw[flecha] ({xb + 0.02:.2f},{y - 0.2:.2f}) -- ({xcol[i + 1][0] - 0.02:.2f},{y - 0.2:.2f});')
    y -= 0.42

    # --- Grupos y filas ---
    k = 0
    for letra, titulo, lista in B['grupos']:
        o.append(f'  \\fill[eGri!14, rounded corners=1pt] (0,{y:.2f}) rectangle ({W},{y - 0.4:.2f});')
        o.append(f'  \\node[anchor=west, fill=eGri, text=white, font=\\small\\bfseries, inner sep=2pt, rounded corners=1pt] at (0.05,{y - 0.2:.2f}) {{{letra}}};')
        o.append(f'  \\node[anchor=west, inner sep=0pt, font=\\footnotesize\\bfseries, text=eGri] at (0.5,{y - 0.2:.2f}) {{{titulo}}};')
        y -= 0.52
        for a in lista:
            c, h = f'eA{k}', a['alto']
            k += 1
            for i, (xa, xb) in enumerate(xcol):
                o.append(f'  \\draw[{c}, fill={c}!7, line width=0.6pt, rounded corners=2pt] ({xa:.2f},{y:.2f}) rectangle ({xb:.2f},{y - h:.2f});')
                if i < len(xcol) - 1:
                    o.append(f'  \\draw[flecha] ({xb + 0.02:.2f},{y - h / 2:.2f}) -- ({xcol[i + 1][0] - 0.02:.2f},{y - h / 2:.2f});')
            (x0, x1), (c0, c1), (r0, r1), (u0, u1), (t0, t1) = xcol
            o.append(texto(x0 + 0.08, y - 0.08, x1 - x0 - 0.16,
                           f'{{\\small\\textbf{{\\textcolor{{{c}!85!black}}{{{a["nombre"]}}}}}}} ({a["anio"]})\\\\[1pt] {a["objetivo"]}'))
            o += escala(c0 + 0.17, y - 0.2, a['escala'], c)
            o.append(texto(c0 + 0.08, y - 0.4, c1 - c0 - 0.16, a['como']))
            g, alto_g = grafico(r0, r1, y, a['grafico'], c)
            o += g
            o.append(texto(r0 + 0.08, y - alto_g, r1 - r0 - 0.16, a['resultado']))
            o.append(texto(u0 + 0.08, y - 0.08, u1 - u0 - 0.16, a['ue']))
            o.append(texto(t0 + 0.08, y - 0.08, t1 - t0 - 0.16, a['tesis']))
            y -= h + 0.18
        y -= 0.06

    # --- Balance y glosario ---
    o.append(f'  \\node[anchor=north west, draw=eGri, fill=white, line width=1.1pt, rounded corners=2pt, text width={W - 0.2:.2f}cm, align=left, '
             f'inner sep=0.1cm] (bal) at (0,{y:.2f}) {{$\\Rightarrow$ \\textbf{{Balance del bloque}}: {B["balance"]}}};')
    o.append(f'  \\node[anchor=north west, text width={W:.2f}cm, align=left, inner sep=0pt, text=black!65] at '
             f'([yshift=-0.2cm]bal.south west) {{\\textit{{Glosario.}} {B["glosario"]} En la escala: círculo hueco, previsto; '
             f'relleno, alcanzado; medio, en parte; aspa, abandonado; gris, no previsto.}};')
    o.append(r'\end{tikzpicture}%')
    destino = TEMA / 'Img' / f'Esquema_{clave}.tikz'
    destino.write_text('\n'.join(o) + '\n', encoding='utf-8')
    print('Escrito', destino.relative_to(TEMA))


if __name__ == '__main__':
    for clave in (sys.argv[1:] or BLOQUES):
        main(clave)
