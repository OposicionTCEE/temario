#!/usr/bin/env python3
"""Figuras económicas propias del bloque de afinidad (3.B.35); las comunes (integración, composición, complementariedad) las
hace Code/figuras_economicas.py. Mismo estilo: paleta validada, letra de 8 puntos, 16 cm, etapas de la cronología al fondo.

  Img/MERCOSUR_tipo_cambio.tikz   (a) tipo de cambio real bilateral peso-real; (b) cuota intrarregional.
  Img/CEFTA_convergencia.tikz     (a) PIB per cápita en PPA en % de la UE-27; (b) hoy frente a los últimos en adherirse.
  Img/CEFTA_ancla.tikz            (a) peso de la UE-27 y de los socios del CEFTA en el comercio del bloque; (b) por miembro.
  Img/AfCFTA_composicion.tikz     manufacturas en las exportaciones dentro y fuera de África: (a) evolución; (b) por país.
  Img/AfCFTA_materias.tikz        (a) estructura de las exportaciones; (b) complementariedad entre las grandes economías.
  Img/AfCFTA_aranceles.tikz       arancel aplicado según el origen de las importaciones y arancel NMF a África.
  Img/PAFTA_sin_petroleo.tikz     (a) cuota árabe con y sin combustibles; (b) por subregión, 2023.
  Img/PAFTA_composicion.tikz      composición de las exportaciones dentro y fuera de la PAFTA, 2005 y 2023.
Datos: Code/datos/wits_extra.csv (Code/descargas_afinidad.py), wdi_series.csv, exportaciones_bilaterales.csv; tablas en
Code/datos/tablas_figuras.xlsx (el libro final lo monta Code/libro_datos.py).
Uso, desde la carpeta del tema:  /ruta/a/python-con-openpyxl Code/figuras_afinidad.py [MERCOSUR|CEFTA|AFCFTA|PAFTA]
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import africa_cer as ac  # noqa: E402
import datos_comercio as dc  # noqa: E402
import datos_wits as dw  # noqa: E402
import figuras_economicas as fe  # noqa: E402
import indicadores_bloque as ib  # noqa: E402
from descargas_afinidad import AFRICA_GRANDES, GRUPOS_CUCI, SECCIONES_SA  # noqa: E402

NOMBRES = {'ALB': 'Albania', 'BIH': 'Bosnia y Herzegovina', 'MKD': 'Macedonia del Norte', 'MNE': 'Montenegro', 'SRB': 'Serbia',
           'MDA': 'Moldavia', 'XKX': 'Kosovo', 'BGR': 'Bulgaria', 'ROU': 'Rumanía', 'HRV': 'Croacia'}
CER_LC = ['CEDEAO', 'CEEAC', 'EAC', 'COMESA', 'SADC']   # comunidades con libre comercio (no la CEN-SAD, la IGAD ni la UMA)
GRUPOS_TXT = {'Food': 'Alimentos', 'AgrRaw': 'Materias primas agrícolas', 'Fuels': 'Combustibles', 'OresMtls': 'Minerales y metales',
              'manuf': 'Manufacturas'}


def escribe(nombre, lineas):
    destino = dc.TEMA / 'Img' / f'{nombre}.tikz'
    destino.write_text('\n'.join(lineas) + '\n', encoding='utf-8')
    print('Escrito', destino)


def tabla(nombre, titulo, fuente, cabecera, filas):
    try:
        ib.hoja(nombre, titulo, fuente, cabecera, filas)
    except ImportError:
        print('Falta openpyxl: no se escribe la tabla', nombre)


def rotulos(series, techo, x):
    o, previo = [], None
    for v, texto in sorted(series, reverse=True):
        y = v if previo is None or previo - v > techo * 0.09 else previo - techo * 0.09
        o.append(f'    \\node[anchor=west, inner sep=1.5pt, text=black!80] at (axis cs:{x},{y:.2f}) {{{texto}}};')
        previo = y
    return o


def barras_h(etiquetas, series, at, ancho, alto, titulo, xlabel='', apilar=False, xmax=None, valores=True, solapar=False,
             con_etiquetas=True, leyenda=True):
    """Barras horizontales (agrupadas, apiladas o superpuestas) con categorías simbólicas;
    series = [(color, leyenda, {etiqueta: valor})]. Sin comas ni paréntesis en etiquetas y leyendas (pgfplots las parte)."""
    cats = ','.join(etiquetas)
    xm = xmax or fe.techo(max((sum(s[2].get(e, 0) for s in series) if apilar else max(s[2].get(e, 0) for s in series))
                              for e in etiquetas), 10)
    estilo = fe.ESTILO.replace('ymajorgrids', 'xmajorgrids')
    tipo = 'xbar stacked' if apilar else 'xbar'
    o = [f'  \\begin{{axis}}[{estilo}, at={{{at}}}, width={ancho}cm, height={alto}cm, {tipo},'
         f' bar width={"6pt" if apilar or solapar else "3.4pt"}, y dir=reverse, symbolic y coords={{{cats}}}, ytick={{{cats}}},'
         + ('' if con_etiquetas else ' yticklabels={},')
         + f' xmin=0, xmax={xm}, enlarge y limits=0.06, title={{{titulo}}}, xlabel={{{xlabel}}},'
         ' legend style={font=\\sffamily\\footnotesize, draw=none, fill=none, at={(0.5,-0.2)}, anchor=north, legend columns=3,'
         ' /tikz/every even column/.append style={column sep=0.25cm}}, legend cell align=left, area legend, reverse legend'
         + (', bar shift=0pt' if solapar else '')
         + (', nodes near coords, nodes near coords style={font=\\sffamily\\footnotesize, text=black!75, /pgf/number format/fixed,'
            ' /pgf/number format/precision=0, /pgf/number format/assume math mode=true}, point meta=x' if valores and not apilar else '')
         + ']']
    for color, ley, datos in reversed(series):
        puntos = [(datos[e], e) for e in etiquetas if e in datos and (apilar or datos[e] > 0.05)]
        if puntos:
            o.append(f'    \\addplot[draw={"white" if apilar else "none"}, line width=0.3pt, fill={color}] coordinates {{'
                     + ' '.join(f'({v:.2f},{e})' for v, e in puntos) + '};')
            if leyenda:
                o.append(f'    \\addlegendentry{{{ley}}}')
    o.append('  \\end{axis}')
    return o


# ---------------------------------------------------------------- MERCOSUR
def mercosur():
    w = ib.wdi()
    q = {}
    for a in range(1980, 2025):
        try:
            e = w[('ARG', 'PA.NUS.FCRF', a)] / w[('BRA', 'PA.NUS.FCRF', a)]
            q[a] = e * w[('BRA', 'NY.GDP.DEFL.ZS', a)] / w[('ARG', 'NY.GDP.DEFL.ZS', a)]
        except KeyError:
            pass
    q = {a: 100 * v / q[1995] for a, v in q.items()}
    f = dc.lee_csv()
    saldo = {a: (f[('ARG', a, 'BRA')][0] - f[('BRA', a, 'ARG')][0]) / 1e9 for a in range(1980, 2024)
             if ('ARG', a, 'BRA') in f and ('BRA', a, 'ARG') in f}
    o = fe.cabecera('MERCOSUR', 'tipo_cambio')
    hi = fe.techo(max(q.values()), 20)
    o += [f'  \\begin{{axis}}[{fe.ESTILO}, width=5.9cm, height=4.2cm, at={{(0cm,0cm)}}, xmin=1980, xmax=2025, ymin=0, ymax={hi},'
          ' xtick={1980,1990,2000,2010,2020}, title={(a) Tipo de cambio real peso-real}, ylabel={índice, 1995 = 100}]',
          *fe.etapas('MERCOSUR', 0, hi, 1980, 2025),
          '    \\draw[black!50, line width=0.4pt] (axis cs:1980,100) -- (axis cs:2025,100);',
          f'    \\addplot[s1, line width=1.3pt, mark=none] coordinates {{{fe.coords(sorted(q.items()))}}};',
          f'    \\node[anchor=south west, inner sep=1.5pt, text=black!75, align=left] at (axis cs:1981,{hi * 0.78:.0f}) '
          '{sube: el peso se abarata\\\\frente al real};',
          '  \\end{axis}']
    cuota = {f[0]: f[3] for f in dc.cuadro('MERCOSUR', 1980, 2023, f) if f[3] is not None}
    hi2 = fe.techo(max(cuota.values()), 5)
    o += [f'  \\begin{{axis}}[{fe.ESTILO}, width=5.9cm, height=4.2cm, at={{(8.6cm,0cm)}}, xmin=1980, xmax=2025, ymin=0, ymax={hi2},'
          ' xtick={1980,1990,2000,2010,2020}, title={(b) Cuota intrarregional}, ylabel={\\% de las exportaciones}]',
          *fe.etapas('MERCOSUR', 0, hi2, 1980, 2025),
          f'    \\addplot[s1, line width=1.3pt, mark=none] coordinates {{{fe.coords(sorted(cuota.items()))}}};',
          '  \\end{axis}', '\\end{tikzpicture}']
    escribe('MERCOSUR_tipo_cambio', o)
    tabla('MERCOSUR_tipo_cambio', 'Tipo de cambio real bilateral peso argentino-real (índice 1995 = 100), cuota intrarregional y saldo de Argentina con Brasil',
          'Banco Mundial (WDI): tipos de cambio oficiales (PA.NUS.FCRF) y deflactores del PIB (NY.GDP.DEFL.ZS), porque WDI no tiene el IPC '
          'argentino; saldo con las exportaciones declaradas por cada país (Code/datos_comercio.py). Cálculo propio (Code/figuras_afinidad.py).',
          ['Año', 'Tipo de cambio real (1995 = 100)', 'Saldo de Argentina con Brasil (miles de millones USD)', 'Cuota intrarregional (%)'],
          [(a, round(q[a], 1) if a in q else None, round(saldo[a], 2) if a in saldo else None,
            round(cuota[a], 2) if a in cuota else None) for a in range(1980, 2025)])
    print('TCR', {a: round(q[a]) for a in (1998, 1999, 2001, 2002, 2008, 2015, 2019, 2023) if a in q})
    print('saldo', {a: round(saldo[a], 1) for a in (1998, 1999, 2001, 2002, 2003, 2008, 2015, 2019, 2023) if a in saldo})


# ---------------------------------------------------------------- CEFTA
def cefta():
    w = ib.wdi()
    miembros = ['ALB', 'BIH', 'MKD', 'MNE', 'SRB', 'MDA', 'XKX']
    rel = {e: {a: 100 * w[(e, 'NY.GDP.PCAP.PP.KD', a)] / w[('EUU', 'NY.GDP.PCAP.PP.KD', a)] for a in range(1990, 2025)
               if (e, 'NY.GDP.PCAP.PP.KD', a) in w and ('EUU', 'NY.GDP.PCAP.PP.KD', a) in w} for e in miembros + ['BGR', 'ROU', 'HRV']}
    ult = max(max(rel[e]) for e in miembros if rel[e])
    color = {e: f's{i + 1}' for i, e in enumerate(miembros)}
    o = fe.cabecera('CEFTA', 'convergencia')
    o += [f'  \\begin{{axis}}[{fe.ESTILO}, width=5.0cm, height=4.4cm, at={{(0cm,0cm)}}, xmin=1995, xmax={ult}, ymin=0, ymax=60,'
          ' xtick={2000,2010,2020}, title={(a) PIB per cápita en PPA, \\% de la UE-27}, ylabel={\\%}, clip mode=individual]',
          *fe.etapas('CEFTA', 0, 60, 1995, ult)]
    for e in miembros:
        if rel[e]:
            o.append(f'    \\addplot[{color[e]}, line width=1.2pt, mark=none] coordinates {{{fe.coords(sorted((a, v) for a, v in rel[e].items() if a >= 1995))}}};')
    o += rotulos([(rel[e][ult], e) for e in miembros if ult in rel[e]], 60, ult + 0.5)
    o.append('  \\end{axis}')
    adh = {'BGR': 2007, 'ROU': 2007, 'HRV': 2013}
    hoy = {NOMBRES[e]: rel[e][ult] for e in miembros if ult in rel[e]}
    refs = {f'{NOMBRES[e]} en {a}': rel[e][a] for e, a in adh.items() if a in rel[e]}
    etiquetas = sorted(hoy, key=lambda k: -hoy[k]) + sorted(refs, key=lambda k: -refs[k])
    o += barras_h(etiquetas, [('s1', f'miembros del CEFTA en {ult}', hoy), ('black!35', 'últimos adheridos a la UE', refs)],
                  '(9.3cm,0cm)', 4.2, 4.4, '(b) Hoy y los últimos adheridos (\\%)', valores=True, xmax=80, solapar=True)
    o.append('\\end{tikzpicture}')
    escribe('CEFTA_convergencia', o)
    tabla('CEFTA_convergencia', 'PIB per cápita en PPA de los miembros del CEFTA y de los últimos en adherirse a la UE, en % de la UE-27',
          'Banco Mundial (WDI), NY.GDP.PCAP.PP.KD (dólares internacionales constantes de 2021); UE-27 = agregado EUU. Cálculo propio.',
          ['Año'] + miembros + ['BGR', 'ROU', 'HRV'],
          [(a, *[round(rel[e][a], 1) if a in rel[e] else None for e in miembros + ['BGR', 'ROU', 'HRV']]) for a in range(1990, ult + 1)])
    print('CEFTA % UE', ult, {e: round(v) for e, v in hoy.items()}, {e: round(v) for e, v in refs.items()})
    # ancla de la UE
    socios_cefta = set(miembros) | {'KSV'}
    out = {}
    for f in ('X', 'M'):
        t = dw.tabla('comercio', f, 'Total')
        for a in range(2006, 2024):
            ue = cef = tot = 0.0
            por = {}
            for p in dc.GRUPOS['CEFTA'][0]:
                d = t.get((p, a))
                if not d or not d.get('WLD'):
                    continue
                u = sum(d.get(e, 0.0) for e in dc.UE27)
                c = sum(v for s, v in d.items() if s in socios_cefta and s != p)
                ue, cef, tot = ue + u, cef + c, tot + d['WLD']
                por[p] = (100 * u / d['WLD'], 100 * c / d['WLD'])
            if tot and len(por) == len(dc.GRUPOS['CEFTA'][0]):   # solo años en que declaran los seis
                out[(f, a)] = (100 * ue / tot, 100 * cef / tot, por)
    o = fe.cabecera('CEFTA', 'ancla')
    anios = sorted(a for f, a in out if f == 'X')
    o += [f'  \\begin{{axis}}[{fe.ESTILO}, width=5.0cm, height=4.4cm, at={{(0cm,0cm)}}, xmin=2006, xmax=2023, ymin=0, ymax=80,'
          ' xtick={2006,2010,2015,2020}, title={(a) Peso en el comercio del bloque}, ylabel={\\% del total}, clip mode=individual]']
    lin = [('s1', 'X', 0, 'UE, export.'), ('s1', 'M', 0, 'UE, import.'), ('s2', 'X', 1, 'CEFTA, export.'), ('s2', 'M', 1, 'CEFTA, import.')]
    for col, f, k, _ in lin:
        estilo = ', densely dashed' if f == 'M' else ''
        o.append(f'    \\addplot[{col}, line width=1.3pt, mark=none{estilo}] coordinates {{'
                 + fe.coords((a, out[(f, a)][k]) for a in anios if (f, a) in out) + '};')
    o += rotulos([(out[(f, anios[-1])][k], t) for _, f, k, t in lin if (f, anios[-1]) in out], 80, anios[-1] + 0.4)
    o.append('  \\end{axis}')
    por = out[('X', anios[-1])][2]
    etiquetas = [NOMBRES[p] for p in sorted(por, key=lambda p: -por[p][0])]
    o += barras_h(etiquetas, [('s1', 'a la UE-27', {NOMBRES[p]: v[0] for p, v in por.items()}),
                              ('s2', 'a los socios del CEFTA', {NOMBRES[p]: v[1] for p, v in por.items()})],
                  '(10.7cm,0cm)', 3.5, 4.4, f'(b) Exportaciones en {anios[-1]} (\\%)', xmax=100)
    o.append('\\end{tikzpicture}')
    escribe('CEFTA_ancla', o)
    tabla('CEFTA_ancla', 'Peso de la UE-27 y de los socios del CEFTA en las exportaciones e importaciones de los miembros del CEFTA (%)',
          'WITS (Banco Mundial), exportaciones e importaciones declaradas por cada miembro; UE-27 como suma de sus Estados miembros. '
          'Kosovo no declara. Cálculo propio (Code/figuras_afinidad.py).',
          ['Año', 'Flujo', 'UE-27 (%)', 'Socios del CEFTA (%)'] + [f'{p}: UE / CEFTA' for p in dc.GRUPOS['CEFTA'][0]],
          [(a, f, round(out[(f, a)][0], 1), round(out[(f, a)][1], 1),
            *[f'{out[(f, a)][2][p][0]:.1f} / {out[(f, a)][2][p][1]:.1f}' if p in out[(f, a)][2] else None for p in dc.GRUPOS['CEFTA'][0]])
           for f in ('X', 'M') for a in range(2006, 2024) if (f, a) in out])
    print('ancla', {f: (round(out[(f, anios[-1])][0]), round(out[(f, anios[-1])][1])) for f in ('X', 'M')}, anios[-1])


# ---------------------------------------------------------------- AfCFTA
def africa():
    africa = set(dc.GRUPOS['AFCFTA'][0])
    tot = dw.tabla('comercio', 'X', 'Total')
    man = dw.tabla('comercio', 'X', 'manuf')
    serie, por_pais, n = {}, {}, {}
    for a in (2000, 2005, 2010, 2015, 2019, 2023):
        ia = it = ea = et = 0.0
        k = 0
        for p in africa:
            t, m = tot.get((p, a)), man.get((p, a))
            if not t or not m or not t.get('WLD'):
                continue
            k += 1
            ti = sum(v for s, v in t.items() if s in africa and s != p)
            mi = sum(v for s, v in m.items() if s in africa and s != p)
            ia, it = ia + mi, it + ti
            ea, et = ea + m.get('WLD', 0) - mi, et + t['WLD'] - ti
            if a == 2023 and p in AFRICA_GRANDES and ti:
                por_pais[p] = (100 * mi / ti, 100 * (m.get('WLD', 0) - mi) / (t['WLD'] - ti))
        if it and et:
            serie[a], n[a] = (100 * ia / it, 100 * ea / et), k
    o = fe.cabecera('AFCFTA', 'composicion')
    o += [f'  \\begin{{axis}}[{fe.ESTILO}, width=5.0cm, height=4.4cm, at={{(0cm,0cm)}}, xmin=1999, xmax=2024, ymin=0, ymax=60,'
          ' xtick={2000,2005,2010,2015,2020}, title={(a) Manufacturas en las exportaciones}, ylabel={\\% de cada destino},'
          ' clip mode=individual]',
          '    \\addplot[s1, line width=1.3pt, mark=*, mark size=1.6pt] coordinates {' + fe.coords((a, v[0]) for a, v in sorted(serie.items())) + '};',
          '    \\addplot[s2, line width=1.3pt, mark=*, mark size=1.6pt] coordinates {' + fe.coords((a, v[1]) for a, v in sorted(serie.items())) + '};']
    ua = max(serie)
    o += rotulos([(serie[ua][0], 'a África'), (serie[ua][1], 'fuera de África')], 60, ua + 0.6)
    o.append('  \\end{axis}')
    etiquetas = sorted(por_pais, key=lambda p: -por_pais[p][0])
    o += barras_h(etiquetas, [('s1', 'a África', {p: v[0] for p, v in por_pais.items()}),
                              ('s2', 'fuera de África', {p: v[1] for p, v in por_pais.items()})],
                  '(9.0cm,0cm)', 5.0, 4.4, '(b) Manufacturas por país en 2023 (\\%)', xmax=100)
    o.append('\\end{tikzpicture}')
    escribe('AfCFTA_composicion', o)
    tabla('AFCFTA_composicion', 'Manufacturas en las exportaciones de los países africanos a África y fuera de África (%)',
          'WITS (Banco Mundial), grupo «manuf» (CUCI 5 a 8 sin 667 y 68) y total, exportaciones declaradas por cada país a cada socio; '
          'solo los países que declaran cada año. Cálculo propio (Code/figuras_afinidad.py).',
          ['Año', 'A África (%)', 'Fuera de África (%)', 'Países que declaran'] + [f'{p} 2023: África / fuera' for p in etiquetas],
          [(a, round(v[0], 1), round(v[1], 1), n[a], *([f'{por_pais[p][0]:.1f} / {por_pais[p][1]:.1f}' for p in etiquetas] if a == 2023 else []))
           for a, v in sorted(serie.items())])
    print('África manuf', {a: (round(v[0]), round(v[1]), n[a]) for a, v in serie.items()})
    # estructura de las exportaciones y complementariedad aproximada
    estr = {}
    for p in AFRICA_GRANDES:
        t = tot.get((p, 2023), {}).get('WLD')
        if not t:
            continue
        d = {g: dw.tabla('comercio', 'X', g).get((p, 2023), {}).get('WLD', 0.0) for g in GRUPOS_CUCI}
        d['otros'] = max(t - sum(d.values()), 0.0)
        estr[p] = {g: 100 * v / t for g, v in d.items()}
    secc = {(p, f): {s: dw.tabla('comercio', f, s).get((p, 2023), {}).get('WLD', 0.0) for s in SECCIONES_SA}
            for p in AFRICA_GRANDES for f in ('X', 'M')}
    for k, d in secc.items():
        t = sum(d.values())
        secc[k] = {s: v / t for s, v in d.items()} if t else {}
    comp = {(i, j): ib.michaely(secc[(i, 'X')], secc[(j, 'M')]) for i in AFRICA_GRANDES for j in AFRICA_GRANDES
            if i != j and secc[(i, 'X')] and secc[(j, 'M')]}
    o = fe.cabecera('AFCFTA', 'materias')
    etiquetas = sorted(estr, key=lambda p: -estr[p]['manuf'])
    colores = [('s1', 'manuf'), ('s3', 'Food'), ('s4', 'AgrRaw'), ('s2', 'Fuels'), ('s7', 'OresMtls'), ('black!30', 'otros')]
    o += barras_h(etiquetas, [(c, GRUPOS_TXT.get(g, 'Otros'), {p: estr[p][g] for p in etiquetas}) for c, g in colores],
                  '(0.9cm,0cm)', 4.6, 5.0, '(a) Exportaciones en 2023 (\\%)', apilar=True, xmax=100)
    cw, ch, xm, ytop = 0.52, 0.4, 8.3, 5.1
    paises = [p for p in AFRICA_GRANDES if secc[(p, 'X')]]
    vmax = max(comp.values())
    for jx, j in enumerate(paises):
        o.append(f'  \\node[anchor=south, inner sep=1pt, rotate=90, anchor=west] at ({xm + (jx + 0.5) * cw:.2f},{ytop + 0.04:.2f}) {{{j}}};')
    for iy, i in enumerate(paises):
        y = ytop - (iy + 1) * ch
        o.append(f'  \\node[anchor=east, inner sep=1pt] at ({xm - 0.06:.2f},{y + ch / 2:.2f}) {{{i}}};')
        for jx, j in enumerate(paises):
            x = xm + jx * cw
            if (i, j) in comp:
                pct = int(10 + 80 * comp[(i, j)] / vmax)
                o.append(f'  \\fill[s1!{pct}!white] ({x + 0.015:.3f},{y + 0.015:.3f}) rectangle ({x + cw - 0.015:.3f},{y + ch - 0.015:.3f});')
                txt = 'white' if pct > 55 else 'black!85'
                o.append(f'  \\node[text={txt}, inner sep=0pt, font=\\sffamily\\footnotesize] at ({x + cw / 2:.3f},{y + ch / 2:.3f}) {{{comp[(i, j)]:.0f}}};')
            else:
                o.append(f'  \\fill[black!6] ({x + 0.015:.3f},{y + 0.015:.3f}) rectangle ({x + cw - 0.015:.3f},{y + ch - 0.015:.3f});')
    yb = ytop - len(paises) * ch - 0.12
    o.append(f'  \\node[anchor=north west, inner sep=1pt, text=black!70] at ({xm - 0.7:.2f},{yb:.2f}) '
             '{exportador (filas), importador (columnas); 0-100};')
    o.append(f'  \\node[anchor=north, font=\\sffamily\\small, inner sep=0pt] at ({xm + len(paises) * cw / 2:.2f},{yb - 0.55:.2f}) '
             '{(b) Complementariedad en 2023};')
    o.append('\\end{tikzpicture}')
    escribe('AfCFTA_materias', o)
    media = sum(comp.values()) / len(comp)
    tabla('AFCFTA_materias', 'Estructura de las exportaciones de las grandes economías africanas y complementariedad entre ellas, 2023',
          'WITS (Banco Mundial): exportaciones por grupos de la CUCI (alimentos, materias primas agrícolas, combustibles, minerales y metales, '
          'manufacturas) y exportaciones e importaciones por las 16 secciones del SA de WITS (complementariedad aproximada, MICHAELY, 1996). '
          'Cálculo propio (Code/figuras_afinidad.py).',
          ['País'] + [GRUPOS_TXT.get(g, 'Otros') + ' (%)' for g in GRUPOS_CUCI + ['otros']] + ['Complementariedad media con los demás'],
          [(p, *[round(estr[p][g], 1) for g in GRUPOS_CUCI + ['otros']],
            round(sum(v for (i, j), v in comp.items() if i == p) / max(1, sum(1 for (i, j) in comp if i == p)), 1)) for p in etiquetas])
    print('estructura', {p: {g: round(v) for g, v in estr[p].items()} for p in etiquetas[:4]}, 'compl. media', round(media, 1))
    # aranceles
    cer = {nom: set(lst.split()) for nom, lst in ac.CER + ac.MONETARIAS if nom in CER_LC + ['UEMOA', 'CEMAC']}
    def misma(p, s):
        return any(p in m and s in m for m in cer.values())
    ahs, mfn, imp = dw.tabla('arancel', 'AHS', 'Total'), dw.tabla('arancel', 'MFN', 'Total'), dw.tabla('comercio', 'M', 'Total')
    res = {}
    for p in africa:
        for a in (2021, 2022, 2020, 2019):   # 2021 primero: en 2022 WITS omite preferencias (COMESA en Kenia)
            if (p, a) in ahs and (p, a) in imp:
                break
        else:
            continue
        h, m, w = ahs[(p, a)], mfn.get((p, a), {}), imp[(p, a)]
        grupos = {'cer': [], 'afr': [], 'mun': []}
        for s, peso in w.items():
            if s in ('WLD', p) or s not in h:
                continue
            g = 'cer' if misma(p, s) else ('afr' if s in africa else 'mun')
            grupos[g].append((h[s], m.get(s, h[s]), peso))
        def media(lista, k):
            tw = sum(x[2] for x in lista)
            return sum(x[k] * x[2] for x in lista) / tw if tw else None
        res[p] = (a, media(grupos['cer'], 0), media(grupos['afr'], 0), media(grupos['mun'], 0),
                  media(grupos['cer'] + grupos['afr'], 1), sum(x[2] for x in grupos['cer'] + grupos['afr']))
    sel = [p for p in AFRICA_GRANDES if p in res]
    o = fe.cabecera('AFCFTA', 'aranceles')
    etiquetas = sorted(sel, key=lambda p: -(res[p][4] or 0))
    series = [('s1', 'aplicado, socios de su comunidad', {p: res[p][1] or 0 for p in etiquetas}),
              ('s3', 'aplicado, resto de África', {p: res[p][2] or 0 for p in etiquetas}),
              ('black!35', 'aplicado, fuera de África', {p: res[p][3] or 0 for p in etiquetas}),
              ('s2', 'NMF, a África', {p: res[p][4] or 0 for p in etiquetas})]
    o += barras_h(etiquetas, series, '(1.0cm,0cm)', 13.6, 7.0, 'Arancel medio ponderado por las importaciones (\\%)', valores=False)
    o.append('\\end{tikzpicture}')
    escribe('AfCFTA_aranceles', o)
    tabla('AFCFTA_aranceles', 'Arancel aplicado y de nación más favorecida de los países africanos según el origen de las importaciones (%)',
          'WITS (Banco Mundial), tradestats-tariff: AHS-WGHTD-AVRG y MFN-WGHTD-AVRG por socio, ponderados por las importaciones de cada '
          'socio (MPRT-TRD-VL); último año disponible entre 2019 y 2022. Comunidad = socio de la misma comunidad con libre comercio '
          '(CEDEAO, CEEAC, EAC, COMESA, SADC, UEMOA, CEMAC). Cálculo propio (Code/figuras_afinidad.py).',
          ['País', 'Año', 'Aplicado, comunidad', 'Aplicado, resto de África', 'Aplicado, fuera de África', 'NMF, a África',
           'Importaciones desde África (USD)'],
          [(p, *[round(x, 2) if isinstance(x, float) else x for x in res[p]]) for p in sorted(res)])
    print('aranceles', {p: tuple(round(x, 1) if isinstance(x, float) else x for x in res[p][:5]) for p in etiquetas})


# ---------------------------------------------------------------- PAFTA
SUBREGIONES = {'Golfo (CCG)': ['ARE', 'BHR', 'KWT', 'OMN', 'QAT', 'SAU'], 'Magreb': ['DZA', 'LBY', 'MAR', 'TUN'],
               'Oriente Próximo y otros': ['EGY', 'IRQ', 'JOR', 'LBN', 'PSE', 'SYR', 'SDN', 'YEM']}


def pafta():
    miembros = set(dc.GRUPOS['PAFTA'][0])
    tot, fue = dw.tabla('comercio', 'X', 'Total'), dw.tabla('comercio', 'X', 'Fuels')
    serie, sub = {}, {}
    for a in range(1998, 2024):
        it = iz = tt = tz = 0.0
        k = 0
        for p in miembros:
            t, f = tot.get((p, a)), fue.get((p, a))
            if not t or f is None or not t.get('WLD'):
                continue
            k += 1
            ti = sum(v for s, v in t.items() if s in miembros and s != p)
            fi = sum(v for s, v in f.items() if s in miembros and s != p)
            it, tt = it + ti, tt + t['WLD']
            iz, tz = iz + ti - fi, tz + t['WLD'] - f.get('WLD', 0.0)
            if a == 2023:
                for nom, lst in SUBREGIONES.items():
                    if p in lst:
                        acu = sub.setdefault(nom, [0.0, 0.0, 0.0, 0.0])
                        acu[0] += ti; acu[1] += t['WLD']; acu[2] += ti - fi; acu[3] += t['WLD'] - f.get('WLD', 0.0)
        if tt and tz and k >= len(miembros) / 2:
            serie[a] = (100 * it / tt, 100 * iz / tz, k)
    o = fe.cabecera('PAFTA', 'sin_petroleo')
    o += [f'  \\begin{{axis}}[{fe.ESTILO}, width=5.0cm, height=4.4cm, at={{(0cm,0cm)}}, xmin=1998, xmax=2023, ymin=0, ymax=40,'
          ' xtick={2000,2005,2010,2015,2020}, title={(a) Exportaciones a otros miembros}, ylabel={\\% del total}, clip mode=individual]',
          *fe.etapas('PAFTA', 0, 40, 1998, 2023),
          '    \\addplot[s2, line width=1.3pt, mark=none] coordinates {' + fe.coords((a, v[0]) for a, v in sorted(serie.items())) + '};',
          '    \\addplot[s1, line width=1.3pt, mark=none] coordinates {' + fe.coords((a, v[1]) for a, v in sorted(serie.items())) + '};']
    ua = max(serie)
    o += rotulos([(serie[ua][0], 'todas'), (serie[ua][1], 'sin combustibles')], 40, ua + 0.4)
    o.append('  \\end{axis}')
    etiquetas = list(SUBREGIONES)
    o += barras_h(etiquetas, [('s2', 'todas', {n: 100 * v[0] / v[1] for n, v in sub.items()}),
                              ('s1', 'sin combustibles', {n: 100 * v[2] / v[3] for n, v in sub.items()})],
                  '(11.0cm,0cm)', 3.3, 4.4, '(b) Por subregión en 2023 (\\%)', xmax=50)
    o.append('\\end{tikzpicture}')
    escribe('PAFTA_sin_petroleo', o)
    tabla('PAFTA_sin_petroleo', 'Exportaciones de los miembros de la PAFTA a otros miembros, con y sin combustibles (% del total)',
          'WITS (Banco Mundial), exportaciones declaradas por cada miembro, total y grupo «Fuels» (CUCI 3); solo los miembros que declaran '
          'cada año (al menos la mitad). El petróleo que se declara sin destino cuenta en el total pero no en ningún socio. Cálculo propio.',
          ['Año', 'Todas las exportaciones (%)', 'Sin combustibles (%)', 'Miembros que declaran'],
          [(a, round(v[0], 1), round(v[1], 1), v[2]) for a, v in sorted(serie.items())])
    print('PAFTA', {a: (round(v[0], 1), round(v[1], 1), v[2]) for a, v in serie.items() if a % 5 == 3 or a == 2023},
          {n: (round(100 * v[0] / v[1]), round(100 * v[2] / v[3])) for n, v in sub.items()})
    # composición
    o = fe.cabecera('PAFTA', 'composicion')
    filas = []
    for k, a in enumerate((2005, 2023)):
        dentro, fuera = {}, {}
        for g in GRUPOS_CUCI + ['Total']:
            d = dw.tabla('comercio', 'X', g)
            dentro[g] = sum(v for p in miembros for s, v in d.get((p, a), {}).items() if s in miembros and s != p)
            fuera[g] = sum(d.get((p, a), {}).get('WLD', 0.0) for p in miembros) - dentro[g]
        for x in (dentro, fuera):
            x['otros'] = max(x['Total'] - sum(x[g] for g in GRUPOS_CUCI), 0.0)
        cats = [GRUPOS_TXT[g] for g in GRUPOS_CUCI] + ['Otros y sin clasificar']
        clave = dict(zip(cats, GRUPOS_CUCI + ['otros']))
        o += barras_h(cats, [('s1', 'a otros miembros', {c: 100 * dentro[clave[c]] / dentro['Total'] for c in cats}),
                             ('s2', 'fuera de la PAFTA', {c: 100 * fuera[clave[c]] / fuera['Total'] for c in cats})],
                      f'({3.6 + k * 5.6}cm,0cm)', 4.6, 4.4, f'({"ab"[k]}) {a} (\\%)', xmax=100, con_etiquetas=(k == 0), leyenda=(k == 1))
        filas += [(a, 'Dentro', *[round(100 * dentro[g] / dentro['Total'], 1) for g in GRUPOS_CUCI + ['otros']]),
                  (a, 'Fuera', *[round(100 * fuera[g] / fuera['Total'], 1) for g in GRUPOS_CUCI + ['otros']])]
    o.append('\\end{tikzpicture}')
    escribe('PAFTA_composicion', o)
    tabla('PAFTA_composicion', 'Composición de las exportaciones de los miembros de la PAFTA a otros miembros y fuera de la PAFTA (%)',
          'WITS (Banco Mundial), exportaciones declaradas por grupos de la CUCI. «Otros y sin clasificar» incluye el petróleo declarado '
          'sin desglose de producto. Cálculo propio (Code/figuras_afinidad.py).',
          ['Año', 'Destino'] + [GRUPOS_TXT[g] + ' (%)' for g in GRUPOS_CUCI] + ['Otros (%)'], filas)
    print('PAFTA composición', filas)


if __name__ == '__main__':
    quien = sys.argv[1:] or ['MERCOSUR', 'CEFTA', 'AFCFTA', 'PAFTA']
    for q in quien:
        {'MERCOSUR': mercosur, 'CEFTA': cefta, 'AFCFTA': africa, 'PAFTA': pafta}[q]()
