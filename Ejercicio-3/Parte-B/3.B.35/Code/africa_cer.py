#!/usr/bin/env python3
"""Genera Img/AfCFTA_comunidades.tikz: pertenencia de cada Estado africano a las ocho comunidades económicas regionales
(CER) reconocidas por la Unión Africana y a las dos uniones monetarias del franco CFA.

Composición en octubre de 2026: Burkina Faso, Malí y Níger salieron de la CEDEAO el 29 de enero de 2025 (siguen en la UEMOA);
Eritrea se retiró de la IGAD en diciembre de 2025; Somalia entró en la EAC en 2024. La lista de la CEN-SAD es la menos
segura (29 miembros según la Comisión Económica para África). Fuentes en la bibliografía del tema.
Uso, desde la carpeta del tema:
  python3 Code/africa_cer.py
  bash Code/generar_figura.sh AfCFTA_comunidades
"""
from pathlib import Path

# Países por región (orden de la Unión Africana), con su nombre corto
REGIONES = [
    ('Norte', [('DZA', 'Argelia'), ('EGY', 'Egipto'), ('LBY', 'Libia'), ('MRT', 'Mauritania'), ('MAR', 'Marruecos'),
               ('TUN', 'Túnez')]),
    ('Oeste', [('BEN', 'Benín'), ('BFA', 'Burkina Faso'), ('CPV', 'Cabo Verde'), ('CIV', 'Costa de Marfil'),
               ('GMB', 'Gambia'), ('GHA', 'Ghana'), ('GIN', 'Guinea'), ('GNB', 'Guinea-Bisáu'), ('LBR', 'Liberia'),
               ('MLI', 'Malí'), ('NER', 'Níger'), ('NGA', 'Nigeria'), ('SEN', 'Senegal'), ('SLE', 'Sierra Leona'),
               ('TGO', 'Togo')]),
    ('Centro', [('BDI', 'Burundi'), ('CMR', 'Camerún'), ('CAF', 'Rep. Centroafricana'), ('TCD', 'Chad'),
                ('COG', 'Congo'), ('COD', 'R. D. del Congo'), ('GNQ', 'Guinea Ecuatorial'), ('GAB', 'Gabón'),
                ('STP', 'Santo Tomé y Príncipe')]),
    ('Este', [('COM', 'Comoras'), ('DJI', 'Yibuti'), ('ERI', 'Eritrea'), ('ETH', 'Etiopía'), ('KEN', 'Kenia'),
              ('MDG', 'Madagascar'), ('MUS', 'Mauricio'), ('RWA', 'Ruanda'), ('SYC', 'Seychelles'), ('SOM', 'Somalia'),
              ('SSD', 'Sudán del Sur'), ('SDN', 'Sudán'), ('TZA', 'Tanzania'), ('UGA', 'Uganda')]),
    ('Sur', [('AGO', 'Angola'), ('BWA', 'Botsuana'), ('SWZ', 'Esuatini'), ('LSO', 'Lesoto'), ('MWI', 'Malaui'),
             ('MOZ', 'Mozambique'), ('NAM', 'Namibia'), ('ZAF', 'Sudáfrica'), ('ZMB', 'Zambia'), ('ZWE', 'Zimbabue')]),
]
CER = [
    ('UMA', 'DZA LBY MRT MAR TUN'),
    ('CEN-SAD', 'BFA TCD LBY MLI NER SDN CAF ERI DJI GMB SEN EGY MAR NGA SOM TUN BEN TGO CIV GNB LBR GHA SLE COM GIN '
                'KEN MRT STP CPV'),
    ('CEDEAO', 'BEN CPV CIV GMB GHA GIN GNB LBR NGA SEN SLE TGO'),
    ('CEEAC', 'AGO BDI CMR CAF TCD COG COD GNQ GAB RWA STP'),
    ('EAC', 'BDI COD KEN RWA SOM SSD TZA UGA'),
    ('IGAD', 'DJI ETH KEN SOM SSD SDN UGA'),
    ('COMESA', 'BDI COM COD DJI EGY ERI SWZ ETH KEN LBY MDG MWI MUS RWA SYC SOM SDN TUN UGA ZMB ZWE'),
    ('SADC', 'AGO BWA COM COD SWZ LSO MDG MWI MUS MOZ NAM SYC ZAF TZA ZMB ZWE'),
]
MONETARIAS = [
    ('UEMOA', 'BEN BFA CIV GNB MLI NER SEN TGO'),
    ('CEMAC', 'CMR CAF TCD COG GNQ GAB'),
]
# Antiguos miembros recientes, en hueco
SALIDAS = {('CEDEAO', 'BFA'), ('CEDEAO', 'MLI'), ('CEDEAO', 'NER'), ('IGAD', 'ERI')}
COL_REG = {'Norte': (200, 120, 60), 'Oeste': (60, 130, 90), 'Centro': (150, 90, 160), 'Este': (40, 110, 170),
           'Sur': (190, 70, 70)}


def main():
    paises = [(r, iso, nom) for r, lista in REGIONES for iso, nom in lista]
    dx, dy = 0.29, 0.36        # ancho de columna (país) y alto de fila (comunidad), en cm
    filas = CER + [None] + MONETARIAS + [None, ('n.º', None)]
    o = ['% Generado por Code/africa_cer.py.']
    for reg, rgb in COL_REG.items():
        o.append('\\definecolor{r%s}{RGB}{%d,%d,%d}' % (reg, *rgb))
    o.append('\\begin{tikzpicture}[font=\\sffamily]')
    x0 = 1.6
    ytop = 0.0
    # Nombres de los países, girados
    for k, (reg, iso, nom) in enumerate(paises):
        x = x0 + k * dx
        o.append(f'  \\node[rotate=90, anchor=west, font=\\sffamily\\tiny, inner sep=1pt] at ({x:.3f},{ytop + 0.1:.2f}) {{{nom}}};')
    # Bandas de región (debajo de la matriz)
    k = 0
    n_filas = len(filas)
    ybot = ytop - n_filas * dy
    for reg, lista in REGIONES:
        xa, xb = x0 + k * dx - dx / 2, x0 + (k + len(lista) - 1) * dx + dx / 2
        o.append(f'  \\fill[r{reg}] ({xa:.3f},{ybot - 0.05:.3f}) rectangle ({xb:.3f},{ybot - 0.22:.3f});')
        o.append(f'  \\node[font=\\sffamily\\scriptsize, text=r{reg}, anchor=north] at ({(xa + xb) / 2:.3f},{ybot - 0.25:.3f}) {{África {reg.lower() if reg != "Centro" else "central"}}};')
        if k:
            o.append(f'  \\draw[black!35, line width=0.4pt] ({xa:.3f},{ytop:.2f}) -- ({xa:.3f},{ybot:.3f});')
        k += len(lista)
    # Filas
    cuenta = {iso: 0 for _, iso, _ in paises}
    for j, fila in enumerate(filas):
        y = ytop - (j + 0.5) * dy
        if fila is None:
            continue
        nombre, miembros = fila
        o.append(f'  \\node[anchor=east, font=\\sffamily\\scriptsize] at ({x0 - 0.2:.2f},{y:.3f}) {{{nombre}}};')
        if miembros is None:   # fila de recuento
            for k, (reg, iso, _) in enumerate(paises):
                o.append(f'  \\node[font=\\sffamily\\tiny\\bfseries, text=r{reg}] at ({x0 + k * dx:.3f},{y:.3f}) {{{cuenta[iso]}}};')
            continue
        o.append(f'  \\draw[black!10, line width=0.3pt] ({x0 - dx / 2:.3f},{y:.3f}) -- ({x0 + (len(paises) - 0.5) * dx:.3f},{y:.3f});')
        mm = set(miembros.split())
        for k, (reg, iso, _) in enumerate(paises):
            x = x0 + k * dx
            if iso in mm:
                if fila in CER:
                    cuenta[iso] += 1
                o.append(f'  \\fill[r{reg}] ({x:.3f},{y:.3f}) circle (0.095);')
            elif (nombre, iso) in SALIDAS:
                o.append(f'  \\draw[r{reg}, line width=0.6pt] ({x:.3f},{y:.3f}) circle (0.085);')
    # Separadores y rótulos de grupo
    ysep = ytop - len(CER) * dy - dy / 2
    o.append(f'  \\node[anchor=east, font=\\sffamily\\tiny\\itshape, text=black!60] at ({x0 - 0.2:.2f},{ysep:.3f}) {{uniones del franco CFA}};')
    ycnt = ytop - (len(CER) + 1 + len(MONETARIAS)) * dy - dy / 2
    o.append(f'  \\node[anchor=east, font=\\sffamily\\tiny\\itshape, text=black!60] at ({x0 - 0.2:.2f},{ycnt:.3f}) {{CER a las que pertenece}};')
    # Leyenda
    ly = ybot - 0.85
    o.append(f'  \\fill[black!70] ({x0:.2f},{ly:.2f}) circle (0.095); \\node[anchor=west, font=\\sffamily\\tiny] at ({x0 + 0.15:.2f},{ly:.2f}) {{miembro (octubre de 2026)}};')
    o.append(f'  \\draw[black!70, line width=0.6pt] ({x0 + 3.2:.2f},{ly:.2f}) circle (0.085); \\node[anchor=west, font=\\sffamily\\tiny] at ({x0 + 3.35:.2f},{ly:.2f}) {{salida reciente (Burkina Faso, Malí y Níger de la CEDEAO, 2025; Eritrea de la IGAD, 2025)}};')
    o.append('\\end{tikzpicture}')
    destino = Path(__file__).resolve().parent.parent / 'Img' / 'AfCFTA_comunidades.tikz'
    destino.write_text('\n'.join(o) + '\n', encoding='utf-8')
    print('Escrito', destino)


if __name__ == '__main__':
    main()
