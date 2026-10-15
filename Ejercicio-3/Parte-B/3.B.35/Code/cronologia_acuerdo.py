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
        'etapas': [(1960, 1973, 'impulso', 'Rival de la CEE'),
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
    'MERCOSUR': {
        'eje': (1984, 2027, range(1990, 2030, 10)),
        'etapas': [(1985, 1991, 'origen', 'Acercamiento'), (1991, 1998, 'impulso', 'Auge'), (1998, 2003, 'crisis', 'Crisis'),
                   (2003, 2019, 'relanzamiento', 'Giro político y social'), (2019, 2027, 'terceros', 'Acuerdos con terceros')],
        'contexto': [
            (1985, 'democracia en Brasil'), (1999, 'devaluación del real'), (2001, 'crisis argentina'),
            (2003, 'auge de las materias primas'), (2025, 'aranceles de EE.\\,UU.')],
        'carriles': [
            ('Miembros', (120, 120, 120), [
                (1991, 'Argentina, Brasil, Paraguay, Uruguay'), (2012, 'entra Venezuela; Paraguay, suspendido'),
                (2016, 'Venezuela, suspendida'), (2024, 'Bolivia, miembro pleno')]),
            ('Comercio', (233, 160, 40), [
                (1985, 'Declaración de Foz de Iguazú'), (1991, 'Tratado de Asunción'), (1995, 'arancel externo común'),
                (2019, 'acuerdo político con la UE'), (2025, 'acuerdo con la EFTA'), (2026, 'acuerdo con la UE, provisional')]),
        ],
    },
    'CEFTA': {   # entradas y salidas en detalle: CEFTA_miembros (valoración)
        'eje': (1989, 2027, range(1990, 2030, 10)),
        'etapas': [(1992, 2006, 'impulso', 'CEFTA de Europa central'), (2006, 2020, 'relanzamiento', 'CEFTA 2006: Balcanes y Moldavia'),
                   (2020, 2027, 'impulso', 'Mercado Regional')],
        'contexto': [
            (1991, 'disolución del COMECON'), (1995, 'paz de Dayton'), (1999, 'Pacto de Estabilidad'), (2003, 'cumbre de Salónica'),
            (2008, 'independencia de Kosovo'), (2014, 'Proceso de Berlín'), (2022, 'invasión rusa de Ucrania')],
        'carriles': [
            ('Miembros', (120, 120, 120), [
                (1992, 'Polonia, Hungría, Checoslovaquia'), (2004, 'salen hacia la UE'),
                (2007, 'Balcanes occidentales y Moldavia'), (2013, 'sale Croacia')]),
            ('Comercio\\\\y normas', (233, 160, 40), [
                (1992, 'firma en Cracovia'), (2006, 'CEFTA 2006 (Bucarest)'), (2018, 'facilitación del comercio'),
                (2020, 'Mercado Regional Común'), (2021, 'servicios'), (2025, 'solución de diferencias, en ratificación')]),
        ],
    },
    'AfCFTA': {   # sustituye a la de Code/cronologia_bloque.py (sin carril de instituciones)
        'eje': (2011, 2027, range(2012, 2028, 2)),
        'etapas': [(2011, 2019.41, 'origen', 'Negociación'), (2019.41, 2027, 'impulso', 'Aplicación')],
        'contexto': [
            (2015.1, 'Agenda 2063'), (2018.1, 'protocolo de libre circulación de la UA'), (2020.2, 'pandemia de COVID-19'),
            (2022.05, 'sistema de pagos PAPSS'), (2025.3, 'aranceles de EE.\\,UU.')],
        'carriles': [
            ('Firma y\\\\ratificación', (30, 75, 135), [
                (2018.22, 'firma en Kigali (44 países)'), (2019.41, 'entra en vigor (24)'), (2019.52, 'firma Nigeria'),
                (2026.75, '50 de 54 ratificaciones')]),
            ('Comercio', (233, 160, 40), [
                (2012.05, 'decisión de Addis Abeba'), (2015.45, 'inicio de las negociaciones'), (2021.0, 'comienza el comercio'),
                (2022.78, 'comercio guiado (8 países)'), (2023.12, 'protocolos de inversión y competencia'),
                (2024.13, 'comercio digital'), (2025.29, 'fin de la fase guiada (39)')]),
        ],
    },
    'PAFTA': {
        'eje': (1943, 2027, range(1950, 2030, 10)),
        'etapas': [(1945, 1997, 'origen', 'Intentos de mercado común'), (1997, 2005, 'impulso', 'Desarme'),
                   (2005, 2027, 'crisis', 'Estancamiento')],
        'contexto': [
            (1945, 'nace la Liga Árabe'), (1973, 'crisis del petróleo'), (1990, 'invasión de Kuwait'), (2004, 'Acuerdo de Agadir'),
            (2011, 'Primavera Árabe'), (2014, 'caída del precio del petróleo')],
        'carriles': [
            ('Comercio\\\\y servicios', (233, 160, 40), [
                (1964, 'Mercado Común Árabe'), (1981, 'acuerdo de facilitación del comercio'), (1998, 'entra en vigor'),
                (2004, 'Ronda de Beirut (servicios)'), (2005, 'aranceles cero'), (2009, 'se suma Argelia'),
                (2020, 'compromisos de servicios')]),
        ],
    },
    'ASEAN': {
        'eje': (1965, 2027, range(1970, 2030, 10)),
        'etapas': [(1967, 1992, 'origen', 'Alianza frente al comunismo'), (1992, 2007, 'impulso', 'Libre comercio (AFTA)'),
                   (2007, 2027, 'relanzamiento', 'Carta y Comunidad Económica')],
        'contexto': [
            (1975, 'caída de Saigón'), (1978, 'Vietnam invade Camboya'), (1997, 'crisis asiática'), (2001, 'China entra en la OMC'),
            (2013, 'Franja y Ruta'), (2021, 'golpe en Myanmar'), (2025, 'aranceles de EE.\\,UU.')],
        'carriles': [
            ('Miembros', (120, 120, 120), [
                (1967, 'Indonesia, Malasia, Filipinas, Singapur, Tailandia'), (1984, 'Brunéi'), (1995, 'Vietnam'),
                (1997, 'Laos y Myanmar'), (1999, 'Camboya'), (2025, 'Timor Oriental')]),
            ('Integración', (233, 160, 40), [
                (1976, 'Cumbre de Bali'), (1977, 'acuerdo preferencial'), (1992, 'AFTA'), (2007, 'Carta de la ASEAN'),
                (2010, 'ATIGA; acuerdo con China'), (2015, 'Comunidad Económica'), (2018, 'aranceles internos casi a cero'),
                (2022, 'RCEP en vigor')]),
        ],
    },
    'CCG': {
        'eje': (1977, 2027, range(1980, 2030, 10)),
        'etapas': [(1981, 2001, 'impulso', 'Alianza y libre comercio'), (2001, 2017, 'relanzamiento', 'Unión aduanera'),
                   (2017, 2021, 'crisis', 'Crisis'), (2021, 2027, 'terceros', 'Terceros')],
        'contexto': [
            (1979, 'revolución iraní'), (1990, 'invasión de Kuwait'), (2003, 'invasión de Irak'), (2011, 'Primavera Árabe'),
            (2014, 'caída del petróleo'), (2015, 'guerra de Yemen')],
        'carriles': [
            ('Integración', (233, 160, 40), [
                (1981, 'Carta (Abu Dabi)'), (1983, 'zona de libre comercio'), (2001, 'Acuerdo Económico'), (2003, 'unión aduanera'),
                (2008, 'mercado común'), (2015, 'unión aduanera plena'), (2026, 'acuerdo con Reino Unido')]),
            ('Moneda', (185, 125, 20), [(2006, 'sale Omán'), (2009, 'sale Emiratos'), (2010, 'Consejo Monetario')]),
            ('Seguridad', (30, 75, 135), [
                (1984, 'Escudo de la Península'), (2011, 'despliegue en Baréin'), (2017, 'bloqueo a Catar'), (2021, 'Al-Ula')]),
        ],
    },
    'RCEP': {
        'eje': (2010, 2027, range(2010, 2028, 2)),
        'etapas': [(2011.87, 2022.0, 'origen', 'Negociación y ratificación'), (2022.0, 2027, 'impulso', 'Aplicación')],
        'contexto': [
            (2013.7, 'Franja y Ruta'), (2016.1, 'firma del TPP'), (2017.05, 'EE.\\,UU. sale del TPP'),
            (2018.5, 'guerra comercial EE.\\,UU.-China'), (2020.2, 'pandemia'), (2025.3, 'aranceles de EE.\\,UU.')],
        'carriles': [
            ('Acuerdo', (233, 160, 40), [
                (2011.87, 'propuesta de la ASEAN'), (2012.87, 'ASEAN y seis socios'), (2019.87, 'sale la India'),
                (2020.87, 'firma (15)'), (2022.0, 'en vigor (10)'), (2023.42, 'en vigor en Filipinas'),
                (2025.0, 'procedimiento de adhesión'), (2026.7, 'cuatro candidatos')]),
        ],
    },
    'CPTPP': {
        'eje': (2004, 2027, range(2005, 2030, 5)),
        'etapas': [(2005.45, 2017.05, 'origen', 'Del P4 al TPP'), (2017.05, 2018.99, 'relanzamiento', 'Rescate'),
                   (2018.99, 2027, 'impulso', 'CPTPP y adhesiones')],
        'contexto': [
            (2008.7, 'crisis financiera'), (2011.9, 'giro de EE.\\,UU. hacia Asia'), (2017.05, 'Trump sale del TPP'),
            (2018.5, 'guerra comercial EE.\\,UU.-China'), (2022.38, 'IPEF'), (2025.3, 'aranceles de EE.\\,UU.')],
        'carriles': [
            ('Acuerdo', (233, 160, 40), [
                (2005.45, 'P4: Brunéi, Chile, Nueva Zelanda, Singapur'), (2008.7, 'se suma EE.\\,UU.'), (2010.2, 'negociación del TPP'),
                (2016.1, 'firma del TPP (12)'), (2017.4, 'los once lo rescatan'), (2018.18, 'firma del CPTPP'), (2018.99, 'en vigor')]),
            ('Adhesiones', (30, 75, 135), [
                (2021.1, 'solicita Reino Unido'), (2021.7, 'China y Taiwán'), (2024.95, 'entra Reino Unido'),
                (2026.4, 'Costa Rica cierra su adhesión')]),
        ],
    },
    'UEE': {
        'eje': (1990, 2027, range(1990, 2030, 10)),
        'etapas': [(1991.95, 2010, 'origen', 'CEI e intentos de unión'), (2010, 2022.15, 'impulso', 'Unión aduanera y UEE'),
                   (2022.15, 2027, 'crisis', 'Sanciones')],
        'contexto': [
            (1991.95, 'disolución de la URSS'), (2009.4, 'Asociación Oriental de la UE'), (2014.2, 'anexión de Crimea'),
            (2022.15, 'invasión de Ucrania')],
        'carriles': [
            ('Miembros', (120, 120, 120), [
                (2010, 'Rusia, Bielorrusia, Kazajistán'), (2015, 'Armenia y Kirguistán'), (2025, 'Armenia aspira a la UE')]),
            ('Integración', (233, 160, 40), [
                (1994, 'propuesta de Nazarbáyev'), (1995, 'acuerdo de unión aduanera'), (2000, 'Comunidad Económica Euroasiática'),
                (2010, 'arancel exterior común'), (2012, 'Espacio Económico Común'), (2015, 'UEE en vigor'),
                (2015.9, 'Kazajistán entra en la OMC')]),
            ('Terceros', (30, 75, 135), [(2016.8, 'Vietnam'), (2019.8, 'Irán, provisional'), (2025.4, 'Irán, pleno'), (2026.8, 'Emiratos')]),
        ],
    },
}


class Cronologia:
    def __init__(self, c):
        self.a0, self.a1, self.marcas = c['eje']
        self.c = c

    def x(self, anio):
        return X0 + (anio - self.a0) / (self.a1 - self.a0) * (X1 - X0)

    def colocar(self, hitos):
        """Asigna a cada hito un lado y un nivel sin solapes; devuelve [(año, texto, lado, nivel, ancla, x)]."""
        ocupado = {'a': [], 'b': []}   # por lado: lista de niveles; cada nivel, lista de intervalos de etiquetas
        tallos = {'a': [], 'b': []}    # por lado: lista de niveles; cada nivel, posiciones de tallos que lo cruzan
        res = []
        # La etiqueta empieza en su hito (se lee mejor); solo si no cabe a la derecha, termina en él. Orden de colocación:
        # primero las que terminan en su hito, de izquierda a derecha, y luego las demás, de derecha a izquierda; así el
        # tallo de un hito no cruza las etiquetas ya colocadas en los niveles más bajos.
        def ancho(h):
            return (len(h[1]) + 5) * CM_POR_CARACTER + 0.1
        al_este = [h for h in hitos if self.x(h[0]) + ancho(h) > X1 + 0.3]
        al_oeste = [h for h in hitos if h not in al_este]
        for h in sorted(al_este, key=lambda h: h[0]) + sorted(al_oeste, key=lambda h: -h[0]):
            anio, texto = h[0], h[1]
            px = self.x(anio)
            mejor = None   # (cruces del tallo con etiquetas más bajas, nivel, preferencia, lado, ancla, intervalo)
            # las que terminan en su hito van todas debajo, en escalera, para dejar arriba sitio a los tallos de las demás
            for lado in ([h[2]] if len(h) > 2 else (['b'] if h in al_este else ['a', 'b'])):
                for pref, ancla in enumerate(['east'] if h in al_este else ['west']):
                    i0, i1 = (px - 0.06, px - 0.06 + ancho(h)) if ancla == 'west' else (px + 0.06 - ancho(h), px + 0.06)
                    k = 0
                    while True:
                        while len(ocupado[lado]) <= k:
                            ocupado[lado].append([]); tallos[lado].append([])
                        libre = all(i1 + 0.12 < a or i0 - 0.12 > b for a, b in ocupado[lado][k])
                        libre = libre and all(not (i0 - 0.05 < t < i1 + 0.05) for t in tallos[lado][k])
                        if libre:
                            break
                        k += 1
                    cruces = sum(a - 0.05 < px < b + 0.05 for j in range(k) for a, b in ocupado[lado][j])
                    if mejor is None or (cruces, k, pref) < mejor[:3]:
                        mejor = (cruces, k, pref, lado, ancla, (i0, i1))
            cruces, k, _, lado, ancla, (i0, i1) = mejor
            if cruces:
                print(f'  aviso: el tallo de {anio} {texto} cruza una etiqueta')
            ocupado[lado][k].append((i0, i1))
            for j in range(k):
                tallos[lado][j].append(px)
            res.append((anio, texto, lado, k, ancla, px))
        return res

    def tikz(self, clave):
        c = self.c
        carriles = [('Contexto', CONTEXTO, c['contexto'], True)] + [(n, rgb, h, False) for n, rgb, h in c['carriles']]
        colocados = [self.colocar(h) for _, _, h, _ in carriles]
        # posición vertical de cada carril, de arriba abajo
        ys, y = [], 0.0
        for col in colocados:
            arriba = 1 + max([k for _, _, lado, k, _, _ in col if lado == 'a'], default=-1)
            abajo = 1 + max([k for _, _, lado, k, _, _ in col if lado == 'b'], default=-1)
            y -= SEP + arriba * NIVEL + 0.05
            ys.append(y)
            y -= SEP + abajo * NIVEL + 0.1
        base = y - 0.1
        alto_etapas = 0.42
        techo = alto_etapas + (0.45 if c.get('estrategias') else 0)
        o = [f'% Generado por Code/cronologia_acuerdo.py ({clave}).', '\\begin{tikzpicture}[font=\\sffamily\\footnotesize]']
        # etapas sombreadas, con su nombre
        for a, b, tipo, nombre in c['etapas']:
            rgb = ETAPAS[tipo]
            o.append('  \\fill[fill={rgb,255:red,%d;green,%d;blue,%d}] (%.2f,%.2f) rectangle (%.2f,%.2f);'
                     % (*rgb, self.x(a), base, self.x(b), alto_etapas))
            o.append(f'  \\node[anchor=north, align=center, font=\\sffamily\\footnotesize\\itshape, text=black!75, inner sep=1pt] '
                     f'at ({(self.x(a) + self.x(b)) / 2:.2f},{alto_etapas - 0.04:.2f}) {{{nombre}}};')
        # estrategias que agrupan etapas
        for a, b, nombre in c.get('estrategias', []):
            ya = techo - 0.12
            o.append(f'  \\draw[black!55, line width=0.5pt] ({self.x(a) + 0.04:.2f},{ya - 0.12:.2f}) -- ({self.x(a) + 0.04:.2f},{ya:.2f}) '
                     f'-- ({self.x(b) - 0.04:.2f},{ya:.2f}) -- ({self.x(b) - 0.04:.2f},{ya - 0.12:.2f});')
            o.append(f'  \\node[fill=white, inner sep=1.5pt, font=\\sffamily\\footnotesize\\bfseries, text=black!70] '
                     f'at ({(self.x(a) + self.x(b)) / 2:.2f},{ya:.2f}) {{{nombre}}};')
        # rejilla y eje
        for d in self.marcas:
            o.append(f'  \\draw[black!12, line width=0.3pt] ({self.x(d):.2f},{base:.2f}) -- ({self.x(d):.2f},{alto_etapas - 0.4:.2f});')
            o.append(f'  \\draw[black!70] ({self.x(d):.2f},{base:.2f}) -- ++(0,-0.07) node[below, inner sep=1.5pt] {{{d}}};')
        o.append(f'  \\draw[black!70, line width=0.5pt, -{{Stealth[length=4pt]}}] ({X0:.2f},{base:.2f}) -- ({X1 + 0.15:.2f},{base:.2f});')
        # carriles
        for i, ((nombre, rgb, hitos, es_contexto), col, yc) in enumerate(zip(carriles, colocados, ys)):
            o.append('  \\definecolor{carril%d}{RGB}{%d,%d,%d}' % (i, *rgb))
            estilo = '\\itshape' if es_contexto else '\\bfseries'
            o.append(f'  \\node[anchor=east, align=right, font=\\sffamily\\footnotesize{estilo}, text=carril{i}] '
                     f'at ({X0 - 0.12:.2f},{yc:.2f}) {{{nombre}}};')
            if es_contexto:
                o.append(f'  \\draw[carril{i}!60, line width=0.6pt, densely dotted] ({X0:.2f},{yc:.2f}) -- ({X1:.2f},{yc:.2f});')
            else:
                o.append(f'  \\draw[carril{i}, line width=1.4pt] ({self.x(min(h[0] for h in hitos)):.2f},{yc:.2f}) -- ({X1:.2f},{yc:.2f});')
            for anio, texto, lado, k, ancla, px in col:
                dy = (SEP + k * NIVEL) * (1 if lado == 'a' else -1)
                vert = 'south' if lado == 'a' else 'north'
                dx = -0.06 if ancla == 'west' else 0.06
                o.append(f'  \\draw[carril{i}!70, line width=0.4pt] ({px:.2f},{yc:.2f}) -- ({px:.2f},{yc + dy:.2f});')
                if es_contexto:
                    o.append(f'  \\fill[carril{i}] ({px:.2f},{yc + 0.07:.2f}) -- ({px + 0.07:.2f},{yc:.2f}) -- ({px:.2f},{yc - 0.07:.2f}) -- ({px - 0.07:.2f},{yc:.2f}) -- cycle;')
                    txt = f'\\textit{{{int(anio)} {texto}}}'
                    color = f', text=carril{i}!85!black'
                else:
                    o.append(f'  \\fill[white] ({px:.2f},{yc:.2f}) circle (1.7pt); \\draw[carril{i}!80!black, line width=0.6pt] ({px:.2f},{yc:.2f}) circle (1.7pt);')
                    txt = f'\\textbf{{{int(anio)}}} {texto}'
                    color = ''
                o.append(f'  \\node[anchor={vert} {ancla}, inner sep=0.8pt{color}] at ({px + dx:.2f},{yc + dy:.2f}) {{{txt}}};')
        o.append('\\end{tikzpicture}')
        return '\n'.join(o) + '\n'


def main(clave):
    destino = Path(__file__).resolve().parent.parent / 'Img' / f'{clave}_cronologia.tikz'
    destino.write_text(Cronologia(CRONOLOGIAS[clave]).tikz(clave), encoding='utf-8')
    print('Escrito', destino)


if __name__ == '__main__':
    main(sys.argv[1])
