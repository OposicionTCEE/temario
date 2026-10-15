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
COLS = [(0.0, 2.85, 'Objetivo'), (3.13, 3.55, 'Cómo se construyó'), (6.96, 3.85, 'Gobierno'), (11.09, W - 11.09, 'Valoración')]
ABAJO = [(0.0, 7.75, 'Con la UE'), (8.05, W - 8.05, r'$\Rightarrow$ ¿Confirma la tesis?')]
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
        'justificacion': (r'\textbf{Estáticas}: creación $>$ desviación (VINER, 1950)\\'
                          r'\textbf{Dinámicas}: escala, competencia, inversión\\'
                          r'\textbf{Vecinos} = socios naturales $\Rightarrow$ poca desviación (WONNACOTT y LUTZ, 1989; KRUGMAN, 1991)\\'
                          r'\textbf{Credibilidad}: un tratado ata las reformas (FERNÁNDEZ y PORTES, 1998)'),
        'medios': [
            ('A', r'\textbf{Regionalismo cerrado} (CEPAL): industrializar tras un AEC a menor coste '
                  r'(COOPER y MASSELL, 1965) $\to$ MCCA, CAN'),
            ('B', r'\textbf{Sin cesión de soberanía}: libre comercio sin AEC ni órganos supranacionales; precio: reglas de '
                  r'origen $\to$ EFTA, NAFTA'),
        ],
        'grupos': [
            ('A', 'Regionalismo cerrado, reconvertido en abierto en los años noventa (CEPAL, 1994)', [
                {'titulo': 'Mercado Común Centroamericano (MCCA, 1960)', 'color': (200, 76, 58),
                 'objetivo': (r'Industrializar cinco economías de café y banano: mercado común tras un AEC y '
                              r'\textbf{reparto de las industrias}'),
                 'escala': {'ZLC': 'a', 'UA': 'p', 'MC': 'v'},
                 'hitos': [('1960', 'Tratado de Managua'), ('1969', 'guerra entre socios'),
                           ('1993', 'regionalismo abierto'), ('2017', 'unión aduanera parcial')],
                 'gobierno': {
                     'nodos': [('pres', 0.85, 0, 'intergub', 'Presidentes', False),
                               ('com', 2.75, 0, 'intergub', 'COMIECO', False),
                               ('sie', 0.55, 1, 'tecnico', 'SIECA', False),
                               ('cor', 1.65, 1, 'judicial', 'Corte', True),
                               ('par', 3.0, 1, 'parlamento', 'Parlamento', True)],
                     'flechas': [('pres', 'com'), ('sie', 'com')],
                     'nota': r'Consenso: nadie hace cumplir'},
                 'valoracion': [r'Cuota alta: $18\%$ (1965) $\to$ $26\%$ (1970) $\to$ $25\%$ (2023)',
                                r'Mercado de la \textbf{industria ligera}, concentrada en Guatemala y El Salvador',
                                r'Honduras y Nicaragua, déficits ($\approx 7\%$ del PIB); el DR-CAFTA pesa más'],
                 'ue': (r'\textbf{Afinidad}: asociación (2012) con la región en bloque, ligada a la democracia; '
                        r'$0{,}4\%$ del comercio de la UE'),
                 'tesis': (r'\textbf{Sí} crea comercio y escala; \textbf{no} reparte: la industria va al más avanzado '
                           r'(\textbf{conflicto distributivo})')},
                {'titulo': 'Comunidad Andina de Naciones (CAN, 1969)', 'color': (233, 160, 40),
                 'objetivo': (r'Lo mismo, con más ambición: \textbf{programación industrial}, control de la IED y negociar '
                              r'en bloque'),
                 'escala': {'ZLC': 'a', 'UA': 'x', 'MC': 'v'},
                 'hitos': [('1969', 'Acuerdo de Cartagena'), ('1976', 'sale Chile'), ('1993', 'zona de libre comercio'),
                           ('2006', 'sale Venezuela')],
                 'gobierno': {
                     'nodos': [('min', 0.85, 0, 'intergub', 'Ministros', False),
                               ('com', 2.75, 0, 'intergub', 'Comisión', False),
                               ('sg', 0.95, 1, 'supra', 'Secretaría Gral.', False),
                               ('tri', 2.75, 1, 'judicial', 'Tribunal', False)],
                     'flechas': [],
                     'nota': r'Decisiones de aplicación directa'},
                 'valoracion': [r'Cuota: $3\%$ (1969) $\to$ $13{,}9\%$ (1998) $\to$ $6\%$ (2023)',
                                r'Economías \textbf{competidoras}: venden materias primas a China y EE.\,UU.',
                                r'Cada socio busca fuera: Alianza del Pacífico, MERCOSUR'],
                 'ue': (r'\textbf{Económica}: acuerdo solo comercial con tres socios, no con el bloque; '
                        r'$0{,}6\%$ del comercio de la UE'),
                 'tesis': (r'\textbf{No}: sin complementariedad no hay mercado regional, ni con las instituciones más '
                           r'\textbf{supranacionales} de la región')},
            ]),
            ('B', 'Integración de mercados sin cesión de soberanía', [
                {'titulo': 'Asociación Europea de Libre Comercio (EFTA, 1960)', 'color': (110, 165, 215),
                 'objetivo': r'Respuesta defensiva a la CEE: \textbf{libre comercio industrial} sin ceder soberanía',
                 'escala': {'ZLC': 'a', 'UA': None, 'MC': None},
                 'hitos': [('1960', 'Convenio de Estocolmo'), ('1972', 'acuerdos con la CEE'),
                           ('1994', 'EEE, sin Suiza'), ('2026', 'Bilaterales III, Suiza')],
                 'gobierno': {
                     'nodos': [('con', 0.85, 0, 'intergub', 'Consejo', False),
                               ('sec', 2.75, 0, 'tecnico', 'Secretaría', False),
                               ('cm', 0.5, 1, 'intergub', 'Comité', False),
                               ('esa', 1.84, 1, 'supra', 'Vigilancia', False),
                               ('tri', 3.27, 1, 'judicial', 'Tribunal', False)],
                     'flechas': [('sec', 'con')],
                     'nota': r'Abajo, los órganos del EEE'},
                 'valoracion': [r'Se \textbf{vació}: seis de diez miembros entraron en la CEE (efecto dominó)',
                                r'La UE compra el $51$-$63\%$ de sus exportaciones; los socios, menos del $1\%$',
                                r'Protección agraria ($\approx 50\%$ de los ingresos; UE, $17\%$): frena la adhesión'],
                 'ue': (r'\textbf{Económica con afinidad}: su socio más integrado ($9{,}6\%$ de su comercio); el EEE les da '
                        r'el mercado interior sin voto'),
                 'tesis': r'Como \textbf{alternativa} a la CEE, fracasó; como \textbf{antesala}, funcionó'},
                {'titulo': 'Tratado de Libre Comercio entre Estados Unidos, México y Canadá (NAFTA, 1994; USMCA, 2020)',
                 'color': (30, 75, 135),
                 'objetivo': (r'México: \textbf{anclar sus reformas}; EE.\,UU.: integración profunda; Canadá: no perder lo '
                              r'ganado en 1988'),
                 'escala': {'ZLC': 'a', 'UA': None, 'MC': None},
                 'hitos': [('1989', r'Canadá-EE.\,UU.'), ('1994', 'NAFTA'),
                           ('2020', 'USMCA, más exigente'), ('2026', r'EE.\,UU. no prorroga')],
                 'gobierno': {
                     'nodos': [('com', 1.25, 0, 'intergub', 'Comisión', False),
                               ('cmt', 3.0, 0, 'tecnico', 'Comités', False),
                               ('sec', 0.85, 1, 'tecnico', 'Secretariado', False),
                               ('pan', 2.2, 1, 'judicial', 'Paneles', False),
                               ('lab', 3.3, 1, 'judicial', 'Laboral', False)],
                     'flechas': [('com', 'cmt')],
                     'nota': r'Sin órganos supranacionales'},
                 'valoracion': [r'Cuota: $41\%$ (1989) $\to$ $56\%$ (2003) $\to$ $51\%$ (2023); \textbf{radios} en torno a EE.\,UU.',
                                r'Cadena del automóvil; bienestar pequeño (CALIENDO y PARRO, 2015)',
                                r'México \textbf{no converge}: del $40\%$ al $29\%$ del PIB per cápita de EE.\,UU.'],
                 'ue': (r'\textbf{Económica}: $19\%$ del comercio de la UE, más que la UE para ellos; desde 2025, '
                        r'diversificar frente a EE.\,UU.'),
                 'tesis': (r'\textbf{Sí} en comercio y cadenas; \textbf{no} en convergencia. Desde 2025, también '
                           r'geoestratégico')},
            ]),
        ],
        'balance': (r'Hay comercio cuando los socios son complementarios o se anclan a un mercado grande (UE, EE.\,UU.), no cuando '
                    r'venden lo mismo; y ningún acuerdo reparte por sí solo las ganancias' + PROB),
    },
    'afinidad': {
        'titulo': 'Afinidad: ¿cuáles son los impulsores de la integración?',
        'tesis': (r'Nacen de una \textbf{afinidad política o identitaria}, no de un cálculo económico: sus '
                  r'\textbf{ambiciones} van por delante del comercio'),
        'justificacion': (r'\textbf{Compromiso político}: un tratado con los vecinos encarece abandonar el régimen (FERNÁNDEZ y '
                          r'PORTES, 1998)\\'
                          r'\textbf{Proyecto identitario}: el mercado común como instrumento de unidad\\'
                          r'\textbf{Pero}: sin complementariedad, las instituciones van por delante del comercio'),
        'medios': [
            ('A', r'\textbf{Afinidad de régimen}: anclar la democracia y el mercado tras las dictaduras o el bloque '
                  r'soviético $\to$ MERCOSUR, CEFTA'),
            ('B', r'\textbf{Identidad panregional}: dar forma económica al panafricanismo (Unión Africana) y al panarabismo '
                  r'(Liga Árabe) $\to$ AfCFTA, PAFTA'),
        ],
        'grupos': [
            ('A', 'Afinidad de régimen político', [
                {'titulo': 'Mercado Común del Sur (MERCOSUR, 1991)', 'color': (30, 75, 135),
                 'objetivo': (r'\textbf{Reconciliar} a Argentina y Brasil y anclar la \textbf{democracia}: el comercio, '
                              r'instrumento'),
                 'escala': {'ZLC': 'p', 'UA': 'p', 'MC': 'v'},
                 'hitos': [('1985', 'Foz de Iguazú'), ('1991', 'Tratado de Asunción'), ('1994', 'Ouro Preto: AEC'),
                           ('1998', 'Ushuaia: democracia')],
                 'gobierno': {
                     'nodos': [('cmc', 0.45, 0, 'intergub', 'Consejo', False),
                               ('gmc', 2.5, 0, 'intergub', 'Grupo Mercado Común', False),
                               ('tpr', 0.6, 1, 'judicial', 'Tribunal', False),
                               ('par', 1.85, 1, 'parlamento', 'Parlasur', True),
                               ('foc', 3.2, 1, 'financiero', 'FOCEM', False)],
                     'flechas': [('cmc', 'gmc')],
                     'nota': r'Consenso; sin aplicación directa'},
                 'valoracion': [r'Cuota: $25\%$ (1998) $\to$ $11\%$ (2023); ¿desviación? (YEATS, 1998)',
                                r'Devaluaciones de 1999 y 2002: sin monedas estables no hay comercio',
                                r'Negociación conjunta en crisis (Uruguay, Argentina)'],
                 'ue': (r'\textbf{Geopolítica}: acuerdo (2026) para diversificar y asegurar materias primas críticas; pesa el '
                        r'$2\%$ del comercio de la UE'),
                 'tesis': (r'\textbf{Sí} en lo político; en el comercio, solo mientras hubo voluntad política y monedas '
                           r'estables')},
                {'titulo': 'Acuerdo Centroeuropeo de Libre Comercio (CEFTA, 1992)', 'color': (200, 76, 58),
                 'objetivo': (r'Anclar en la \textbf{democracia} y el mercado a los que salían del bloque soviético: una '
                              r'\textbf{antesala} de la UE'),
                 'escala': {'ZLC': 'a', 'UA': None, 'MC': None},
                 'hitos': [('1992', 'Cracovia: Visegrado'), ('2004', 'se vacía hacia la UE'), ('2006', 'CEFTA 2006: Balcanes'),
                           ('2020', 'cuatro libertades')],
                 'gobierno': {
                     'nodos': [('cm', 0.85, 0, 'intergub', 'Comité Mixto', False),
                               ('sec', 2.75, 0, 'tecnico', 'Secretaría', False),
                               ('sub', 0.85, 1, 'tecnico', 'Subcomités', False),
                               ('dif', 2.75, 1, 'judicial', 'Diferencias', True)],
                     'flechas': [('sec', 'cm')],
                     'nota': r'Consenso; lo financia la UE'},
                 'valoracion': [r'Cumplió: los fundadores, salvo Macedonia del Norte, están en la UE',
                                r'Cuota del $22{,}5\%$ al $15\%$; la UE, el $68\%$',
                                r'Afinidad frágil: Kosovo contra Serbia (2018-2020)'],
                 'ue': (r'\textbf{Geopolítica}, con la adhesión como horizonte: frente a Rusia y China; pesa el $1{,}7\%$ del '
                        r'comercio de la UE'),
                 'tesis': r'\textbf{Sí}: su éxito se mide por su \textbf{desaparición}; el mercado regional nunca fue el objetivo'},
            ]),
            ('B', 'Identidad panregional', [
                {'titulo': 'Área Continental Africana de Libre Comercio (AfCFTA, 2018)', 'color': (60, 140, 90),
                 'objetivo': r'Dar forma económica al \textbf{panafricanismo}: un mercado único de $54$ economías',
                 'escala': {'ZLC': 'p', 'UA': 'v', 'MC': 'v'},
                 'hitos': [('2012', 'decisión en Addis Abeba'), ('2018', 'firma en Kigali'), ('2021', 'comienza el comercio'),
                           ('2025', '39 países ya comercian')],
                 'gobierno': {
                     'nodos': [('asa', 0.85, 0, 'intergub', 'Asamblea', False),
                               ('min', 2.75, 0, 'intergub', 'Ministros', False),
                               ('sec', 0.63, 1, 'tecnico', 'Secretaría', False),
                               ('osd', 2.0, 1, 'judicial', 'Diferencias', False),
                               ('pap', 3.35, 1, 'financiero', 'PAPSS', False)],
                     'flechas': [('asa', 'min')],
                     'nota': r'Sobre ocho comunidades regionales'},
                 'valoracion': [r'Cuota: $12\%$ $\to$ $20\%$, antes del acuerdo',
                                r'Poca \textbf{complementariedad}: materias primas fuera, manufacturas dentro',
                                r'Ganancias \textbf{dinámicas}: con IED, $+109\%$ de comercio intraafricano en 2035'],
                 'ue': (r'\textbf{Geopolítica} con afinidad: \textit{Global Gateway} frente a la Franja y la Ruta china; '
                        r'$6{,}8\%$ del comercio de la UE'),
                 'tesis': (r'\textbf{Sí} para firmar y ratificar casi en bloque; \textbf{no}, todavía, para aplicar: la identidad '
                           r'no crea complementariedad')},
                {'titulo': 'Zona de Libre Comercio Pan-Árabe (PAFTA, 1998)', 'color': (150, 90, 160),
                 'objetivo': (r'Dar contenido económico al \textbf{panarabismo} de la Liga Árabe, en su versión menos '
                              r'ambiciosa'),
                 'escala': {'ZLC': 'a', 'UA': 'v', 'MC': 'v'},
                 'hitos': [('1964', 'Mercado Común Árabe'), ('1998', 'programa ejecutivo'), ('2005', 'aranceles cero'),
                           ('2017', 'bloqueo a Catar')],
                 'gobierno': {
                     'nodos': [('ces', 0.85, 0, 'intergub', 'Consejo', False),
                               ('sg', 2.75, 0, 'tecnico', 'Secretaría', False),
                               ('com', 0.85, 1, 'tecnico', 'Comités', False),
                               ('fma', 2.75, 1, 'financiero', 'Fondo Monetario', False)],
                     'flechas': [('sg', 'ces')],
                     'nota': r'Consenso; sin arbitraje eficaz'},
                 'valoracion': [r'Cuota: $6\%$ (1998) $\to$ $13\%$ $\to$ $10\%$ (2023)',
                                r'Sin combustibles, un tercio va a los socios: el petróleo se vende fuera',
                                r'Cada subregión mira fuera: el Golfo, a Asia; el Magreb, a la UE'],
                 'ue': (r'\textbf{Geopolítica}: vecindad (estabilidad, migración, energía), nunca con el bloque; $7{,}5\%$ del '
                        r'comercio de la UE'),
                 'tesis': (r'\textbf{Sí} en aranceles; \textbf{no} en comercio: economías demasiado parecidas, que venden '
                           r'petróleo fuera')},
            ]),
        ],
        'balance': (r'La afinidad basta para firmar y crear instituciones, no para crear comercio: sin complementariedad, el '
                    r'comercio sigue mirando fuera, y el único éxito pleno, el CEFTA, lo es porque su meta era entrar en la UE'
                    + PROB),
    },
    'geoestrategico': {
        'titulo': 'Integración por motivos geoestratégicos',
        'hueco': 0.26,
        'tesis': (r'La integración como \textbf{instrumento de política exterior}: avanza con la geopolítica, y su comercio '
                  r'mira \textbf{fuera del bloque}'),
        'justificacion': (r'\textbf{Comercio = poder}: quien concentra los intercambios de sus socios gana influencia '
                          r'(HIRSCHMAN, 1945)\\'
                          r'\textbf{Se juzgan} por el equilibrio de poder, no solo por el comercio\\'
                          r'\textbf{Complementariedad}: casi siempre baja'),
        'medios': [
            ('A', r'\textbf{Seguridad frente a una amenaza}: Estados débiles frente al comunismo o a Irán; el comercio, '
                  r'después $\to$ ASEAN, CCG'),
            ('B', r'\textbf{Esferas de influencia}: potencias que compiten por escribir las reglas y atar a sus vecinos '
                  r'$\to$ RCEP, CPTPP, UEE'),
        ],
        'grupos': [
            ('A', 'Seguridad frente a una amenaza', [
                {'titulo': 'Asociación de Naciones del Sudeste Asiático (ASEAN, 1967)', 'color': (200, 76, 58),
                 'objetivo': (r'Cinco gobiernos frente al comunismo: el \textbf{crecimiento como defensa}'),
                 'escala': {'ZLC': 'a', 'UA': None, 'MC': 'v'},
                 'hitos': [('1967', 'Declaración de Bangkok'), ('1992', 'zona de libre comercio'), ('2015', 'Comunidad Económica')],
                 'gobierno': {
                     'nodos': [('cum', 0.85, 0, 'intergub', 'Cumbre', False),
                               ('cc', 2.75, 0, 'intergub', 'Consejos', False),
                               ('sec', 0.85, 1, 'tecnico', 'Secretaría', False),
                               ('cmi', 2.75, 1, 'financiero', 'Chiang Mai', False)],
                     'flechas': [('cum', 'cc')],
                     'nota': r'Consenso y no injerencia'},
                 'valoracion': [r'Cuota estancada: $21\%$ (1967), $22\%$ (2023)',
                                r'\textbf{Eslabón} de la fábrica china: insumos a China, bienes finales a EE.\,UU.',
                                r'Ventaja frente a China: de $1{,}8$ a $0{,}4$ puntos'],
                 'ue': (r'\textbf{Económica}, teñida de geopolítica: acuerdos bilaterales (Singapur, Vietnam, Indonesia); '
                        r'$5\%$ del comercio de la UE'),
                 'tesis': (r'\textbf{Sí} en estabilidad; el comercio mira fuera, y la rivalidad China-EE.\,UU. amenaza su '
                           r'centralidad')},
                {'titulo': 'Consejo de Cooperación del Golfo (CCG, 1981)', 'color': (60, 140, 90),
                 'objetivo': r'\textbf{Alianza de seguridad} de seis monarquías frente a Irán; la economía, complemento',
                 'escala': {'ZLC': 'a', 'UA': 'a', 'MC': 'p'},
                 'hitos': [('1981', 'fundación en Riad'), ('2008', 'mercado común'), ('2015', 'unión aduanera plena')],
                 'gobierno': {
                     'nodos': [('sup', 1.1, 0, 'intergub', 'Consejo Supremo', False),
                               ('sg', 3.0, 0, 'tecnico', 'Secretaría', False),
                               ('min', 0.85, 1, 'intergub', 'Ministros', False),
                               ('mon', 2.75, 1, 'financiero', 'Consejo Monetario', True)],
                     'flechas': [('sg', 'sup')],
                     'nota': r'Unanimidad en lo importante'},
                 'valoracion': [r'Cuota baja: $3\%$ (1998) $\to$ $8\%$ (2023)',
                                r'Vende a Asia (China, $19\%$) y \textbf{se arma en Occidente} (EE.\,UU., $60$-$66\%$)',
                                r'Exporta hidrocarburos (hasta el $93\%$)'],
                 'ue': (r'\textbf{Geopolítica}: energía y seguridad; negociación comercial parada desde 2008; $3{,}1\%$ del '
                        r'comercio de la UE'),
                 'tesis': (r'\textbf{Sí}: la amenaza dio cohesión y unión aduanera, pero depende de la política (bloqueo a '
                           r'Catar, 2017)')},
            ]),
            ('B', 'Construcción de esferas de influencia', [
                {'titulo': 'Asociación Económica Integral Regional (RCEP, 2022)', 'color': (233, 160, 40),
                 'objetivo': r'Asegurar a \textbf{China} un espacio propio en Asia, sin EE.\,UU. ni la India',
                 'escala': {'ZLC': 'p', 'UA': None, 'MC': None},
                 'hitos': [('2012', 'lanzamiento (ASEAN)'), ('2019', 'sale la India'), ('2022', 'entra en vigor')],
                 'gobierno': {
                     'nodos': [('min', 0.85, 0, 'intergub', 'Ministros', False),
                               ('cc', 2.75, 0, 'intergub', 'Comité Conjunto', False),
                               ('sec', 0.85, 1, 'tecnico', 'Secretaría', False),
                               ('pan', 2.75, 1, 'judicial', 'Paneles', False)],
                     'flechas': [('min', 'cc')],
                     'nota': r'Método ASEAN: consenso'},
                 'valoracion': [r'El mayor bloque, pero libera poco',
                                r'Nuevos enlaces: China-Japón y Japón-Corea',
                                r'\textbf{Dependencia asimétrica} de China (HIRSCHMAN)'],
                 'ue': (r'\textbf{Económica}: sus miembros pesan el $26\%$ del comercio de la UE; riesgo de desviación y '
                        r'acuerdos con cinco de ellos'),
                 'tesis': (r'\textbf{Sí}: libera poco, pero consolida a \textbf{China} como centro de Asia en lugar de Japón')},
                {'titulo': 'Acuerdo Amplio y Progresista de Asociación Transpacífico (CPTPP, 2018)', 'color': (30, 75, 135),
                 'objetivo': r'Escribir las \textbf{reglas} de Asia-Pacífico antes que China; sin EE.\,UU., lo lidera Japón',
                 'escala': {'ZLC': 'a', 'UA': None, 'MC': None},
                 'hitos': [('2017', r'EE.\,UU. deja el TPP'), ('2018', 'CPTPP en vigor'), ('2024', 'entra Reino Unido')],
                 'gobierno': {
                     'nodos': [('com', 0.85, 0, 'intergub', 'Comisión', False),
                               ('cmt', 2.75, 0, 'tecnico', 'Comités', False),
                               ('pan', 0.85, 1, 'judicial', 'Paneles', False),
                               ('isds', 2.75, 1, 'judicial', 'Inversiones', True)],
                     'flechas': [('com', 'cmt')],
                     'nota': r'Ministros, por consenso'},
                 'valoracion': [r'Sin EE.\,UU., $70\%$ menos de ganancias',
                                r'Comercio interno del $9\%$: lo valioso son las \textbf{reglas}',
                                r'China y Taiwán piden entrar'],
                 'ue': (r'\textbf{Afinidad de reglas}: ya tiene acuerdos con casi todos ($20\%$ de su comercio); diálogo '
                        r'desde 2025 frente al proteccionismo'),
                 'tesis': r'\textbf{Sí}: fija las reglas sin EE.\,UU., aunque el comercio que crea es poco'},
                {'titulo': 'Unión Económica Euroasiática (UEE, 2015)', 'color': (150, 90, 160),
                 'objetivo': r'Instrumento de \textbf{Rusia} ($80\%$ del PIB) para reconstruir su esfera postsoviética',
                 'escala': {'ZLC': 'a', 'UA': 'p', 'MC': 'p'},
                 'hitos': [('1994', 'idea de Nazarbáyev'), ('2010', 'unión aduanera'), ('2015', 'Unión Económica')],
                 'gobierno': {
                     'nodos': [('sup', 1.1, 0, 'intergub', 'Consejo Supremo', False),
                               ('com', 3.05, 0, 'supra', 'Comisión', False),
                               ('tri', 0.85, 1, 'judicial', 'Tribunal', True),
                               ('ban', 2.75, 1, 'financiero', 'Banco', False)],
                     'flechas': [('sup', 'com')],
                     'nota': r'Forma supranacional, fondo ruso'},
                 'valoracion': [r'No crea comercio: cuota del $9$-$13\%$',
                                r'Movilidad laboral avanzada, pero Tayikistán, fuera, recibe más remesas',
                                r'Tras 2022, \textbf{desvío}: UE a Kirguistán $\times 9$'],
                 'ue': (r'\textbf{Geopolítica en negativo}: sin relación formal, para no legitimar la esfera rusa; vigila la '
                        r'elusión de sanciones'),
                 'tesis': (r'\textbf{Sí} para Rusia, como esfera de influencia; \textbf{no} como mercado: el comercio interno no '
                           r'crece')},
            ]),
        ],
        'balance': (r'Los acuerdos de seguridad dan cohesión mientras dura la amenaza, y los de influencia atan a los socios '
                    r'con dependencias asimétricas; en ninguno, el comercio entre los miembros es el resultado principal'
                    + PROB),
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
    ancho_t = ancho - (0.68 if marca is None else 0.3)
    cuerpo = []
    for f in filas:
        izq, der = (f if marca is None else (marca, f))
        cuerpo.append(f'{izq} & \\raggedright {der}\\tabularnewline')
    sep = r'\noalign{\vskip 1.5pt}'
    return (f'\\begin{{tabular}}{{@{{}}l@{{\\hspace{{4pt}}}}p{{{ancho_t:.2f}cm}}@{{}}}}' + sep.join(cuerpo) + r'\end{tabular}')


def gobierno(k, g):
    """Organigrama mínimo en dos filas (0, la que decide; 1, la que apoya, vigila o juzga), relativo al origen de la columna."""
    o = []
    for clave, x, fila, tipo, txt, disc in g['nodos']:
        o.append(f'    \\node[gob={tipo}{", dashed" if disc else ""}] (g{k}{clave}) at ({x:.2f},{-0.17 - 0.62 * fila:.2f}) {{{txt}}};')
    for a, b in g['flechas']:
        o.append(f'    \\draw[gflecha] (g{k}{a}) -- (g{k}{b});')
    o.append(f'    \\node[anchor=north west, inner sep=0pt, font=\\footnotesize\\itshape, text=black!70] (g{k}nota) '
             f'at (0,-1.05) {{{g["nota"]}}};')
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
    cab = [(0.0, 3.0, 'Tesis'), (3.3, 6.4, 'Justificación'), (10.0, W - 10.0, 'Medios: dos estrategias')]
    for i, (x, w, r) in enumerate(cab):
        o.append(f'  \\node[rot] at ({x:.2f},-0.2) {{{r}}};')
        if i < len(cab) - 1:
            o.append(f'  \\draw[flecha] ({x + w + 0.02:.2f},-0.32) -- ({cab[i + 1][0] - 0.04:.2f},-0.32);')
    o.append(f'  \\node[txt, text width={cab[0][1]:.2f}cm] (tesis) at (0,-0.6) {{{B["tesis"]}}};')
    o.append(f'  \\node[txt, text width={cab[1][1]:.2f}cm] (just) at ({cab[1][0]:.2f},-0.6) {{{B["justificacion"]}}};')
    previo = None
    for letra, cont in B['medios']:
        donde = f'({cab[2][0] + 0.45:.2f},-0.6)' if previo is None else f'([yshift=-0.14cm]{previo}.south west)'
        o.append(f'  \\node[txt, text width={cab[2][1] - 0.45:.2f}cm] (med{letra}) at {donde} {{{cont}}};')
        o.append(f'  \\node[anchor=north east, fill=eGri, text=white, font=\\small\\bfseries, inner sep=2pt] '
                 f'at ([shift={{(-0.12,0.04)}}]med{letra}.north west) {{{letra}}};')
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
            o.append(f'    \\draw[{c}, line width=1pt] (0,-0.4) -- ({W},-0.4);')
            for i, (x, w, r) in enumerate(COLS):
                o.append(f'    \\node[rot] at ({x:.2f},-0.5) {{{r}}};')
                if i < len(COLS) - 1:
                    o.append(f'    \\draw[flecha] ({x + w + 0.02:.2f},-0.62) -- ({COLS[i + 1][0] - 0.04:.2f},-0.62);')
            (x0, w0, _), (x1, w1, _), (x2, w2, _), (x3, w3, _) = COLS
            o.append(f'    \\node[txt, text width={w0:.2f}cm] (obj{k}) at ({x0:.2f},-0.88) {{{a["objetivo"]}}};')
            o += escala(x1 + 0.12, -1.0, a['escala'], c)
            hitos = [(f'\\textbf{{\\textcolor{{{c}!85!black}}{{{an}}}}}', t) for an, t in a['hitos']]
            o.append(f'    \\node[txt] (como{k}) at ({x1:.2f},-1.24) {{{lista(hitos, w1)}}};')
            o.append(f'    \\begin{{scope}}[shift={{({x2:.2f},-0.88)}}]')
            o += ['  ' + l for l in gobierno(k, a['gobierno'])]
            o.append(f'    \\end{{scope}}')
            o.append(f'    \\node[txt] (val{k}) at ({x3:.2f},-0.88) {{{lista(a["valoracion"], w3, marca=f"\\textcolor{{{c}}}{{$\\triangleright$}}")}}};')
            o.append(f'  \\end{{scope}}')
            o.append(f'  \\path let \\p1=(obj{k}.south), \\p2=(como{k}.south), \\p3=(g{k}nota.south), \\p4=(val{k}.south), '
                     f'\\n1={{min(\\y1,\\y2,\\y3,\\y4)}} in coordinate (fondo) at (0,\\n1-0.2cm);')
            (y0, v0, r0), (y1, v1, r1) = ABAJO
            o.append(f'  \\draw[flecha] ([shift={{({y0 + v0 + 0.02:.2f},-0.15)}}]fondo) -- ([shift={{({y1 - 0.04:.2f},-0.15)}}]fondo);')
            o.append(f'  \\node[txt, text width={v0:.2f}cm] (ue{k}) at ([xshift={y0:.2f}cm]fondo) '
                     f'{{\\textcolor{{eGri}}{{\\textbf{{{r0}.}}}} {a["ue"]}}};')
            o.append(f'  \\node[txt, text width={v1:.2f}cm] (tes{k}) at ([xshift={y1:.2f}cm]fondo) '
                     f'{{\\textcolor{{eGri}}{{\\textbf{{{r1}}}}} {a["tesis"]}}};')
            o.append(f'  \\path let \\p1=(ue{k}.south), \\p2=(tes{k}.south), \\n1={{min(\\y1,\\y2)}} in coordinate (sig) at (0,\\n1-{B.get("hueco", 0.42):.2f}cm);')
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
