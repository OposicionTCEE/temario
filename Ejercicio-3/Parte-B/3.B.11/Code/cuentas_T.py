#!/usr/bin/env python3
"""Cuentas en T del bloque II del 3.B.11 (sucesión de cuentas de la balanza de pagos, rúbricas agregadas, en letras).

Una sola T continua con las cuentas apiladas, como la sucesión de cuentas de la contabilidad nacional: cada cuenta
se cierra con su saldo en el lado de los débitos y ese saldo abre la cuenta siguiente en el lado de los créditos
(una flecha une las dos anotaciones). La cuenta financiera se cierra con los errores y omisiones:
dAF = dP + CNF + EO, es decir, CF = dAF - dP = CNF + EO.

Cada figura del cuerpo es un tramo de esa T (la cuenta anterior en gris y la nueva en negro) y la última es la T completa.
Uso, desde la carpeta del tema:
    python3 -I -B Code/cuentas_T.py
    for f in b2_cuenta_bienes b2_cuenta_rentas b2_cuenta_capital b2_cuenta_financiera b2_sucesion; do bash Code/generar_figura.sh $f; done
Fuente de las rúbricas: FMI (2009), cap. 10 a 12; SEC 2010 (sucesión de cuentas).
"""
import os
import sys

ANCHO = 15.6          # ancho total de la T (cm), el del texto
COL = ANCHO / 2       # ancho de cada lado
FILA = 0.53           # alto de una fila (cm)
SANGRIA = r'\hspace*{1em}'

# Cada cuenta: título, saldo que arrastra de la anterior (o None), anotaciones de cada lado y saldo con que se cierra.
CUENTAS = {
    'bienes': dict(
        titulo='Cuenta de bienes y servicios',
        arrastre=None,
        izq=[r'Importaciones de bienes, $M_b$', r'Importaciones de servicios, $M_s$'],
        der=[r'Exportaciones de bienes, $X_b$', r'Exportaciones de servicios, $X_s$'],
        saldo=r'Saldo de bienes y servicios, $XN=X-M$',
    ),
    'primaria': dict(
        titulo='Cuenta de renta primaria',
        arrastre=r'Saldo de bienes y servicios, $XN$',
        izq=['Remuneración de asalariados', 'Rentas de la inversión', 'Otra renta primaria'],
        der=['Remuneración de asalariados', 'Rentas de la inversión', 'Otra renta primaria'],
        saldo=r'Saldo tras la renta primaria, $XN+RPN$',
    ),
    'secundaria': dict(
        titulo='Cuenta de renta secundaria',
        arrastre=r'Saldo tras la renta primaria, $XN+RPN$',
        izq=['Transferencias personales', 'Otras transferencias corrientes'],
        der=['Transferencias personales', 'Otras transferencias corrientes'],
        saldo=r'Saldo de la cuenta corriente, $CC=XN+RPN+TCN$',
    ),
    'capital': dict(
        titulo='Cuenta de capital',
        arrastre=r'Saldo de la cuenta corriente, $CC$',
        izq=['Transferencias de capital', 'Adquisiciones de activos no producidos'],
        der=['Transferencias de capital', 'Cesiones de activos no producidos'],
        saldo=r'Capacidad o necesidad de financiación, $CNF=CC+CK$',
    ),
    'financiera': dict(
        titulo='Cuenta financiera',
        arrastre=r'Capacidad o necesidad de financiación, $CNF$',
        izq=[r'\textit{Adquisición neta de activos}, $\Delta AF$:',
             SANGRIA + 'Inversión directa', SANGRIA + 'Inversión de cartera',
             SANGRIA + 'Derivados financieros (neto)', SANGRIA + 'Otra inversión',
             SANGRIA + 'Activos de reserva'],
        der=[r'\textit{Contracción neta de pasivos}, $\Delta P$:',
             SANGRIA + 'Inversión directa', SANGRIA + 'Inversión de cartera',
             SANGRIA + 'Otra inversión'],
        saldo=None,
        cierre_der=r'Errores y omisiones, $EO$',
        pie=r'$\Delta AF=\Delta P+CNF+EO$, \ es decir, \ $CF=\Delta AF-\Delta P=CNF+EO$',
    ),
}

# Figuras: (nombre, [(cuenta, gris)], comentario). Desde el 17/11/2026 (nota del usuario), cada figura del cuerpo
# muestra solo su cuenta, que se abre con el saldo que recibe de la anterior (en cursiva), sin la cuenta anterior en gris.
FIGURAS = [
    ('b2_cuenta_bienes', [('bienes', False)],
     'Cuerpo, 3.1.1: la cuenta de bienes y servicios en T; su saldo, XN, abre la cuenta siguiente.'),
    ('b2_cuenta_primaria', [('primaria', False)],
     'Cuerpo, 3.2.1: la cuenta de renta primaria; la abre el saldo de bienes y servicios y la cierra XN + RPN.'),
    ('b2_cuenta_secundaria', [('secundaria', False)],
     'Cuerpo, 3.2.1: la cuenta de renta secundaria; la abre XN + RPN y la cierra el saldo de la cuenta corriente.'),
    ('b2_cuenta_capital', [('capital', False)],
     'Cuerpo, 3.3.1: la cuenta de capital; la abre el saldo corriente y la cierra la capacidad o necesidad de financiación.'),
    ('b2_cuenta_financiera', [('financiera', False)],
     'Cuerpo, 3.4.2: la cuenta financiera; la abre la CNF y la cierran los errores y omisiones.'),
    ('b2_sucesion', [('bienes', False), ('primaria', False), ('secundaria', False), ('capital', False),
                     ('financiera', False)],
     'Cuerpo, 3.4.3: la sucesión completa (puesta en común); cada saldo cierra una cuenta y abre la siguiente.'),
]


def nodo(nombre, x, y, texto, gris, negrita=False, cursiva=False):
    # Los saldos y sus arrastres llevan ancho natural, para que la flecha una el final de uno con el principio del otro
    estilo = ['ent' if not nombre else 'sal']
    if gris:
        estilo.append('vis')
    if negrita:
        texto = r'\textbf{' + texto + '}'
    if cursiva:
        texto = r'\textit{' + texto + '}'
    nom = f' ({nombre})' if nombre else ''
    return f'\\node[{", ".join(estilo)}]{nom} at ({x:.2f},{y:.3f}) {{{texto}}};'


def figura(nombre, tramos, comentario):
    lineas = [
        f'% {comentario}',
        '% Generada por Code/cuentas_T.py (no editar a mano). Rúbricas agregadas, en letras; fuente: FMI (2009); SEC 2010.',
        r'\begin{tikzpicture}[',
        r'  font=\footnotesize,',
        r'  >={Stealth[length=1.8mm]},',
        r'  every node/.append style={execute at begin node={\hyphenpenalty=10000\exhyphenpenalty=10000}},',
        rf'  ent/.style={{anchor=west, align=left, text width={COL - 0.35:.2f}cm, inner sep=1.5pt}},',
        r'  sal/.style={anchor=west, align=left, inner sep=1.5pt},',
        r'  vis/.style={text=black!45},',
        r'  arr/.style={->, thick, black!55, rounded corners=2pt},',
        ']',
    ]
    # Cabecera de la T
    lineas += [
        rf'\node[font=\small\bfseries] at ({COL / 2:.2f},0.66) {{Débitos}};',
        rf'\node[font=\small\bfseries] at ({COL + COL / 2:.2f},0.66) {{Créditos}};',
        rf'\node[text=black!60, align=center, font=\scriptsize] at ({COL / 2:.2f},0.25) {{importaciones, pagos y adquisición neta de activos}};',
        rf'\node[text=black!60, align=center, font=\scriptsize] at ({COL + COL / 2:.2f},0.25) {{exportaciones, ingresos y contracción neta de pasivos}};',
        rf'\draw[thick] (0,0) -- ({ANCHO:.2f},0);',
    ]
    y = 0.0
    saldo_previo = None
    for k, (clave, gris) in enumerate(tramos):
        c = CUENTAS[clave]
        if k > 0:
            col = 'black!30' if gris else 'black!55'
            lineas.append(rf'\draw[{col}] (0,{y:.3f}) -- ({ANCHO:.2f},{y:.3f});')
        filas_izq = [(None, c['titulo'], 'titulo')] + [(None, t, 'ent') for t in c['izq']]
        filas_der = []
        if c['arrastre']:
            filas_der.append((f'C{k}', c['arrastre'], 'arrastre'))
        filas_der += [(None, t, 'ent') for t in c['der']]
        n = max(len(filas_izq), len(filas_der))
        if c.get('saldo'):
            filas_izq += [(None, '', 'vacio')] * (n - len(filas_izq)) + [(f'S{k}', c['saldo'], 'saldo')]
        if c.get('cierre_der'):
            filas_der += [(None, '', 'vacio')] * (n - len(filas_der)) + [(None, c['cierre_der'], 'saldo')]
        filas = max(len(filas_izq), len(filas_der))
        for lado, filas_lado in (('izq', filas_izq), ('der', filas_der)):
            x = 0.12 if lado == 'izq' else COL + 0.18
            for i, (nom, texto, tipo) in enumerate(filas_lado):
                if tipo == 'vacio':
                    continue
                yy = y - FILA * (i + 0.5) - 0.08
                lineas.append(nodo(nom, x, yy, texto, gris,
                                   negrita=tipo in ('titulo', 'saldo'), cursiva=(tipo == 'arrastre')))
        # Flecha del saldo anterior a su anotación en esta cuenta
        if saldo_previo and c['arrastre']:
            lineas.append(rf'\draw[arr] ({saldo_previo}.east) to[out=0, in=180] (C{k}.west);')
        saldo_previo = f'S{k}' if c.get('saldo') else None
        y -= FILA * filas + 0.16
        if c.get('pie') and not gris:
            pie = c['pie']
    lineas.append(rf'\draw[thick] ({COL:.2f},0) -- ({COL:.2f},{y:.3f});')
    if any(CUENTAS[cl].get('pie') and not g for cl, g in tramos):
        lineas.append(rf'\node[font=\small] at ({COL:.2f},{y - 0.5:.3f}) {{{pie}}};')
    lineas.append(r'\end{tikzpicture}%')
    return '\n'.join(lineas) + '\n'


def main():
    tema = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for nombre, tramos, comentario in FIGURAS:
        ruta = os.path.join(tema, 'Img', nombre + '.tikz')
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(figura(nombre, tramos, comentario))
        print('Escrito Img/' + nombre + '.tikz')


if __name__ == '__main__':
    sys.exit(main())
