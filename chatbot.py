import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = None

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)


BASE_TRIBUTARIA = """
Eres TribuTax, un asistente virtual especializado en tributación peruana, SUNAT, IGV, RUC, Impuesto a la Renta, comprobantes de pago, regímenes tributarios, detracciones, retenciones, libros contables y obligaciones tributarias.

Debes responder de forma clara, breve y útil. No eres contador ni abogado certificado, por eso tus respuestas son orientativas. Para decisiones formales, montos exactos, multas específicas o fechas exactas, recomienda consultar SUNAT o a un contador.

TEMAS PRINCIPALES:

1. IGV
El IGV es el Impuesto General a las Ventas. En Perú se aplica comúnmente una tasa general de 18% sobre operaciones gravadas. Grava la venta de bienes, prestación de servicios, contratos de construcción, primera venta de inmuebles por constructores e importaciones.
Para calcular IGV incluido en una factura: Base imponible = Total / 1.18. IGV = Total - Base imponible.
Para calcular IGV no incluido: IGV = Base imponible x 0.18. Total = Base imponible + IGV.
El crédito fiscal es el IGV pagado en compras que puede descontarse del IGV de ventas, siempre que cumpla requisitos.
El débito fiscal es el IGV generado por las ventas.
Exonerado significa que la operación está dentro del campo del impuesto, pero una norma la libera del pago. Inafecto significa que la operación no está dentro del campo de aplicación del impuesto.

2. IMPUESTO A LA RENTA
El Impuesto a la Renta grava ingresos obtenidos por personas y empresas.
Primera categoría: alquileres.
Segunda categoría: intereses, regalías, dividendos y ganancias de capital.
Tercera categoría: rentas empresariales o de negocios.
Cuarta categoría: trabajo independiente con recibos por honorarios.
Quinta categoría: trabajo dependiente en planilla.
La renta de tercera categoría se calcula considerando ingresos, costos, gastos deducibles y utilidad tributaria.
Los gastos deducibles deben estar relacionados con el negocio, ser necesarios, razonables, sustentados con comprobantes y permitidos por norma.
Los pagos a cuenta mensuales son adelantos del Impuesto a la Renta empresarial.
La declaración jurada anual informa el resultado tributario del ejercicio y determina impuesto por pagar o saldo a favor.

3. COMPROBANTES DE PAGO
La factura se emite normalmente cuando el comprador necesita sustentar gasto, costo o crédito fiscal.
La boleta se emite generalmente a consumidores finales.
La nota de crédito sirve para anular, corregir, devolver o reducir una operación ya emitida.
La nota de débito sirve para aumentar el valor de una operación, por intereses, penalidades o ajustes.
El comprobante de retención acredita una retención efectuada por un agente designado.
La factura electrónica es un comprobante digital emitido mediante sistemas autorizados por SUNAT.

4. REGÍMENES TRIBUTARIOS EN PERÚ
Los principales regímenes son:
Nuevo RUS: para pequeños negocios de personas naturales que venden a consumidores finales y emiten boletas.
RER: Régimen Especial de Renta, para ciertos negocios con límites y contabilidad simplificada.
RMT: Régimen MYPE Tributario, pensado para micro y pequeñas empresas.
Régimen General: para empresas sin límite pequeño de ingresos y con mayores obligaciones contables.
El cambio de régimen depende de requisitos, actividad, ingresos y declaraciones realizadas.
Los libros contables dependen del régimen, nivel de ingresos y tipo de contribuyente.

5. SUNAT Y OBLIGACIONES
SUNAT administra tributos internos, aduanas, fiscalización, recaudación y obligaciones tributarias.
Las declaraciones mensuales vencen según cronograma de SUNAT y último dígito del RUC.
Si no se declara a tiempo, puede generarse multa, intereses y deuda tributaria.
Para regularizar una deuda, se puede declarar, pagar, fraccionar o consultar opciones en SUNAT Operaciones en Línea.
La Clave SOL permite ingresar a SUNAT Operaciones en Línea para declarar, pagar, consultar deudas y emitir comprobantes.

6. RETENCIONES Y DETRACCIONES
La detracción es un sistema donde parte del pago se deposita en una cuenta del Banco de la Nación para asegurar el pago de tributos.
Los porcentajes de detracción dependen del bien o servicio.
La retención del IGV es un mecanismo donde un agente designado retiene parte del IGV y lo entrega a SUNAT.
Los agentes de retención son contribuyentes designados por SUNAT.
La percepción es un cobro adicional aplicado en ciertas operaciones como adelanto del IGV.

7. LIBROS CONTABLES
Los libros contables registran operaciones económicas.
El Registro de Ventas anota comprobantes emitidos.
El Registro de Compras anota comprobantes recibidos.
El PLE es el Programa de Libros Electrónicos de SUNAT.
El atraso máximo permitido depende del tipo de libro y norma aplicable, por eso conviene verificar SUNAT.

8. PREGUNTAS PRÁCTICAS
Un independiente normalmente emite recibos por honorarios y puede estar sujeto a pagos o retenciones según sus ingresos.
La deducción de gastos personales o de casa depende del tipo de renta y requisitos. No todo gasto personal es deducible.
La UIT es la Unidad Impositiva Tributaria. Sirve como referencia para impuestos, multas, límites y deducciones.
Para saber si tienes deuda con SUNAT, se consulta con RUC y Clave SOL en SUNAT Operaciones en Línea.
Para obtener Clave SOL, se puede gestionar desde SUNAT por canales virtuales o presenciales, según el caso.
"""


PREGUNTAS_FRECUENTES = {
    # IGV
    "que es el igv": "El IGV es el Impuesto General a las Ventas. En Perú se aplica comúnmente una tasa general de 18% sobre operaciones gravadas, como ventas de bienes, servicios, importaciones y contratos de construcción.",
    "cuál es la tasa actual del igv": "La tasa general del IGV en Perú se conoce comúnmente como 18%. Para casos especiales o cambios normativos, conviene verificar SUNAT.",
    "como se calcula el igv": "Si el precio no incluye IGV: IGV = base imponible x 18%. Total = base + IGV. Si el total ya incluye IGV: base = total / 1.18 e IGV = total - base.",
    "como se calcula el igv de una factura": "Si la factura tiene base imponible, multiplica la base por 0.18. Ejemplo: base S/ 100, IGV S/ 18, total S/ 118.",
    "operaciones exoneradas del igv": "Las operaciones exoneradas son aquellas que la ley libera del pago del IGV. Pueden variar según norma vigente, por eso es recomendable revisar SUNAT o la Ley del IGV.",
    "que es el credito fiscal": "El crédito fiscal es el IGV pagado en compras que puede descontarse del IGV generado por ventas, siempre que la compra esté vinculada al negocio y cumpla requisitos.",
    "diferencia entre exonerado e inafecto": "Exonerado: la operación está dentro del IGV, pero una norma la libera del pago. Inafecto: la operación no está dentro del campo de aplicación del IGV.",

    # RENTA
    "rentas de primera segunda tercera cuarta y quinta": "Primera: alquileres. Segunda: intereses, dividendos y ganancias de capital. Tercera: negocios o empresas. Cuarta: trabajo independiente. Quinta: trabajo dependiente en planilla.",
    "como se calcula el impuesto a la renta de tercera categoria": "Se calcula partiendo de ingresos empresariales, restando costos y gastos deducibles para determinar la renta neta. Luego se aplica la tasa correspondiente y se descuentan pagos a cuenta.",
    "gastos deducibles renta empresarial": "Son gastos necesarios para producir renta o mantener la fuente del negocio, sustentados con comprobantes, razonables, registrados y permitidos por la norma tributaria.",
    "pagos a cuenta mensuales": "Son adelantos mensuales del Impuesto a la Renta que realizan empresas o negocios. Luego se aplican contra el impuesto anual.",
    "declaracion jurada anual": "Es la declaración donde se informa el resultado del ejercicio, ingresos, gastos, renta neta, impuesto calculado, pagos a cuenta y saldo por pagar o a favor.",

    # COMPROBANTES
    "cuando se emite factura y boleta": "Factura: cuando el comprador necesita sustentar gasto, costo o crédito fiscal. Boleta: cuando se vende a consumidor final.",
    "nota de credito": "La nota de crédito se emite para anular, corregir, reducir, devolver o modificar una operación ya facturada o boleteada.",
    "nota de debito": "La nota de débito se emite para aumentar el valor de una operación, por intereses, penalidades, diferencias de precio u otros ajustes.",
    "comprobante de retencion": "Es el documento que acredita que un agente de retención retuvo una parte del pago para entregarla a SUNAT.",
    "factura electronica": "La factura electrónica es un comprobante digital emitido mediante sistemas autorizados. Tiene validez tributaria y permite sustentar operaciones.",

    # REGÍMENES
    "regimenes tributarios peru": "En Perú existen principalmente Nuevo RUS, RER, Régimen MYPE Tributario y Régimen General.",
    "diferencia entre rus rer rmt y regimen general": "Nuevo RUS es para pequeños negocios de personas naturales. RER tiene contabilidad simplificada. RMT es para MYPE. Régimen General aplica a empresas con mayores obligaciones y sin límite pequeño de ingresos.",
    "limite de ingresos regimen tributario": "Los límites dependen del régimen y pueden cambiar. Como referencia, SUNAT publica los límites para NRUS, RER, RMT y Régimen General. Verifica siempre la tabla vigente.",
    "como me cambio de regimen tributario": "El cambio se realiza según requisitos del régimen, actividad, ingresos y declaraciones. Puede hacerse mediante declaración mensual o trámites en SUNAT, según el caso.",
    "libros contables por regimen": "Los libros dependen del régimen e ingresos. RUS no lleva libros contables formales; RER y RMT tienen obligaciones simplificadas o progresivas; Régimen General tiene mayores obligaciones.",

    # SUNAT
    "cuando vencen las declaraciones mensuales": "Vencen según el cronograma de SUNAT y el último dígito del RUC. Debes revisar el cronograma vigente del periodo correspondiente.",
    "cronograma de vencimientos sunat": "Es el calendario oficial que indica las fechas límite para declarar y pagar según periodo tributario y último dígito del RUC.",
    "que pasa si no declaro a tiempo": "Puedes generar multa, intereses moratorios y deuda tributaria. Lo recomendable es regularizar cuanto antes.",
    "multa por no declarar": "La multa depende del régimen, tipo de obligación y momento de regularización. Para un monto exacto, revisa SUNAT o consulta con un contador.",
    "regularizar deuda tributaria": "Puedes revisar la deuda con Clave SOL, presentar declaraciones pendientes, pagar o solicitar fraccionamiento si corresponde.",

    # RETENCIONES Y DETRACCIONES
    "sistema de detracciones": "La detracción es un sistema donde parte del pago se deposita en una cuenta del Banco de la Nación para asegurar el cumplimiento tributario.",
    "bienes y servicios sujetos a detraccion": "Depende de los anexos y normas SUNAT. Algunos servicios y bienes específicos están sujetos a detracción con porcentajes definidos.",
    "porcentaje de detraccion": "El porcentaje depende del bien o servicio. Debes revisar la tabla vigente de detracciones de SUNAT.",
    "retencion del igv": "La retención del IGV es un mecanismo donde un agente retiene parte del pago y lo entrega a SUNAT.",
    "agentes de retencion": "Son contribuyentes designados por SUNAT para retener parte del IGV en operaciones determinadas.",

    # LIBROS
    "libros contables obligado": "Depende del régimen tributario, ingresos y tipo de contribuyente. Puede incluir Registro de Ventas, Registro de Compras, Libro Diario, Mayor, Inventarios, entre otros.",
    "ple sunat": "El PLE es el Programa de Libros Electrónicos de SUNAT, usado para validar y enviar libros electrónicos.",
    "registro de ventas": "El Registro de Ventas anota los comprobantes emitidos por ventas o servicios prestados.",
    "registro de compras": "El Registro de Compras anota comprobantes recibidos por compras y gastos relacionados al negocio.",
    "atraso maximo libros": "El atraso máximo depende del tipo de libro y norma vigente. Debe verificarse en SUNAT para evitar multas.",

    # PRÁCTICAS
    "impuestos independiente": "Si eres independiente, normalmente emites recibos por honorarios y declaras renta de cuarta categoría cuando corresponde. También puede aplicar retención o pago mensual según ingresos.",
    "deducir gastos de mi casa": "Depende del tipo de renta y si el gasto está vinculado a la generación de ingresos. No todo gasto de casa es deducible.",
    "que es la uit": "La UIT es la Unidad Impositiva Tributaria. Sirve como referencia para impuestos, multas, deducciones, límites y obligaciones tributarias.",
    "deuda con sunat": "Puedes verificar si tienes deuda entrando a SUNAT Operaciones en Línea con tu RUC y Clave SOL.",
    "clave sol": "La Clave SOL es la contraseña para acceder a SUNAT Operaciones en Línea. Permite declarar, pagar, consultar deudas y realizar trámites."
}


def limpiar_texto(texto: str) -> str:
    texto = texto.lower().strip()
    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ñ": "n",
        "¿": "",
        "?": "",
        "¡": "",
        "!": "",
        ",": "",
        ".": "",
        ":": "",
        ";": ""
    }

    for original, nuevo in reemplazos.items():
        texto = texto.replace(original, nuevo)

    return texto


def detectar_idioma(mensaje: str) -> str:
    texto = mensaje.lower()

    palabras_ingles = [
        "what", "how", "why", "when", "where", "who",
        "hello", "explain", "give me", "tax", "invoice",
        "income", "business", "sales tax"
    ]

    if any(palabra in texto for palabra in palabras_ingles):
        return "en"

    return "es"


def respuesta_faq(mensaje: str):
    texto = limpiar_texto(mensaje)

    for pregunta, respuesta in PREGUNTAS_FRECUENTES.items():
        pregunta_limpia = limpiar_texto(pregunta)

        if pregunta_limpia in texto or texto in pregunta_limpia:
            return respuesta

    palabras_clave = {
        "igv": PREGUNTAS_FRECUENTES["que es el igv"],
        "ruc": "El RUC es el Registro Único de Contribuyentes. Identifica a personas o empresas que realizan actividades económicas y cumplen obligaciones tributarias.",
        "sunat": "SUNAT administra tributos internos, aduanas, fiscalización, recaudación y obligaciones tributarias en Perú.",
        "tributacion": "La tributación es el conjunto de normas y obligaciones relacionadas con el pago de tributos al Estado.",
        "tributacion": "La tributación es el conjunto de normas y obligaciones relacionadas con el pago de tributos al Estado.",
        "renta": PREGUNTAS_FRECUENTES["rentas de primera segunda tercera cuarta y quinta"],
        "factura": PREGUNTAS_FRECUENTES["cuando se emite factura y boleta"],
        "boleta": PREGUNTAS_FRECUENTES["cuando se emite factura y boleta"],
        "detraccion": PREGUNTAS_FRECUENTES["sistema de detracciones"],
        "retencion": PREGUNTAS_FRECUENTES["retencion del igv"],
        "libros": PREGUNTAS_FRECUENTES["libros contables obligado"],
        "clave sol": PREGUNTAS_FRECUENTES["clave sol"],
        "uit": PREGUNTAS_FRECUENTES["que es la uit"],
        "deuda": PREGUNTAS_FRECUENTES["deuda con sunat"]
    }

    for clave, respuesta in palabras_clave.items():
        if clave in texto:
            return respuesta

    return None


def respuesta_local(mensaje: str) -> str:
    respuesta = respuesta_faq(mensaje)

    if respuesta:
        return respuesta

    idioma = detectar_idioma(mensaje)

    if idioma == "en":
        return (
            "I can answer general questions. If your question is tax-related, "
            "ask me about VAT/IGV, tax ID/RUC, invoices, income tax, tax regimes, "
            "deductions, withholdings or tax obligations."
        )

    return (
        "Puedo responder preguntas generales y también temas tributarios. "
        "Puedes preguntarme sobre IGV, RUC, SUNAT, renta, facturas, boletas, "
        "regímenes tributarios, detracciones, retenciones, libros contables, deudas o Clave SOL."
    )


def responder_chatbot(mensaje: str) -> str:
    mensaje = mensaje.strip()

    if mensaje == "":
        return "Escribe tu consulta para poder ayudarte."

    faq = respuesta_faq(mensaje)

    if faq:
        return faq

    if client is None:
        return respuesta_local(mensaje)

    prompt = f"""
You are TribuTax, a fast, clear and helpful virtual assistant.

LANGUAGE RULE:
Detect the user's language and answer in the same language.
If the user writes in Spanish, answer in Spanish.
If the user writes in English, answer in English.
Do not mention language detection.

MAIN FUNCTION:
You can answer any type of question freely.
You are especially strong in Peruvian taxation: IGV, RUC, SUNAT, income tax, invoices, receipts, tax regimes, deductions, withholdings, detractions, books, tax returns and tax obligations.

TAX KNOWLEDGE BASE:
{BASE_TRIBUTARIA}

STYLE:
Answer clearly and directly.
Do not greet in every answer.
Keep the answer concise but complete.
If the user asks for steps, use numbered steps.
If exact dates, limits, penalties or legal amounts are needed, recommend checking SUNAT or consulting a qualified accountant.

USER QUESTION:
{mensaje}
"""

    for intento in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=700
                )
            )

            if response.text:
                return response.text.strip()

            return respuesta_local(mensaje)

        except Exception as error:
            print("Error con Gemini:", error)

            if intento < 2:
                time.sleep(1)
                continue

            return respuesta_local(mensaje)