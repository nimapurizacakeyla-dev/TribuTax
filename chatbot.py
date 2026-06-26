import os
import re
import time
from dotenv import load_dotenv

load_dotenv()

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = None

if GEMINI_API_KEY and genai is not None:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception:
        client = None


BASE_TRIBUTARIA = """
Eres TribuTax, un asistente virtual especializado en tributación peruana.
Respondes de forma clara, rápida, sencilla y útil.

Temas principales:
IGV, Impuesto a la Renta, SUNAT, RUC, comprobantes de pago, factura, boleta,
regímenes tributarios, detracciones, retenciones, libros contables, Clave SOL,
declaraciones mensuales, deudas tributarias, multas y orientación para independientes.

Tus respuestas son orientativas. Para montos exactos, fechas vigentes, multas específicas
o decisiones formales, recomienda revisar SUNAT o consultar con un contador.
"""


PREGUNTAS_FRECUENTES = {
    # SALUDOS E IDENTIDAD
    "hola": "¡Hola! Soy TribuTax, tu asistente virtual tributario. Puedo ayudarte con IGV, RUC, SUNAT, comprobantes de pago, Impuesto a la Renta, regímenes tributarios, detracciones, retenciones, libros contables y Clave SOL.",
    "buenos dias": "¡Buenos días! Soy TribuTax. ¿En qué consulta tributaria o general puedo ayudarte hoy?",
    "buenas tardes": "¡Buenas tardes! Soy TribuTax. Puedo ayudarte con consultas sobre SUNAT, IGV, RUC, renta, comprobantes y más.",
    "buenas noches": "¡Buenas noches! Soy TribuTax. Escríbeme tu consulta y te orientaré de forma clara.",
    "que es tribu": "TribuTax es un asistente virtual creado para responder consultas tributarias y preguntas generales de forma rápida, clara y sencilla.",
    "que es tributax": "TribuTax es un chatbot de ayuda virtual enfocado en temas tributarios de Perú, como IGV, RUC, SUNAT, comprobantes, renta, regímenes tributarios y obligaciones fiscales.",
    "tributax": "Soy TribuTax, tu asistente virtual. Puedo ayudarte con consultas tributarias y también responder preguntas generales.",
    "quien eres": "Soy TribuTax, un asistente virtual especializado en orientación tributaria peruana. Puedo ayudarte con IGV, SUNAT, RUC, comprobantes, renta y más.",
    "como funcionas": "Funciono como un chatbot: escribes una consulta y te respondo usando una base tributaria local. Si está disponible, también puedo apoyarme en inteligencia artificial.",

    # IGV
    "que es el igv y cual es su tasa actual": "El IGV es el Impuesto General a las Ventas. En Perú grava principalmente la venta de bienes, la prestación de servicios, los contratos de construcción, la primera venta de inmuebles realizada por constructores y la importación de bienes. Su tasa general es 18%, compuesta por 16% de IGV y 2% de Impuesto de Promoción Municipal.",
    "que es el igv": "El IGV es el Impuesto General a las Ventas. En Perú se aplica principalmente a ventas de bienes, servicios, importaciones, contratos de construcción y ciertas operaciones gravadas. Su tasa general es 18%.",
    "cual es la tasa actual del igv": "La tasa general del IGV en Perú es 18%. Está compuesta por 16% de IGV y 2% de Impuesto de Promoción Municipal.",
    "como se calcula el igv de una factura": "Para calcular el IGV de una factura, primero identifica la base imponible. Si el precio no incluye IGV: IGV = base imponible x 18%. Ejemplo: base S/ 100, IGV S/ 18, total S/ 118. Si el total ya incluye IGV: base = total / 1.18 e IGV = total - base.",
    "como se calcula el igv": "Si el monto no incluye IGV, multiplica la base por 0.18. Si el monto ya incluye IGV, divide el total entre 1.18 para hallar la base y resta para obtener el IGV.",
    "que operaciones estan exoneradas del igv": "Las operaciones exoneradas del IGV son aquellas que, aunque están dentro del ámbito del impuesto, una norma las libera del pago. Pueden incluir ciertos bienes o servicios señalados por ley. Como estas listas pueden cambiar, conviene revisar la Ley del IGV o SUNAT.",
    "que es el credito fiscal y como se usa": "El crédito fiscal es el IGV que una empresa paga en sus compras y que puede descontar del IGV generado por sus ventas. Para usarlo, la compra debe estar relacionada con el negocio, sustentada con comprobante válido, registrada correctamente y cumplir los requisitos tributarios.",
    "que es el credito fiscal": "El crédito fiscal es el IGV pagado en compras que puede descontarse del IGV de ventas, siempre que la compra esté vinculada al negocio y cumpla los requisitos tributarios.",
    "cual es la diferencia entre exonerado e inafecto": "Exonerado significa que la operación sí está dentro del campo del IGV, pero una norma la libera temporal o expresamente del pago. Inafecto significa que la operación no está dentro del campo de aplicación del IGV desde el inicio.",
    "exonerado e inafecto": "Una operación exonerada pertenece al ámbito del IGV, pero no paga por disposición legal. Una operación inafecta no pertenece al ámbito del impuesto.",

    # IMPUESTO A LA RENTA
    "cuales son las rentas de primera segunda tercera cuarta y quinta categoria": "Las rentas se clasifican así: Primera categoría: alquileres de bienes muebles o inmuebles. Segunda categoría: intereses, regalías, dividendos y ganancias de capital. Tercera categoría: actividades empresariales o negocios. Cuarta categoría: trabajo independiente con recibos por honorarios. Quinta categoría: trabajo dependiente en planilla.",
    "rentas de primera segunda tercera cuarta y quinta": "Primera: alquileres. Segunda: intereses, dividendos, regalías y ganancias de capital. Tercera: negocios o empresas. Cuarta: trabajo independiente. Quinta: trabajo dependiente en planilla.",
    "como se calcula el impuesto a la renta de tercera categoria": "El Impuesto a la Renta de tercera categoría se calcula partiendo de los ingresos empresariales, restando costos y gastos deducibles para obtener la renta neta. Luego se aplican las tasas correspondientes y se descuentan los pagos a cuenta realizados durante el año.",
    "que gastos son deducibles para la renta empresarial": "Son deducibles los gastos necesarios para producir renta o mantener la fuente del negocio, siempre que sean razonables, estén sustentados con comprobantes válidos, estén registrados y cumplan las normas tributarias. Ejemplos: alquiler del local, servicios, compras vinculadas al negocio, sueldos, transporte empresarial y gastos administrativos.",
    "gastos deducibles renta empresarial": "Los gastos deducibles deben estar relacionados con el negocio, ser necesarios, razonables, sustentados y permitidos por norma tributaria.",
    "cuales son los pagos a cuenta mensuales": "Los pagos a cuenta mensuales son adelantos del Impuesto a la Renta que realizan las empresas durante el año. Luego se aplican contra el impuesto anual determinado en la declaración jurada anual.",
    "pagos a cuenta mensuales": "Son adelantos mensuales del Impuesto a la Renta empresarial. Se pagan durante el ejercicio y luego se descuentan del impuesto anual.",
    "que es la declaracion jurada anual": "La declaración jurada anual es la declaración donde el contribuyente informa sus ingresos, costos, gastos, renta neta, pagos a cuenta y determina si tiene impuesto por pagar o saldo a favor.",
    "declaracion jurada anual": "Es una declaración presentada a SUNAT donde se informa el resultado tributario del año y se calcula el impuesto final.",

    # COMPROBANTES DE PAGO
    "cuando se emite una factura y cuando una boleta": "Se emite factura cuando el cliente necesita sustentar crédito fiscal, gasto o costo tributario, normalmente empresas o personas con RUC. Se emite boleta cuando la venta o servicio es para un consumidor final que no necesita sustentar crédito fiscal.",
    "cuando se emite factura": "La factura se emite cuando el comprador necesita sustentar crédito fiscal, gasto o costo tributario. Generalmente se entrega a empresas o personas con RUC.",
    "cuando se emite boleta": "La boleta se emite generalmente a consumidores finales que no necesitan usar crédito fiscal ni sustentar gasto tributario.",
    "que es una nota de credito y cuando se emite": "La nota de crédito es un comprobante que se emite para anular, corregir, reducir o modificar una factura o boleta ya emitida. Se usa, por ejemplo, por devoluciones, descuentos, errores en el comprobante o anulación de operaciones.",
    "que es una nota de credito": "La nota de crédito sirve para corregir, anular, reducir o modificar una operación ya emitida en una factura o boleta.",
    "que es una nota de debito": "La nota de débito se emite para aumentar el valor de una operación ya facturada, por ejemplo, por intereses, penalidades, diferencia de precio, gastos adicionales o ajustes.",
    "que es el comprobante de retencion": "El comprobante de retención acredita que un agente de retención designado por SUNAT retuvo parte del pago correspondiente, generalmente vinculado al IGV, para luego entregarlo al fisco.",
    "como funciona la factura electronica": "La factura electrónica funciona como un comprobante digital con validez tributaria. Se emite mediante sistemas autorizados por SUNAT, se envía al cliente y queda registrada electrónicamente para sustentar operaciones.",
    "factura electronica": "La factura electrónica es un comprobante digital válido ante SUNAT. Permite sustentar ventas, gastos, costos y crédito fiscal cuando corresponde.",

    # REGÍMENES TRIBUTARIOS
    "cuales son los regimenes tributarios en peru": "En Perú existen principalmente cuatro regímenes tributarios: Nuevo RUS, Régimen Especial de Renta o RER, Régimen MYPE Tributario o RMT y Régimen General. Cada uno tiene requisitos, límites, obligaciones y formas de declarar diferentes.",
    "regimenes tributarios en peru": "Los principales regímenes tributarios en Perú son: Nuevo RUS, RER, RMT y Régimen General.",
    "cual es la diferencia entre rus rer rmt y regimen general": "Nuevo RUS está dirigido a pequeños negocios de personas naturales que venden a consumidores finales. RER es para ciertos negocios con límites y obligaciones simplificadas. RMT está orientado a micro y pequeñas empresas. Régimen General es para empresas con mayores operaciones y obligaciones contables completas.",
    "diferencia entre rus rer rmt y regimen general": "Nuevo RUS: pequeños negocios. RER: régimen especial con límites. RMT: micro y pequeñas empresas. Régimen General: empresas con obligaciones completas y sin límite pequeño de ingresos.",
    "que limite de ingresos tiene cada regimen": "Los límites de ingresos dependen del régimen y pueden actualizarse. En general, el Nuevo RUS y el RER tienen límites más reducidos, el RMT está orientado a MYPE y el Régimen General no tiene un límite pequeño de ingresos. Para montos exactos vigentes, revisa SUNAT.",
    "limite de ingresos de cada regimen": "Los límites varían según el régimen y pueden cambiar. Lo recomendable es verificar la tabla vigente de SUNAT antes de elegir o cambiar de régimen.",
    "como me cambio de regimen tributario": "El cambio de régimen tributario depende del régimen actual, el régimen al que deseas pasar, tus ingresos, actividad y declaraciones. En algunos casos se realiza mediante la declaración mensual; en otros, con trámites o condiciones específicas en SUNAT.",
    "que libros contables lleva cada regimen": "Los libros contables dependen del régimen y del nivel de ingresos. En general, el Nuevo RUS no lleva libros contables formales; el RER lleva registros simplificados; el RMT lleva libros según ingresos; y el Régimen General tiene obligaciones contables más completas.",
    "libros contables lleva cada regimen": "Nuevo RUS: usualmente no lleva libros formales. RER: Registro de Compras y Registro de Ventas. RMT y Régimen General: libros según ingresos y obligaciones, como Registro de Ventas, Compras, Diario, Mayor e Inventarios cuando corresponda.",

    # SUNAT Y OBLIGACIONES
    "cuando vencen las declaraciones mensuales": "Las declaraciones mensuales vencen según el cronograma de SUNAT, el periodo tributario y el último dígito del RUC. Debes revisar el cronograma vigente en SUNAT para conocer tu fecha exacta.",
    "que es el cronograma de vencimientos de sunat": "El cronograma de vencimientos de SUNAT es el calendario oficial que indica las fechas límite para declarar y pagar impuestos según el periodo tributario y el último dígito del RUC.",
    "cronograma de vencimientos de sunat": "Es el calendario de SUNAT que fija cuándo debes declarar y pagar, según el último dígito de tu RUC.",
    "que pasa si no declaro a tiempo": "Si no declaras a tiempo, puedes generar multas, intereses moratorios, deuda tributaria y posibles restricciones. Lo recomendable es regularizar cuanto antes.",
    "cuanto es la multa por no declarar": "La multa por no declarar depende del régimen tributario, tipo de obligación, tributo omitido y si regularizas voluntariamente. Para conocer el monto exacto debes revisar SUNAT o consultar a un contador.",
    "multa por no declarar": "La multa varía según el régimen y la obligación incumplida. También puede reducirse si regularizas voluntariamente, según corresponda.",
    "como se regulariza una deuda tributaria": "Para regularizar una deuda tributaria debes ingresar a SUNAT con tu RUC y Clave SOL, revisar la deuda, presentar declaraciones pendientes si corresponde, pagar la deuda o solicitar fraccionamiento si está permitido.",
    "regularizar deuda tributaria": "Puedes regularizar revisando tu deuda en SUNAT, declarando lo pendiente, pagando o solicitando fraccionamiento cuando corresponda.",

    # RETENCIONES Y DETRACCIONES
    "que es el sistema de detracciones": "El sistema de detracciones es un mecanismo donde una parte del pago se deposita en una cuenta del Banco de la Nación a nombre del proveedor. Ese dinero se usa para asegurar el cumplimiento de obligaciones tributarias.",
    "sistema de detracciones": "La detracción consiste en separar un porcentaje del pago y depositarlo en el Banco de la Nación para cubrir obligaciones tributarias.",
    "que bienes y servicios estan sujetos a detraccion": "Los bienes y servicios sujetos a detracción están definidos por normas de SUNAT y pueden incluir determinados servicios, transporte, construcción, bienes específicos y operaciones señaladas en anexos. Como la lista puede variar, conviene revisar la tabla vigente de SUNAT.",
    "bienes y servicios sujetos a detraccion": "Dependen de los anexos y normas vigentes de SUNAT. Se debe revisar la tabla oficial para saber si una operación está afecta.",
    "cual es el porcentaje de detraccion": "El porcentaje de detracción depende del bien o servicio. No existe un solo porcentaje para todos los casos. Debes revisar la tabla vigente de SUNAT según la operación.",
    "porcentaje de detraccion": "El porcentaje varía según el tipo de bien o servicio. Para exactitud, revisa la tabla vigente de detracciones de SUNAT.",
    "que es la retencion del igv": "La retención del IGV es un mecanismo por el cual un agente designado por SUNAT retiene parte del IGV al proveedor y luego lo entrega a SUNAT.",
    "retencion del igv": "Es cuando un agente de retención descuenta parte del IGV de una operación y lo entrega a SUNAT.",
    "quienes son agentes de retencion": "Los agentes de retención son contribuyentes designados por SUNAT para retener parte del IGV en determinadas operaciones y entregarlo al fisco.",
    "agentes de retencion": "Son contribuyentes designados por SUNAT para aplicar retenciones en operaciones específicas.",

    # LIBROS CONTABLES
    "que libros contables estoy obligado a llevar": "Los libros contables que debes llevar dependen de tu régimen tributario, nivel de ingresos y tipo de contribuyente. Pueden incluir Registro de Ventas, Registro de Compras, Libro Diario, Libro Mayor, Libro de Inventarios y Balances, entre otros.",
    "libros contables estoy obligado": "Depende de tu régimen e ingresos. Los más comunes son Registro de Ventas, Registro de Compras, Libro Diario y Libro Mayor.",
    "que es el ple de sunat": "El PLE es el Programa de Libros Electrónicos de SUNAT. Sirve para validar, generar y presentar libros electrónicos como Registro de Ventas, Registro de Compras y otros libros contables.",
    "ple de sunat": "El PLE es el Programa de Libros Electrónicos usado para presentar libros contables electrónicos ante SUNAT.",
    "como se lleva el registro de ventas": "El Registro de Ventas se lleva anotando los comprobantes emitidos por ventas o servicios, como facturas, boletas, notas de crédito y notas de débito, siguiendo los formatos y plazos establecidos.",
    "registro de ventas": "El Registro de Ventas contiene los comprobantes emitidos por la empresa por sus ventas o servicios.",
    "como se lleva el registro de compras": "El Registro de Compras se lleva anotando los comprobantes recibidos por compras, gastos y servicios vinculados al negocio. Sirve para sustentar costos, gastos y crédito fiscal cuando corresponde.",
    "registro de compras": "El Registro de Compras contiene comprobantes recibidos por compras y gastos del negocio.",
    "cual es el atraso maximo permitido en los libros": "El atraso máximo permitido depende del tipo de libro contable y de la norma vigente. Para evitar sanciones, debes revisar los plazos oficiales de SUNAT según cada libro.",
    "atraso maximo permitido en los libros": "El atraso máximo varía según el libro. Conviene revisar SUNAT para confirmar el plazo vigente.",

    # PREGUNTAS PRÁCTICAS
    "como calculo mis impuestos si soy independiente": "Si eres independiente, normalmente generas renta de cuarta categoría y emites recibos por honorarios. Debes revisar tus ingresos mensuales y anuales, posibles retenciones, pagos a cuenta y obligación de declarar. Si superas ciertos límites, puede corresponder pago o declaración.",
    "impuestos si soy independiente": "Como independiente, usualmente tributas por renta de cuarta categoría mediante recibos por honorarios. Puede aplicar retención o pago mensual según tus ingresos.",
    "puedo deducir gastos de mi casa si trabajo desde ahi": "Depende del tipo de renta, la actividad y si el gasto está directamente vinculado a generar ingresos. No todo gasto del hogar es deducible. Para sustentar deducción debe existir relación con la actividad, comprobantes válidos y cumplimiento de requisitos.",
    "deducir gastos de mi casa": "Solo algunos gastos podrían ser deducibles si están vinculados a la actividad económica y cumplen requisitos. Los gastos personales no suelen ser deducibles.",
    "que es la uit y para que sirve": "La UIT es la Unidad Impositiva Tributaria. Sirve como valor de referencia para calcular impuestos, multas, deducciones, límites de ingresos, sanciones y obligaciones tributarias.",
    "que es la uit": "La UIT es una unidad de referencia usada en Perú para impuestos, multas, deducciones, límites y obligaciones tributarias.",
    "como se si tengo deuda con sunat": "Puedes saber si tienes deuda ingresando a SUNAT Operaciones en Línea con tu RUC, usuario y Clave SOL. Allí puedes consultar deudas, valores pendientes, declaraciones y pagos.",
    "deuda con sunat": "Consulta tu deuda entrando a SUNAT Operaciones en Línea con tu RUC y Clave SOL.",
    "como obtengo mi clave sol": "Puedes obtener tu Clave SOL desde SUNAT, por canales virtuales o presenciales, según tu caso. Necesitarás validar tu identidad y datos del contribuyente.",
    "clave sol": "La Clave SOL es tu contraseña para ingresar a SUNAT Operaciones en Línea. Te permite declarar, pagar, consultar deudas, emitir comprobantes y hacer trámites.",
}


def limpiar_texto(texto: str) -> str:
    texto = texto.lower().strip()

    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",
        "ñ": "n"
    }

    for original, nuevo in reemplazos.items():
        texto = texto.replace(original, nuevo)

    texto = re.sub(r"[¿?¡!.,:;(){}\[\]\"']", "", texto)
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def detectar_idioma(mensaje: str) -> str:
    texto = mensaje.lower()

    palabras_ingles = [
        "what", "how", "why", "when", "where", "who",
        "hello", "hi", "explain", "tax", "invoice",
        "income", "business", "sales tax", "vat"
    ]

    if any(palabra in texto for palabra in palabras_ingles):
        return "en"

    return "es"


def respuesta_faq(mensaje: str):
    texto = limpiar_texto(mensaje)

    for pregunta, respuesta in PREGUNTAS_FRECUENTES.items():
        pregunta_limpia = limpiar_texto(pregunta)

        if pregunta_limpia == texto:
            return respuesta

        if pregunta_limpia in texto:
            return respuesta

        if texto in pregunta_limpia and len(texto) > 4:
            return respuesta

    palabras_clave = {
        "hola": PREGUNTAS_FRECUENTES["hola"],
        "buenos dias": PREGUNTAS_FRECUENTES["buenos dias"],
        "buenas tardes": PREGUNTAS_FRECUENTES["buenas tardes"],
        "buenas noches": PREGUNTAS_FRECUENTES["buenas noches"],

        "igv": PREGUNTAS_FRECUENTES["que es el igv"],
        "credito fiscal": PREGUNTAS_FRECUENTES["que es el credito fiscal"],
        "exonerado": PREGUNTAS_FRECUENTES["cual es la diferencia entre exonerado e inafecto"],
        "inafecto": PREGUNTAS_FRECUENTES["cual es la diferencia entre exonerado e inafecto"],

        "renta": PREGUNTAS_FRECUENTES["cuales son las rentas de primera segunda tercera cuarta y quinta categoria"],
        "tercera categoria": PREGUNTAS_FRECUENTES["como se calcula el impuesto a la renta de tercera categoria"],
        "cuarta categoria": PREGUNTAS_FRECUENTES["como calculo mis impuestos si soy independiente"],
        "quinta categoria": PREGUNTAS_FRECUENTES["cuales son las rentas de primera segunda tercera cuarta y quinta categoria"],

        "factura": PREGUNTAS_FRECUENTES["cuando se emite una factura y cuando una boleta"],
        "boleta": PREGUNTAS_FRECUENTES["cuando se emite una factura y cuando una boleta"],
        "nota de credito": PREGUNTAS_FRECUENTES["que es una nota de credito y cuando se emite"],
        "nota de debito": PREGUNTAS_FRECUENTES["que es una nota de debito"],

        "regimen": PREGUNTAS_FRECUENTES["cuales son los regimenes tributarios en peru"],
        "rus": PREGUNTAS_FRECUENTES["cual es la diferencia entre rus rer rmt y regimen general"],
        "rer": PREGUNTAS_FRECUENTES["cual es la diferencia entre rus rer rmt y regimen general"],
        "rmt": PREGUNTAS_FRECUENTES["cual es la diferencia entre rus rer rmt y regimen general"],

        "sunat": "SUNAT es la Superintendencia Nacional de Aduanas y de Administración Tributaria. Administra tributos, fiscaliza obligaciones, recauda impuestos y permite realizar trámites como declaraciones, pagos, consulta de deudas, RUC y Clave SOL.",
        "ruc": "El RUC es el Registro Único de Contribuyentes. Identifica a personas o empresas ante SUNAT para realizar actividades económicas y cumplir obligaciones tributarias.",
        "cronograma": PREGUNTAS_FRECUENTES["que es el cronograma de vencimientos de sunat"],
        "multa": PREGUNTAS_FRECUENTES["cuanto es la multa por no declarar"],
        "deuda": PREGUNTAS_FRECUENTES["como se si tengo deuda con sunat"],

        "detraccion": PREGUNTAS_FRECUENTES["que es el sistema de detracciones"],
        "retencion": PREGUNTAS_FRECUENTES["que es la retencion del igv"],
        "agente de retencion": PREGUNTAS_FRECUENTES["quienes son agentes de retencion"],

        "libros": PREGUNTAS_FRECUENTES["que libros contables estoy obligado a llevar"],
        "ple": PREGUNTAS_FRECUENTES["que es el ple de sunat"],
        "registro de ventas": PREGUNTAS_FRECUENTES["como se lleva el registro de ventas"],
        "registro de compras": PREGUNTAS_FRECUENTES["como se lleva el registro de compras"],

        "uit": PREGUNTAS_FRECUENTES["que es la uit y para que sirve"],
        "clave sol": PREGUNTAS_FRECUENTES["como obtengo mi clave sol"],
        "independiente": PREGUNTAS_FRECUENTES["como calculo mis impuestos si soy independiente"],
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
            "Hello! I am TribuTax. I can help you with general questions and Peruvian tax topics "
            "such as IGV/VAT, RUC, SUNAT, invoices, income tax, tax regimes, deductions, "
            "withholdings, detractions, accounting books and tax obligations."
        )

    return (
        "Soy TribuTax. Puedo ayudarte con IGV, RUC, SUNAT, comprobantes de pago, "
        "Impuesto a la Renta, regímenes tributarios, detracciones, retenciones, "
        "libros contables, deudas tributarias, multas, UIT y Clave SOL. "
        "Escríbeme tu pregunta de forma específica y te responderé."
    )


def responder_con_gemini(mensaje: str) -> str | None:
    if client is None or types is None:
        return None

    prompt = f"""
Eres TribuTax, un asistente virtual rápido, claro y útil.

REGLA DE IDIOMA:
Responde en el mismo idioma del usuario.

FUNCIÓN:
Puedes responder preguntas generales, pero eres especialista en tributación peruana.

BASE:
{BASE_TRIBUTARIA}

ESTILO:
Responde claro, directo y sin mencionar errores técnicos.
No saludes en cada respuesta.
Si la pregunta requiere pasos, usa una lista numerada.
Si se necesitan fechas, límites, multas o montos exactos vigentes, recomienda verificar SUNAT.

PREGUNTA DEL USUARIO:
{mensaje}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=500
            )
        )

        if response and response.text:
            return response.text.strip()

        return None

    except Exception as error:
        print("Gemini no disponible, usando base local:", error)
        return None


def responder_chatbot(mensaje: str) -> str:
    mensaje = mensaje.strip()

    if mensaje == "":
        return "Escribe tu consulta para poder ayudarte."

    # Primero responde con base local para que sea rápido
    respuesta = respuesta_faq(mensaje)

    if respuesta:
        return respuesta

    # Solo usa Gemini si no encuentra respuesta local
    respuesta_gemini = responder_con_gemini(mensaje)

    if respuesta_gemini:
        return respuesta_gemini

    # Si Gemini falla o no hay cuota, responde local
    return respuesta_local(mensaje)