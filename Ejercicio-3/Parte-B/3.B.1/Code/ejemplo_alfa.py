"""Ejemplo ALFA, S.L. (Anexo II del tema 3.B.1): Libro Diario del ejercicio 2026, balance de comprobación,
regularización y cierre. Importes en miles de euros. Uso: python3 Code/ejemplo_alfa.py

Los asientos reproducen los del anexo (numeración del texto). Sirve para comprobar que todo cuadra y para
obtener las cifras de las tablas (sumas y saldos, cuenta de pérdidas y ganancias, balance, estado de flujos)."""
from decimal import Decimal as D
from collections import OrderedDict

NOMBRES = {
    '100': 'Capital social', '112': 'Reserva legal', '113': 'Reservas voluntarias', '129': 'Resultado del ejercicio',
    '170': 'Deudas a largo plazo con entidades de crédito', '206': 'Aplicaciones informáticas', '216': 'Mobiliario',
    '217': 'Equipos para procesos de información', '218': 'Elementos de transporte',
    '2806': 'Amortización acumulada de aplicaciones informáticas', '2816': 'Amortización acumulada de mobiliario',
    '2817': 'Amortización acumulada de equipos para procesos de información',
    '2818': 'Amortización acumulada de elementos de transporte', '300': 'Mercaderías', '400': 'Proveedores',
    '430': 'Clientes', '436': 'Clientes de dudoso cobro', '472': 'Hacienda Pública, IVA soportado',
    '473': 'Hacienda Pública, retenciones y pagos a cuenta', '4750': 'Hacienda Pública, acreedora por IVA',
    '4751': 'Hacienda Pública, acreedora por retenciones practicadas',
    '4752': 'Hacienda Pública, acreedora por impuesto sobre sociedades', '476': 'Organismos de la Seguridad Social, acreedores',
    '477': 'Hacienda Pública, IVA repercutido', '480': 'Gastos anticipados',
    '490': 'Deterioro de valor de créditos por operaciones comerciales', '520': 'Deudas a corto plazo con entidades de crédito',
    '523': 'Proveedores de inmovilizado a corto plazo', '526': 'Dividendo activo a pagar', '572': 'Bancos',
    '600': 'Compras de mercaderías', '606': 'Descuentos sobre compras por pronto pago',
    '608': 'Devoluciones de compras y operaciones similares', '610': 'Variación de existencias de mercaderías',
    '621': 'Arrendamientos y cánones', '625': 'Primas de seguros', '628': 'Suministros', '6300': 'Impuesto corriente',
    '640': 'Sueldos y salarios', '642': 'Seguridad Social a cargo de la empresa', '662': 'Intereses de deudas',
    '671': 'Pérdidas procedentes del inmovilizado material', '680': 'Amortización del inmovilizado intangible',
    '681': 'Amortización del inmovilizado material', '694': 'Pérdidas por deterioro de créditos por operaciones comerciales',
    '700': 'Ventas de mercaderías', '708': 'Devoluciones de ventas y operaciones similares',
}

def a(*partidas):
    """Asiento: lista de (cuenta, debe, haber)."""
    return [(c, D(str(d)), D(str(h))) for c, d, h in partidas]

ASIENTOS = OrderedDict()
ASIENTOS[1] = a(('206', 5, 0), ('216', 15, 0), ('218', 30, 0), ('300', 40, 0), ('430', 30, 0), ('572', 32, 0),
                ('2806', 0, 1), ('2816', 0, 1.5), ('2818', 0, 5), ('100', 0, 60), ('129', 0, 17), ('170', 0, 30),
                ('520', 0, 10), ('400', 0, 20), ('4750', 0, 2), ('4751', 0, 1), ('4752', 0, 3), ('476', 0, 1.5))
ASIENTOS[2] = a(('600', 230, 0), ('472', 48.3, 0), ('400', 0, 278.3))
ASIENTOS[3] = a(('400', 12.1, 0), ('608', 0, 10), ('472', 0, 2.1))
ASIENTOS[4] = a(('400', 12.1, 0), ('606', 0, 10), ('472', 0, 2.1))
ASIENTOS[5] = a(('430', 435.6, 0), ('700', 0, 360), ('477', 0, 75.6))
ASIENTOS[6] = a(('708', 10, 0), ('477', 2.1, 0), ('430', 0, 12.1))
ASIENTOS[7] = a(('640', 60, 0), ('642', 20, 0), ('4751', 0, 7), ('476', 0, 24), ('572', 0, 49))
ASIENTOS[8] = a(('621', 20, 0), ('472', 4.2, 0), ('4751', 0, 3.8), ('572', 0, 20.4))
ASIENTOS[9] = a(('628', 10, 0), ('472', 2.1, 0), ('572', 0, 12.1))
ASIENTOS[10] = a(('625', 2, 0), ('572', 0, 2))
ASIENTOS[11] = a(('572', 413.5, 0), ('430', 0, 413.5))
ASIENTOS[12] = a(('400', 249.1, 0), ('572', 0, 249.1))
ASIENTOS[13] = a(('476', 23.5, 0), ('572', 0, 23.5))
ASIENTOS[14] = a(('4751', 9.1, 0), ('572', 0, 9.1))
ASIENTOS[15] = a(('4750', 2, 0), ('572', 0, 2))
ASIENTOS[16] = a(('4752', 3, 0), ('572', 0, 3))
ASIENTOS[17] = a(('681', 0.2, 0), ('2816', 0, 0.2))
ASIENTOS[18] = a(('572', 2.42, 0), ('2816', 0.6, 0), ('671', 1.4, 0), ('216', 0, 4), ('477', 0, 0.42))
ASIENTOS[19] = a(('217', 10, 0), ('472', 2.1, 0), ('523', 0, 12.1))
ASIENTOS[20] = a(('523', 12.1, 0), ('572', 0, 12.1))
ASIENTOS[21] = a(('680', 1, 0), ('681', 7.1, 0), ('2806', 0, 1), ('2816', 0, 1.1), ('2817', 0, 1), ('2818', 0, 5))
ASIENTOS[22] = a(('520', 10, 0), ('662', 2, 0), ('572', 0, 12))
ASIENTOS[23] = a(('170', 10, 0), ('520', 0, 10))
ASIENTOS[24] = a(('129', 17, 0), ('112', 0, 1.7), ('113', 0, 5.3), ('526', 0, 10))
ASIENTOS[25] = a(('526', 10, 0), ('4751', 0, 1.9), ('572', 0, 8.1))
ASIENTOS[26] = a(('4751', 1.9, 0), ('572', 0, 1.9))
ASIENTOS[27] = a(('436', 2.42, 0), ('430', 0, 2.42))
ASIENTOS[28] = a(('694', 2, 0), ('490', 0, 2))
# --- Ajustes de cierre (tanda 5) ---
ASIENTOS[29] = a(('477', 55, 0), ('472', 0, 39), ('4750', 0, 16))           # liquidaciones de IVA 1T-3T
ASIENTOS[30] = a(('4750', 16, 0), ('572', 0, 16))                           # pagos de IVA 1T-3T
ASIENTOS[31] = a(('477', 18.92, 0), ('472', 0, 13.5), ('4750', 0, 5.42))    # liquidación del 4T
ASIENTOS[32] = a(('473', 1.08, 0), ('572', 0, 1.08))                        # pagos fraccionados del IS
ASIENTOS[33] = a(('610', 40, 0), ('300', 0, 40), ('300', 34.7, 0), ('610', 0, 34.7))  # existencias
ASIENTOS[34] = a(('480', 1, 0), ('625', 0, 1))                              # seguro pagado por anticipado
ASIENTOS[35] = a(('6300', 1.5, 0), ('473', 0, 1.08), ('4752', 0, 0.42))     # impuesto sobre beneficios


def saldos(hasta):
    s = OrderedDict()
    for n, asiento in ASIENTOS.items():
        if n > hasta:
            break
        for c, d, h in asiento:
            s.setdefault(c, [D(0), D(0)])
            s[c][0] += d
            s[c][1] += h
    return s


def comprobar():
    for n, asiento in ASIENTOS.items():
        d = sum(x[1] for x in asiento); h = sum(x[2] for x in asiento)
        assert d == h, f'El asiento {n} no cuadra: {d} != {h}'


def num(x):
    """Cifra en formato del tema: coma decimal y, si hay millares, punto protegido ($1{.}981,14$)."""
    x = x.normalize() if x != x.to_integral() else x.quantize(D(1))
    t = f'{x:f}'
    ent, _, dec = t.partition('.')
    if len(ent) > 3:
        ent = ent[:-3] + '{.}' + ent[-3:]
    return '$' + ent + (',' + dec if dec else '') + '$'


def nombre_corto(c):
    return (NOMBRES[c].replace('Hacienda Pública', 'HP').replace('Organismos de la Seguridad Social', 'Org. Seg. Social')
            .replace('Amortización acumulada', 'Amort. acumulada').replace('por operaciones comerciales', 'comerciales')
            .replace('procesos de información', 'proc. de información'))


def latex_sumas_y_saldos(hasta=35):
    s = saldos(hasta)
    filas = []
    td = th = sd = sa = D(0)
    for c in sorted(s, key=lambda c: (c[0], c)):
        d, h = s[c]
        dif = d - h
        td += d; th += h
        sd += dif if dif > 0 else 0; sa += -dif if dif < 0 else 0
        filas.append(f'({c}) & \\raggedright {nombre_corto(c)} & {num(d)} & {num(h)} & '
                     f'{num(dif) if dif > 0 else ""} & {num(-dif) if dif < 0 else ""} \\tabularnewline')
    filas.append(f' & \\textbf{{Total}} & {num(td)} & {num(th)} & {num(sd)} & {num(sa)} \\tabularnewline')
    return '\n'.join(filas)


if __name__ == '__main__':
    import sys
    comprobar()
    if '--latex' in sys.argv:
        print(latex_sumas_y_saldos())
        sys.exit()
    s = saldos(35)
    orden = sorted(s, key=lambda c: (c[0], c))
    td = th = sd = sa = D(0)
    print(f'{"Cuenta":<6} {"Nombre":<62} {"Sum. debe":>9} {"Sum. haber":>10} {"S. deudor":>9} {"S. acreedor":>11}')
    for c in orden:
        d, h = s[c]
        dif = d - h
        td += d; th += h
        if dif > 0: sd += dif
        else: sa += -dif
        print(f'{c:<6} {NOMBRES.get(c, "?"):<62} {d:>9} {h:>10} {dif if dif > 0 else "":>9} {-dif if dif < 0 else "":>11}')
    print(f'{"":<6} {"TOTAL":<62} {td:>9} {th:>10} {sd:>9} {sa:>11}')
    gastos = {c: s[c][0] - s[c][1] for c in orden if c[0] in '67'}
    resultado = -sum(gastos.values())
    print('Resultado del ejercicio:', resultado)
    print('Bancos:', s['572'][0] - s['572'][1])
