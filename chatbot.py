import os
import re
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
Respondes rápido, claro y sencillo.
Ayudas con IGV, SUNAT, RUC, comprobantes de pago, Impuesto a la Renta,
regímenes tributarios, detracciones, retenciones, libros contables, UIT y Clave SOL.
"""


  # BASE AMPLIADA DE RESPUESTAS TRIBUTARIAS
RESPUESTAS.update({
    # RUC
    "que es el ruc": "El RUC es el Registro Único de Contribuyentes. Es el número que identifica a una persona natural o empresa ante SUNAT para realizar actividades económicas y cumplir obligaciones tributarias.",
    "para que sirve el ruc": "El RUC sirve para identificarte ante SUNAT, emitir comprobantes de pago, declarar impuestos, realizar actividades económicas formales y cumplir obligaciones tributarias.",
    "quienes deben tener ruc": "Deben tener RUC las personas o empresas que realizan actividades económicas, prestan servicios, venden bienes, alquilan inmuebles o generan ingresos sujetos a obligaciones tributarias.",
    "como sacar ruc": "Puedes obtener tu RUC en SUNAT de forma virtual o presencial. Debes validar tu identidad, registrar tu domicilio fiscal, actividad económica y datos del contribuyente.",
    "que es domicilio fiscal": "El domicilio fiscal es la dirección registrada ante SUNAT donde el contribuyente realiza sus actividades o recibe notificaciones tributarias.",
    "que es condicion de domicilio habido": "La condición de domicilio habido significa que SUNAT reconoce que el contribuyente puede ser ubicado en su domicilio fiscal declarado.",
    "que significa no habido": "No habido significa que SUNAT no pudo ubicar al contribuyente en su domicilio fiscal. Esto puede generar restricciones para emitir comprobantes o realizar trámites.",

    # CLAVE SOL
    "que es clave sol": "La Clave SOL es la contraseña que permite ingresar a SUNAT Operaciones en Línea. Sirve para declarar impuestos, pagar tributos, consultar deudas, emitir comprobantes y realizar trámites virtuales.",
    "para que sirve clave sol": "La Clave SOL sirve para acceder a los servicios virtuales de SUNAT, como declarar impuestos, pagar deudas, consultar RUC, emitir comprobantes electrónicos y revisar notificaciones.",
    "como recuperar clave sol": "Puedes recuperar tu Clave SOL desde la plataforma de SUNAT, siguiendo el proceso de recuperación con tus datos de identidad y validación.",
    "como cambiar clave sol": "Puedes cambiar tu Clave SOL ingresando a SUNAT Operaciones en Línea y modificando tus credenciales desde las opciones de seguridad.",

    # IGV AMPLIADO
    "que significa igv": "IGV significa Impuesto General a las Ventas. Es un impuesto que grava el consumo de bienes y servicios en Perú.",
    "igv incluido": "Cuando un precio tiene IGV incluido, significa que el monto total ya contiene el 18%. Para hallar la base imponible, se divide el total entre 1.18.",
    "precio con igv": "Si el precio ya incluye IGV, la base se calcula dividiendo el total entre 1.18. Luego el IGV se obtiene restando la base al total.",
    "precio sin igv": "Si el precio no incluye IGV, se calcula multiplicando la base por 18%. Luego se suma el IGV a la base para obtener el total.",
    "base imponible igv": "La base imponible del IGV es el valor sobre el cual se calcula el impuesto. Por ejemplo, si el valor de venta es S/ 100, esa es la base imponible.",
    "igv por pagar": "El IGV por pagar se calcula restando el crédito fiscal del débito fiscal. Es decir: IGV de ventas menos IGV de compras.",
    "debito fiscal": "El débito fiscal es el IGV que una empresa cobra en sus ventas y que debe declarar ante SUNAT.",
    "credito fiscal": "El crédito fiscal es el IGV pagado en las compras del negocio y que puede descontarse del IGV de las ventas, siempre que cumpla los requisitos tributarios.",
    "requisitos del credito fiscal": "Para usar crédito fiscal, la compra debe estar vinculada al negocio, estar sustentada con comprobante válido, estar registrada correctamente y cumplir las normas tributarias.",
    "que compras dan credito fiscal": "Dan crédito fiscal las compras vinculadas a la actividad del negocio, sustentadas con comprobantes válidos y registradas correctamente.",
    "cuando no puedo usar credito fiscal": "No puedes usar crédito fiscal si la compra no está relacionada con el negocio, no tiene comprobante válido, no está registrada correctamente o corresponde a gastos no aceptados tributariamente.",

    # COMPROBANTES
    "que es comprobante de pago": "Un comprobante de pago es un documento que acredita la transferencia de bienes, la entrega en uso o la prestación de servicios. Puede ser factura, boleta, recibo por honorarios, nota de crédito, nota de débito, entre otros.",
    "tipos de comprobantes de pago": "Los principales comprobantes de pago son factura, boleta de venta, recibo por honorarios, nota de crédito, nota de débito, liquidación de compra, ticket y comprobantes electrónicos.",
    "diferencia entre factura y boleta": "La factura se emite cuando el comprador necesita sustentar gasto, costo o crédito fiscal. La boleta se emite normalmente a consumidores finales y no permite usar crédito fiscal.",
    "factura": "La factura es un comprobante de pago que permite sustentar una operación comercial. Sirve para respaldar crédito fiscal, gasto o costo tributario cuando corresponde.",
    "boleta": "La boleta es un comprobante que se emite generalmente a consumidores finales. Acredita la venta o servicio, pero normalmente no permite usar crédito fiscal.",
    "recibo por honorarios": "El recibo por honorarios es el comprobante que emiten los trabajadores independientes por la prestación de servicios profesionales u oficios.",
    "que es recibo por honorarios": "El recibo por honorarios es un comprobante usado por personas que prestan servicios independientes. Está relacionado con rentas de cuarta categoría.",
    "cuando emito recibo por honorarios": "Debes emitir recibo por honorarios cuando prestas un servicio independiente y no estás en planilla por esa actividad.",
    "factura electronica": "La factura electrónica es un comprobante digital con validez tributaria. Se emite a través de sistemas autorizados por SUNAT y queda registrada electrónicamente.",
    "boleta electronica": "La boleta electrónica es un comprobante digital emitido a consumidores finales. Tiene validez tributaria y se registra electrónicamente.",
    "comprobante electronico": "Un comprobante electrónico es un documento digital autorizado por SUNAT que acredita operaciones comerciales y tributarias.",

    # NOTAS DE CRÉDITO Y DÉBITO
    "para que sirve nota de debito": "La nota de débito sirve para aumentar el valor de una operación ya facturada. Se usa por intereses, penalidades, diferencia de precio, gastos adicionales o ajustes.",
    "cuando se emite nota de debito": "La nota de débito se emite cuando se necesita incrementar el monto de una factura o boleta ya emitida.",
    "ejemplo de nota de debito": "Ejemplo: emitiste una factura por S/ 500, pero luego debes cobrar S/ 50 adicionales por transporte. Entonces emites una nota de débito por S/ 50.",
    "para que sirve nota de credito": "La nota de crédito sirve para disminuir, corregir o anular total o parcialmente una factura o boleta ya emitida.",
    "cuando se emite nota de credito": "La nota de crédito se emite por devoluciones, descuentos posteriores, errores en el comprobante o anulación de una operación.",
    "ejemplo de nota de credito": "Ejemplo: emitiste una factura por S/ 300 y el cliente devolvió mercadería por S/ 80. Entonces emites una nota de crédito por S/ 80.",

    # IMPUESTO A LA RENTA
    "que es impuesto a la renta": "El Impuesto a la Renta grava los ingresos obtenidos por personas naturales y empresas. En Perú se clasifica en rentas de primera, segunda, tercera, cuarta y quinta categoría.",
    "renta de primera categoria": "La renta de primera categoría proviene principalmente del alquiler de bienes muebles o inmuebles, como casas, departamentos, locales o vehículos.",
    "renta de segunda categoria": "La renta de segunda categoría proviene de intereses, regalías, dividendos, ganancias de capital y venta de valores, según corresponda.",
    "renta de tercera categoria": "La renta de tercera categoría corresponde a ingresos empresariales generados por negocios, comercios, empresas o actividades productivas.",
    "renta de cuarta categoria": "La renta de cuarta categoría corresponde al trabajo independiente, como servicios profesionales prestados mediante recibos por honorarios.",
    "renta de quinta categoria": "La renta de quinta categoría corresponde al trabajo dependiente, es decir, sueldos, salarios y remuneraciones de trabajadores en planilla.",
    "diferencia entre cuarta y quinta categoria": "La cuarta categoría corresponde al trabajo independiente con recibo por honorarios. La quinta categoría corresponde al trabajo dependiente en planilla.",
    "que es renta neta": "La renta neta es el resultado de restar a los ingresos los costos, gastos o deducciones permitidas por la norma tributaria.",
    "que es renta bruta": "La renta bruta es el ingreso obtenido antes de aplicar deducciones, costos o gastos permitidos.",
    "que es pago a cuenta": "El pago a cuenta es un adelanto mensual del Impuesto a la Renta que luego se descuenta del impuesto anual.",
    "que son pagos a cuenta": "Los pagos a cuenta son adelantos mensuales del Impuesto a la Renta. Al final del año se comparan con el impuesto anual determinado.",
    "declaracion anual": "La declaración anual es la presentación ante SUNAT donde se informa el resultado tributario del año, pagos a cuenta, impuesto por pagar o saldo a favor.",
    "saldo a favor": "El saldo a favor ocurre cuando el contribuyente pagó más impuesto del que correspondía. Puede aplicarse contra futuras obligaciones o solicitar devolución si corresponde.",

    # REGÍMENES TRIBUTARIOS
    "nuevo rus": "El Nuevo RUS es un régimen tributario para pequeños negocios de personas naturales. Tiene pagos mensuales fijos y obligaciones simplificadas.",
    "que es nuevo rus": "El Nuevo RUS es un régimen para pequeños negocios que venden a consumidores finales. No permite emitir facturas y tiene pagos mensuales fijos según categoría.",
    "rer": "El RER es el Régimen Especial de Renta. Está dirigido a ciertos negocios con límites de ingresos y obligaciones tributarias simplificadas.",
    "que es rer": "El RER es un régimen tributario para negocios que cumplen ciertos requisitos. Permite emitir facturas y declarar IGV y renta mensual.",
    "rmt": "El RMT es el Régimen MYPE Tributario. Está orientado a micro y pequeñas empresas, con una tributación más gradual según la utilidad.",
    "que es rmt": "El Régimen MYPE Tributario está dirigido a micro y pequeñas empresas. Permite emitir comprobantes y llevar obligaciones según ingresos.",
    "regimen general": "El Régimen General es para empresas con operaciones más amplias. No tiene límites pequeños de ingresos y exige obligaciones contables más completas.",
    "que regimen me conviene": "El régimen que te conviene depende de tus ingresos, tipo de negocio, clientes, gastos, necesidad de emitir factura y obligaciones contables. Para elegir correctamente, conviene revisar SUNAT o consultar a un contador.",
    "puedo cambiar de regimen": "Sí, puedes cambiar de régimen tributario si cumples las condiciones del régimen al que deseas ingresar. El procedimiento depende de tu situación y debe revisarse en SUNAT.",

    # SUNAT Y DECLARACIONES
    "que es declaracion mensual": "La declaración mensual es la presentación que realiza el contribuyente ante SUNAT para informar ventas, compras, IGV, renta mensual u otras obligaciones del periodo.",
    "que es pdt": "El PDT es un Programa de Declaración Telemática usado para presentar ciertas declaraciones tributarias ante SUNAT.",
    "que es declara facil": "Declara Fácil es una plataforma de SUNAT que permite presentar declaraciones y pagos de manera virtual.",
    "que pasa si no pago impuestos": "Si no pagas impuestos, puedes generar intereses, multas, cobranza coactiva, embargos o restricciones tributarias. Lo recomendable es regularizar cuanto antes.",
    "que pasa si declaro fuera de plazo": "Declarar fuera de plazo puede generar multa e intereses. En algunos casos puede haber gradualidad o reducción si regularizas voluntariamente.",
    "interes moratorio": "El interés moratorio es el interés que se genera cuando una deuda tributaria no se paga dentro del plazo establecido.",
    "cobranza coactiva": "La cobranza coactiva es el procedimiento mediante el cual SUNAT exige el pago de deudas tributarias vencidas, pudiendo aplicar medidas como embargos.",
    "fraccionamiento tributario": "El fraccionamiento tributario permite pagar una deuda tributaria en cuotas, siempre que se cumplan los requisitos establecidos por SUNAT.",
    "aplazamiento tributario": "El aplazamiento permite postergar el pago de una deuda tributaria por un tiempo determinado, según las condiciones de SUNAT.",

    # DETRACCIONES, RETENCIONES Y PERCEPCIONES
    "detraccion": "La detracción es un sistema donde una parte del pago se deposita en una cuenta del Banco de la Nación para asegurar el cumplimiento de obligaciones tributarias.",
    "para que sirve la detraccion": "La detracción sirve para asegurar que el proveedor tenga fondos destinados al pago de tributos administrados por SUNAT.",
    "cuenta de detracciones": "La cuenta de detracciones es una cuenta del Banco de la Nación donde se depositan los montos detraídos por operaciones sujetas al sistema.",
    "retencion": "La retención es un mecanismo donde un agente designado retiene parte del impuesto y luego lo entrega a SUNAT.",
    "percepcion": "La percepción es un mecanismo mediante el cual se cobra por adelantado una parte del impuesto que corresponderá pagar en una operación futura.",
    "diferencia entre retencion detraccion y percepcion": "La detracción separa parte del pago y lo deposita en el Banco de la Nación. La retención descuenta parte del impuesto al proveedor. La percepción cobra un adelanto adicional al comprador.",

    # LIBROS CONTABLES
    "registro de ventas": "El Registro de Ventas contiene los comprobantes emitidos por ventas o servicios. Permite sustentar ingresos y determinar el débito fiscal del IGV.",
    "registro de compras": "El Registro de Compras contiene los comprobantes recibidos por compras y gastos del negocio. Sirve para sustentar crédito fiscal, costos y gastos.",
    "libro diario": "El Libro Diario registra cronológicamente las operaciones económicas de una empresa mediante asientos contables.",
    "libro mayor": "El Libro Mayor organiza las operaciones por cuentas contables, permitiendo conocer movimientos y saldos.",
    "libro de inventarios y balances": "El Libro de Inventarios y Balances muestra información sobre activos, pasivos, patrimonio, inventarios y estados financieros del negocio.",
    "libros electronicos": "Los libros electrónicos son registros contables llevados en formato digital y presentados o validados según las disposiciones de SUNAT.",
    "sire sunat": "El SIRE es el Sistema Integrado de Registros Electrónicos de SUNAT, relacionado con registros de ventas y compras electrónicos.",

    # INDEPENDIENTES
    "soy independiente que debo pagar": "Si eres independiente, normalmente generas renta de cuarta categoría. Debes emitir recibos por honorarios y revisar si corresponde retención, pago a cuenta o declaración según tus ingresos.",
    "trabajador independiente": "Un trabajador independiente presta servicios por cuenta propia y normalmente emite recibos por honorarios. Sus ingresos corresponden a renta de cuarta categoría.",
    "suspension de cuarta categoria": "La suspensión de cuarta categoría permite evitar retenciones o pagos a cuenta cuando tus ingresos proyectados no superan los límites establecidos por SUNAT.",
    "retencion cuarta categoria": "La retención de cuarta categoría se aplica a recibos por honorarios cuando corresponde, según el monto y condiciones establecidas por SUNAT.",
    "recibo por honorarios electronico": "El recibo por honorarios electrónico es el comprobante digital que emite un trabajador independiente por sus servicios.",

    # EMPRESAS Y GASTOS
    "gastos deducibles": "Los gastos deducibles son aquellos necesarios para generar renta o mantener la fuente productora, siempre que estén sustentados, sean razonables y cumplan la norma tributaria.",
    "gastos no deducibles": "Los gastos no deducibles son aquellos que la norma tributaria no permite descontar para calcular el Impuesto a la Renta, como gastos personales o sin sustento válido.",
    "principio de causalidad": "El principio de causalidad indica que un gasto debe estar relacionado con la generación de ingresos o el mantenimiento de la fuente productora para ser deducible.",
    "bancarizacion": "La bancarización consiste en usar medios de pago del sistema financiero para sustentar ciertas operaciones y permitir su reconocimiento tributario.",
    "comprobante valido": "Un comprobante válido debe cumplir los requisitos establecidos por SUNAT y estar correctamente emitido para sustentar una operación.",
    "sustento tributario": "El sustento tributario es la documentación que respalda una operación, como comprobantes de pago, contratos, medios de pago, registros contables y evidencias.",

    # MULTAS
    "que es una multa tributaria": "Una multa tributaria es una sanción aplicada por incumplir obligaciones tributarias, como no declarar, declarar fuera de plazo, no emitir comprobantes o llevar libros con atraso.",
    "gradualidad": "La gradualidad es un régimen que puede permitir reducir multas si el contribuyente regulariza voluntariamente o cumple ciertas condiciones.",
    "multa por no emitir comprobante": "No emitir comprobante de pago puede generar sanciones como multa o cierre temporal, según la infracción y la normativa aplicable.",
    "multa por libros atrasados": "Llevar libros contables con atraso puede generar multa. El monto depende del tipo de infracción y la norma vigente.",

    # EXPORTACIÓN / IMPORTACIÓN
    "exportacion": "La exportación es la venta de bienes o servicios hacia el exterior. En materia tributaria puede tener tratamiento especial, como saldo a favor del exportador en ciertos casos.",
    "importacion": "La importación es el ingreso de bienes desde el exterior al país. Puede estar sujeta a tributos aduaneros, IGV y otras obligaciones.",
    "drawback": "El drawback es un mecanismo de restitución de derechos arancelarios para ciertos exportadores que cumplen requisitos.",
    "aduanas": "Aduanas es el área encargada del control de ingreso y salida de mercancías del país, administrada por SUNAT.",

    # PREGUNTAS GENERALES
    "gracias": "¡De nada! Soy TribuTax. Si tienes otra consulta tributaria, escríbeme.",
    "ok": "Perfecto. Puedes hacerme otra consulta sobre IGV, SUNAT, RUC, comprobantes, renta o regímenes tributarios.",
    "adios": "Hasta luego. Recuerda que TribuTax puede ayudarte con tus consultas tributarias cuando lo necesites.",
    "ayuda": "Puedo ayudarte con IGV, RUC, SUNAT, comprobantes, facturas, boletas, notas de crédito, notas de débito, renta, regímenes tributarios, detracciones, retenciones, libros contables, UIT y Clave SOL.",
}

def limpiar_texto(texto):
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


def buscar_respuesta_local(mensaje):
    texto = limpiar_texto(mensaje)

    # 1. Coincidencia exacta o incluida
    for pregunta, respuesta in RESPUESTAS.items():
        pregunta_limpia = limpiar_texto(pregunta)

        if texto == pregunta_limpia:
            return respuesta

        if pregunta_limpia in texto:
            return respuesta

        if texto in pregunta_limpia and len(texto) > 4:
            return respuesta

    # 2. Coincidencia por palabras clave
    claves = {
        "hola": RESPUESTAS["hola"],
        "buenos dias": RESPUESTAS["buenos dias"],
        "buenas tardes": RESPUESTAS["buenas tardes"],
        "buenas noches": RESPUESTAS["buenas noches"],
        "quien eres": RESPUESTAS["quien eres"],
        "tributax": RESPUESTAS["que es tributax"],

        "igv": RESPUESTAS["que es el igv"],
        "impuesto general a las ventas": RESPUESTAS["que es el igv"],
        "credito fiscal": RESPUESTAS["credito fiscal"],
        "debito fiscal": RESPUESTAS["debito fiscal"],
        "base imponible": RESPUESTAS["base imponible igv"],

        "ruc": RESPUESTAS["que es el ruc"],
        "clave sol": RESPUESTAS["que es clave sol"],
        "sunat": RESPUESTAS["que es sunat"],
        "domicilio fiscal": RESPUESTAS["que es domicilio fiscal"],

        "factura electronica": RESPUESTAS["factura electronica"],
        "boleta electronica": RESPUESTAS["boleta electronica"],
        "factura": RESPUESTAS["factura"],
        "boleta": RESPUESTAS["boleta"],
        "comprobante": RESPUESTAS["que es comprobante de pago"],
        "recibo por honorarios": RESPUESTAS["recibo por honorarios"],

        "nota de debito": RESPUESTAS["que es nota de debito"],
        "debito": RESPUESTAS["que es nota de debito"],
        "nota de credito": RESPUESTAS["que es nota de credito"],

        "renta": RESPUESTAS["que es impuesto a la renta"],
        "primera categoria": RESPUESTAS["renta de primera categoria"],
        "segunda categoria": RESPUESTAS["renta de segunda categoria"],
        "tercera categoria": RESPUESTAS["renta de tercera categoria"],
        "cuarta categoria": RESPUESTAS["renta de cuarta categoria"],
        "quinta categoria": RESPUESTAS["renta de quinta categoria"],
        "pago a cuenta": RESPUESTAS["que es pago a cuenta"],
        "declaracion anual": RESPUESTAS["declaracion anual"],

        "nuevo rus": RESPUESTAS["que es nuevo rus"],
        "rus": RESPUESTAS["que es nuevo rus"],
        "rer": RESPUESTAS["que es rer"],
        "rmt": RESPUESTAS["que es rmt"],
        "regimen general": RESPUESTAS["regimen general"],
        "regimen": RESPUESTAS["cuales son los regimenes tributarios en peru"],

        "declaracion mensual": RESPUESTAS["que es declaracion mensual"],
        "cronograma": RESPUESTAS["que es el cronograma de vencimientos de sunat"],
        "multa": RESPUESTAS["que es una multa tributaria"],
        "interes moratorio": RESPUESTAS["interes moratorio"],
        "cobranza coactiva": RESPUESTAS["cobranza coactiva"],
        "fraccionamiento": RESPUESTAS["fraccionamiento tributario"],

        "detraccion": RESPUESTAS["detraccion"],
        "detracciones": RESPUESTAS["detraccion"],
        "retencion": RESPUESTAS["retencion"],
        "retenciones": RESPUESTAS["retencion"],
        "percepcion": RESPUESTAS["percepcion"],

        "registro de ventas": RESPUESTAS["registro de ventas"],
        "registro de compras": RESPUESTAS["registro de compras"],
        "libro diario": RESPUESTAS["libro diario"],
        "libro mayor": RESPUESTAS["libro mayor"],
        "libros electronicos": RESPUESTAS["libros electronicos"],
        "libros": RESPUESTAS["que libros contables estoy obligado a llevar"],
        "ple": RESPUESTAS["que es el ple de sunat"],
        "sire": RESPUESTAS["sire sunat"],

        "independiente": RESPUESTAS["soy independiente que debo pagar"],
        "honorarios": RESPUESTAS["recibo por honorarios"],
        "suspension": RESPUESTAS["suspension de cuarta categoria"],

        "gastos deducibles": RESPUESTAS["gastos deducibles"],
        "gastos no deducibles": RESPUESTAS["gastos no deducibles"],
        "causalidad": RESPUESTAS["principio de causalidad"],
        "bancarizacion": RESPUESTAS["bancarizacion"],
        "sustento": RESPUESTAS["sustento tributario"],

        "uit": RESPUESTAS["que es la uit"],
        "deuda": RESPUESTAS["como se si tengo deuda con sunat"],
        "exportacion": RESPUESTAS["exportacion"],
        "importacion": RESPUESTAS["importacion"],
        "aduanas": RESPUESTAS["aduanas"],
        "drawback": RESPUESTAS["drawback"],

        "gracias": RESPUESTAS["gracias"],
        "ayuda": RESPUESTAS["ayuda"],
        "adios": RESPUESTAS["adios"],
    }

    for clave, respuesta in claves.items():
        if clave in texto:
            return respuesta

    return None


def construir_contexto(historial):
    if not historial:
        return ""

    partes = []

    for item in historial[-6:]:
        usuario = item.get("usuario", "")
        bot = item.get("bot", "")

        if usuario:
            partes.append(f"Usuario: {usuario}")

        if bot:
            partes.append(f"TribuTax: {bot}")

    return "\n".join(partes)


def es_seguimiento(mensaje):
    texto = limpiar_texto(mensaje)

    frases = [
        "para que sirve",
        "y para que sirve",
        "como funciona",
        "cuando se usa",
        "cuando se emite",
        "dame un ejemplo",
        "un ejemplo",
        "ejemplo",
        "explicame mas",
        "mas informacion",
        "dame mas informacion",
        "como se calcula",
        "cual es su tasa",
        "quien lo emite",
        "quienes lo usan",
    ]

    if texto in frases:
        return True

    if len(texto.split()) <= 5 and any(p in texto for p in ["sirve", "ejemplo", "funciona", "usa", "emite", "calcula"]):
        return True

    return False


def respuesta_contextual_local(mensaje, historial):
    if not historial:
        return None

    if not es_seguimiento(mensaje):
        return None

    ultimo = historial[-1]
    tema = limpiar_texto(ultimo.get("usuario", "") + " " + ultimo.get("bot", ""))
    pregunta = limpiar_texto(mensaje)

    if "nota de debito" in tema or "debito" in tema:
        if "sirve" in pregunta:
            return "La nota de débito sirve para aumentar el valor de una operación ya facturada. Se usa cuando hay intereses, penalidades, diferencia de precio, gastos adicionales o ajustes."
        if "ejemplo" in pregunta:
            return "Ejemplo: emitiste una factura por S/ 500, pero luego debes cobrar S/ 50 adicionales por transporte. Entonces emites una nota de débito por S/ 50."
        if "emite" in pregunta or "usa" in pregunta:
            return "La nota de débito se emite cuando necesitas incrementar el monto de una factura o boleta ya emitida."
        return "Sobre la nota de débito: sirve para aumentar el valor de una operación ya facturada."

    if "nota de credito" in tema:
        if "sirve" in pregunta:
            return "La nota de crédito sirve para disminuir, corregir o anular total o parcialmente una factura o boleta ya emitida."
        if "ejemplo" in pregunta:
            return "Ejemplo: si emitiste una factura por S/ 300 y el cliente devuelve productos por S/ 80, emites una nota de crédito por S/ 80."
        return "Sobre la nota de crédito: se usa para reducir, corregir o anular una operación ya emitida."

    if "igv" in tema:
        if "sirve" in pregunta:
            return "El IGV sirve para gravar el consumo de bienes y servicios en Perú. Las empresas lo cobran en sus ventas y luego lo declaran ante SUNAT."
        if "calcula" in pregunta:
            return "El IGV se calcula aplicando el 18% sobre la base imponible. Si la base es S/ 100, el IGV es S/ 18 y el total S/ 118."
        if "ejemplo" in pregunta:
            return "Ejemplo: si vendes un producto con base de S/ 200, el IGV será S/ 36 y el total será S/ 236."
        return "Sobre el IGV: es el Impuesto General a las Ventas y su tasa general en Perú es 18%."

    if "uit" in tema:
        if "sirve" in pregunta:
            return "La UIT sirve como valor de referencia para calcular impuestos, multas, deducciones, límites de ingresos, sanciones y obligaciones tributarias."
        return "Sobre la UIT: es la Unidad Impositiva Tributaria usada como referencia en normas tributarias y administrativas."

    if "clave sol" in tema:
        if "sirve" in pregunta:
            return "La Clave SOL sirve para ingresar a SUNAT Operaciones en Línea y realizar trámites como declarar, pagar, consultar deudas y emitir comprobantes."
        return "Sobre la Clave SOL: es la contraseña para acceder a los servicios virtuales de SUNAT."

    return None


def responder_con_gemini(mensaje, historial=None):
    if client is None or types is None:
        return None

    contexto = construir_contexto(historial or [])

    prompt = f"""
{BASE_TRIBUTARIA}

Historial reciente:
{contexto}

Pregunta actual:
{mensaje}

Responde de forma clara y directa.
Si la pregunta actual es corta como "para qué sirve", "dame un ejemplo" o "cómo funciona",
usa el historial para entender a qué tema se refiere.
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

    except Exception as e:
        print("Gemini no disponible:", str(e))
        return None


def respuesta_fallback():
    return (
        "Soy TribuTax. Puedo ayudarte con IGV, SUNAT, RUC, comprobantes de pago, "
        "Impuesto a la Renta, regímenes tributarios, detracciones, retenciones, "
        "libros contables, UIT y Clave SOL."
    )


def responder_chatbot(mensaje, historial=None):
    if historial is None:
        historial = []

    try:
        mensaje = mensaje.strip()

        if mensaje == "":
            return "Escribe tu consulta para poder ayudarte."

        contextual = respuesta_contextual_local(mensaje, historial)

        if contextual:
            return contextual

        local = buscar_respuesta_local(mensaje)

        if local:
            return local

        gemini = responder_con_gemini(mensaje, historial)

        if gemini:
            return gemini

        return respuesta_fallback()

    except Exception as e:
        print("ERROR EN responder_chatbot:", str(e))
        return respuesta_fallback()