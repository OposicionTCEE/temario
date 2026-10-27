#!/usr/bin/env python3
"""Caso del anexo de valoración del tema 3.B.4 (27/10/2026): A, la empresa de almacenaje del cuerpo, valora la compra de
ALFA, S.L., la distribuidora de material de oficina del 3.B.1 (cuentas de 2026 en 3.B.1/Code/ejemplo_alfa.py).
Importes en miles de euros.

Calcula la proyección 2027-2031, el valor de ALFA por sí sola (descuento de flujos con valor terminal por la fórmula de
los inductores de valor), la sensibilidad a la tasa y al crecimiento, la sinergia, el intervalo de precio y el contraste
con múltiplos. Escribe:
  Code/datos/caso_alfa.csv       todas las cifras, en formato largo (bloque, concepto, año, valor, unidad, origen);
  Img/anx_val_alfa_valor.tikz    cascada del valor de ALFA por sí sola;
  Img/anx_val_alfa_precio.tikz   intervalos de valor por método y precio negociado.
Uso: python3 -I Code/valoracion_alfa.py; después bash Code/generar_figura.sh anx_val_alfa_valor (y _precio) y
python -I Code/libro_datos.py (con openpyxl).
"""
import csv
from pathlib import Path

TEMA = Path(__file__).resolve().parent.parent
FILAS = []


def guarda(bloque, concepto, año, valor, unidad, origen):
    FILAS.append((bloque, concepto, año, round(valor, 6) if isinstance(valor, float) else valor, unidad, origen))
    return valor


# --- Punto de partida: cuentas de 2026 de ALFA (3.B.1) ---
B3B1 = 'Tema 3.B.1, cuentas de 2026'
VENTAS0 = guarda('Partida', 'Importe neto de la cifra de negocios', 2026, 350.0, 'miles de euros', B3B1)
BAII0 = guarda('Partida', 'Resultado de explotación', 2026, 12.0, 'miles de euros', B3B1)
NO_RECURRENTE = guarda('Partida', 'Pérdida por la venta de un mueble (no recurrente)', 2026, 1.4, 'miles de euros', B3B1)
BAII0_N = guarda('Partida', 'Resultado de explotación normalizado', 2026, BAII0 + NO_RECURRENTE, 'miles de euros',
                 'Cálculo: resultado de explotación + pérdida no recurrente')
AMORT0 = guarda('Partida', 'Amortización', 2026, 8.3, 'miles de euros', B3B1)
INM0 = guarda('Partida', 'Inmovilizado neto (intangible y material)', 2026, 40.8, 'miles de euros', B3B1)
NOF0 = guarda('Partida', 'Necesidades operativas de fondos', 2026, 38.16, 'miles de euros', B3B1)
EXIST0 = guarda('Partida', 'Existencias', 2026, 34.7, 'miles de euros', B3B1)
DEUDA = guarda('Partida', 'Deuda financiera (largo y corto plazo)', 2026, 30.0, 'miles de euros', B3B1)
CAJA = guarda('Partida', 'Tesorería', 2026, 26.54, 'miles de euros', B3B1)
PN0 = guarda('Partida', 'Patrimonio neto', 2026, 75.5, 'miles de euros', B3B1)
ALQUILER0 = guarda('Partida', 'Arrendamientos', 2026, 20.0, 'miles de euros', B3B1)
KD = guarda('Supuesto', 'Coste de la deuda antes de impuestos', '—', 0.057, 'tanto por uno', 'Tema 3.B.1 (coste de 2026)')

# --- Supuestos ---
SUP = 'Supuesto ilustrativo'
CREC = guarda('Supuesto', 'Crecimiento de las ventas 2027-2031', '—', 0.05, 'tanto por uno', SUP)
G = guarda('Supuesto', 'Crecimiento a largo plazo (desde 2032)', '—', 0.02, 'tanto por uno', SUP)
TAU = guarda('Supuesto', 'Tipo del impuesto sobre sociedades', '—', 0.25, 'tanto por uno', 'Tipo general (supuesto)')
BETA_A = guarda('Supuesto', 'Beta de los activos de las comparables', '—', 0.9, '—', SUP)
DV = guarda('Supuesto', 'Deuda sobre valor (estructura objetivo)', '—', 0.20, 'tanto por uno', SUP)
GAMMA = guarda('Supuesto', 'Tipo sin riesgo', '—', 0.03, 'tanto por uno', SUP)
PRIMA = guarda('Supuesto', 'Prima de riesgo del mercado', '—', 0.06, 'tanto por uno', SUP)
M = BAII0_N / VENTAS0            # margen de explotación normalizado
R_INM = INM0 / VENTAS0           # inmovilizado neto / ventas
R_AM = AMORT0 / VENTAS0          # amortización / ventas
R_NOF = NOF0 / VENTAS0           # NOF / ventas
for c, v in [('Margen de explotación normalizado', M), ('Inmovilizado neto / ventas', R_INM),
             ('Amortización / ventas', R_AM), ('NOF / ventas', R_NOF)]:
    guarda('Supuesto', c + ' (constante, el de 2026)', '—', v, 'tanto por uno', 'Cálculo con las cuentas de 2026')

# --- Tasa ---
BETA_E = BETA_A * (1 + DV / (1 - DV))     # beta de la deuda nula (Tema 3.B.2)
KE = GAMMA + BETA_E * PRIMA
K = (1 - DV) * KE + DV * KD * (1 - TAU)
guarda('Tasa', 'Beta de las acciones reapalancada', '—', BETA_E, '—', 'Cálculo')
guarda('Tasa', 'Coste de los recursos propios (CAPM)', '—', KE, 'tanto por uno', 'Cálculo')
guarda('Tasa', 'Coste medio ponderado del capital de ALFA, k_B', '—', K, 'tanto por uno', 'Cálculo')
NOPAT0 = BAII0_N * (1 - TAU)
CI0 = INM0 + NOF0
ROIC = NOPAT0 / CI0
guarda('Tasa', 'Rentabilidad del capital invertido (2026, normalizada, tipo general)', 2026, ROIC, 'tanto por uno', 'Cálculo')


def valor(k=K, g=G, ronic=ROIC, crec=CREC, guardar=False):
    """Valor de ALFA por sí sola: flujos 2027-2031 y valor terminal en 2031 (inductores de valor)."""
    ventas_ant, inm_ant, nof_ant = VENTAS0, INM0, NOF0
    va_flujos, filas = 0.0, []
    for t in range(1, 6):
        ventas = VENTAS0 * (1 + crec) ** t
        baii = M * ventas
        nopat = baii * (1 - TAU)
        amort = R_AM * ventas
        inm, nof = R_INM * ventas, R_NOF * ventas
        inversion = amort + (inm - inm_ant)
        dnof = nof - nof_ant
        fcl = nopat + amort - inversion - dnof
        fd = 1 / (1 + k) ** t
        va_flujos += fcl * fd
        filas.append((2026 + t, ventas, baii, nopat, amort, inversion, dnof, fcl, fd, fcl * fd))
        ventas_ant, inm_ant, nof_ant = ventas, inm, nof
    nopat_T1 = filas[-1][3] * (1 + g)
    vt = nopat_T1 * (1 - g / ronic) / (k - g)
    va_vt = vt * filas[-1][8]
    if guardar:
        for año, ventas, baii, nopat, amort, inversion, dnof, fcl, fd, va in filas:
            for c, v in [('Ventas', ventas), ('Resultado de explotación', baii),
                         ('Resultado de explotación después de impuestos', nopat), ('Amortización', amort),
                         ('Inversión en inmovilizado', inversion), ('Aumento de las NOF', dnof),
                         ('Flujo de caja libre', fcl), ('Valor actual del flujo', va)]:
                guarda('Proyección', c, año, v, 'miles de euros', 'Cálculo')
            guarda('Proyección', 'Factor de descuento', año, fd, '—', 'Cálculo')
        guarda('Valor', 'Resultado de explotación después de impuestos de 2032', 2032, nopat_T1, 'miles de euros', 'Cálculo')
        guarda('Valor', 'Valor terminal en 2031', 2031, vt, 'miles de euros', 'Cálculo')
        guarda('Valor', 'Valor actual de los flujos 2027-2031', '—', va_flujos, 'miles de euros', 'Cálculo')
        guarda('Valor', 'Valor actual del valor terminal', '—', va_vt, 'miles de euros', 'Cálculo')
    return va_flujos + va_vt, va_flujos, va_vt, filas


VB, VA_FLUJOS, VA_VT, FILAS_PROY = valor(guardar=True)
E = VB + CAJA - DEUDA
guarda('Valor', 'Valor de ALFA por sí sola, V_B', '—', VB, 'miles de euros', 'Cálculo')
guarda('Valor', 'Peso del valor terminal', '—', VA_VT / VB, 'tanto por uno', 'Cálculo')
guarda('Valor', 'Valor de las acciones, E = V_B + tesorería - deuda', '—', E, 'miles de euros', 'Cálculo')
guarda('Valor', 'Valor de las acciones / patrimonio neto', '—', E / PN0, 'veces', 'Cálculo')
BAII1 = FILAS_PROY[0][2]
guarda('Valor', 'Múltiplo implícito V_B / resultado de explotación de 2027', '—', VB / BAII1, 'veces', 'Cálculo')
VB_RK = valor(ronic=K)[0]
guarda('Valor', 'V_B con RONIC = k_B', '—', VB_RK, 'miles de euros', 'Cálculo')

# --- Sensibilidad ---
TASAS = [K - 0.01, K, K + 0.01]
CRECS = [G - 0.005, G, G + 0.005]
SENS = [[valor(k=k, g=g)[0] for g in CRECS] for k in TASAS]
for k, fila in zip(TASAS, SENS):
    for g, v in zip(CRECS, fila):
        guarda('Sensibilidad', f'V_B con k_B = {100 * k:.2f} % y g = {100 * g:.1f} %', '—', v, 'miles de euros', 'Cálculo')

# --- Sinergia ---
AHORRO = guarda('Supuesto', 'Ahorro de alquiler desde 2028 (un cuarto del de 2026, crece con g)', '—', 0.25 * ALQUILER0,
                'miles de euros', SUP)
EXIST_NUEVA = guarda('Supuesto', 'Existencias / ventas desde 2028', '—', 0.085, 'tanto por uno', SUP)
INTEGRACION = guarda('Supuesto', 'Costes de integración en 2027, antes de impuestos', 2027, 6.0, 'miles de euros', SUP)
ratio_ant = EXIST0 / VENTAS0
dif = ratio_ant - EXIST_NUEVA
ventas = [VENTAS0 * (1 + CREC) ** t for t in range(0, 6)]


def sinergia(k=K, g=G):
    """Ahorro de alquiler (renta perpetua creciente desde 2028) y menos existencias (liberación en 2028 y menor inversión
    en circulante después), a k_B; costes de integración, casi ciertos, al tipo sin riesgo. Todo después de impuestos."""
    ahorro = AHORRO * (1 - TAU) * (1 + g) ** 2 / (k - g) / (1 + k)
    exist = dif * ventas[2] / (1 + k) ** 2
    for t in range(3, 6):
        exist += dif * (ventas[t] - ventas[t - 1]) / (1 + k) ** t
    exist += dif * ventas[5] * g / (k - g) / (1 + k) ** 5
    integ = INTEGRACION * (1 - TAU) / (1 + GAMMA)
    return ahorro + exist - integ, ahorro, exist, integ


S, va_ahorro, va_exist, va_integ = sinergia()
SENS_S = [[valor(k=k, g=g)[0] + sinergia(k, g)[0] for g in CRECS] for k in TASAS]
guarda('Sinergia', 'Valor actual del ahorro de alquiler', '—', va_ahorro, 'miles de euros', 'Cálculo, a k_B')
guarda('Sinergia', 'Valor actual de la reducción de existencias', '—', va_exist, 'miles de euros', 'Cálculo, a k_B')
guarda('Sinergia', 'Valor actual de los costes de integración', '—', va_integ, 'miles de euros', 'Cálculo, al tipo sin riesgo')
guarda('Sinergia', 'Sinergia, S', '—', S, 'miles de euros', 'Cálculo')

# --- Precio ---
BETA_N = guarda('Supuesto', 'Poder negociador del vendedor (NASH asimétrica)', '—', 0.5, '—', SUP)
P = VB + BETA_N * S
S2 = guarda('Supuesto', 'Sinergia del segundo comprador / S', '—', 0.6, '—', SUP) * S
P2 = VB + S2
for c, v in [('Máximo para A, V_B + S', VB + S), ('Precio negociado, V_B + beta S', P),
             ('Precio de las acciones negociado', P + CAJA - DEUDA), ('Prima sobre el valor de las acciones', BETA_N * S),
             ('Prima / valor de las acciones', BETA_N * S / E), ('Precio con un segundo comprador, V_B + S_2', P2),
             ('Lo que conserva A con un segundo comprador, S - S_2', S - S2)]:
    guarda('Precio', c, '—', v, 'miles de euros' if 'Prima /' not in c else 'tanto por uno', 'Cálculo')

# --- Múltiplos (supuestos ilustrativos de comparables) ---
MULT = {'Comparables cotizadas': (8.5, 9.5, 10.5), 'Transacciones comparables': (11.0, 12.0, 13.0)}
for nombre, (q1, med, q3) in MULT.items():
    for c, v in [('primer cuartil', q1), ('mediana', med), ('tercer cuartil', q3)]:
        guarda('Múltiplos', f'{nombre}: valor / resultado de explotación de 2027, {c}', '—', v, 'veces', SUP)
        guarda('Múltiplos', f'{nombre}: valor de ALFA con el {c}', '—', v * BAII1, 'miles de euros', 'Cálculo')

# --- Salidas ---
with open(TEMA / 'Code' / 'datos' / 'caso_alfa.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['bloque', 'concepto', 'año', 'valor', 'unidad', 'origen'])
    w.writerows(FILAS)


def n(x, d=1):
    """Cifra con coma decimal para el texto."""
    return f'{x:.{d}f}'.replace('.', '{,}')


# Figura (a): cascada del valor por sí sola
CAB = ('% Figura del anexo de valoración, caso ALFA. Generada por Code/valoracion_alfa.py (no editar a mano).\n')
esc = 0.025  # cm por miles de euros
partes = [('VA de los flujos\\\\ 2027-2031', 0, VA_FLUJOS, 'teal!25'),
          ('VA del valor\\\\ terminal', VA_FLUJOS, VA_FLUJOS + VA_VT, 'teal!45'),
          ('$V_B$', 0, VB, 'teal!70!black'),
          ('$+$ tesorería', VB, VB + CAJA, 'black!20'),
          ('$-$ deuda', VB + CAJA, E, 'black!45'),
          ('$E$', 0, E, 'black!65')]
lineas = [CAB + '% Cascada: valor actual de los flujos 2027-2031, del valor terminal, V_B, tesorería, deuda y valor de las\n'
          '% acciones de ALFA (miles de euros).\n% Generar con: bash Code/generar_figura.sh anx_val_alfa_valor\n',
          '\\begin{tikzpicture}[font=\\footnotesize]\n']
x = 0.0
for i, (rot, a, b, col) in enumerate(partes):
    y0, y1 = sorted((a * esc, b * esc))
    lineas.append(f'  \\fill[{col}] ({x:.2f},{y0:.3f}) rectangle ({x + 1.0:.2f},{y1:.3f});\n')
    lineas.append(f'  \\draw[black!70] ({x:.2f},{y0:.3f}) rectangle ({x + 1.0:.2f},{y1:.3f});\n')
    valor_et = b - a if i not in (2, 5) else b
    lineas.append(f'  \\node[above, font=\\scriptsize] at ({x + 0.5:.2f},{y1:.3f}) {{${n(abs(valor_et))}$}};\n')
    lineas.append(f'  \\node[below, align=center, font=\\scriptsize] at ({x + 0.5:.2f},0) {{{rot}}};\n')
    if i < len(partes) - 1:
        nivel = b * esc
        lineas.append(f'  \\draw[dotted] ({x + 1.0:.2f},{nivel:.3f}) -- ({x + 1.6:.2f},{nivel:.3f});\n')
    x += 1.6
lineas.append(f'  \\draw (-0.3,0) -- ({x - 0.3:.2f},0);\n\\end{{tikzpicture}}\n')
(TEMA / 'Img' / 'anx_val_alfa_valor.tikz').write_text(''.join(lineas), encoding='utf-8')

# Figura (b): intervalos de valor y precio
sens = [v for fila in SENS for v in fila]
sens_s = [v for fila in SENS_S for v in fila]
barras = [('Descuento de flujos, $V_B$', min(sens), max(sens)),
          ('Descuento de flujos con sinergia, $V_B+S$', min(sens_s), max(sens_s)),
          ('Comparables cotizadas', MULT['Comparables cotizadas'][0] * BAII1, MULT['Comparables cotizadas'][2] * BAII1),
          ('Transacciones comparables', MULT['Transacciones comparables'][0] * BAII1,
           MULT['Transacciones comparables'][2] * BAII1)]
x0, esc2 = 90.0, 0.045
lineas = [CAB + '% Intervalos del valor de ALFA (miles de euros) según cada método: descuento de flujos (sensibilidad a k_B\n'
          '% +-1 punto y g +-0,5 puntos), con sinergia, comparables cotizadas y transacciones comparables (cuartiles); la línea\n'
          '% es el precio negociado, V_B + beta S, con beta = 0,5.\n% Generar con: bash Code/generar_figura.sh anx_val_alfa_precio\n',
          '\\begin{tikzpicture}[font=\\footnotesize, >={Stealth[length=4pt]}, y=0.75cm]\n']
for j, (rot, a, b) in enumerate(barras):
    y = 4 - j
    lineas.append(f'  \\fill[teal!35] ({(a - x0) * esc2:.3f},{y - 0.28:.2f}) rectangle ({(b - x0) * esc2:.3f},{y + 0.28:.2f});\n')
    lineas.append(f'  \\draw[black!70] ({(a - x0) * esc2:.3f},{y - 0.28:.2f}) rectangle ({(b - x0) * esc2:.3f},{y + 0.28:.2f});\n')
    lineas.append(f'  \\node[left] at (0,{y}) {{{rot}}};\n')
    lineas.append(f'  \\node[left, font=\\scriptsize] at ({(a - x0) * esc2:.3f},{y}) {{${n(a, 0)}$}};\n')
    lineas.append(f'  \\node[right, font=\\scriptsize] at ({(b - x0) * esc2:.3f},{y}) {{${n(b, 0)}$}};\n')
xmax = (240 - x0) * esc2
lineas.append(f'  \\draw[->] (0,0.2) -- ({xmax:.2f},0.2) node[below left] {{miles de euros}};\n')
for v in range(100, 241, 20):
    lineas.append(f'  \\draw ({(v - x0) * esc2:.3f},0.28) -- ({(v - x0) * esc2:.3f},0.12) node[below, font=\\scriptsize] {{${v}$}};\n')
xp = (P - x0) * esc2
lineas.append(f'  \\draw[dashed, thick, teal!70!black] ({xp:.3f},0.2) -- ({xp:.3f},4.7) node[above] {{$P={n(P)}$}};\n')
lineas.append('\\end{tikzpicture}\n')
(TEMA / 'Img' / 'anx_val_alfa_precio.tikz').write_text(''.join(lineas), encoding='utf-8')

# Resumen para el texto
print(f'margen {100*M:.2f} %, ROIC {100*ROIC:.2f} %, beta_E {BETA_E:.3f}, k_E {100*KE:.2f} %, k_B {100*K:.3f} %')
print('año ventas BAII NOPAT A I dNOF FCL fd VA')
for fila in FILAS_PROY:
    print(' '.join(f'{v:.3f}' if isinstance(v, float) else str(v) for v in fila))
print(f'VA flujos {VA_FLUJOS:.2f}; NOPAT 2032 {FILAS_PROY[-1][3]*(1+G):.3f}; VT {VA_VT/FILAS_PROY[-1][8]:.2f}; '
      f'VA VT {VA_VT:.2f}; V_B {VB:.2f}; peso VT {100*VA_VT/VB:.1f} %; E {E:.2f}; E/PN {E/PN0:.2f}; '
      f'múltiplo {VB/BAII1:.2f}; BAII 2027 {BAII1:.3f}; V_B(RONIC=k) {VB_RK:.2f}')
print('sensibilidad (filas k, columnas g):', [f'{100*k:.2f}' for k in TASAS], [f'{100*g:.1f}' for g in CRECS])
for fila in SENS:
    print(' '.join(f'{v:.1f}' for v in fila))
print(f'sinergia: ahorro {va_ahorro:.2f}, existencias {va_exist:.2f} (liberación 2028 {dif*ventas[2]:.2f}), '
      f'integración {va_integ:.2f}; S {S:.2f}; V_B+S {VB+S:.2f}')
print(f'precio: P {P:.2f}; P acciones {P+CAJA-DEUDA:.2f}; prima {BETA_N*S:.2f} ({100*BETA_N*S/E:.1f} %); '
      f'S2 {S2:.2f}; P2 {P2:.2f}; A conserva {S-S2:.2f}')
for nombre, (q1, med, q3) in MULT.items():
    print(f'{nombre}: {q1*BAII1:.1f} / {med*BAII1:.1f} / {q3*BAII1:.1f}')
