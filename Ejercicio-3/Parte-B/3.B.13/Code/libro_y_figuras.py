# Libro de datos del tema (Code/datos_3B13.xlsx) y figuras con datos del anexo III (anx_contrapartes, anx_lineas_swap_uso,
# anx_volumen, anx_pares, anx_monedas, anx_plazas y anx_liquidacion). Fuentes: Banco de Pagos Internacionales (BPI), encuesta trienal del
# volumen de divisas y derivados extrabursátiles (conjunto WS_DER_OTC_TOV), saldos semestrales de los derivados
# extrabursátiles (WS_OTC_DERIV2) y volumen de los derivados negociados en bolsa (WS_XTD_DERIV), descargas masivas de
# data.bis.org; saldo semanal de las líneas swap de la Reserva Federal (serie SWPT de FRED, Banco de la Reserva Federal de
# San Luis); y exportaciones mundiales de bienes y servicios (Banco Mundial, indicador NE.EXP.GNFS.CD).
# Uso, desde la carpeta del tema:  python3 -I Code/libro_y_figuras.py [carpeta …]
#   Las carpetas deben contener, en ellas o en subcarpetas, WS_DER_OTC_TOV_csv_flat.csv, WS_OTC_DERIV2_csv_flat.csv,
#   WS_XTD_DERIV_csv_flat.csv, swpt.csv y exportaciones.json. Sin carpeta, los descarga en una carpeta temporal (unos 18 MB
#   comprimidos y 920 MB sin comprimir; el CSV del volumen se lee en un par de minutos).
#   Después, para cada figura:  bash Code/generar_figura.sh <nombre>
# Descarga usada en el tema: 04/11/2026 (encuesta trienal hasta abril de 2025; saldos hasta diciembre de 2025; bolsa hasta
# junio de 2026; SWPT hasta el 28/10/2026; exportaciones hasta 2025). Unidades: el BPI y FRED publican millones de dólares y
# el Banco Mundial, dólares; aquí, miles de millones de dólares (volumen y líneas swap) o billones (saldos y exportaciones).

import collections, csv, glob, json, os, sys, tempfile, urllib.request, zipfile

sys.path.insert(0, "/Users/marceloortega/TCEE/main/herramientas")
from xlsx_simple import escribir_xlsx

TEMA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL_TOV = "https://data.bis.org/static/bulk/WS_DER_OTC_TOV_csv_flat.zip"
URL_OTC = "https://data.bis.org/static/bulk/WS_OTC_DERIV2_csv_flat.zip"
URL_XTD = "https://data.bis.org/static/bulk/WS_XTD_DERIV_csv_flat.zip"
URL_SWPT = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=SWPT"
URL_WDI = "https://api.worldbank.org/v2/country/WLD/indicator/NE.EXP.GNFS.CD?format=json&per_page=200"
FECHA_DESCARGA = "04/11/2026"
ANIOS = [str(a) for a in range(1989, 2026, 3)]
DIAS_HABILES = 250
# Miembros actuales de la Unión Europea que declaran a la encuesta (Croacia y Chipre no declaran) y miembros de la zona del
# euro en abril de 2025 que declaran (Bulgaria entró en 2026).
UE = ["AT", "BE", "BG", "CZ", "DE", "DK", "EE", "ES", "FI", "FR", "GR", "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL",
      "PT", "RO", "SE", "SI", "SK"]
ZONA_EURO = ["AT", "BE", "DE", "EE", "ES", "FI", "FR", "GR", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PT", "SI", "SK"]

INSTR = {"A": "Todos", "B": "Contado", "E": "Plazo simple", "G": "Contratos a plazo sin entrega (dentro del plazo simple)",
         "H": "FX swaps", "I": "Swaps de divisas", "R": "Opciones", "Z": "Otros instrumentos"}
SECTOR = {"A": "Todas", "B": "Intermediarios declarantes", "C": "Otras instituciones financieras",
          "D": "Bancos no declarantes", "E": "Inversores institucionales",
          "F": "Fondos de cobertura y empresas de negociación por cuenta propia", "G": "Sector oficial",
          "P": "Otras instituciones financieras residuales", "H": "Sin distribuir", "U": "Clientes no financieros",
          "V": "Pro memoria: con corretaje principal", "W": "Pro memoria: de origen minorista"}
MONEDA = {"USD": "Dólar estadounidense", "EUR": "Euro", "JPY": "Yen", "GBP": "Libra esterlina", "CNY": "Renminbi",
          "AUD": "Dólar australiano", "CAD": "Dólar canadiense", "CHF": "Franco suizo", "HKD": "Dólar de Hong Kong",
          "SGD": "Dólar de Singapur", "SEK": "Corona sueca", "KRW": "Won surcoreano", "NOK": "Corona noruega",
          "NZD": "Dólar neozelandés", "INR": "Rupia india", "MXN": "Peso mexicano", "DEM": "Marco alemán",
          "FRF": "Franco francés", "XEU": "Ecu", "ITL": "Lira italiana", "NLG": "Florín neerlandés"}
PAIS = {"AE": "Emiratos Árabes Unidos", "AR": "Argentina", "AT": "Austria", "AU": "Australia", "BE": "Bélgica",
        "BG": "Bulgaria", "BH": "Baréin", "BR": "Brasil", "CA": "Canadá", "CH": "Suiza", "CL": "Chile", "CN": "China",
        "CO": "Colombia", "CZ": "Chequia", "DE": "Alemania", "DK": "Dinamarca", "EE": "Estonia", "ES": "España",
        "FI": "Finlandia", "FR": "Francia", "GB": "Reino Unido", "GR": "Grecia", "HK": "Hong Kong", "HU": "Hungría",
        "ID": "Indonesia", "IE": "Irlanda", "IL": "Israel", "IN": "India", "IT": "Italia", "JP": "Japón", "KR": "Corea",
        "LT": "Lituania", "LU": "Luxemburgo", "LV": "Letonia", "MT": "Malta", "MX": "México", "MY": "Malasia",
        "NL": "Países Bajos", "NO": "Noruega", "NZ": "Nueva Zelanda", "PE": "Perú", "PH": "Filipinas", "PL": "Polonia",
        "PT": "Portugal", "RO": "Rumanía", "RU": "Rusia", "SA": "Arabia Saudí", "SE": "Suecia", "SG": "Singapur",
        "SI": "Eslovenia", "SK": "Eslovaquia", "TH": "Tailandia", "TR": "Turquía", "TW": "Taipéi Chino",
        "US": "Estados Unidos", "ZA": "Sudáfrica"}
PLAZO = {"3": "Un día", "4": "Más de un día y menos de siete", "G": "Siete días o menos", "H": "Más de siete días y hasta un mes",
         "J": "Más de un mes y hasta tres", "V": "Más de tres meses y hasta seis", "2": "Más de seis meses",
         "P": "Más de siete días y hasta un año", "W": "Más de un año"}
PRIORIDAD = ["EUR", "GBP", "AUD", "NZD", "USD", "CAD", "CHF", "JPY"]
# Liquidación (dimensión DER_RATING del volumen). 2022: volumen de abril por método de liquidación; 2025: obligaciones de
# pago brutas liquidadas en abril, con preguntas nuevas que no son comparables con las de 2022.
LIQ_2022 = {"K": "Volumen que se liquida con dos pagos (contado y plazo)", "L": "Volumen que se liquida con cuatro pagos (swaps)",
            "J": "Volumen que se liquida con un solo pago (sin entrega)", "O": "Con protección: pago contra pago y mismo liquidador sin exposición",
            "P": "Por CLS (pago contra pago)", "Q": "Por otros sistemas de pago contra pago",
            "R": "Mismo liquidador o en la propia entidad, sin exposición", "S": "Sin pago contra pago",
            "T": "Mismo liquidador o en la propia entidad, con exposición"}
LIQ_2025 = {"2": "Obligaciones de pago brutas liquidadas", "3": "Por sistemas de pago contra pago",
            "4": "Sujetas a neteo previo (importe bruto)", "5": "Importe neto tras el neteo",
            "7": "Dentro del grupo: entre sucursales", "8": "Dentro del grupo: entre filiales",
            "9": "En cuentas en que el intermediario controla el momento del pago",
            "C": "Liquidación bruta bilateral", "G": "Bruta bilateral pese a poder liquidarse con pago contra pago",
            "U": "Bruta bilateral por no poder liquidarse con pago contra pago",
            "V": "No admitidas: par de monedas", "W": "No admitidas: tipo de operación",
            "X": "No admitidas: la contraparte no es miembro", "Y": "Fallidas (no liquidadas en la fecha prevista)"}
DIMS = ["DER_INSTR:Instrument", "DER_REP_CTY:Reporting country", "DER_SECTOR_CPY:Counterparty sector",
        "DER_CPC:Counterparty country", "DER_CURR_LEG1:Currency leg 1", "DER_CURR_LEG2:Currency leg 2",
        "DER_ISSUE_MAT:Maturity", "DER_RATING:Rating (outstanding) or settlement (FX turnover)",
        "DER_EX_METHOD:Execution method", "DER_BASIS:Basis"]


def descargar(carpeta):
    for url, nombre in ((URL_TOV, "tov.zip"), (URL_OTC, "otc.zip"), (URL_XTD, "xtd.zip")):
        destino = os.path.join(carpeta, nombre)
        urllib.request.urlretrieve(url, destino)
        with zipfile.ZipFile(destino) as z:
            z.extractall(carpeta)
    urllib.request.urlretrieve(URL_SWPT, os.path.join(carpeta, "swpt.csv"))
    urllib.request.urlretrieve(URL_WDI, os.path.join(carpeta, "exportaciones.json"))


def buscar(carpetas, patron):
    for c in carpetas:
        hallados = glob.glob(os.path.join(c, "**", patron), recursive=True)
        if hallados:
            return hallados[0]
    raise FileNotFoundError(patron)


def codigo(fila, columna):
    return fila[columna].split(":")[0].strip()


def leer_tov(ruta):
    """Volumen de divisas de la encuesta trienal en los años de encuesta, con todas sus dimensiones: instrumento, país
    declarante, contraparte, país de la contraparte, monedas, plazo, liquidación, método de ejecución y base."""
    datos = collections.defaultdict(dict)
    with open(ruta, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if codigo(r, "DER_RISK:Risk category") != "B":
                continue
            p, v = r["TIME_PERIOD:Time period or range"], r["OBS_VALUE:Observation Value"]
            if p not in ANIOS or v in ("", "NaN"):
                continue
            datos[tuple(codigo(r, c) for c in DIMS)][p] = float(v) / 1e3
    return datos


def leer_otc(ruta):
    """Saldos vivos semestrales de los derivados de divisas (importe nocional y valor de mercado bruto): todos los países
    declarantes, contrapartes, monedas y plazos, base neta-neta."""
    filtro = {"DER_RISK:Risk category": "B", "DER_REP_CTY:Reporting country": "5J", "DER_CPC:Counterparty country": "5J",
              "DER_SECTOR_CPY:Counterparty sector": "A", "DER_CURR_LEG1:Currency leg 1": "TO1",
              "DER_CURR_LEG2:Currency leg 2": "TO1", "DER_ISSUE_MAT:Maturity": "A", "DER_BASIS:Basis": "C",
              "DER_RATING:Rating (outstanding) or settlement (FX turnover)": "A", "DER_EX_METHOD:Execution method": "3"}
    datos = collections.defaultdict(dict)
    with open(ruta, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if any(codigo(r, c) != v for c, v in filtro.items()):
                continue
            v = r["OBS_VALUE:Observation Value"]
            if v in ("", "NaN"):
                continue
            clave = (codigo(r, "DER_TYPE:Measure"), codigo(r, "DER_INSTR:Instrument"))
            datos[clave][r["TIME_PERIOD:Time period or range"]] = float(v) / 1e6
    return datos


def leer_xtd(ruta):
    """Volumen de los futuros y opciones de divisas negociados en bolsa: media diaria anual, todas las bolsas y monedas."""
    datos = collections.defaultdict(dict)
    with open(ruta, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if codigo(r, "OD_RISK_CAT:Risk category") != "B" or codigo(r, "FREQ:Frequency") != "A":
                continue
            if codigo(r, "XD_EXCHANGE:Location of trade (Exchange or country)") != "8A":
                continue
            if codigo(r, "OD_TYPE:Measure") != "U" or codigo(r, "ISSUE_CUR:Issue currency") != "TO1":
                continue
            try:
                datos[codigo(r, "OD_INSTR:Instrument")][r["TIME_PERIOD:Time period or range"]] = float(r["OBS_VALUE:Observation Status"]) / 1e3
            except ValueError:
                pass
    return datos


def leer_swpt(ruta):
    with open(ruta, newline="", encoding="utf-8") as f:
        return [(r["observation_date"], float(r["SWPT"]) / 1e3) for r in csv.DictReader(f) if r["SWPT"] not in ("", ".")]


def leer_wdi(ruta):
    filas = json.load(open(ruta, encoding="utf-8"))[1]
    return {r["date"]: r["value"] / 1e12 for r in filas if r["value"]}


def coma(v, dec=1):
    return f"{v:.{dec}f}".replace(".", "{,}")


def par(a, b):
    """Nombre del par con el convenio de mercado (la moneda de mayor prioridad, delante)."""
    ra = PRIORIDAD.index(a) if a in PRIORIDAD else len(PRIORIDAD)
    rb = PRIORIDAD.index(b) if b in PRIORIDAD else len(PRIORIDAD)
    return f"{a}/{b}" if ra <= rb else f"{b}/{a}"


def repartir(etiquetas, hueco):
    """Separa verticalmente los rótulos del final de las líneas para que no se monten: [(y, texto)] -> [(y', texto)]."""
    orden = sorted(etiquetas, key=lambda e: e[0])
    for i in range(1, len(orden)):
        if orden[i][0] - orden[i - 1][0] < hueco:
            orden[i] = (orden[i - 1][0] + hueco, orden[i][1])
    return orden


def main():
    carpetas = sys.argv[1:] or [tempfile.mkdtemp()]
    if len(sys.argv) == 1:
        descargar(carpetas[0])
    vol = leer_tov(buscar(carpetas, "WS_DER_OTC_TOV*.csv"))
    otc = leer_otc(buscar(carpetas, "WS_OTC_DERIV2*.csv"))
    xtd = leer_xtd(buscar(carpetas, "WS_XTD_DERIV*.csv"))
    swpt = leer_swpt(buscar(carpetas, "swpt.csv"))
    exp = leer_wdi(buscar(carpetas, "exportaciones.json"))

    def s(ins="A", rep="5J", sec="A", cpc="5J", l1="TO1", l2="TO1", mat="A", rat="A", ex="3", bas="C"):
        return vol.get((ins, rep, sec, cpc, l1, l2, mat, rat, ex, bas), {})

    tot, tot_ng = s(), s(bas="B")
    cuota = lambda sec, p: 100 * s(sec=sec)[p] / tot[p]
    otras = lambda p: s(sec="P")[p] + s(sec="H")[p]
    paises = sorted({k[1] for k in vol if k[1] != "5J" and k[0] == "A" and k[9] == "B" and k[4] == "TO1"})
    suma = lambda lista, **kw: {p: sum(s(rep=c, bas="B", **kw).get(p, 0) for c in lista) for p in ANIOS}
    pares = {(k[4], k[5]): ser for k, ser in vol.items() if k[0] == "A" and k[1] == "5J" and k[2] == "A" and k[3] == "5J"
             and k[6:] == ("A", "A", "3", "C") and "TO1" not in (k[4], k[5]) and k[4] < k[5]}

    # ---------- Indicadores (formato largo) ----------
    filas = [["Conjunto", "Medida", "Instrumento", "Contraparte", "Moneda o par", "Plaza", "Plazo", "Periodo", "Fecha",
              "Valor", "Unidad", "Fuente", "Tratamiento", "Figura"]]
    F = lambda *c: filas.append(list(c))
    MB, PCT = "miles de millones de dólares", "% del total"
    for (ins, sec), clave in sorted({(k[0], k[2]): k for k in vol if k[1] == "5J" and k[3] == "5J" and k[4:] == ("TO1", "TO1", "A", "A", "3", "C")}.items()):
        if ins not in INSTR or sec not in SECTOR or (ins != "A" and sec != "A"):
            continue
        fig = ("anx_contrapartes" if ins == "A" and sec in ("B", "C", "U", "D", "E", "F", "G", "P", "H")
               else "anx_volumen" if sec == "A" and ins in ("A", "B", "E", "H", "I", "R", "Z") else "texto")
        for p, v in sorted(vol[clave].items()):
            F("Volumen de divisas", "Media diaria en abril", INSTR[ins], SECTOR[sec], "Todas", "Mundo", "Todos", p, f"{p}-04",
              round(v, 1), MB, "BPI-TOV", "T1", fig)
            F("Volumen de divisas", "Cuota en el volumen total", INSTR[ins], SECTOR[sec], "Todas", "Mundo", "Todos", p,
              f"{p}-04", round(100 * v / tot[p], 2), PCT, "BPI-TOV", "T2", fig)
    for bas, nombre in (("A", "bruta-bruta"), ("B", "neta-bruta"), ("C", "neta-neta")):
        for p, v in sorted(s(bas=bas).items()):
            F("Volumen de divisas", f"Media diaria en abril, base {nombre}", "Todos", "Todas", "Todas", "Mundo", "Todos", p,
              f"{p}-04", round(v, 1), MB, "BPI-TOV", "T1", "texto")
    for cpc, nombre in (("1E", "Locales (residentes)"), ("5Z", "Transfronterizas (no residentes)")):
        for p, v in sorted(s(cpc=cpc).items()):
            F("Volumen de divisas", "Cuota en el volumen total", "Todos", f"Todas: {nombre}", "Todas", "Mundo", "Todos", p,
              f"{p}-04", round(100 * v / tot[p], 2), PCT, "BPI-TOV", "T2", "texto")
    for ins in ("E", "H"):
        for mat in PLAZO:
            for p, v in sorted(s(ins=ins, mat=mat).items()):
                F("Volumen de divisas", "Cuota en el volumen del instrumento", INSTR[ins], "Todas", "Todas", "Mundo",
                  PLAZO[mat], p, f"{p}-04", round(100 * v / s(ins=ins)[p], 2), "% del instrumento", "BPI-TOV", "T10", "texto")
    for mon in MONEDA:
        for p, v in sorted(s(l1=mon).items()):
            fig = "anx_monedas" if mon in ("USD", "EUR", "JPY", "GBP", "CNY", "DEM") else "texto"
            F("Volumen de divisas", "Media diaria en abril", "Todos", "Todas", MONEDA[mon], "Mundo", "Todos", p, f"{p}-04",
              round(v, 1), MB, "BPI-TOV", "T1", fig)
            F("Volumen de divisas", "Cuota de la moneda (las cuotas suman 200)", "Todos", "Todas", MONEDA[mon], "Mundo",
              "Todos", p, f"{p}-04", round(100 * v / tot[p], 2), PCT, "BPI-TOV", "T4", fig)
    top_pares = sorted(pares, key=lambda k: -pares[k].get("2025", 0))[:16]
    for a, b in top_pares:
        for p, v in sorted(pares[(a, b)].items()):
            fig = "anx_pares" if p == "2025" and top_pares.index((a, b)) < 12 else "texto"
            F("Volumen de divisas", "Cuota del par en el volumen total", "Todos", "Todas", par(a, b), "Mundo", "Todos", p,
              f"{p}-04", round(100 * v / tot[p], 2), PCT, "BPI-TOV", "T2", fig)
    for c in paises:
        for p, v in sorted(s(rep=c, bas="B").items()):
            fig = "anx_plazas" if c in ("GB", "US", "SG", "HK", "JP") else "texto"
            F("Volumen de divisas", "Cuota de la plaza (base neta-bruta)", "Todos", "Todas", "Todas", PAIS.get(c, c), "Todos",
              p, f"{p}-04", round(100 * v / tot_ng[p], 2), "% del total neto-bruto", "BPI-TOV", "T5", fig)
    for nombre, lista in (("Unión Europea (miembros actuales que declaran)", UE), ("Zona del euro (miembros de 2025 que declaran)", ZONA_EURO)):
        for p, v in sorted(suma(lista).items()):
            F("Volumen de divisas", "Cuota de la plaza (base neta-bruta)", "Todos", "Todas", "Todas", nombre, "Todos", p,
              f"{p}-04", round(100 * v / tot_ng[p], 2), "% del total neto-bruto", "BPI-TOV", "T5",
              "anx_plazas" if lista is UE else "texto")
    reparto = {}
    for mon in ("USD", "EUR", "JPY", "GBP", "CNY"):
        total_m = suma(paises, l1=mon)
        reparto[mon] = {c: 100 * s(rep=c, bas="B", l1=mon).get("2025", 0) / total_m["2025"] for c in paises}
        reparto[mon]["zona del euro"] = sum(reparto[mon][c] for c in ZONA_EURO if c in reparto[mon])
        for c, v in sorted(reparto[mon].items(), key=lambda x: -x[1])[:8]:
            F("Volumen de divisas", "Cuota de la plaza en el volumen de la moneda (base neta-bruta)", "Todos", "Todas",
              MONEDA[mon], PAIS.get(c, c), "Todos", "2025", "2025-04", round(v, 2), "% del volumen de la moneda", "BPI-TOV",
              "T9", "anx_plazas")
    for p in ANIOS:
        F("Volumen de divisas y comercio", "Volumen anual de divisas entre exportaciones mundiales", "Todos", "Todas", "Todas",
          "Mundo", "Todos", p, p, round(tot[p] * DIAS_HABILES / 1e3 / exp[p], 1), "veces", "BPI-TOV y BM-WDI", "T6", "b3_comercio")
    F("Volumen de divisas y comercio", "Volumen anual con clientes no financieros entre exportaciones mundiales", "Todos",
      SECTOR["U"], "Todas", "Mundo", "Todos", "2025", "2025", round(s(sec="U")["2025"] * DIAS_HABILES / 1e3 / exp["2025"], 1),
      "veces", "BPI-TOV y BM-WDI", "T6", "texto")
    for p, v in sorted(exp.items()):
        if p >= "1989":
            F("Comercio mundial", "Exportaciones de bienes y servicios", "", "", "", "Mundo", "", p, p, round(v, 2),
              "billones de dólares", "BM-WDI", "T11", "texto")
    OTC_I = {"A": "Todos", "D": "Plazo simple y FX swaps", "I": "Swaps de divisas", "R": "Opciones"}
    for (med, ins), ser in sorted(otc.items()):
        if med in ("A", "D") and ins in OTC_I:
            for p, v in sorted(ser.items()):
                F("Saldos de derivados de divisas", "Importe nocional" if med == "A" else "Valor de mercado bruto", OTC_I[ins],
                  "Todas", "Todas", "Mundo", "Todos", p, p, round(v, 2), "billones de dólares", "BPI-OTC", "T7", "texto")
    XTD_I = {"A": "Futuros y opciones", "T": "Futuros", "H": "Opciones"}
    for ins, ser in sorted(xtd.items()):
        if ins in XTD_I:
            for p, v in sorted(ser.items()):
                F("Derivados de divisas en bolsa", "Media diaria del año", XTD_I[ins], "Todas", "Todas", "Todas las bolsas",
                  "Todos", p, p, round(v, 1), MB, "BPI-XTD", "T8", "texto")
    entregable22 = s(rat="K")["2022"] + s(rat="L")["2022"]
    for cod, nombre in LIQ_2022.items():
        v = s(rat=cod)["2022"]
        F("Liquidación de divisas, 2022", "Volumen de abril por método de liquidación", "Todos", "Todas", "Todas", "Mundo",
          "Todos", "2022", "2022-04", round(v, 1), MB, "BPI-TOV", "T12", "texto")
        F("Liquidación de divisas, 2022", "Cuota en el volumen entregable", "Todos", "Todas", nombre, "Mundo", "Todos", "2022",
          "2022-04", round(100 * v / entregable22, 2), "% del volumen entregable", "BPI-TOV", "T12", "texto")
    oblig25 = s(rat="2")["2025"]
    for cod, nombre in LIQ_2025.items():
        v = s(rat=cod)["2025"]
        fig = "anx_liquidacion" if cod in ("3", "4", "7", "8", "9", "C") else "texto"
        F("Liquidación de divisas, 2025", "Obligaciones de pago brutas liquidadas en abril", "Todos", "Todas", nombre, "Mundo",
          "Todos", "2025", "2025-04", round(v, 1), MB, "BPI-TOV", "T13", fig)
        F("Liquidación de divisas, 2025", "Cuota en las obligaciones de pago brutas", "Todos", "Todas", nombre, "Mundo",
          "Todos", "2025", "2025-04", round(100 * v / oblig25, 2), "% de las obligaciones", "BPI-TOV", "T13", fig)
    for d, v in swpt:
        if d >= "2007-01-01":
            F("Líneas swap de la Reserva Federal", "Saldo vivo del miércoles", "Swaps de liquidez entre bancos centrales",
              "Bancos centrales extranjeros", "Dólar estadounidense", "Estados Unidos", "Todos", d[:7], d, round(v, 3), MB,
              "FRED-SWPT", "T3", "anx_lineas_swap_uso")

    # ---------- Cifras citadas en el texto ----------
    pico = lambda desde, hasta: max(((d, v) for d, v in swpt if desde <= d <= hasta), key=lambda x: x[1])
    p08, p12, p20 = pico("2008-01-01", "2009-12-31"), pico("2011-01-01", "2012-12-31"), pico("2020-01-01", "2020-12-31")
    cifras = [["Cifra", "Valor", "Unidad", "Periodo", "Fuente", "Tratamiento", "Apartado"]]
    C = lambda *c: cifras.append(list(c))
    for p in ("1998", "2019", "2022", "2025"):
        for sec in ("B", "C", "U"):
            C(f"Cuota: {SECTOR[sec]}", round(cuota(sec, p), 1), "%", p, "BPI-TOV", "T2", "III.1")
    for sec in ("D", "E", "F", "G", "V", "W"):
        C(f"Volumen: {SECTOR[sec]}", round(s(sec=sec)["2025"], 0), MB, "2025", "BPI-TOV", "T1", "III.1-III.4")
        C(f"Cuota: {SECTOR[sec]}", round(cuota(sec, "2025"), 1), "%", "2025", "BPI-TOV", "T2", "III.1-III.4")
    C("Volumen total", round(tot["2025"], 0), MB, "2025", "BPI-TOV", "T1", "III.1, III.6")
    C("Cuota: otras financieras residuales y sin distribuir", round(100 * otras("2025") / tot["2025"], 1), "%", "2025", "BPI-TOV", "T2", "III.1")
    C("Volumen: clientes no financieros", round(s(sec="U")["2025"], 0), MB, "2025", "BPI-TOV", "T1", "III.3, III.6")
    C("Máximo de las líneas swap, 2008-2009", round(p08[1], 0), MB, p08[0], "FRED-SWPT", "T3", "III.4")
    C("Máximo de las líneas swap, 2011-2012", round(p12[1], 0), MB, p12[0], "FRED-SWPT", "T3", "III.4")
    C("Máximo de las líneas swap, 2020", round(p20[1], 0), MB, p20[0], "FRED-SWPT", "T3", "III.4")
    for p in ("1989", "1998", "2001", "2007", "2013", "2016", "2022", "2025"):
        C("Volumen total", round(tot[p], 0), MB, p, "BPI-TOV", "T1", "III.6")
    for a0, a1 in (("1989", "2025"), ("1998", "2001"), ("2004", "2007"), ("2013", "2016"), ("2022", "2025")):
        C(f"Variación del volumen total, {a0}-{a1}", round(100 * (tot[a1] / tot[a0] - 1), 0), "%", a1, "BPI-TOV", "T1", "III.5, III.6")
    C("Volumen total de 2025 entre el de 1989", round(tot["2025"] / tot["1989"], 1), "veces", "2025", "BPI-TOV", "T1", "III.6")
    for bas, nombre in (("A", "bruta-bruta"), ("B", "neta-bruta")):
        C(f"Volumen total, base {nombre}", round(s(bas=bas)["2025"], 0), MB, "2025", "BPI-TOV", "T1", "III.6")
    for ins in ("B", "E", "G", "H", "I", "R"):
        C(f"Cuota: {INSTR[ins]}", round(100 * s(ins=ins)["2025"] / tot["2025"], 1), "%", "2025", "BPI-TOV", "T2", "III.6")
        C(f"Variación 2022-2025: {INSTR[ins]}", round(100 * (s(ins=ins)["2025"] / s(ins=ins)["2022"] - 1), 0), "%", "2025", "BPI-TOV", "T1", "III.6")
    C("Cuota del contado", round(100 * s(ins="B")["1989"] / tot["1989"], 1), "%", "1989", "BPI-TOV", "T2", "III.6")
    C("Cuota del contado", round(100 * s(ins="B")["2022"] / tot["2022"], 1), "%", "2022", "BPI-TOV", "T2", "III.6")
    C("Cuota del plazo simple", round(100 * s(ins="E")["1992"] / tot["1992"], 1), "%", "1992", "BPI-TOV", "T2", "III.6")
    for ins in ("E", "H"):
        for mat in ("3", "G", "2"):
            C(f"{INSTR[ins]} a plazo de {PLAZO[mat].lower()}", round(100 * s(ins=ins, mat=mat)["2025"] / s(ins=ins)["2025"], 1),
              "% del instrumento", "2025", "BPI-TOV", "T10", "III.6")
    C("FX swaps a siete días o menos", round(100 * s(ins="H", mat="G")["2025"] / tot["2025"], 1), "% del total", "2025", "BPI-TOV", "T2", "III.6")
    C("FX swaps a un día", round(100 * s(ins="H", mat="3")["2025"] / tot["2025"], 1), "% del total", "2025", "BPI-TOV", "T2", "III.6")
    for p in ("1998", "2025"):
        C("Operaciones transfronterizas", round(100 * s(cpc="5Z")[p] / tot[p], 1), "%", p, "BPI-TOV", "T2", "III.6")
    for p in ("1989", "2001", "2025"):
        C("Volumen anual entre exportaciones mundiales", round(tot[p] * DIAS_HABILES / 1e3 / exp[p], 0), "veces", p,
          "BPI-TOV y BM-WDI", "T6", "III.6")
    C("Exportaciones mundiales de bienes y servicios", round(exp["2025"], 1), "billones de dólares", "2025", "BM-WDI", "T11", "III.6")
    C("Volumen anual con clientes no financieros entre exportaciones", round(s(sec="U")["2025"] * DIAS_HABILES / 1e3 / exp["2025"], 1),
      "veces", "2025", "BPI-TOV y BM-WDI", "T6", "III.6")
    for p in ("2025-S1", "2025-S2"):
        for (med, ins) in (("A", "A"), ("A", "D"), ("A", "I"), ("A", "R"), ("D", "A")):
            C(f"{'Importe nocional' if med == 'A' else 'Valor de mercado bruto'}: {OTC_I[ins]}", round(otc[(med, ins)][p], 1),
              "billones de dólares", p, "BPI-OTC", "T7", "III.6")
    for ins in ("A", "T", "H"):
        C(f"Derivados de divisas en bolsa: {XTD_I[ins]}", round(xtd[ins]["2025"], 0), MB, "2025", "BPI-XTD", "T8", "III.6")
    C("Derivados en bolsa entre el volumen extrabursátil", round(100 * xtd["A"]["2025"] / tot["2025"], 1), "%", "2025",
      "BPI-XTD y BPI-TOV", "T8", "III.6")
    for mon in ("USD", "EUR", "JPY", "GBP", "CNY", "DEM"):
        for p in ("1992", "2001", "2010", "2022", "2025"):
            if p in s(l1=mon):
                C(f"Cuota: {MONEDA[mon]}", round(100 * s(l1=mon)[p] / tot[p], 1), "% (suma 200)", p, "BPI-TOV", "T4", "III.7")
    C("Operaciones sin el dólar", round(100 - 100 * s(l1="USD")["2025"] / tot["2025"], 1), "%", "2025", "BPI-TOV", "T4", "III.7")
    for a, b in top_pares[:12]:
        C(f"Cuota del par {par(a, b)}", round(100 * pares[(a, b)]["2025"] / tot["2025"], 1), "%", "2025", "BPI-TOV", "T2", "III.7")
    for c in ("GB", "US", "SG", "HK", "JP", "DE", "CN", "ES"):
        for p in ("2013", "2019", "2022", "2025"):
            C(f"Cuota de la plaza: {PAIS[c]}", round(100 * s(rep=c, bas="B")[p] / tot_ng[p], 2), "% (neta-bruta)", p, "BPI-TOV", "T5", "III.7")
    C("Volumen de la plaza: España", round(s(rep="ES", bas="B")["2025"], 0), MB, "2025", "BPI-TOV", "T1", "III.7")
    for p in ("2019", "2025"):
        C("Cuota de la plaza: Unión Europea", round(100 * suma(UE)[p] / tot_ng[p], 1), "% (neta-bruta)", p, "BPI-TOV", "T5", "III.7")
    C("Cuota de las cuatro primeras plazas", round(sum(100 * s(rep=c, bas="B")["2025"] / tot_ng["2025"] for c in ("GB", "US", "SG", "HK")), 1),
      "% (neta-bruta)", "2025", "BPI-TOV", "T5", "III.7")
    for mon, lista in (("USD", ("GB", "US", "SG", "HK")), ("EUR", ("GB", "US", "zona del euro", "DE")), ("JPY", ("GB", "US", "SG", "JP")),
                       ("GBP", ("GB", "US")), ("CNY", ("HK", "GB", "CN", "SG", "US"))):
        for c in lista:
            C(f"{MONEDA[mon]} negociado en {PAIS.get(c, c)}", round(reparto[mon][c], 1), "% del volumen de la moneda", "2025",
              "BPI-TOV", "T9", "III.7")
    C("Volumen entregable (dos y cuatro pagos)", round(entregable22, 0), MB, "2022", "BPI-TOV", "T12", "III.8")
    for cod in ("P", "Q", "R", "S", "T"):
        C(f"Liquidación 2022: {LIQ_2022[cod]}", round(100 * s(rat=cod)["2022"] / entregable22, 1), "% del volumen entregable",
          "2022", "BPI-TOV", "T12", "III.8")
    C("Liquidación 2022: sin pago contra pago", round(s(rat="S")["2022"], 0), MB, "2022", "BPI-TOV", "T12", "III.8")
    C("Liquidación 2022: neteo previo", round(100 * (entregable22 - s(rat="O")["2022"] - s(rat="S")["2022"]) / entregable22, 1),
      "% del volumen entregable", "2022", "BPI-TOV", "T12", "III.8")
    C("Liquidación 2025: obligaciones de pago brutas", round(oblig25, 0), MB, "2025", "BPI-TOV", "T13", "III.8")
    for cod in ("3", "4", "9", "C", "G", "U", "Y"):
        C(f"Liquidación 2025: {LIQ_2025[cod]}", round(100 * s(rat=cod)["2025"] / oblig25, 2), "% de las obligaciones", "2025",
          "BPI-TOV", "T13", "III.8")
        C(f"Liquidación 2025: {LIQ_2025[cod]}", round(s(rat=cod)["2025"], 0), MB, "2025", "BPI-TOV", "T13", "III.8")
    C("Liquidación 2025: dentro del grupo (sucursales y filiales)", round(100 * (s(rat="7")["2025"] + s(rat="8")["2025"]) / oblig25, 1),
      "% de las obligaciones", "2025", "BPI-TOV", "T13", "III.8")
    C("Liquidación 2025: bruta bilateral que podía usar pago contra pago", round(100 * s(rat="G")["2025"] / s(rat="C")["2025"], 1),
      "% de la bruta bilateral", "2025", "BPI-TOV", "T13", "III.8")
    for cod in ("V", "W", "X"):
        C(f"Liquidación 2025: {LIQ_2025[cod]}", round(100 * s(rat=cod)["2025"] / s(rat="U")["2025"], 1),
          "% de la bruta bilateral no admitida (los motivos se solapan)", "2025", "BPI-TOV", "T13", "III.8")

    leeme = [["Léeme"],
             ["Libro de datos del tema 3.B.13 (mercado de divisas). Una fila por dato, en formato largo; filtrar por conjunto, medida, instrumento, contraparte, moneda o par, plaza, plazo y periodo."],
             ["Hojas: Fuentes (códigos de fuente), Tratamientos (códigos de tratamiento), Indicadores (todas las series usadas en figuras y texto) y Cifras_citadas (las cifras que aparecen en el texto, con su apartado)."],
             [f"Datos descargados el {FECHA_DESCARGA}. Script: Code/libro_y_figuras.py, que vuelve a descargarlos y rehace el libro y las figuras anx_contrapartes, anx_lineas_swap_uso, anx_volumen, anx_pares, anx_monedas, anx_plazas y anx_liquidacion (anexo III) y b3_comercio (cuerpo)."],
             ["Encuesta trienal: abril de cada año de encuesta (1989-2025), media diaria. Saldos de derivados: final de junio (S1) y de diciembre (S2). Derivados en bolsa: media diaria del año. Líneas swap: saldo de cada miércoles. Exportaciones: año natural."]]
    fuentes = [["Código", "Fuente", "Dirección", "Descarga"],
               ["BPI-TOV", "Banco de Pagos Internacionales, encuesta trienal de bancos centrales, volumen de divisas y derivados extrabursátiles (conjunto WS_DER_OTC_TOV)", URL_TOV, FECHA_DESCARGA],
               ["BPI-OTC", "Banco de Pagos Internacionales, estadísticas semestrales de derivados extrabursátiles, saldos vivos (conjunto WS_OTC_DERIV2); todos los países declarantes, base neta-neta", URL_OTC, FECHA_DESCARGA],
               ["BPI-XTD", "Banco de Pagos Internacionales, estadísticas de derivados negociados en bolsa (conjunto WS_XTD_DERIV); todas las bolsas", URL_XTD, FECHA_DESCARGA],
               ["FRED-SWPT", "Junta de Gobernadores de la Reserva Federal, balance de la Reserva Federal (H.4.1): Assets: Other: Central Bank Liquidity Swaps, Wednesday Level (SWPT), a través de FRED", URL_SWPT, FECHA_DESCARGA],
               ["BM-WDI", "Banco Mundial, Indicadores del desarrollo mundial: exportaciones de bienes y servicios (US$ a precios actuales), NE.EXP.GNFS.CD, mundo (WLD)", URL_WDI, FECHA_DESCARGA]]
    trat = [["Código", "Tratamiento"],
            ["T1", "Valor publicado en millones de dólares de media diaria en abril, dividido por mil: miles de millones de dólares. Salvo que se diga otra cosa, base neta-neta: sin la doble contabilización de las operaciones entre intermediarios declarantes del mismo país (neta-bruta) ni de países distintos (neta-neta)."],
            ["T2", "Cuota: volumen de la contraparte, del instrumento o del par dividido por el volumen total del mismo año (base neta-neta), en porcentaje."],
            ["T3", "Saldo publicado en millones de dólares, dividido por mil: miles de millones de dólares."],
            ["T4", "Cuota de una moneda: volumen de las operaciones en que la moneda está en uno de los dos lados dividido por el volumen total del mismo año; como cada operación tiene dos monedas, las cuotas suman 200."],
            ["T5", "Cuota de una plaza: volumen declarado por los intermediarios de la plaza (por la ubicación de la mesa que negocia), en base neta-bruta, dividido por el volumen mundial neto-bruto del mismo año. Unión Europea y zona del euro: suma de los países que declaran."],
            ["T6", f"Volumen anual estimado (media diaria de abril por {DIAS_HABILES} días hábiles) dividido por las exportaciones mundiales de bienes y servicios del mismo año."],
            ["T7", "Saldo vivo publicado en millones de dólares, dividido por un millón: billones de dólares. Importe nocional: valor de referencia de los contratos vivos; valor de mercado bruto: suma de los valores de reposición positivos y del valor absoluto de los negativos."],
            ["T8", "Media diaria anual publicada en millones de dólares, dividida por mil: miles de millones de dólares; todas las bolsas y monedas."],
            ["T9", "Cuota de una plaza en el volumen de una moneda: volumen neto-bruto en esa moneda declarado en la plaza dividido por la suma del de todas las plazas."],
            ["T10", "Cuota de un plazo: volumen del instrumento a ese plazo dividido por el volumen total del instrumento. Desde 2019 los plazos se detallan más (un día, hasta siete días, hasta un mes, tres, seis y más de seis meses)."],
            ["T11", "Valor publicado en dólares corrientes, dividido por un billón: billones de dólares."],
            ["T12", "Liquidación en 2022: volumen de abril por método de liquidación (base neta-neta), en miles de millones de dólares, y su cuota en el volumen entregable, el que se liquida con dos pagos (contado y plazo) o con cuatro (swaps); el neteo previo es la diferencia entre el volumen entregable y el liquidado con y sin pago contra pago."],
            ["T13", "Liquidación en 2025: obligaciones de pago brutas liquidadas en abril, media diaria, según las preguntas nuevas de la encuesta (no comparables con las de 2022); cuota en el total de obligaciones; dentro del grupo es la suma de lo liquidado entre sucursales y entre filiales; los motivos por los que una operación no admitía el pago contra pago se solapan y su cuota se calcula sobre la liquidación bruta bilateral no admitida."]]
    escribir_xlsx(os.path.join(TEMA, "Code", "datos_3B13.xlsx"),
                  [("Léeme", leeme), ("Fuentes", fuentes), ("Tratamientos", trat), ("Indicadores", filas),
                   ("Cifras_citadas", cifras)])

    # ---------- anx_contrapartes ----------
    anios = [p for p in ANIOS if p >= "1998"]
    X = lambda p: (int(p) - 1998) * 0.22
    Y = lambda v: v * 0.05
    linea = lambda sec: " ".join(f"({X(p):.3f},{Y(cuota(sec, p)):.3f})" for p in anios)
    ejes = ("    \\draw[->] (0,0) -- (6.4,0);\n    \\draw[->] (0,0) -- (0,3.55) node[left] {$\\%$};\n"
            + "".join(f"    \\draw (0,{Y(y):.2f}) -- (-0.06,{Y(y):.2f}) node[left] {{${y}$}};\n" for y in (20, 40, 60))
            + "".join(f"    \\draw ({X(str(a)):.2f},0) -- ({X(str(a)):.2f},-0.06) node[below] {{${a}$}};\n" for a in (1998, 2007, 2016, 2025)))
    barras = ""
    comp = [("B", "intermediarios declarantes"), ("D", "bancos no declarantes"), ("E", "inversores institucionales"),
            ("F", "fondos de cobertura y\\\\negociación por cuenta propia"), ("G", "sector oficial"),
            ("PH", "otras financieras"), ("U", "clientes no financieros")]
    for i, (sec, nombre) in enumerate(comp):
        y = 3.0 - i * 0.46
        v = 100 * otras("2025") / tot["2025"] if sec == "PH" else cuota(sec, "2025")
        tono = "black!70" if sec == "B" else "black!25" if sec == "U" else "black!45"
        barras += (f"    \\fill[{tono}] (0,{y - 0.15:.2f}) rectangle ({v * 0.05:.3f},{y + 0.15:.2f});\n"
                   f"    \\node[anchor=east, align=right, font=\\scriptsize] at (-0.06,{y:.2f}) {{{nombre}}};\n"
                   f"    \\node[anchor=west, font=\\scriptsize] at ({v * 0.05:.3f},{y:.2f}) {{${coma(v)}$}};\n")
    fig = (r"""% Figura (Anexo III, «Participantes»): (a) cuota en el volumen de divisas de las operaciones entre intermediarios
% declarantes, con otras instituciones financieras y con clientes no financieros, en abril de cada año de encuesta,
% 1998-2025. (b) Desglose del volumen de abril de 2025 por contraparte, en porcentaje del total; las otras instituciones
% financieras se dividen en bancos no declarantes, inversores institucionales, fondos de cobertura y empresas de
% negociación por cuenta propia, sector oficial y otras (residuales y sin distribuir).
% Fuente: BPI, encuesta trienal, conjunto WS_DER_OTC_TOV, base neta-neta, descarga del """ + FECHA_DESCARGA + r""".
% Datos y tratamientos en Code/datos_3B13.xlsx; generada con Code/libro_y_figuras.py.
% Generar con: bash Code/generar_figura.sh anx_contrapartes
\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]
  % ---------------- (a) Evolución ----------------
  \begin{scope}
    \node[font=\footnotesize\bfseries\boldmath] at (3.0,4.0) {(a) Cuota en el volumen, $1998$-$2025$};
""" + ejes + r"""    \draw[very thick] plot coordinates {""" + linea("B") + r"""};
    \draw[very thick, dashed] plot coordinates {""" + linea("C") + r"""};
    \draw[very thick, dotted] plot coordinates {""" + linea("U") + r"""};
    \node[anchor=west] at (0.15,3.42) {intermediarios declarantes};
    \node[anchor=west, align=left] at (3.55,3.17) {otras instituciones\\financieras};
    \node[anchor=west] at (3.3,0.62) {clientes no financieros};
  \end{scope}
  % ---------------- (b) Desglose de 2025 ----------------
  \begin{scope}[xshift=10.6cm, yshift=0.1cm]
    \node[font=\footnotesize\bfseries\boldmath] at (0.3,3.9) {(b) Desglose de $2025$ ($\%$ del volumen)};
    \draw (0,0.05) -- (0,3.3);
""" + barras + r"""  \end{scope}
\end{tikzpicture}
""")
    open(os.path.join(TEMA, "Img", "anx_contrapartes.tikz"), "w", encoding="utf-8").write(fig)

    # ---------- anx_lineas_swap_uso ----------
    XS = lambda d: (int(d[:4]) + (int(d[5:7]) - 1) / 12 + (int(d[8:10]) - 1) / 365 - 2007) * 0.72
    YS = lambda v: v / 150
    serie = " ".join(f"({XS(d):.3f},{YS(v):.3f})" for d, v in swpt if d >= "2007-01-01")
    mes = {"01": "enero", "02": "febrero", "03": "marzo", "04": "abril", "05": "mayo", "06": "junio", "07": "julio",
           "08": "agosto", "09": "septiembre", "10": "octubre", "11": "noviembre", "12": "diciembre"}
    rot = lambda d, v: f"{mes[d[5:7]]} de ${d[:4]}$: ${v:.0f}$"
    ejes_s = ("  \\draw[->] (0,0) -- (14.3,0);\n  \\draw[->] (0,0) -- (0,4.35);\n"
              + "".join(f"  \\draw (0,{YS(y):.2f}) -- (-0.06,{YS(y):.2f}) node[left] {{${y}$}};\n" for y in (200, 400, 600))
              + "".join(f"  \\draw ({XS(f'{a}-01-01'):.2f},0) -- ({XS(f'{a}-01-01'):.2f},-0.06) node[below] {{${a}$}};\n"
                        for a in (2008, 2012, 2016, 2020, 2024)))
    fig2 = (r"""% Figura (Anexo III, «Bancos centrales»): saldo vivo de las líneas swap de la Reserva Federal con otros bancos centrales,
% cada miércoles, en miles de millones de dólares, de 2007 a 2026, con los máximos de 2008, 2012 y 2020.
% Fuente: Junta de Gobernadores de la Reserva Federal (balance H.4.1), serie SWPT de FRED, descarga del """ + FECHA_DESCARGA + r""".
% Datos y tratamientos en Code/datos_3B13.xlsx; generada con Code/libro_y_figuras.py.
% Generar con: bash Code/generar_figura.sh anx_lineas_swap_uso
\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]
""" + ejes_s + r"""  \node[anchor=south west] at (0.05,4.0) {miles de millones de dólares};
  \draw[thick] plot coordinates {""" + serie + r"""};
  \node[anchor=west] at (""" + f"{XS(p08[0]) + 0.15:.2f},{YS(p08[1]) - 0.1:.2f}" + r""") {""" + rot(*p08) + r"""};
  \node[anchor=south] at (""" + f"{XS(p12[0]):.2f},{YS(p12[1]) + 0.08:.2f}" + r""") {""" + rot(*p12) + r"""};
  \node[anchor=west] at (""" + f"{XS(p20[0]) + 0.15:.2f},{YS(p20[1]) - 0.1:.2f}" + r""") {""" + rot(*p20) + r"""};
\end{tikzpicture}
""")
    open(os.path.join(TEMA, "Img", "anx_lineas_swap_uso.tikz"), "w", encoding="utf-8").write(fig2)

    # ---------- anx_volumen: volumen por instrumento, 1989-2025 ----------
    XV = lambda i: 0.55 + i * 1.06
    YV = lambda v: v / 1000 * 0.48
    capas = [("B", "black!75"), ("E", "black!50"), ("H", "black!25"), ("IRZ", "white")]
    cuerpo = ""
    for i, p in enumerate(ANIOS):
        x0, x1, y = XV(i) - 0.34, XV(i) + 0.34, 0.0
        if p == "1989":
            vb = s(ins="B")[p]
            cuerpo += (f"  \\filldraw[fill=black!75] ({x0:.2f},0) rectangle ({x1:.2f},{YV(vb):.3f});\n"
                       f"  \\draw[dashed] ({x0:.2f},{YV(vb):.3f}) rectangle ({x1:.2f},{YV(tot[p]):.3f});\n")
        else:
            for letras, tono in capas:
                v = sum(s(ins=l).get(p, 0) for l in letras)
                cuerpo += f"  \\filldraw[fill={tono}] ({x0:.2f},{YV(y):.3f}) rectangle ({x1:.2f},{YV(y + v):.3f});\n"
                y += v
        cuerpo += (f"  \\node[above, font=\\scriptsize] at ({XV(i):.2f},{YV(max(y, tot[p])):.3f}) {{${coma(tot[p] / 1000)}$}};\n"
                   f"  \\node[below] at ({XV(i):.2f},0) {{${p}$}};\n")
    leyenda = ""
    for j, (texto, estilo) in enumerate((("contado", "fill=black!75"), ("plazo simple", "fill=black!50"), ("\\textit{FX swaps}", "fill=black!25"),
                                         ("swaps de divisas, opciones y otros", "fill=white"), ("sin desglose ($1989$)", "dashed, fill=white"))):
        yl = 4.55 - j * 0.36
        cuerpo += (f"  \\filldraw[{estilo}] (0.55,{yl - 0.1:.2f}) rectangle (0.85,{yl + 0.1:.2f});\n"
                   f"  \\node[anchor=west] at (0.9,{yl:.2f}) {{{texto}}};\n")
    ejes_v = ("  \\draw (0,0) -- (" + f"{XV(12) + 0.6:.2f}" + ",0);\n  \\draw[->] (0,0) -- (0,5.15);\n"
              + "".join(f"  \\draw (0,{YV(y * 1000):.2f}) -- (-0.06,{YV(y * 1000):.2f}) node[left] {{${y}$}};\n" for y in (2, 4, 6, 8, 10))
              + "  \\node[anchor=south west] at (0.05,5.15) {billones de dólares diarios};\n")
    fig3 = (r"""% Figura (Anexo III, «Tamaño y composición»): volumen medio diario del mercado de divisas en abril de cada año de encuesta,
% 1989-2025, en billones de dólares, por instrumento (contado, plazo simple, FX swaps y el resto: swaps de divisas, opciones
% y otros). En 1989 solo se publica el contado; el resto del volumen de ese año va sin desglose. Encima de cada barra, el total.
% Fuente: BPI, encuesta trienal, conjunto WS_DER_OTC_TOV, base neta-neta, descarga del """ + FECHA_DESCARGA + r""".
% Datos y tratamientos en Code/datos_3B13.xlsx; generada con Code/libro_y_figuras.py.
% Generar con: bash Code/generar_figura.sh anx_volumen
\begin{tikzpicture}[font=\footnotesize]
""" + ejes_v + cuerpo + r"""\end{tikzpicture}
""")
    open(os.path.join(TEMA, "Img", "anx_volumen.tikz"), "w", encoding="utf-8").write(fig3)

    # ---------- anx_pares: los doce pares más negociados en 2025 ----------
    cuerpo = ""
    for i, (a, b) in enumerate(top_pares[:12]):
        c = 100 * pares[(a, b)]["2025"] / tot["2025"]
        y = 4.6 - i * 0.4
        tono = "black!55" if "USD" in (a, b) else "white"
        cuerpo += (f"  \\filldraw[fill={tono}] (0,{y - 0.13:.2f}) rectangle ({c * 0.36:.3f},{y + 0.13:.2f});\n"
                   f"  \\node[anchor=east] at (-0.06,{y:.2f}) {{{par(a, b)}}};\n"
                   f"  \\node[anchor=west] at ({c * 0.36:.3f},{y:.2f}) {{${coma(c)}$}};\n")
    fig4 = (r"""% Figura (Anexo III, «Concentración»): los doce pares de monedas más negociados en abril de 2025, en porcentaje del volumen
% total; en gris oscuro, los pares con el dólar; en blanco, el primero sin él (EUR/GBP, undécimo).
% Fuente: BPI, encuesta trienal, conjunto WS_DER_OTC_TOV, base neta-neta, descarga del """ + FECHA_DESCARGA + r""".
% Datos y tratamientos en Code/datos_3B13.xlsx; generada con Code/libro_y_figuras.py.
% Generar con: bash Code/generar_figura.sh anx_pares
\begin{tikzpicture}[font=\footnotesize]
  \draw (0,0.1) -- (0,4.9);
""" + cuerpo + r"""  \filldraw[fill=black!55] (4.6,2.1) rectangle (4.9,2.3); \node[anchor=west] at (4.95,2.2) {pares con el dólar};
  \filldraw[fill=white] (4.6,1.7) rectangle (4.9,1.9); \node[anchor=west] at (4.95,1.8) {pares sin el dólar};
  \node[anchor=west] at (4.6,1.3) {($\%$ del volumen total)};
\end{tikzpicture}
""")
    open(os.path.join(TEMA, "Img", "anx_pares.tikz"), "w", encoding="utf-8").write(fig4)

    # ---------- anx_monedas: cuota de las principales monedas, 1989-2025 ----------
    XM = lambda p: (int(p) - 1989) * 0.34
    YM = lambda c: c * 0.045
    curva = lambda mon: " ".join(f"({XM(p):.3f},{YM(100 * s(l1=mon)[p] / tot[p]):.3f})" for p in ANIOS if p in s(l1=mon))
    estilos = [("USD", "line width=1.6pt", "dólar"), ("EUR", "very thick", "euro"), ("JPY", "very thick, dashed", "yen"),
               ("GBP", "very thick, dotted", "libra esterlina"), ("CNY", "very thick, dash dot", "renminbi")]
    cuerpo = "".join(f"  \\draw[{e}] plot coordinates {{{curva(m)}}};\n" for m, e, _ in estilos)
    cuerpo += f"  \\draw[very thick, black!45] plot coordinates {{{curva('DEM')}}};\n"
    finales = repartir([(YM(100 * s(l1=m)["2025"] / tot["2025"]), t) for m, _, t in estilos], 0.27)
    cuerpo += "".join(f"  \\node[anchor=west] at ({XM('2025') + 0.1:.2f},{y:.3f}) {{{t}}};\n" for y, t in finales)
    cuerpo += f"  \\node[anchor=south, black!60] at ({XM('1992'):.2f},{YM(100 * s(l1='DEM')['1992'] / tot['1992']) + 0.05:.3f}) {{marco alemán}};\n"
    ejes_m = (f"  \\draw (0,0) -- ({XM('2025') + 0.3:.2f},0);\n  \\draw[->] (0,0) -- (0,4.75) node[left] {{$\\%$}};\n"
              + "".join(f"  \\draw (0,{YM(y):.2f}) -- (-0.06,{YM(y):.2f}) node[left] {{${y}$}};\n" for y in (20, 40, 60, 80, 100))
              + "".join(f"  \\draw ({XM(str(a)):.2f},0) -- ({XM(str(a)):.2f},-0.06) node[below] {{${a}$}};\n" for a in (1989, 1998, 2007, 2016, 2025)))
    fig5 = (r"""% Figura (Anexo III, «Concentración»): cuota de las principales monedas en el volumen del mercado de divisas en abril de
% cada año de encuesta, 1989-2025: dólar, euro (desde 2001), marco alemán (hasta 1998, en gris), yen, libra esterlina y
% renminbi. Como cada operación tiene dos monedas, las cuotas suman 200.
% Fuente: BPI, encuesta trienal, conjunto WS_DER_OTC_TOV, base neta-neta, descarga del """ + FECHA_DESCARGA + r""".
% Datos y tratamientos en Code/datos_3B13.xlsx; generada con Code/libro_y_figuras.py.
% Generar con: bash Code/generar_figura.sh anx_monedas
\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]
""" + ejes_m + cuerpo + r"""\end{tikzpicture}
""")
    open(os.path.join(TEMA, "Img", "anx_monedas.tikz"), "w", encoding="utf-8").write(fig5)

    # ---------- anx_plazas: (a) cuota de las plazas, 1989-2025; (b) dónde se negocia cada moneda, 2025 ----------
    XL = lambda p: (int(p) - 1989) * 0.17
    YL = lambda c: c * 0.085
    def curva_p(serie, desde="1989"):
        return " ".join(f"({XL(p):.3f},{YL(100 * serie[p] / tot_ng[p]):.3f})" for p in ANIOS if serie.get(p) and p >= desde)
    plazas = [("GB", "line width=1.6pt", "Reino Unido"), ("US", "very thick", "Estados Unidos"),
              ("SG", "very thick, dashed", "Singapur"), ("HK", "very thick, dotted", "Hong Kong"),
              ("JP", "very thick, dash dot", "Japón")]
    cuerpo = "".join(f"    \\draw[{e}] plot coordinates {{{curva_p(s(rep=c, bas='B'))}}};\n" for c, e, _ in plazas)
    cuerpo += f"    \\draw[very thick, black!45] plot coordinates {{{curva_p(suma(UE), '1992')}}};\n"
    finales = repartir([(YL(100 * s(rep=c, bas="B")["2025"] / tot_ng["2025"]), t) for c, _, t in plazas]
                       + [(YL(100 * suma(UE)["2025"] / tot_ng["2025"]), "Unión Europea")], 0.27)
    cuerpo += "".join(f"    \\node[anchor=west{', black!60' if t == 'Unión Europea' else ''}] at ({XL('2025') + 0.08:.2f},{y:.3f}) {{{t}}};\n"
                      for y, t in finales)
    ejes_l = (f"    \\draw (0,0) -- ({XL('2025') + 0.2:.2f},0);\n    \\draw[->] (0,0) -- (0,4.1) node[left] {{$\\%$}};\n"
              + "".join(f"    \\draw (0,{YL(y):.2f}) -- (-0.06,{YL(y):.2f}) node[left] {{${y}$}};\n" for y in (10, 20, 30, 40))
              + "".join(f"    \\draw ({XL(str(a)):.2f},0) -- ({XL(str(a)):.2f},-0.06) node[below] {{${a}$}};\n" for a in (1989, 2007, 2025)))
    barras = ""
    monedas = [("USD", "US", "dólar"), ("EUR", "zona del euro", "euro"), ("JPY", "JP", "yen"), ("GBP", "GB", "libra"),
               ("CNY", "CN", "renminbi")]
    for i, (mon, casa, nombre) in enumerate(monedas):
        y = 3.3 - i * 0.72
        vc, vg = reparto[mon][casa], reparto[mon]["GB"]
        barras += (f"    \\node[anchor=east] at (-0.06,{y - 0.13:.2f}) {{{nombre}}};\n"
                   f"    \\fill[black!60] (0,{y - 0.02:.2f}) rectangle ({vc * 0.075:.3f},{y + 0.2:.2f});\n"
                   f"    \\node[anchor=west, font=\\scriptsize] at ({vc * 0.075:.3f},{y + 0.09:.2f}) {{${coma(vc)}$}};\n")
        if mon != "GBP":
            barras += (f"    \\fill[black!22] (0,{y - 0.46:.2f}) rectangle ({vg * 0.075:.3f},{y - 0.24:.2f});\n"
                       f"    \\node[anchor=west, font=\\scriptsize] at ({vg * 0.075:.3f},{y - 0.35:.2f}) {{${coma(vg)}$}};\n")
    fig6 = (r"""% Figura (Anexo III, «Concentración»): (a) cuota de las principales plazas en el volumen del mercado de divisas en abril de
% cada año de encuesta, 1989-2025 (por la ubicación de la mesa que negocia, base neta-bruta), con la de la Unión Europea
% (suma de sus miembros actuales que declaran, en gris, desde 1992: antes no declaraba Alemania). (b) Parte del volumen de
% cada moneda que se negocia en su propio
% país (zona del euro para el euro; Reino Unido para la libra) y en el Reino Unido, en abril de 2025.
% Fuente: BPI, encuesta trienal, conjunto WS_DER_OTC_TOV, base neta-bruta, descarga del """ + FECHA_DESCARGA + r""".
% Datos y tratamientos en Code/datos_3B13.xlsx; generada con Code/libro_y_figuras.py.
% Generar con: bash Code/generar_figura.sh anx_plazas
\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]
  % ---------------- (a) Plazas ----------------
  \begin{scope}
    \node[font=\footnotesize\bfseries\boldmath] at (3.5,4.55) {(a) Cuota de cada plaza, $1989$-$2025$};
""" + ejes_l + cuerpo + r"""  \end{scope}
  % ---------------- (b) Monedas ----------------
  \begin{scope}[xshift=10.55cm]
    \node[font=\footnotesize\bfseries\boldmath] at (1.6,4.55) {(b) Dónde se negocia cada moneda, $2025$};
    \fill[black!60] (-0.2,3.95) rectangle (0.1,4.12); \node[anchor=west] at (0.12,4.03) {en su país};
    \fill[black!22] (1.9,3.95) rectangle (2.2,4.12); \node[anchor=west] at (2.22,4.03) {en el Reino Unido};
    \draw (0,0) -- (0,3.7);
""" + barras + r"""  \end{scope}
\end{tikzpicture}
""")
    open(os.path.join(TEMA, "Img", "anx_plazas.tikz"), "w", encoding="utf-8").write(fig6)

    # ---------- anx_liquidacion: cómo se liquidaron las obligaciones de pago, abril de 2025 ----------
    metodos = [("pago contra pago", ["3"], "black!70"), ("neteo previo", ["4"], "black!35"),
               ("dentro del grupo", ["7", "8"], "black!35"), ("cuentas con control del pago", ["9"], "black!35"),
               ("liquidación bruta bilateral", ["C"], "white")]
    cuerpo = ""
    for i, (nombre, cods, tono) in enumerate(metodos):
        v = sum(s(rat=c)["2025"] for c in cods)
        c = 100 * v / oblig25
        y = 2.6 - i * 0.55
        borde = "very thick" if tono == "white" else ""
        cuerpo += (f"  \\filldraw[fill={tono}{', ' + borde if borde else ''}] (0,{y - 0.17:.2f}) rectangle ({c * 0.2:.3f},{y + 0.17:.2f});\n"
                   f"  \\node[anchor=east] at (-0.08,{y:.2f}) {{{nombre}}};\n"
                   f"  \\node[anchor=west] at ({c * 0.2 + 0.05:.3f},{y:.2f}) {{${coma(c)}\\%$ ($" + coma(v / 1000 + 1e-9) + "$ billones)};\n")
    fig7 = (r"""% Figura (Anexo III, «Riesgos»): obligaciones de pago brutas liquidadas en una media diaria de abril de 2025 (unos 14,2
% billones de dólares), por método de liquidación, en porcentaje del total y en billones de dólares. En gris oscuro, el
% pago contra pago, que elimina el riesgo de liquidación; en gris claro, los métodos que lo reducen sin eliminarlo (neteo
% previo, liquidación dentro del grupo y cuentas en que el intermediario controla el momento del pago); en blanco, la
% liquidación bruta bilateral, expuesta por todo el importe.
% Fuente: BPI, encuesta trienal, conjunto WS_DER_OTC_TOV (preguntas de liquidación de 2025), descarga del """ + FECHA_DESCARGA + r""".
% Datos y tratamientos en Code/datos_3B13.xlsx; generada con Code/libro_y_figuras.py.
% Generar con: bash Code/generar_figura.sh anx_liquidacion
\begin{tikzpicture}[font=\footnotesize]
  \draw (0,0.1) -- (0,2.95);
""" + cuerpo + r"""  \filldraw[fill=black!70] (-3.4,-0.42) rectangle (-3.1,-0.22); \node[anchor=west] at (-3.05,-0.32) {elimina el riesgo};
  \filldraw[fill=black!35] (0.6,-0.42) rectangle (0.9,-0.22); \node[anchor=west] at (0.95,-0.32) {lo reduce};
  \filldraw[fill=white, very thick] (3.4,-0.42) rectangle (3.7,-0.22); \node[anchor=west] at (3.75,-0.32) {expuesta por todo el importe};
\end{tikzpicture}
""")
    open(os.path.join(TEMA, "Img", "anx_liquidacion.tikz"), "w", encoding="utf-8").write(fig7)

    # ---------- b3_comercio (cuerpo, bloque 3): volumen anual de divisas entre exportaciones mundiales, 1989-2025 ----------
    XC = lambda p: (int(p) - 1989) * 0.27
    YC = lambda r: r * 0.055
    pts = [(p, tot[p] * DIAS_HABILES / 1e3 / exp[p]) for p in ANIOS]
    cuerpo = (f"  \\draw[very thick] plot coordinates {{{' '.join(f'({XC(p):.3f},{YC(r):.3f})' for p, r in pts)}}};\n"
              + "".join(f"  \\fill ({XC(p):.3f},{YC(r):.3f}) circle (1.5pt);\n" for p, r in pts)
              + f"  \\node[below right] at ({XC(pts[0][0]) + 0.05:.3f},{YC(pts[0][1]):.3f}) {{${pts[0][1]:.0f}$}};\n"
              + f"  \\node[above] at ({XC(pts[-1][0]):.3f},{YC(pts[-1][1]) + 0.05:.3f}) {{${pts[-1][1]:.0f}$}};\n")
    ejes_c = (f"  \\draw (0,0) -- ({XC('2025') + 0.4:.2f},0);\n  \\draw[->] (0,0) -- (0,4.5) node[left] {{veces}};\n"
              + "".join(f"  \\draw (0,{YC(y):.2f}) -- (-0.06,{YC(y):.2f}) node[left] {{${y}$}};\n" for y in (20, 40, 60))
              + "".join(f"  \\draw ({XC(str(a)):.2f},0) -- ({XC(str(a)):.2f},-0.06) node[below] {{${a}$}};\n"
                        for a in (1989, 1998, 2007, 2016, 2025)))
    fig8 = (r"""% Figura (cuerpo, bloque 3, «Tamaño»): volumen anual del mercado de divisas (media diaria de abril por 250 días hábiles)
% dividido entre las exportaciones mundiales de bienes y servicios del mismo año, en los años de encuesta, 1989-2025.
% Fuente: BPI, encuesta trienal, conjunto WS_DER_OTC_TOV, base neta-neta, y Banco Mundial, NE.EXP.GNFS.CD, descarga del """ + FECHA_DESCARGA + r""".
% Datos y tratamientos en Code/datos_3B13.xlsx (tratamiento T6); generada con Code/libro_y_figuras.py.
% Generar con: bash Code/generar_figura.sh b3_comercio
\begin{tikzpicture}[font=\footnotesize, >={Stealth[length=4pt]}]
""" + ejes_c + cuerpo + r"""\end{tikzpicture}
""")
    open(os.path.join(TEMA, "Img", "b3_comercio.tikz"), "w", encoding="utf-8").write(fig8)

    for fila_c in cifras[1:]:
        if fila_c[6].startswith("III.8"):
            print(fila_c[0], "|", fila_c[1], fila_c[2], "|", fila_c[3])


if __name__ == "__main__":
    main()
