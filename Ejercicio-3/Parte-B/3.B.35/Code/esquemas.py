#!/usr/bin/env python3
"""Genera Img/Esquema_<bloque>.tikz: el esquema de una página de cada bloque, para el anexo «Material de estudio: Esquemas».

Formato acordado con el usuario (15/10/2026, nota magenta del anexo y revisión del primer borrador):
- arriba, la cadena del bloque, sin recuadros: tesis -> justificación -> medios (los dos tipos del bloque, con sus acuerdos);
- después, cada acuerdo como un seguimiento de su contenido, bajo su título completo y separado de los demás:
  objetivo -> cómo se construyó (escala de BALASSA e hitos) -> gobierno (organigrama mínimo, con los colores de las figuras
  de gobernanza: color = naturaleza del órgano, discontinuo = competencias limitadas) -> valoración (claves);
  y, debajo, qué busca la UE -> ¿confirma la tesis del bloque?;
- al pie, el balance del bloque.
Sin título ni fuente (GUIA_TEMAS §4), una página, letra de 8 puntos como mínimo, sin tiempos de cante, sin gráficos de datos ni
glosario (elección del usuario). Las alturas las calcula TikZ: cada acuerdo empieza bajo el anterior.
Todo sale del cuerpo del tema; lo que no está en él lleva etiqueta naranja (primera pasada).
Colores de los acuerdos: los de los mapas de bloque (Code/mapa_bloque.py).

Uso, desde la carpeta del tema:  python3 Code/esquemas.py economico && bash Code/generar_figura.sh Esquema_economico
"""
import sys
from pathlib import Path

TEMA = Path(__file__).resolve().parent.parent

W = 15.94                                   # cm: ancho del texto menos el grosor de las rayas
# Columnas de cada acuerdo: (inicio, ancho, rótulo)
COLS = [(0.0, 3.0, 'Objetivo'), (3.3, 3.5, 'Cómo se construyó'), (7.1, 3.6, 'Gobierno'), (11.0, W - 11.0, 'Valoración')]
ABAJO = [(0.0, 7.75, 'Relación con la UE'), (8.05, W - 8.05, r'$\Rightarrow$ ¿Confirma la tesis?')]
ESCALA = ['ZLC', 'UA', 'MC']                # grados de BALASSA que se dibujan
PROB = r'\textcolor{orange}{\textsuperscript{[Probable]}}'
TIPOS = {   # naturaleza del órgano (Code/gobernanza.py): (borde, relleno)
    'intergub': ((30, 75, 135), (218, 232, 246)),
    'supra': ((175, 55, 45), (247, 220, 212)),
    'tecnico': ((105, 105, 105), (236, 236, 236)),
    'judicial': ((105, 65, 140), (233, 223, 242)),
    'parlamento': ((55, 125, 65), (223, 238, 214)),
    'financiero': ((185, 125, 20), (252, 236, 206)),
    'estados': ((70, 70, 70), (255, 255, 255)),
}

BLOQUES = {
    'economico': {
        'titulo': 'Lógica económica: ¿regionalismo abierto o cerrado?',
        'tesis': (r'Los cuatro nacen para \textbf{ampliar el mercado} y ganar eficiencia, escala o credibilidad, '
                  r'con \textbf{dos estrategias opuestas}'),
        'justificacion': (r'\textbf{Estáticas}: creación $>$ desviación de comercio (VINER, 1950)\\'
                          r'\textbf{Dinámicas}: escala, competencia, inversión\\'
                          r'\textbf{Vecinos} = socios naturales $\Rightarrow$ poca desviación (WONNACOTT y LUTZ, 1989; KRUGMAN, 1991)\\'
                          r'\textbf{Credibilidad}: un tratado ata las reformas (FERNÁNDEZ y PORTES, 1998)'),
        'medios': [
            ('A', r'\textbf{Regionalismo cerrado} (CEPAL): industrializar tras un AEC, a menor coste que cada país solo '
                  r'(COOPER y MASSELL, 1965) $\to$ MCCA, CAN'),
            ('B', r'\textbf{Sin cesión de soberanía}: libre comercio sin AEC ni órganos supranacionales, para entrar en un '
                  r'mercado grande; precio: reglas de origen $\to$ EFTA, NAFTA'),
        ],
        'grupos': [
            ('A', 'Regionalismo cerrado, reconvertido en abierto en los años noventa (CEPAL, 1994)', [
                {'titulo': 'Mercado Común Centroamericano (MCCA, 1960)', 'color': (200, 76, 58),
                 'objetivo': (r'Industrializar cinco economías de café y banano: mercado común tras un AEC y '
                              r'\textbf{reparto de las industrias}'),
                 'escala': {'ZLC': 'a', 'UA': 'p', 'MC': 'v'},
                 'hitos': [('1960', 'Tratado de Managua'), ('1969', 'guerra Honduras-El Salvador'),
                           ('1991', 'SICA: regionalismo abierto'), ('2017', 'unión aduanera parcial')],
                 'gobierno': {
                     'nodos': [('pres', 1.8, 0.0, 'intergub', 'Reunión de Presidentes', False),
                               ('com', 1.0, -0.78, 'intergub', 'COMIECO', False),
                               ('sie', 2.9, -0.78, 'tecnico', 'SIECA', False),
                               ('cor', 0.9, -1.5, 'judicial', 'Corte', True),
                               ('par', 2.7, -1.5, 'parlamento', 'Parlamento', True)],
                     'flechas': [('pres', 'com'), ('sie', 'com')],
                     'nota': r'Por consenso: nadie hace cumplir lo acordado'},
                 'valoracion': [r'Cuota intrarregional alta: $18\%$ (1965) $\to$ $26\%$ (1970) $\to$ $25\%$ (2023), con caída en las guerras',
                                r'Mercado de la \textbf{industria ligera}, concentrada en Guatemala y El Salvador ($68\%$)',
                                r'Honduras y Nicaragua, déficits de $\approx 7\%$ del PIB; el DR-CAFTA pesa más que la región'],
                 'ue': (r'\textbf{Afinidad}: Acuerdo de Asociación (2012) con la región en bloque, ligado a la democracia; '
                        r'$0{,}4\%$ del comercio de la UE'),
                 'tesis': (r'\textbf{Sí} crea comercio y escala; \textbf{no} reparte: la industria va al más avanzado y el '
                           r'\textbf{conflicto distributivo} frena el mercado común')},
                {'titulo': 'Comunidad Andina de Naciones (CAN, 1969)', 'color': (233, 160, 40),
                 'objetivo': (r'Lo mismo, con más ambición: \textbf{programación industrial}, control de la IED y negociar '
                              r'en bloque frente a la ALALC'),
                 'escala': {'ZLC': 'a', 'UA': 'x', 'MC': 'v'},
                 'hitos': [('1969', 'Acuerdo de Cartagena'), ('1976', 'sale Chile'), ('1993', 'zona de libre comercio'),
                           ('1996', 'Protocolo de Trujillo'), ('2006', 'sale Venezuela')],
                 'gobierno': {
                     'nodos': [('pres', 1.8, 0.0, 'intergub', 'Consejo Presidencial', False),
                               ('min', 0.9, -0.72, 'intergub', 'Ministros', False),
                               ('com', 2.7, -0.72, 'intergub', 'Comisión', False),
                               ('sg', 0.9, -1.5, 'supra', 'Secretaría Gral.', False),
                               ('tri', 2.7, -1.5, 'judicial', 'Tribunal', False)],
                     'flechas': [('pres', 'min'), ('pres', 'com')],
                     'nota': r'La más \textbf{supranacional} de América Latina'},
                 'valoracion': [r'Cuota: $3\%$ (1969) $\to$ $13{,}9\%$ (1998) $\to$ $6\%$ (2023): su mejor época fue el regionalismo abierto',
                                r'Economías \textbf{competidoras}: venden materias primas a China y EE.\,UU., no a los socios',
                                r'Cada socio busca fuera: Alianza del Pacífico, MERCOSUR'],
                 'ue': (r'\textbf{Económica}: acuerdo solo comercial con Colombia, Perú y Ecuador, no con el bloque; '
                        r'$0{,}6\%$ del comercio de la UE'),
                 'tesis': (r'\textbf{No}: sin complementariedad no hay mercado regional, y ni las instituciones más fuertes '
                           r'de la región lo suplen')},
            ]),
            ('B', 'Integración de mercados sin cesión de soberanía', [
                {'titulo': 'Asociación Europea de Libre Comercio (EFTA, 1960)', 'color': (110, 165, 215),
                 'objetivo': (r'Respuesta defensiva a la CEE: \textbf{libre comercio industrial} sin ceder soberanía '
                              r'(Commonwealth, neutrales)'),
                 'escala': {'ZLC': 'a', 'UA': None, 'MC': None},
                 'hitos': [('1960', 'Convenio de Estocolmo'), ('1972', 'libre comercio con la CEE'),
                           ('1994', 'EEE, sin Suiza'), ('2026', 'Bilaterales III, Suiza')],
                 'gobierno': {
                     'nodos': [('con', 0.9, 0.0, 'intergub', 'Consejo', False),
                               ('sec', 2.7, 0.0, 'tecnico', 'Secretaría', False),
                               ('cm', 1.8, -0.75, 'intergub', 'Comité Mixto del EEE', False),
                               ('esa', 0.9, -1.5, 'supra', 'Vigilancia', False),
                               ('tri', 2.7, -1.5, 'judicial', 'Tribunal', False)],
                     'flechas': [('sec', 'con')],
                     'nota': r'Por consenso; Suiza, por comités mixtos'},
                 'valoracion': [r'Se \textbf{vació}: seis de sus diez miembros entraron en la CEE (efecto dominó, BALDWIN, 1993)',
                                r'La UE compra el $51$-$63\%$ de sus exportaciones; los socios, menos del $1\%$',
                                r'La protección agraria ($\approx 50\%$ de los ingresos; UE, $17\%$) frena la adhesión'],
                 'ue': (r'\textbf{Económica con afinidad}: su socio más integrado ($9{,}6\%$ de su comercio); el EEE les da el '
                        r'mercado interior sin voto'),
                 'tesis': (r'Como \textbf{alternativa} a la CEE, fracasó; como \textbf{antesala}, funcionó: liberalizó su '
                           r'industria antes de adherirse')},
                {'titulo': 'Tratado de Libre Comercio entre Estados Unidos, México y Canadá (NAFTA, 1994; USMCA, 2020)',
                 'color': (30, 75, 135),
                 'objetivo': (r'México: \textbf{anclar sus reformas}; EE.\,UU.: integración profunda; Canadá: no perder lo '
                              r'ganado en 1988'),
                 'escala': {'ZLC': 'a', 'UA': None, 'MC': None},
                 'hitos': [('1989', r'Canadá-EE.\,UU.'), ('1994', 'NAFTA'),
                           ('2020', 'USMCA: automóvil, China'), ('2026', r'EE.\,UU. no prorroga')],
                 'gobierno': {
                     'nodos': [('com', 1.8, 0.0, 'intergub', 'Comisión de Libre Comercio', False),
                               ('sec', 0.9, -0.75, 'tecnico', 'Secretariado', False),
                               ('cmt', 2.7, -0.75, 'tecnico', 'Comités', False),
                               ('pan', 0.9, -1.5, 'judicial', 'Paneles', False),
                               ('lab', 2.7, -1.5, 'judicial', 'Mec. laboral', False)],
                     'flechas': [('sec', 'com'), ('com', 'cmt')],
                     'nota': r'Sin órganos supranacionales: la credibilidad está en los paneles'},
                 'valoracion': [r'Cuota: $41\%$ (1989) $\to$ $56\%$ (2002-2004) $\to$ $51\%$ (2023); \textbf{radios} en torno a EE.\,UU.',
                                r'Cadena del automóvil; bienestar pequeño (CALIENDO y PARRO, 2015)',
                                r'México \textbf{no converge}: del $40\%$ al $29\%$ del PIB per cápita de EE.\,UU.'],
                 'ue': (r'\textbf{Económica}: pesan el $19\%$ del comercio de la UE, más que la UE para ellos; desde 2025, '
                        r'diversificar frente a EE.\,UU.'),
                 'tesis': (r'\textbf{Sí} en comercio y cadenas de valor; \textbf{no} en convergencia. Desde 2025, también '
                           r'geoestratégico')},
            ]),
        ],
        'balance': (r'Hay comercio cuando los socios son complementarios o se anclan a un mercado grande (UE, EE.\,UU.), no cuando '
                    r'venden lo mismo; y ningún acuerdo reparte por sí solo las ganancias' + PROB),
    },
}

def color(nombre, c):
    return r'\definecolor{%s}{RGB}{%d,%d,%d}%%' % (nombre, *c)


def escala(x, y, grados, c):
    """Escala de BALASSA: círculo hueco = previsto; relleno = alcanzado; medio = en parte; aspa = abandonado; gris = no previsto."""
    o, paso = [], 0.92
    o.append(f'    \\draw[black!25, line width=0.5pt] ({x:.2f},{y:.2f}) -- ({x + paso * (len(ESCALA) - 1):.2f},{y:.2f});')
    for i, g in enumerate(ESCALA):
        xi, est = x + i * paso, grados.get(g)
        if est is None:
            o.append(f'    \\fill[black!25] ({xi:.2f},{y:.2f}) circle (1.3pt);')
            o.append(f'    \\node[anchor=west, inner sep=1.5pt, text=black!40, fill=white] at ({xi + 0.1:.2f},{y:.2f}) {{{g}}};')
            continue
        o.append(f'    \\draw[{c}, fill=white, line width=0.8pt] ({xi:.2f},{y:.2f}) circle (3.3pt);')
        if est == 'a':
            o.append(f'    \\fill[{c}] ({xi:.2f},{y:.2f}) circle (2.1pt);')
        elif est == 'p':
            o.append(f'    \\fill[{c}] ({xi:.2f},{y:.2f}) ++(0,2.1pt) arc (90:270:2.1pt) -- cycle;')
        elif est == 'x':
            o.append(f'    \\draw[{c}, line width=0.8pt] ({xi:.2f},{y:.2f}) ++(-2.3pt,-2.3pt) -- ++(4.6pt,4.6pt) '
                     f'++(-4.6pt,0) -- ++(4.6pt,-4.6pt);')
        o.append(f'    \\node[anchor=west, inner sep=1.5pt, fill=white] at ({xi + 0.12:.2f},{y:.2f}) {{{g}}};')
    return o


def lista(filas, ancho, marca=None):
    """Tabla de dos columnas (año o marca a la izquierda, texto que se parte): sin el paquete array, con \\tabularnewline."""
    ancho_t = ancho - (0.75 if marca is None else 0.3)
    cuerpo = []
    for f in filas:
        izq, der = (f if marca is None else (marca, f))
        cuerpo.append(f'{izq} & \\raggedright {der}\\tabularnewline')
    sep = r'\noalign{\vskip 1.5pt}'
    return (f'\\begin{{tabular}}{{@{{}}l@{{\\hspace{{4pt}}}}p{{{ancho_t:.2f}cm}}@{{}}}}' + sep.join(cuerpo) + r'\end{tabular}')


def gobierno(k, g):
    """Organigrama mínimo, en coordenadas relativas al origen de la columna (x = centro de cada órgano)."""
    o = []
    for clave, x, y, tipo, txt, disc in g['nodos']:
        o.append(f'    \\node[gob={tipo}{", dashed" if disc else ""}] (g{k}{clave}) at ({x:.2f},{y * 0.8 - 0.17:.2f}) {{{txt}}};')
    for a, b in g['flechas']:
        o.append(f'    \\draw[gflecha] (g{k}{a}) -- (g{k}{b});')
    ymin = min(y for _, _, y, *_ in g['nodos'])
    o.append(f'    \\node[anchor=north west, text width=3.55cm, align=left, inner sep=0pt, font=\\footnotesize\\itshape, '
             f'text=black!70] (g{k}nota) at (0,{ymin * 0.8 - 0.42:.2f}) {{{g["nota"]}}};')
    return o


def main(clave):
    B = BLOQUES[clave]
    o = [f'% Esquema de una página del bloque «{B["titulo"]}», para el anexo «Material de estudio: Esquemas».',
         '% Generado por Code/esquemas.py (no editar a mano). Generar el PDF con: bash Code/generar_figura.sh Esquema_' + clave,
         color('eGri', (110, 110, 110))]
    for t, (borde, relleno) in TIPOS.items():
        o += [color(f'b{t}', borde), color(f'r{t}', relleno)]
    acuerdos = [a for _, _, lista_ in B['grupos'] for a in lista_]
    for i, a in enumerate(acuerdos):
        o.append(color(f'eA{i}', a['color']))
    o += [r'\begin{tikzpicture}[font=\footnotesize, x=1cm, y=1cm,',
          r'    every node/.append style={execute at begin node={\hyphenpenalty=10000\exhyphenpenalty=10000}},',
          r'    flecha/.style={-{Latex[length=1.5mm]}, line width=0.6pt, black!55},',
          r'    gflecha/.style={-{Latex[length=1.2mm]}, line width=0.5pt, black!60},',
          r'    gob/.style={draw=b#1, fill=r#1, line width=0.6pt, rounded corners=1.5pt, inner sep=1.8pt, align=center},',
          r'    rot/.style={anchor=north west, inner sep=0pt, font=\footnotesize\bfseries, text=eGri},',
          r'    txt/.style={anchor=north west, inner sep=0pt, align=left}]']

    # --- Rótulo del bloque y cadena: tesis -> justificación -> medios ---
    o.append(f'  \\node[anchor=south west, inner sep=0pt, font=\\normalsize\\bfseries, text=eGri] at (0,0.05) {{{B["titulo"]}}};')
    o.append(f'  \\draw[eGri, line width=0.8pt] (0,-0.05) -- ({W},-0.05);')
    cab = [(0.0, 3.3, 'Tesis'), (3.6, 6.0, 'Justificación'), (9.9, W - 9.9, 'Medios: dos estrategias')]
    for i, (x, w, r) in enumerate(cab):
        o.append(f'  \\node[rot] at ({x:.2f},-0.2) {{{r}}};')
        if i < len(cab) - 1:
            o.append(f'  \\draw[flecha] ({x + w + 0.02:.2f},-0.32) -- ({cab[i + 1][0] - 0.04:.2f},-0.32);')
    o.append(f'  \\node[txt, text width={cab[0][1]:.2f}cm] (tesis) at (0,-0.6) {{{B["tesis"]}}};')
    o.append(f'  \\node[txt, text width={cab[1][1]:.2f}cm] (just) at ({cab[1][0]:.2f},-0.6) {{{B["justificacion"]}}};')
    previo = None
    for letra, cont in B['medios']:
        donde = f'({cab[2][0]:.2f},-0.6)' if previo is None else f'([yshift=-0.12cm]{previo}.south west)'
        o.append(f'  \\node[txt, text width={cab[2][1]:.2f}cm] (med{letra}) at {donde} {{\\hangindent=0.45cm\\hangafter=0'
                 f'\\llap{{\\colorbox{{eGri}}{{\\textcolor{{white}}{{\\textbf{{{letra}}}}}}}\\hspace{{0.12cm}}}}{cont}}};')
        previo = f'med{letra}'
    o.append(f'  \\path let \\p1=(tesis.south), \\p2=(just.south), \\p3=({previo}.south), \\n1={{min(\\y1,\\y2,\\y3)}} in '
             f'coordinate (sig) at (0,\\n1-0.35cm);')

    # --- Grupos y acuerdos ---
    k = 0
    for letra, titulo, lista_ in B['grupos']:
        o.append(f'  \\fill[eGri!14] (sig) rectangle ([shift={{({W},-0.42)}}]sig);')
        o.append(f'  \\node[anchor=west, fill=eGri, text=white, font=\\small\\bfseries, inner sep=2pt] at ([shift={{(0.04,-0.21)}}]sig) {{{letra}}};')
        o.append(f'  \\node[anchor=west, inner sep=0pt, font=\\footnotesize\\bfseries, text=eGri] at ([shift={{(0.5,-0.21)}}]sig) {{{titulo}}};')
        o.append(f'  \\coordinate (sig) at ([yshift=-0.62cm]sig);')
        for a in lista_:
            c = f'eA{k}'
            o.append(f'  % ----- {a["titulo"]} -----')
            o.append(f'  \\begin{{scope}}[shift={{(sig)}}]')
            o.append(f'    \\node[anchor=north west, inner sep=0pt, font=\\small\\bfseries, text={c}!85!black] at (0,0) {{{a["titulo"]}}};')
            o.append(f'    \\draw[{c}, line width=1pt] (0,-0.42) -- ({W},-0.42);')
            for i, (x, w, r) in enumerate(COLS):
                o.append(f'    \\node[rot] at ({x:.2f},-0.55) {{{r}}};')
                if i < len(COLS) - 1:
                    o.append(f'    \\draw[flecha] ({x + w + 0.02:.2f},-0.67) -- ({COLS[i + 1][0] - 0.04:.2f},-0.67);')
            (x0, w0, _), (x1, w1, _), (x2, w2, _), (x3, w3, _) = COLS
            o.append(f'    \\node[txt, text width={w0:.2f}cm] (obj{k}) at ({x0:.2f},-0.95) {{{a["objetivo"]}}};')
            o += escala(x1 + 0.12, -1.07, a['escala'], c)
            hitos = [(f'\\textbf{{\\textcolor{{{c}!85!black}}{{{an}}}}}', t) for an, t in a['hitos']]
            o.append(f'    \\node[txt] (como{k}) at ({x1:.2f},-1.32) {{{lista(hitos, w1)}}};')
            o.append(f'    \\begin{{scope}}[shift={{({x2:.2f},-0.95)}}]')
            o += ['  ' + l for l in gobierno(k, a['gobierno'])]
            o.append(f'    \\end{{scope}}')
            o.append(f'    \\node[txt] (val{k}) at ({x3:.2f},-0.95) {{{lista(a["valoracion"], w3, marca=f"\\textcolor{{{c}}}{{$\\triangleright$}}")}}};')
            o.append(f'  \\end{{scope}}')
            o.append(f'  \\path let \\p1=(obj{k}.south), \\p2=(como{k}.south), \\p3=(g{k}nota.south), \\p4=(val{k}.south), '
                     f'\\n1={{min(\\y1,\\y2,\\y3,\\y4)}} in coordinate (fondo) at (0,\\n1-0.2cm);')
            (y0, v0, r0), (y1, v1, r1) = ABAJO
            o.append(f'  \\draw[flecha] ([shift={{({y0 + v0 + 0.02:.2f},-0.15)}}]fondo) -- ([shift={{({y1 - 0.04:.2f},-0.15)}}]fondo);')
            o.append(f'  \\node[txt, text width={v0:.2f}cm] (ue{k}) at ([xshift={y0:.2f}cm]fondo) '
                     f'{{\\textcolor{{eGri}}{{\\textbf{{{r0}.}}}} {a["ue"]}}};')
            o.append(f'  \\node[txt, text width={v1:.2f}cm] (tes{k}) at ([xshift={y1:.2f}cm]fondo) '
                     f'{{\\textcolor{{eGri}}{{\\textbf{{{r1}}}}} {a["tesis"]}}};')
            o.append(f'  \\path let \\p1=(ue{k}.south), \\p2=(tes{k}.south), \\n1={{min(\\y1,\\y2)}} in coordinate (sig) at (0,\\n1-0.38cm);')
            k += 1

    # --- Balance del bloque ---
    o.append(f'  \\draw[eGri, line width=0.8pt] ([yshift=0.12cm]sig) -- ([shift={{({W},0.12)}}]sig);')
    o.append(f'  \\node[txt, text width={W:.2f}cm] at ([yshift=-0.05cm]sig) {{$\\Rightarrow$ \\textbf{{Balance del bloque}}: {B["balance"]}}};')
    o.append(r'\end{tikzpicture}%')
    destino = TEMA / 'Img' / f'Esquema_{clave}.tikz'
    destino.write_text('\n'.join(o) + '\n', encoding='utf-8')
    print('Escrito', destino.relative_to(TEMA))


if __name__ == '__main__':
    for clave in (sys.argv[1:] or BLOQUES):
        main(clave)
