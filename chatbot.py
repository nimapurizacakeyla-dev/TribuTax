import os
import re
import difflib
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

Respondes en español, de forma clara, rápida, sencilla y útil.
Puedes responder teoría, consultas cortas, preguntas con errores de escritura y casos prácticos.

Temas:
IGV, crédito fiscal, débito fiscal, exonerado, inafecto, RUC, SUNAT, Clave SOL,
comprobantes de pago, factura, boleta, recibo por honorarios, nota de crédito,
nota de débito, guía de remisión, factura electrónica, XML, CDR, OSE, PSE,
Impuesto a la Renta, rentas de primera, segunda, tercera, cuarta y quinta categoría,
pagos a cuenta, declaración jurada anual, gastos deducibles, gastos no deducibles,
adiciones tributarias, deducciones tributarias, renta neta imponible,
Nuevo RUS, RER, RMT, Régimen General, detracciones, retenciones, percepciones,
libros contables, Registro de Ventas, Registro de Compras, PLE, SIRE, RVIE, RCE,
UIT, multas, gradualidad, deuda tributaria, fraccionamiento, aplazamiento,
cobranza coactiva, fiscalización, carta inductiva, esquela, requerimiento SUNAT,
reclamación, apelación, Tribunal Fiscal, bancarización, medios de pago,
planilla, EsSalud, ONP, AFP, independientes, suspensión de cuarta,
ITAN, ITF, ISC, impuesto predial, alcabala, arbitrios, aduanas, importación,
exportación y drawback.

Reglas:
- Si el usuario menciona un tema nuevo, responde ese tema y no el anterior.
- Si el usuario pregunta algo corto como "¿para qué sirve?", "dame un ejemplo",
  "¿cómo funciona?", usa el último tema del historial.
- Si el usuario escribe con errores, intenta interpretar la intención.
- Si el usuario pega un caso práctico con números, intenta resolverlo.
- Si faltan datos para resolver, explica qué datos faltan y da la fórmula.
- No ayudes a evadir impuestos, falsificar comprobantes, ocultar ingresos o engañar a SUNAT.
- Si la pregunta es ilegal, rechaza esa parte y ofrece una alternativa legal.
- Si se necesitan tasas, límites, fechas o montos vigentes exactos, recomienda verificar SUNAT,
  municipalidad o consultar con un contador.
"""


PREGUNTAS_PROHIBIDAS = [
    "como evadir impuestos",
    "evadir impuestos",
    "como no pagar impuestos",
    "no pagar impuestos",
    "ocultar ingresos",
    "como ocultar ingresos",
    "facturas falsas",
    "hacer factura falsa",
    "comprobante falso",
    "como engañar a sunat",
    "enganar a sunat",
    "engañar a sunat",
    "burlar sunat",
    "declarar menos ventas",
    "bajar impuestos ilegalmente",
    "no declarar ventas",
    "falsificar factura",
    "falsificar comprobante",
    "lavar dinero",
    "lavado de dinero",
    "crear gastos falsos",
    "inventar gastos",
    "boletas falsas",
    "ruc falso",
    "como pagar menos mintiendo",
    "como reducir impuestos ilegalmente",
]


RESPUESTAS_DIRECTAS = {
    "hola": "¡Hola! Soy TribuTax, tu asistente virtual tributario. Puedo ayudarte con IGV, RUC, SUNAT, comprobantes, Impuesto a la Renta, regímenes tributarios, detracciones, retenciones, libros contables, UIT, multas, deudas y casos prácticos.",
    "buenos dias": "¡Buenos días! Soy TribuTax. Escríbeme tu consulta tributaria o pega tu caso práctico y te ayudo a resolverlo.",
    "buenas tardes": "¡Buenas tardes! Soy TribuTax. Puedo ayudarte con teoría tributaria y cálculos prácticos.",
    "buenas noches": "¡Buenas noches! Soy TribuTax. Estoy listo para ayudarte con tus dudas tributarias.",
    "quien eres": "Soy TribuTax, un asistente virtual tributario creado para responder consultas sobre tributación peruana y resolver casos prácticos.",
    "que eres": "Soy TribuTax, un chatbot de orientación tributaria de Perú.",
    "que es tributax": "TribuTax es un chatbot de ayuda tributaria que responde sobre IGV, RUC, SUNAT, comprobantes, renta, regímenes, detracciones, retenciones, libros contables y casos prácticos.",
    "tributax": "Soy TribuTax, tu asistente virtual tributario.",
    "ayuda": "Puedo ayudarte con IGV, RUC, SUNAT, facturas, boletas, notas de crédito, notas de débito, renta, regímenes, detracciones, retenciones, percepciones, libros contables, multas, deudas, planilla, aduanas y casos prácticos.",
    "gracias": "¡De nada! Si tienes otra consulta tributaria o un caso práctico, escríbeme.",
    "ok": "Perfecto. Puedes hacerme otra consulta tributaria o pegar un caso para resolverlo.",
    "adios": "Hasta luego. Recuerda que TribuTax puede ayudarte con consultas tributarias y casos prácticos.",
}


PREGUNTAS_ESPECIFICAS = {
    "que es el igv y cual es su tasa actual": "El IGV es el Impuesto General a las Ventas. En Perú grava principalmente la venta de bienes, la prestación de servicios, contratos de construcción, primera venta de inmuebles realizada por constructores e importaciones. Su tasa general es 18%, compuesta por 16% de IGV y 2% de Impuesto de Promoción Municipal.",
    "como se calcula el igv de una factura": "Si el precio no incluye IGV: IGV = base x 18% y total = base + IGV. Ejemplo: base S/ 100, IGV S/ 18, total S/ 118. Si el precio ya incluye IGV: base = total / 1.18 e IGV = total - base.",
    "que operaciones estan exoneradas del igv": "Las operaciones exoneradas del IGV son aquellas que están dentro del ámbito del impuesto, pero una norma las libera del pago. La lista puede variar, por eso se recomienda revisar SUNAT.",
    "que es el credito fiscal y como se usa": "El crédito fiscal es el IGV pagado en compras del negocio que puede descontarse del IGV generado por ventas. Para usarlo, la compra debe estar vinculada al negocio, tener comprobante válido, estar registrada correctamente y cumplir requisitos tributarios.",
    "cual es la diferencia entre exonerado e inafecto": "Una operación exonerada está dentro del campo del IGV, pero una norma la libera del pago. Una operación inafecta no está dentro del campo de aplicación del IGV.",

    "cuales son las rentas de primera segunda tercera cuarta y quinta categoria": "Primera categoría: alquileres. Segunda categoría: intereses, regalías, dividendos y ganancias de capital. Tercera categoría: actividades empresariales. Cuarta categoría: trabajo independiente con recibos por honorarios. Quinta categoría: trabajo dependiente en planilla.",
    "como se calcula el impuesto a la renta de tercera categoria": "El Impuesto a la Renta de tercera categoría se calcula partiendo de los ingresos empresariales. Luego se restan costos y gastos deducibles para obtener la renta neta. Después se agregan adiciones tributarias, se restan deducciones permitidas y se aplica la tasa correspondiente, como 29.5% si corresponde.",
    "que gastos son deducibles para la renta empresarial": "Son deducibles los gastos necesarios para generar renta o mantener la fuente productora. Deben cumplir causalidad, razonabilidad, sustento documentario, comprobante válido, registro contable y bancarización cuando corresponda.",
    "cuales son los pagos a cuenta mensuales": "Los pagos a cuenta mensuales son adelantos del Impuesto a la Renta que se realizan durante el año. Luego se descuentan del impuesto anual determinado en la declaración jurada anual.",
    "que es la declaracion jurada anual": "La declaración jurada anual es la declaración donde el contribuyente informa ingresos, costos, gastos, renta neta, pagos a cuenta y determina si tiene impuesto por pagar o saldo a favor.",

    "cuando se emite una factura y cuando una boleta": "Se emite factura cuando el cliente necesita sustentar crédito fiscal, gasto o costo tributario, normalmente empresas o personas con RUC. Se emite boleta cuando la venta o servicio es para un consumidor final.",
    "que es una nota de credito y cuando se emite": "La nota de crédito es un comprobante que reduce, corrige o anula total o parcialmente una factura o boleta. Se emite por devoluciones, descuentos posteriores, errores o anulación de operaciones.",
    "que es una nota de debito": "La nota de débito es un comprobante que aumenta el valor de una factura o boleta ya emitida. Se usa por intereses, penalidades, diferencias de precio, gastos adicionales o ajustes posteriores.",
    "que es el comprobante de retencion": "El comprobante de retención acredita que un agente de retención designado por SUNAT retuvo parte del pago, generalmente vinculado al IGV, para luego entregarlo al fisco.",
    "como funciona la factura electronica": "La factura electrónica es un comprobante digital con validez tributaria. Se emite mediante sistemas autorizados por SUNAT, se envía al cliente y queda registrada electrónicamente.",

    "cuales son los regimenes tributarios en peru": "En Perú existen principalmente cuatro regímenes tributarios: Nuevo RUS, RER, RMT y Régimen General. Cada uno tiene requisitos, límites, comprobantes permitidos y obligaciones contables distintas.",
    "cual es la diferencia entre rus rer rmt y regimen general": "Nuevo RUS: pequeños negocios de personas naturales con cuota fija. RER: régimen especial con límites. RMT: régimen para micro y pequeñas empresas. Régimen General: empresas con obligaciones completas.",
    "que limite de ingresos tiene cada regimen": "Los límites de ingresos dependen del régimen tributario y pueden actualizarse. Para montos exactos vigentes se debe revisar SUNAT.",
    "como me cambio de regimen tributario": "El cambio de régimen depende del régimen actual, ingresos, actividad y régimen al que deseas pasar. Puede realizarse mediante declaración mensual o trámites SUNAT según el caso.",
    "que libros contables lleva cada regimen": "Nuevo RUS normalmente no lleva libros formales. RER lleva Registro de Compras y Registro de Ventas. RMT y Régimen General llevan libros según ingresos, como Registro de Ventas, Registro de Compras, Diario, Mayor e Inventarios si corresponde.",

    "cuando vencen las declaraciones mensuales": "Las declaraciones mensuales vencen según el cronograma de SUNAT, el periodo tributario y el último dígito del RUC.",
    "que es el cronograma de vencimientos de sunat": "Es el calendario oficial de SUNAT que indica las fechas límite para declarar y pagar impuestos según el último dígito del RUC.",
    "que pasa si no declaro a tiempo": "Si no declaras a tiempo puedes generar multas, intereses moratorios, deuda tributaria y posibles restricciones. Lo recomendable es regularizar cuanto antes.",
    "cuanto es la multa por no declarar": "La multa por no declarar depende del régimen, tipo de obligación, tributo omitido y si regularizas voluntariamente. Para monto exacto se debe revisar SUNAT.",
    "como se regulariza una deuda tributaria": "Para regularizar una deuda tributaria debes ingresar a SUNAT con RUC y Clave SOL, revisar la deuda, presentar declaraciones omitidas, pagar o solicitar fraccionamiento/aplazamiento si corresponde.",

    "que es el sistema de detracciones": "El sistema de detracciones consiste en depositar un porcentaje del pago en una cuenta del Banco de la Nación a nombre del proveedor. Ese dinero se usa para pagar obligaciones tributarias.",
    "que bienes y servicios estan sujetos a detraccion": "Los bienes y servicios sujetos a detracción están definidos por SUNAT y pueden incluir determinados servicios, transporte, construcción, bienes específicos y otras operaciones. Se debe revisar la tabla vigente.",
    "cual es el porcentaje de detraccion": "El porcentaje de detracción depende del bien o servicio. No existe un solo porcentaje para todos los casos. Se debe revisar la tabla vigente de SUNAT.",
    "que es la retencion del igv": "La retención del IGV es un mecanismo por el cual un agente designado por SUNAT retiene parte del IGV al proveedor y luego lo entrega al fisco.",
    "quienes son agentes de retencion": "Los agentes de retención son contribuyentes designados por SUNAT para retener parte del IGV en determinadas operaciones.",

    "que libros contables estoy obligado a llevar": "Los libros contables dependen del régimen tributario, nivel de ingresos y tipo de contribuyente. Pueden incluir Registro de Ventas, Registro de Compras, Libro Diario, Libro Mayor e Inventarios.",
    "que es el ple de sunat": "El PLE es el Programa de Libros Electrónicos de SUNAT. Sirve para validar y presentar libros contables electrónicos.",
    "como se lleva el registro de ventas": "El Registro de Ventas se lleva anotando comprobantes emitidos por ventas o servicios, como facturas, boletas, notas de crédito y notas de débito.",
    "como se lleva el registro de compras": "El Registro de Compras se lleva anotando comprobantes recibidos por compras, gastos y servicios vinculados al negocio.",
    "cual es el atraso maximo permitido en los libros": "El atraso máximo depende del tipo de libro contable y norma vigente. Para evitar sanciones se deben revisar los plazos oficiales de SUNAT.",

    "como calculo mis impuestos si soy independiente": "Si eres independiente, normalmente generas renta de cuarta categoría y emites recibos por honorarios. Debes revisar ingresos, retenciones, pagos a cuenta y obligación de declarar.",
    "puedo deducir gastos de mi casa si trabajo desde ahi": "Depende de si el gasto está directamente vinculado a generar ingresos y si cumple requisitos. No todo gasto del hogar es deducible.",
    "que es la uit y para que sirve": "La UIT es la Unidad Impositiva Tributaria. Sirve como referencia para calcular impuestos, multas, deducciones, límites de ingresos, sanciones e infracciones.",
    "como se si tengo deuda con sunat": "Puedes consultar deuda ingresando a SUNAT Operaciones en Línea con tu RUC, usuario y Clave SOL.",
    "como obtengo mi clave sol": "Puedes obtener tu Clave SOL desde SUNAT por canales virtuales o presenciales, validando tu identidad y datos del contribuyente.",
}


TEMAS = {
    "igv": {
        "aliases": ["igv", "impuesto general a las ventas", "tasa igv", "igv incluido", "precio con igv", "precio sin igv", "base imponible"],
        "que_es": PREGUNTAS_ESPECIFICAS["que es el igv y cual es su tasa actual"],
        "para_que_sirve": "El IGV sirve para gravar el consumo de bienes y servicios. Las empresas lo cobran en sus ventas y luego lo declaran ante SUNAT.",
        "como_funciona": "El IGV funciona comparando el débito fiscal de ventas con el crédito fiscal de compras. Si el débito es mayor, se paga la diferencia.",
        "como_se_calcula": PREGUNTAS_ESPECIFICAS["como se calcula el igv de una factura"],
        "ejemplo": "Ejemplo: si vendes por S/ 1,000 más IGV, el IGV es S/ 180 y el total es S/ 1,180.",
        "extra": "El IGV se declara normalmente de forma mensual y se determina con ventas, compras, crédito fiscal y débito fiscal.",
    },
    "credito fiscal": {
        "aliases": ["credito fiscal", "crédito fiscal", "igv compras", "usar credito fiscal"],
        "que_es": "El crédito fiscal es el IGV pagado en compras del negocio que puede descontarse del IGV de ventas.",
        "para_que_sirve": "Sirve para reducir el IGV por pagar.",
        "como_funciona": "Funciona restando el IGV de compras aceptado al IGV de ventas.",
        "como_se_calcula": "Se suma el IGV de compras aceptadas y se descuenta del débito fiscal.",
        "ejemplo": "Si el IGV de ventas es S/ 500 y el de compras es S/ 200, pagas S/ 300.",
        "extra": "Debe cumplir causalidad, comprobante válido, registro y relación con operaciones gravadas.",
    },
    "ruc": {
        "aliases": ["ruc", "registro unico de contribuyentes", "sacar ruc", "numero ruc"],
        "que_es": "El RUC es el Registro Único de Contribuyentes. Identifica a personas y empresas ante SUNAT.",
        "para_que_sirve": "Sirve para emitir comprobantes, declarar impuestos, consultar deudas y operar formalmente.",
        "como_funciona": "SUNAT registra tu actividad, domicilio fiscal, régimen, comprobantes, declaraciones y pagos mediante tu RUC.",
        "como_se_calcula": "No se calcula. SUNAT lo asigna al inscribirte.",
        "ejemplo": "Si abres una tienda, necesitas RUC para emitir boletas o facturas.",
        "extra": "Deben tener RUC quienes realizan actividades económicas, venden, prestan servicios o alquilan bienes.",
    },
    "sunat": {
        "aliases": ["sunat", "administracion tributaria", "portal sunat", "operaciones en linea"],
        "que_es": "SUNAT es la Superintendencia Nacional de Aduanas y de Administración Tributaria.",
        "para_que_sirve": "Sirve para registrar contribuyentes, recaudar impuestos, fiscalizar obligaciones y controlar aduanas.",
        "como_funciona": "Funciona mediante RUC, declaraciones, pagos, fiscalizaciones, notificaciones y cobranza.",
        "como_se_calcula": "SUNAT no se calcula; es una entidad pública.",
        "ejemplo": "Una empresa declara IGV y renta mensual en SUNAT Operaciones en Línea.",
        "extra": "Permite consultar RUC, deudas, comprobantes, declaraciones y trámites aduaneros.",
    },
    "clave sol": {
        "aliases": ["clave sol", "contraseña sunat", "usuario sol", "recuperar clave sol"],
        "que_es": "La Clave SOL es la contraseña para ingresar a SUNAT Operaciones en Línea.",
        "para_que_sirve": "Sirve para declarar, pagar, consultar deudas, emitir comprobantes y realizar trámites virtuales.",
        "como_funciona": "Ingresas con RUC, usuario y Clave SOL al portal SUNAT.",
        "como_se_calcula": "No se calcula; se obtiene o recupera en SUNAT.",
        "ejemplo": "Para consultar deuda, ingresas con RUC y Clave SOL.",
        "extra": "No debes compartirla porque permite hacer trámites a nombre del contribuyente.",
    },
    "factura": {
        "aliases": ["factura", "factra", "facura", "fatura", "factura electronica"],
        "que_es": "La factura es un comprobante que acredita una venta o servicio y permite sustentar gasto, costo o crédito fiscal.",
        "para_que_sirve": "Sirve para sustentar operaciones ante SUNAT y respaldar crédito fiscal si corresponde.",
        "como_funciona": "El vendedor la emite, el comprador la recibe y ambos la registran según corresponda.",
        "como_se_calcula": "Puede incluir base imponible, IGV y total. Ejemplo: base S/ 100, IGV S/ 18, total S/ 118.",
        "ejemplo": "Una empresa vende mercadería a otra empresa y emite factura.",
        "extra": "La factura electrónica tiene validez tributaria si se emite mediante sistemas autorizados.",
    },
    "boleta": {
        "aliases": ["boleta", "voleta", "boleto", "boleta de venta"],
        "que_es": "La boleta es un comprobante que se emite generalmente a consumidores finales.",
        "para_que_sirve": "Sirve para acreditar una venta o servicio a consumidor final.",
        "como_funciona": "El negocio la emite y registra la operación como ingreso.",
        "como_se_calcula": "Puede incluir IGV dentro del precio final.",
        "ejemplo": "Una tienda vende una mochila a una persona natural y emite boleta.",
        "extra": "Generalmente no permite usar crédito fiscal.",
    },
    "nota de debito": {
        "aliases": ["nota de debito", "nota debito", "debito", "nota débito"],
        "que_es": PREGUNTAS_ESPECIFICAS["que es una nota de debito"],
        "para_que_sirve": "Sirve para aumentar el valor de una operación ya facturada.",
        "como_funciona": "Modifica una operación anterior aumentando el importe.",
        "como_se_calcula": "Se calcula por el monto adicional a cobrar más IGV si corresponde.",
        "ejemplo": "Factura S/ 500 y faltó cobrar S/ 50: emites nota de débito por S/ 50.",
        "extra": "Se usa por recargos, intereses, penalidades o diferencias de precio.",
    },
    "nota de credito": {
        "aliases": ["nota de credito", "nota credito", "nota crédito"],
        "que_es": "La nota de crédito reduce, corrige o anula total o parcialmente una factura o boleta.",
        "para_que_sirve": "Sirve para disminuir el valor de una operación o corregir errores.",
        "como_funciona": "Modifica una operación anterior disminuyendo el importe.",
        "como_se_calcula": "Se calcula por el monto a descontar o devolver.",
        "ejemplo": "Factura S/ 300 y devolución S/ 80: emites nota de crédito por S/ 80.",
        "extra": "Se usa por devoluciones, descuentos, errores o anulaciones.",
    },
    "impuesto a la renta": {
        "aliases": ["impuesto a la renta", "renta", "ir", "renta empresarial"],
        "que_es": "El Impuesto a la Renta grava ingresos de personas y empresas.",
        "para_que_sirve": "Sirve para tributar ingresos, ganancias o utilidades.",
        "como_funciona": "Clasifica ingresos por categorías: primera, segunda, tercera, cuarta y quinta.",
        "como_se_calcula": "Depende de la categoría. En empresas: ingresos - costos - gastos deducibles + adiciones - deducciones.",
        "ejemplo": "Una empresa genera renta de tercera; un independiente renta de cuarta; un trabajador en planilla renta de quinta.",
        "extra": PREGUNTAS_ESPECIFICAS["cuales son las rentas de primera segunda tercera cuarta y quinta categoria"],
    },
    "renta de primera categoria": {
        "aliases": ["primera categoria", "renta de primera", "alquiler", "alquileres", "arrendamiento"],
        "que_es": "La renta de primera categoría proviene principalmente del alquiler de bienes muebles o inmuebles.",
        "para_que_sirve": "Sirve para tributar ingresos por arrendamiento.",
        "como_funciona": "El propietario declara y paga impuesto por alquileres.",
        "como_se_calcula": "Depende de las reglas vigentes para rentas de primera categoría.",
        "ejemplo": "Alquilas un departamento y recibes una mensualidad.",
        "extra": "Debe declararse según corresponda.",
    },
    "renta de segunda categoria": {
        "aliases": ["segunda categoria", "renta de segunda", "dividendos", "intereses", "ganancia de capital"],
        "que_es": "La renta de segunda categoría proviene de intereses, regalías, dividendos y ganancias de capital.",
        "para_que_sirve": "Sirve para tributar ingresos de capital o inversiones.",
        "como_funciona": "Puede declararse o retenerse según el tipo de ingreso.",
        "como_se_calcula": "Depende del tipo de ingreso y norma vigente.",
        "ejemplo": "Recibir dividendos puede generar renta de segunda categoría.",
        "extra": "Puede aplicar a venta de valores o inmuebles según la norma.",
    },
    "renta de tercera categoria": {
        "aliases": ["tercera categoria", "renta de tercera", "renta empresarial", "empresa", "negocio"],
        "que_es": "La renta de tercera categoría corresponde a ingresos empresariales.",
        "para_que_sirve": "Sirve para tributar utilidades de empresas o negocios.",
        "como_funciona": "Se registran ingresos, costos, gastos, adiciones y deducciones para determinar renta neta.",
        "como_se_calcula": PREGUNTAS_ESPECIFICAS["como se calcula el impuesto a la renta de tercera categoria"],
        "ejemplo": "Una tienda que compra y vende productos genera renta de tercera.",
        "extra": "Se relaciona con RER, RMT y Régimen General.",
    },
    "renta de cuarta categoria": {
        "aliases": ["cuarta categoria", "renta de cuarta", "honorarios", "independiente", "trabajador independiente"],
        "que_es": "La renta de cuarta categoría corresponde al trabajo independiente con recibos por honorarios.",
        "para_que_sirve": "Sirve para tributar ingresos por servicios independientes.",
        "como_funciona": "El trabajador emite recibos y puede estar sujeto a retención o pago a cuenta.",
        "como_se_calcula": "Depende de ingresos, retenciones, pagos a cuenta y límites vigentes.",
        "ejemplo": "Un contador independiente emite recibo por honorarios.",
        "extra": "Puede solicitarse suspensión de retenciones si cumple requisitos.",
    },
    "renta de quinta categoria": {
        "aliases": ["quinta categoria", "renta de quinta", "planilla", "sueldo", "trabajador en planilla"],
        "que_es": "La renta de quinta categoría corresponde al trabajo dependiente en planilla.",
        "para_que_sirve": "Sirve para tributar sueldos y remuneraciones.",
        "como_funciona": "El empleador calcula y retiene el impuesto si corresponde.",
        "como_se_calcula": "Se calcula sobre ingresos anuales proyectados y deducciones aplicables.",
        "ejemplo": "Un trabajador contratado recibe sueldo mensual y figura en planilla.",
        "extra": "El empleador suele encargarse de la retención.",
    },
    "regimen tributario": {
        "aliases": ["regimen", "regimenes", "regimen tributario", "regimenes tributarios"],
        "que_es": "Un régimen tributario define cómo un contribuyente declara, paga impuestos, emite comprobantes y lleva libros.",
        "para_que_sirve": "Sirve para ordenar obligaciones tributarias según tipo de negocio e ingresos.",
        "como_funciona": "Cada régimen tiene requisitos, límites y obligaciones distintas.",
        "como_se_calcula": "No se calcula; se elige o determina según actividad, ingresos y requisitos.",
        "ejemplo": "Una bodega pequeña puede estar en Nuevo RUS; una MYPE en RMT.",
        "extra": PREGUNTAS_ESPECIFICAS["cual es la diferencia entre rus rer rmt y regimen general"],
    },
    "nuevo rus": {
        "aliases": ["nuevo rus", "rus", "regimen unico simplificado"],
        "que_es": "El Nuevo RUS es un régimen para pequeños negocios de personas naturales.",
        "para_que_sirve": "Sirve para pagar una cuota mensual fija con obligaciones simplificadas.",
        "como_funciona": "Se paga cuota según categoría y normalmente no se emiten facturas.",
        "como_se_calcula": "La cuota depende de ingresos o compras del periodo.",
        "ejemplo": "Una pequeña bodega podría estar en Nuevo RUS si cumple requisitos.",
        "extra": "No todos los negocios pueden acogerse.",
    },
    "rer": {
        "aliases": ["rer", "regimen especial", "regimen especial de renta"],
        "que_es": "El RER es el Régimen Especial de Renta.",
        "para_que_sirve": "Sirve para negocios con límites y obligaciones simplificadas.",
        "como_funciona": "Declara IGV y renta mensual con obligaciones menores al Régimen General.",
        "como_se_calcula": "Depende de las reglas vigentes del régimen.",
        "ejemplo": "Un pequeño negocio comercial que emite facturas podría estar en RER.",
        "extra": "No todas las actividades pueden estar en RER.",
    },
    "rmt": {
        "aliases": ["rmt", "regimen mype tributario", "mype tributario", "mype"],
        "que_es": "El RMT es el Régimen MYPE Tributario.",
        "para_que_sirve": "Sirve para que micro y pequeñas empresas tributen según utilidad.",
        "como_funciona": "Declara mensualmente y determina renta anual según resultados.",
        "como_se_calcula": "Se calcula con ingresos, costos, gastos y tasas aplicables.",
        "ejemplo": "Una pequeña empresa formal puede estar en RMT.",
        "extra": "Permite obligaciones acordes al nivel de ingresos.",
    },
    "regimen general": {
        "aliases": ["regimen general", "general"],
        "que_es": "El Régimen General es para empresas con obligaciones completas.",
        "para_que_sirve": "Sirve para empresas con operaciones amplias.",
        "como_funciona": "Declara IGV mensual, pagos a cuenta y declaración anual.",
        "como_se_calcula": "Se calcula con ingresos, costos, gastos deducibles y renta neta.",
        "ejemplo": "Una empresa grande suele estar en Régimen General.",
        "extra": "Implica contabilidad completa.",
    },
    "detraccion": {
        "aliases": ["detraccion", "detracciones", "sistema de detracciones", "spott"],
        "que_es": PREGUNTAS_ESPECIFICAS["que es el sistema de detracciones"],
        "para_que_sirve": "Sirve para asegurar fondos destinados al pago de tributos.",
        "como_funciona": "El comprador deposita un porcentaje en la cuenta de detracciones del proveedor.",
        "como_se_calcula": "Monto de la operación x porcentaje de detracción.",
        "ejemplo": "S/ 1,000 con 12% de detracción: depósito S/ 120 y saldo S/ 880.",
        "extra": "Verifica el porcentaje exacto en SUNAT.",
    },
    "retencion": {
        "aliases": ["retencion", "retenciones", "retencion igv", "agente de retencion"],
        "que_es": PREGUNTAS_ESPECIFICAS["que es la retencion del igv"],
        "para_que_sirve": "Sirve para asegurar la recaudación del IGV.",
        "como_funciona": "El agente retiene parte del impuesto y lo entrega a SUNAT.",
        "como_se_calcula": "Monto x porcentaje de retención.",
        "ejemplo": "S/ 2,000 con 3% de retención: retención S/ 60.",
        "extra": "Solo aplica si corresponde agente de retención.",
    },
    "percepcion": {
        "aliases": ["percepcion", "percepciones", "percepcion igv"],
        "que_es": "La percepción es un cobro adelantado del impuesto que se adiciona al comprador.",
        "para_que_sirve": "Sirve para adelantar recaudación tributaria.",
        "como_funciona": "El agente cobra un importe adicional al comprador.",
        "como_se_calcula": "Monto x porcentaje de percepción; total = monto + percepción.",
        "ejemplo": "S/ 1,000 con percepción 2%: percepción S/ 20, total S/ 1,020.",
        "extra": "No es igual a detracción ni retención.",
    },
    "libros contables": {
        "aliases": ["libros", "libros contables", "contabilidad", "libro diario", "libro mayor"],
        "que_es": "Los libros contables son registros de operaciones económicas del contribuyente.",
        "para_que_sirve": "Sirven para sustentar compras, ventas, gastos, ingresos y declaraciones.",
        "como_funciona": "Registran comprobantes, movimientos y operaciones según régimen.",
        "como_se_calcula": "No se calculan, pero sirven para calcular impuestos.",
        "ejemplo": "Registro de Ventas y Registro de Compras.",
        "extra": PREGUNTAS_ESPECIFICAS["que libros contables estoy obligado a llevar"],
    },
    "ple": {
        "aliases": ["ple", "programa de libros electronicos", "libros electronicos"],
        "que_es": PREGUNTAS_ESPECIFICAS["que es el ple de sunat"],
        "para_que_sirve": "Sirve para validar y presentar libros electrónicos.",
        "como_funciona": "Generas archivos con estructura SUNAT y los validas en PLE.",
        "como_se_calcula": "No se calcula; es herramienta de validación.",
        "ejemplo": "Validar Registro de Compras electrónico.",
        "extra": "Exige formatos y plazos.",
    },
    "sire": {
        "aliases": ["sire", "sistema integrado de registros electronicos", "rvie", "rce"],
        "que_es": "El SIRE es el Sistema Integrado de Registros Electrónicos de SUNAT.",
        "para_que_sirve": "Facilita registros electrónicos de ventas y compras.",
        "como_funciona": "SUNAT propone información y el contribuyente revisa o ajusta.",
        "como_se_calcula": "No se calcula; es un sistema de registro.",
        "ejemplo": "Revisar Registro de Compras Electrónico antes de declarar.",
        "extra": "Cruza comprobantes electrónicos con declaraciones.",
    },
    "registro de ventas": {
        "aliases": ["registro de ventas", "registro ventas", "rvie"],
        "que_es": "El Registro de Ventas contiene los comprobantes emitidos por ventas o servicios.",
        "para_que_sirve": "Sirve para sustentar ingresos y determinar el débito fiscal.",
        "como_funciona": PREGUNTAS_ESPECIFICAS["como se lleva el registro de ventas"],
        "como_se_calcula": "No se calcula como impuesto, pero sirve para determinar ventas e IGV.",
        "ejemplo": "Se registran facturas, boletas, notas de crédito y notas de débito emitidas.",
        "extra": "Puede llevarse electrónicamente.",
    },
    "registro de compras": {
        "aliases": ["registro de compras", "registro compras", "rce"],
        "que_es": "El Registro de Compras contiene comprobantes recibidos por compras, gastos y servicios.",
        "para_que_sirve": "Sirve para sustentar crédito fiscal, costos y gastos.",
        "como_funciona": PREGUNTAS_ESPECIFICAS["como se lleva el registro de compras"],
        "como_se_calcula": "No se calcula como impuesto, pero sirve para determinar crédito fiscal y gastos.",
        "ejemplo": "Se registran facturas de proveedores vinculadas al negocio.",
        "extra": "Debe cumplir requisitos formales y plazos.",
    },
    "uit": {
        "aliases": ["uit", "unidad impositiva tributaria", "valor uit"],
        "que_es": "La UIT es un valor de referencia usado para multas, deducciones, límites y sanciones.",
        "para_que_sirve": PREGUNTAS_ESPECIFICAS["que es la uit y para que sirve"],
        "como_funciona": "Las normas expresan montos en porcentajes o múltiplos de UIT.",
        "como_se_calcula": "La fija el Estado cada año.",
        "ejemplo": "Una multa puede ser un porcentaje de la UIT.",
        "extra": "Consulta el valor vigente en norma oficial.",
    },
    "deuda tributaria": {
        "aliases": ["deuda", "deuda tributaria", "deuda sunat", "regularizar deuda"],
        "que_es": "La deuda tributaria es el monto pendiente por tributos, multas, intereses u obligaciones.",
        "para_que_sirve": "Sirve para identificar obligaciones pendientes y regularizarlas.",
        "como_funciona": "SUNAT registra deuda cuando no se declara o paga correctamente.",
        "como_se_calcula": "Tributo pendiente + intereses + multas si corresponde.",
        "ejemplo": "No pagar IGV mensual dentro del plazo genera deuda.",
        "extra": PREGUNTAS_ESPECIFICAS["como se regulariza una deuda tributaria"],
    },
    "fraccionamiento": {
        "aliases": ["fraccionamiento", "fraccionar", "cuotas", "aplazamiento"],
        "que_es": "El fraccionamiento permite pagar deuda tributaria en cuotas si se cumplen requisitos.",
        "para_que_sirve": "Sirve para facilitar el pago de una deuda.",
        "como_funciona": "Solicitas a SUNAT y se aprueba un cronograma si procede.",
        "como_se_calcula": "Depende de deuda, cuotas, intereses y condiciones.",
        "ejemplo": "Deuda S/ 1,200 en 6 cuotas: cuota referencial S/ 200 sin intereses.",
        "extra": "Si no pagas cuotas, puedes perder el fraccionamiento.",
    },
    "multa tributaria": {
        "aliases": ["multa", "multas", "multa tributaria", "gradualidad", "multa declarar"],
        "que_es": "Una multa tributaria es una sanción por incumplir obligaciones tributarias.",
        "para_que_sirve": "Sirve para sancionar e incentivar cumplimiento.",
        "como_funciona": "SUNAT aplica multas y puede haber rebajas por gradualidad.",
        "como_se_calcula": PREGUNTAS_ESPECIFICAS["cuanto es la multa por no declarar"],
        "ejemplo": "Declarar fuera de plazo puede generar multa e intereses.",
        "extra": "Revisa gradualidad para reducir sanciones si corresponde.",
    },
    "fiscalizacion": {
        "aliases": ["fiscalizacion", "fiscalización", "carta inductiva", "esquela", "requerimiento sunat", "auditoria sunat"],
        "que_es": "La fiscalización es la revisión de SUNAT sobre el cumplimiento tributario.",
        "para_que_sirve": "Sirve para verificar declaraciones, comprobantes, gastos, ingresos y pagos.",
        "como_funciona": "SUNAT puede pedir información mediante cartas, esquelas o requerimientos.",
        "como_se_calcula": "No se calcula; es un procedimiento.",
        "ejemplo": "SUNAT pide sustento de compras para validar crédito fiscal.",
        "extra": "Responde dentro del plazo y conserva documentación.",
    },
    "gastos deducibles": {
        "aliases": ["gastos deducibles", "gasto deducible", "gastos no deducibles", "causalidad", "gastos reparables"],
        "que_es": "Los gastos deducibles son gastos que pueden restarse para calcular Impuesto a la Renta si cumplen requisitos.",
        "para_que_sirve": "Sirven para determinar la renta neta y reducir la base imponible legalmente.",
        "como_funciona": "Deben cumplir causalidad, sustento, razonabilidad, registro y bancarización si corresponde.",
        "como_se_calcula": "Se restan de los ingresos junto con costos permitidos.",
        "ejemplo": "Alquiler del local, servicios del negocio, sueldos, publicidad vinculada.",
        "extra": "Los gastos personales, sin sustento o multas suelen ser no deducibles.",
    },
    "bancarizacion": {
        "aliases": ["bancarizacion", "bancarización", "medios de pago", "pago bancarizado"],
        "que_es": "La bancarización es el uso de medios financieros para sustentar operaciones.",
        "para_que_sirve": "Sirve para que ciertos gastos o créditos sean aceptados tributariamente.",
        "como_funciona": "Se paga con transferencia, depósito, cheque, tarjeta u otro medio permitido.",
        "como_se_calcula": "No se calcula; aplica según montos y normas vigentes.",
        "ejemplo": "Pagar una factura con transferencia bancaria.",
        "extra": "Si correspondía bancarizar y no se hizo, el gasto podría no aceptarse.",
    },
    "planilla": {
        "aliases": ["planilla", "trabajador en planilla", "essalud", "onp", "afp", "boleta de pago"],
        "que_es": "La planilla es el registro de trabajadores dependientes.",
        "para_que_sirve": "Sirve para formalizar relación laboral, remuneraciones, aportes y retenciones.",
        "como_funciona": "El empleador registra trabajador, paga sueldo, aporta a EsSalud y retiene si corresponde.",
        "como_se_calcula": "Depende de sueldo, beneficios, descuentos y régimen laboral.",
        "ejemplo": "Un trabajador contratado recibe sueldo y figura en planilla.",
        "extra": "Se vincula con renta de quinta categoría.",
    },
    "itan": {
        "aliases": ["itan", "impuesto temporal a los activos netos", "activos netos"],
        "que_es": "El ITAN es el Impuesto Temporal a los Activos Netos.",
        "para_que_sirve": "Sirve como impuesto relacionado con activos de ciertas empresas.",
        "como_funciona": "Se determina en función de activos netos y puede usarse como crédito contra renta en ciertos casos.",
        "como_se_calcula": "Depende de activos netos y reglas vigentes.",
        "ejemplo": "Una empresa con activos significativos puede estar obligada.",
        "extra": "No todos los contribuyentes están obligados.",
    },
    "itf": {
        "aliases": ["itf", "impuesto a las transacciones financieras"],
        "que_es": "El ITF es el Impuesto a las Transacciones Financieras.",
        "para_que_sirve": "Sirve para gravar ciertos movimientos financieros.",
        "como_funciona": "Las entidades financieras aplican el impuesto en operaciones gravadas.",
        "como_se_calcula": "Operación financiera x tasa vigente.",
        "ejemplo": "Algunas transferencias bancarias pueden estar sujetas al ITF.",
        "extra": "Verifica tasa y operaciones afectas vigentes.",
    },
    "isc": {
        "aliases": ["isc", "impuesto selectivo al consumo", "selectivo al consumo"],
        "que_es": "El ISC es el Impuesto Selectivo al Consumo.",
        "para_que_sirve": "Sirve para gravar productos específicos como combustibles, alcohol, cigarrillos u otros.",
        "como_funciona": "Se aplica según el producto y sistema de cálculo.",
        "como_se_calcula": "Puede ser por valor, monto fijo o sistema específico.",
        "ejemplo": "Ciertos combustibles o bebidas pueden estar sujetos al ISC.",
        "extra": "Revisa tasas vigentes por producto.",
    },
    "impuesto predial": {
        "aliases": ["predial", "impuesto predial", "autovaluo", "autoavaluo"],
        "que_es": "El impuesto predial es un tributo municipal que grava predios urbanos y rústicos.",
        "para_que_sirve": "Financia servicios y funciones municipales.",
        "como_funciona": "Lo administra la municipalidad donde está el predio.",
        "como_se_calcula": "Sobre valor del predio y tasas/escalas municipales.",
        "ejemplo": "Tener una casa genera obligación de impuesto predial.",
        "extra": "Consulta municipalidad para monto exacto.",
    },
    "alcabala": {
        "aliases": ["alcabala", "impuesto de alcabala", "compra inmueble", "venta inmueble"],
        "que_es": "El impuesto de alcabala grava transferencias de propiedad de inmuebles.",
        "para_que_sirve": "Sirve para tributar compra o transferencia de inmuebles.",
        "como_funciona": "Generalmente lo paga el comprador ante municipalidad.",
        "como_se_calcula": "Sobre valor de transferencia o autovalúo según reglas vigentes.",
        "ejemplo": "Comprar un departamento puede generar alcabala.",
        "extra": "Consulta SAT o municipalidad.",
    },
    "arbitrios": {
        "aliases": ["arbitrios", "arbitrios municipales", "limpieza publica", "serenazgo"],
        "que_es": "Los arbitrios son tasas municipales por servicios como limpieza, serenazgo, parques y jardines.",
        "para_que_sirve": "Sirven para financiar servicios municipales.",
        "como_funciona": "La municipalidad cobra según criterios de sus ordenanzas.",
        "como_se_calcula": "Depende de cada municipalidad.",
        "ejemplo": "Pago por limpieza pública o serenazgo.",
        "extra": "Consulta tu municipalidad para importes exactos.",
    },
    "aduanas": {
        "aliases": ["aduanas", "importacion", "exportacion", "tributos aduaneros", "mercancias", "mercancías"],
        "que_es": "Aduanas es el área de SUNAT que controla ingreso y salida de mercancías.",
        "para_que_sirve": "Controla importaciones, exportaciones y tributos aduaneros.",
        "como_funciona": "Revisa declaraciones, mercancías, pagos y requisitos.",
        "como_se_calcula": "Tributos pueden depender de valor, aranceles, IGV y otros conceptos.",
        "ejemplo": "Importar productos requiere declaración y pago de tributos si corresponde.",
        "extra": "Para operaciones reales conviene asesoría aduanera.",
    },
    "drawback": {
        "aliases": ["drawback", "restitucion arancelaria", "restitución arancelaria"],
        "que_es": "El drawback es un mecanismo de restitución de derechos arancelarios para ciertos exportadores.",
        "para_que_sirve": "Sirve para devolver parte de derechos arancelarios por insumos usados en bienes exportados.",
        "como_funciona": "El exportador solicita restitución si cumple requisitos.",
        "como_se_calcula": "Depende de reglas y porcentajes vigentes aplicables al valor exportado.",
        "ejemplo": "Una empresa exportadora solicita drawback por insumos importados usados en productos exportados.",
        "extra": "Revisa requisitos documentarios vigentes.",
    },
}


def limpiar_texto(texto):
    texto = str(texto).lower().strip()
    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",
        "ñ": "n",
    }

    for original, nuevo in reemplazos.items():
        texto = texto.replace(original, nuevo)

    texto = re.sub(r"[¿?¡!.,:;(){}\[\]\"']", " ", texto)
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def detectar_pregunta_prohibida(mensaje):
    texto = limpiar_texto(mensaje)

    for frase in PREGUNTAS_PROHIBIDAS:
        if limpiar_texto(frase) in texto:
            return True

    palabras_riesgo = ["evadir", "ocultar", "falsificar", "enganar", "burlar", "falsa", "falso", "inventar"]
    temas_riesgo = ["impuesto", "sunat", "factura", "comprobante", "ventas", "ingresos", "gastos"]

    return any(p in texto for p in palabras_riesgo) and any(t in texto for t in temas_riesgo)


def respuesta_segura():
    return (
        "No puedo ayudarte a evadir impuestos, falsificar comprobantes, ocultar ingresos o engañar a SUNAT.\n\n"
        "Sí puedo ayudarte con alternativas legales:\n"
        "1. Elegir el régimen tributario adecuado.\n"
        "2. Usar gastos deducibles reales y sustentados.\n"
        "3. Aplicar correctamente crédito fiscal.\n"
        "4. Regularizar declaraciones pendientes.\n"
        "5. Solicitar fraccionamiento si tienes deuda.\n"
        "6. Revisar gradualidad para reducir multas legalmente.\n\n"
        "Puedes preguntarme: ¿qué gastos son deducibles? o ¿cómo regularizo mi deuda?"
    )


def obtener_aliases():
    aliases = []

    for tema, data in TEMAS.items():
        aliases.append(tema)
        aliases.extend(data["aliases"])

    aliases.extend(RESPUESTAS_DIRECTAS.keys())
    aliases.extend(PREGUNTAS_ESPECIFICAS.keys())

    return list(set(aliases))


def corregir_texto(texto):
    texto_limpio = limpiar_texto(texto)

    correcciones = {
        "factra": "factura",
        "fatura": "factura",
        "facura": "factura",
        "fctura": "factura",
        "voleta": "boleta",
        "boleto": "boleta",
        "bolta": "boleta",
        "deito": "debito",
        "debito": "nota de debito",
        "débito": "nota de debito",
        "credito": "nota de credito",
        "crédito": "nota de credito",
        "notadebito": "nota de debito",
        "notacredito": "nota de credito",
        "tributario": "regimen tributario",
        "regimenes": "regimen tributario",
        "regimen": "regimen tributario",
        "detraciones": "detraccion",
        "detracción": "detraccion",
        "detracciones": "detraccion",
        "retenciones": "retencion",
        "retención": "retencion",
        "percepciones": "percepcion",
        "percepción": "percepcion",
        "clavesol": "clave sol",
        "cla sol": "clave sol",
        "renta4": "renta de cuarta categoria",
        "renta5": "renta de quinta categoria",
        "predial": "impuesto predial",
        "coactiva": "cobranza coactiva",
    }

    palabras = texto_limpio.split()
    texto_corregido = " ".join([correcciones.get(p, p) for p in palabras])

    aliases = obtener_aliases()
    match = difflib.get_close_matches(texto_corregido, aliases, n=1, cutoff=0.84)

    if match:
        return match[0]

    return texto_corregido


def extraer_numeros(mensaje):
    texto = str(mensaje).lower()
    texto = texto.replace(",", "")
    numeros = re.findall(r"\d+(?:\.\d+)?", texto)
    return [float(numero) for numero in numeros]


def formato_soles(numero):
    return f"S/ {numero:,.2f}"


def contiene(texto, palabras):
    return any(palabra in texto for palabra in palabras)


def normalizar_numero(numero_texto):
    numero_texto = str(numero_texto).replace("S/", "").replace("s/", "")
    numero_texto = numero_texto.replace(",", "").replace(" ", "")

    try:
        return float(numero_texto)
    except Exception:
        return None


def extraer_montos_con_etiquetas(mensaje):
    texto_original = str(mensaje).lower()

    patrones = {
        "ingresos": [
            r"ingresos?\s*(?:tributarios|gravados|netos|totales|contables)?\s*(?:por|de|:)?\s*s?/?\s*([\d,]+(?:\.\d+)?)",
            r"ventas?\s*(?:netas|gravadas|totales)?\s*(?:por|de|:)?\s*s?/?\s*([\d,]+(?:\.\d+)?)",
        ],
        "costos": [
            r"costos?\s*(?:computables|de ventas|deducibles)?\s*(?:por|de|:)?\s*s?/?\s*([\d,]+(?:\.\d+)?)",
            r"costo\s*de\s*ventas\s*(?:por|de|:)?\s*s?/?\s*([\d,]+(?:\.\d+)?)",
        ],
        "gastos_deducibles": [
            r"gastos?\s*(?:deducibles|aceptados|permitidos|administrativos|ventas|operativos)?\s*(?:por|de|:)?\s*s?/?\s*([\d,]+(?:\.\d+)?)",
        ],
        "gastos_no_deducibles": [
            r"gastos?\s*(?:no deducibles|reparables|no aceptados)\s*(?:por|de|:)?\s*s?/?\s*([\d,]+(?:\.\d+)?)",
            r"multas?\s*(?:sunat|tributarias|administrativas)?\s*(?:por|de|:)?\s*s?/?\s*([\d,]+(?:\.\d+)?)",
            r"gastos?\s*personales\s*(?:por|de|:)?\s*s?/?\s*([\d,]+(?:\.\d+)?)",
        ],
        "pagos_a_cuenta": [
            r"pagos?\s*a\s*cuenta\s*(?:del impuesto a la renta|de renta)?\s*(?:por|de|:)?\s*s?/?\s*([\d,]+(?:\.\d+)?)",
        ],
        "tasa": [
            r"tasa\s*(?:del)?\s*(?:impuesto a la renta|ir|renta)?\s*(?:de|del|:)?\s*([\d]+(?:\.\d+)?)\s*%",
            r"([\d]+(?:\.\d+)?)\s*%\s*(?:de impuesto a la renta|renta|ir)",
        ],
        "adiciones": [
            r"adiciones?\s*(?:tributarias)?\s*(?:por|de|:)?\s*s?/?\s*([\d,]+(?:\.\d+)?)",
        ],
        "deducciones": [
            r"deducciones?\s*(?:tributarias)?\s*(?:por|de|:)?\s*s?/?\s*([\d,]+(?:\.\d+)?)",
        ],
    }

    resultado = {}

    for campo, lista_patrones in patrones.items():
        total = 0
        encontrado = False

        for patron in lista_patrones:
            coincidencias = re.findall(patron, texto_original)

            for coincidencia in coincidencias:
                numero = normalizar_numero(coincidencia)

                if numero is not None:
                    total += numero
                    encontrado = True

        if encontrado:
            resultado[campo] = total

    return resultado


def resolver_caso_renta_empresarial_avanzado(mensaje):
    texto = limpiar_texto(mensaje)

    palabras_caso = [
        "ingresos tributarios",
        "costos computables",
        "gastos deducibles",
        "gastos no deducibles",
        "adiciones tributarias",
        "renta neta imponible",
        "impuesto a la renta",
        "saldo por pagar",
        "saldo a favor",
        "pagos a cuenta",
        "29.5",
    ]

    if not any(palabra in texto for palabra in palabras_caso):
        return None

    montos = extraer_montos_con_etiquetas(mensaje)

    ingresos = montos.get("ingresos")
    costos = montos.get("costos", 0)
    gastos_deducibles = montos.get("gastos_deducibles", 0)
    gastos_no_deducibles = montos.get("gastos_no_deducibles", 0)
    pagos_a_cuenta = montos.get("pagos_a_cuenta", 0)
    adiciones = montos.get("adiciones", 0)
    deducciones = montos.get("deducciones", 0)
    tasa = montos.get("tasa", 29.5)

    if ingresos is None:
        return (
            "Puedo resolver este caso de Impuesto a la Renta empresarial, pero faltan datos numéricos.\n\n"
            "Necesito como mínimo:\n"
            "1. Ingresos o ventas.\n"
            "2. Costos computables.\n"
            "3. Gastos deducibles.\n"
            "4. Gastos no deducibles o reparables.\n"
            "5. Pagos a cuenta.\n"
            "6. Tasa del impuesto, por ejemplo 29.5%.\n\n"
            "Fórmula general:\n"
            "Renta neta imponible = ingresos - costos - gastos deducibles + adiciones - deducciones.\n"
            "Impuesto a la Renta = renta neta imponible x tasa.\n"
            "Saldo = impuesto calculado - pagos a cuenta.\n\n"
            "Ejemplo:\n"
            "Ingresos 500000, costos 230000, gastos deducibles 80000, gastos no deducibles 15000, pagos a cuenta 42000, tasa 29.5%."
        )

    renta_neta = ingresos - costos - gastos_deducibles + gastos_no_deducibles + adiciones - deducciones
    impuesto = renta_neta * (tasa / 100)
    saldo = impuesto - pagos_a_cuenta

    if saldo > 0:
        resultado_saldo = f"Saldo por pagar: {formato_soles(saldo)}"
    elif saldo < 0:
        resultado_saldo = f"Saldo a favor: {formato_soles(abs(saldo))}"
    else:
        resultado_saldo = "No hay saldo por pagar ni saldo a favor."

    return (
        "Resolución del caso práctico de Impuesto a la Renta empresarial:\n\n"
        "1. Ingresos tributarios\n"
        f"Ingresos considerados: {formato_soles(ingresos)}\n\n"
        "2. Costos computables\n"
        f"Costos considerados: {formato_soles(costos)}\n\n"
        "3. Gastos deducibles\n"
        f"Gastos deducibles: {formato_soles(gastos_deducibles)}\n\n"
        "4. Gastos no deducibles\n"
        f"Gastos no deducibles: {formato_soles(gastos_no_deducibles)}\n\n"
        "5. Adiciones tributarias\n"
        f"Adiciones tributarias: {formato_soles(gastos_no_deducibles + adiciones)}\n\n"
        "6. Renta neta imponible\n"
        "Fórmula:\n"
        "Renta neta imponible = ingresos - costos - gastos deducibles + adiciones - deducciones\n\n"
        f"Renta neta imponible = {formato_soles(ingresos)} - {formato_soles(costos)} - {formato_soles(gastos_deducibles)} + {formato_soles(gastos_no_deducibles + adiciones)} - {formato_soles(deducciones)}\n"
        f"Renta neta imponible = {formato_soles(renta_neta)}\n\n"
        "7. Impuesto a la Renta\n"
        f"Tasa aplicada: {tasa}%\n"
        f"Impuesto calculado: {formato_soles(impuesto)}\n\n"
        "8. Saldo por pagar o saldo a favor\n"
        f"Pagos a cuenta: {formato_soles(pagos_a_cuenta)}\n"
        f"{resultado_saldo}"
    )


def resolver_caso_practico(mensaje):
    texto = limpiar_texto(mensaje)
    numeros = extraer_numeros(mensaje)

    caso_renta = resolver_caso_renta_empresarial_avanzado(mensaje)

    if caso_renta:
        return caso_renta

    if "igv" in texto and contiene(texto, ["mas igv", "sin igv", "agregar igv", "adicionar igv", "sumar igv"]):
        if len(numeros) >= 1:
            base = numeros[0]
            igv = base * 0.18
            total = base + igv

            return (
                "Caso práctico de IGV sin incluir:\n\n"
                f"Base imponible: {formato_soles(base)}\n"
                f"IGV 18%: {formato_soles(igv)}\n"
                f"Total a cobrar: {formato_soles(total)}\n\n"
                "Fórmula:\n"
                "IGV = base x 18%\n"
                "Total = base + IGV"
            )

    if "igv" in texto and contiene(texto, ["incluido", "incluye", "con igv", "ya tiene igv", "precio final"]):
        if len(numeros) >= 1:
            total = numeros[0]
            base = total / 1.18
            igv = total - base

            return (
                "Caso práctico de IGV incluido:\n\n"
                f"Total con IGV: {formato_soles(total)}\n"
                f"Base imponible: {formato_soles(base)}\n"
                f"IGV 18%: {formato_soles(igv)}\n\n"
                "Fórmula:\n"
                "Base = total / 1.18\n"
                "IGV = total - base"
            )

    if "igv" in texto and "ventas" in texto and "compras" in texto:
        if len(numeros) >= 2:
            ventas = numeros[0]
            compras = numeros[1]

            igv_ventas = ventas * 0.18
            igv_compras = compras * 0.18
            igv_pagar = igv_ventas - igv_compras

            if igv_pagar > 0:
                resultado = f"IGV por pagar: {formato_soles(igv_pagar)}"
            elif igv_pagar < 0:
                resultado = f"Saldo a favor: {formato_soles(abs(igv_pagar))}"
            else:
                resultado = "No hay IGV por pagar ni saldo a favor."

            return (
                "Caso práctico de IGV mensual:\n\n"
                f"Ventas del periodo: {formato_soles(ventas)}\n"
                f"IGV de ventas / débito fiscal: {formato_soles(igv_ventas)}\n\n"
                f"Compras del periodo: {formato_soles(compras)}\n"
                f"IGV de compras / crédito fiscal: {formato_soles(igv_compras)}\n\n"
                f"{resultado}\n\n"
                "Fórmula:\n"
                "IGV por pagar = IGV de ventas - IGV de compras"
            )

    if contiene(texto, ["nota de debito", "nota debito", "aumentar factura", "incrementar factura", "cobrar adicional", "aumentar monto"]):
        if len(numeros) >= 2:
            original = numeros[0]
            adicional = numeros[1]
            nuevo_total = original + adicional

            return (
                "Caso práctico de nota de débito:\n\n"
                f"Factura original: {formato_soles(original)}\n"
                f"Monto adicional: {formato_soles(adicional)}\n"
                f"Nuevo monto de la operación: {formato_soles(nuevo_total)}\n\n"
                "Corresponde emitir una nota de débito porque estás aumentando el valor de una operación ya facturada."
            )

    if contiene(texto, ["nota de credito", "nota credito", "devolucion", "descuento", "rebaja", "anular parte", "disminuir factura"]):
        if len(numeros) >= 2:
            original = numeros[0]
            descuento = numeros[1]
            nuevo_total = original - descuento

            if nuevo_total < 0:
                nuevo_total = 0

            return (
                "Caso práctico de nota de crédito:\n\n"
                f"Factura original: {formato_soles(original)}\n"
                f"Monto a descontar/devolver: {formato_soles(descuento)}\n"
                f"Nuevo monto de la operación: {formato_soles(nuevo_total)}\n\n"
                "Corresponde emitir una nota de crédito porque estás reduciendo, corrigiendo o anulando parte de una operación ya facturada."
            )

    if contiene(texto, ["detraccion", "detracciones"]):
        if len(numeros) >= 2:
            monto = numeros[0]
            porcentaje = numeros[1]

            detraccion = monto * (porcentaje / 100)
            saldo = monto - detraccion

            return (
                "Caso práctico de detracción:\n\n"
                f"Monto de la operación: {formato_soles(monto)}\n"
                f"Porcentaje de detracción: {porcentaje}%\n"
                f"Monto a depositar en Banco de la Nación: {formato_soles(detraccion)}\n"
                f"Saldo a pagar al proveedor: {formato_soles(saldo)}\n\n"
                "Recuerda verificar en SUNAT el porcentaje exacto según el bien o servicio."
            )

    if contiene(texto, ["retencion", "retenciones"]):
        if len(numeros) >= 2:
            monto = numeros[0]
            porcentaje = numeros[1]

            retencion = monto * (porcentaje / 100)
            neto = monto - retencion

            return (
                "Caso práctico de retención:\n\n"
                f"Monto de la operación: {formato_soles(monto)}\n"
                f"Porcentaje de retención: {porcentaje}%\n"
                f"Monto retenido: {formato_soles(retencion)}\n"
                f"Neto a pagar: {formato_soles(neto)}\n\n"
                "El porcentaje exacto debe verificarse según la norma vigente."
            )

    if contiene(texto, ["percepcion", "percepciones"]):
        if len(numeros) >= 2:
            monto = numeros[0]
            porcentaje = numeros[1]

            percepcion = monto * (porcentaje / 100)
            total = monto + percepcion

            return (
                "Caso práctico de percepción:\n\n"
                f"Monto de la operación: {formato_soles(monto)}\n"
                f"Porcentaje de percepción: {porcentaje}%\n"
                f"Monto de percepción: {formato_soles(percepcion)}\n"
                f"Total a pagar: {formato_soles(total)}\n\n"
                "La percepción se cobra como un adicional al comprador."
            )

    if contiene(texto, ["fraccionar", "fraccionamiento", "cuotas", "dividir deuda"]):
        if len(numeros) >= 2:
            deuda = numeros[0]
            cuotas = int(numeros[1])

            if cuotas <= 0:
                return "El número de cuotas debe ser mayor a cero."

            cuota = deuda / cuotas

            return (
                "Caso práctico de fraccionamiento simple:\n\n"
                f"Deuda tributaria: {formato_soles(deuda)}\n"
                f"Número de cuotas: {cuotas}\n"
                f"Cuota aproximada sin intereses: {formato_soles(cuota)}\n\n"
                "Este cálculo es referencial. SUNAT puede aplicar intereses, requisitos y condiciones."
            )

    if contiene(texto, ["renta", "utilidad", "impuesto a la renta"]) and contiene(texto, ["ingresos", "gastos", "costos"]):
        if len(numeros) >= 2:
            ingresos = numeros[0]
            gastos = numeros[1]
            utilidad = ingresos - gastos

            return (
                "Caso práctico de renta empresarial simple:\n\n"
                f"Ingresos: {formato_soles(ingresos)}\n"
                f"Gastos/costos deducibles: {formato_soles(gastos)}\n"
                f"Utilidad o renta neta aproximada: {formato_soles(utilidad)}\n\n"
                "Fórmula:\n"
                "Renta neta = ingresos - gastos deducibles\n\n"
                "Para determinar el impuesto exacto se debe revisar régimen tributario, adiciones, deducciones y tasas vigentes."
            )

    if contiene(texto, ["descuento", "rebaja"]) and len(numeros) >= 2:
        monto = numeros[0]
        descuento = numeros[1]

        if descuento <= 100 and contiene(texto, ["%", "por ciento"]):
            descuento_monto = monto * (descuento / 100)
            total = monto - descuento_monto

            return (
                "Caso práctico de descuento porcentual:\n\n"
                f"Monto inicial: {formato_soles(monto)}\n"
                f"Descuento: {descuento}%\n"
                f"Monto descontado: {formato_soles(descuento_monto)}\n"
                f"Total final: {formato_soles(total)}"
            )

        total = monto - descuento

        if total < 0:
            total = 0

        return (
            "Caso práctico de descuento fijo:\n\n"
            f"Monto inicial: {formato_soles(monto)}\n"
            f"Descuento: {formato_soles(descuento)}\n"
            f"Total final: {formato_soles(total)}"
        )

    if contiene(texto, ["interes", "mora", "moratorio"]) and len(numeros) >= 3:
        deuda = numeros[0]
        tasa = numeros[1]
        periodos = numeros[2]

        interes = deuda * (tasa / 100) * periodos
        total = deuda + interes

        return (
            "Caso práctico de interés simple referencial:\n\n"
            f"Deuda: {formato_soles(deuda)}\n"
            f"Tasa aplicada: {tasa}%\n"
            f"Periodos: {periodos}\n"
            f"Interés aproximado: {formato_soles(interes)}\n"
            f"Total aproximado: {formato_soles(total)}\n\n"
            "Este cálculo es referencial. Para intereses tributarios reales debes verificar la tasa vigente de SUNAT."
        )

    if contiene(texto, ["saldo a favor", "compensar", "aplicar saldo"]) and len(numeros) >= 2:
        deuda = numeros[0]
        saldo = numeros[1]
        resultado = deuda - saldo

        if resultado > 0:
            return (
                "Caso práctico de aplicación de saldo a favor:\n\n"
                f"Deuda: {formato_soles(deuda)}\n"
                f"Saldo a favor: {formato_soles(saldo)}\n"
                f"Monto pendiente por pagar: {formato_soles(resultado)}"
            )

        if resultado < 0:
            return (
                "Caso práctico de aplicación de saldo a favor:\n\n"
                f"Deuda: {formato_soles(deuda)}\n"
                f"Saldo a favor: {formato_soles(saldo)}\n"
                f"Nuevo saldo a favor: {formato_soles(abs(resultado))}"
            )

        return (
            "Caso práctico de aplicación de saldo a favor:\n\n"
            f"Deuda: {formato_soles(deuda)}\n"
            f"Saldo a favor: {formato_soles(saldo)}\n"
            "La deuda queda cancelada."
        )

    if "renta neta imponible" in texto or "impuesto a la renta" in texto or "pagos a cuenta" in texto:
        return (
            "Este es un caso práctico de Impuesto a la Renta empresarial.\n\n"
            "Para resolverlo se sigue este orden:\n\n"
            "1. Identificar ingresos tributarios.\n"
            "2. Determinar costos computables.\n"
            "3. Separar gastos deducibles y no deducibles.\n"
            "4. Calcular adiciones tributarias.\n"
            "5. Determinar la renta neta imponible.\n"
            "6. Aplicar la tasa del Impuesto a la Renta, por ejemplo 29.5%.\n"
            "7. Restar los pagos a cuenta.\n"
            "8. Determinar saldo por pagar o saldo a favor.\n\n"
            "Fórmula general:\n"
            "Renta neta imponible = ingresos - costos - gastos deducibles + adiciones - deducciones.\n"
            "Impuesto a la Renta = renta neta imponible x tasa.\n"
            "Saldo = impuesto calculado - pagos a cuenta.\n\n"
            "Para darte resultado exacto, escríbeme así:\n"
            "Ingresos 500000, costos 230000, gastos deducibles 80000, gastos no deducibles 15000, pagos a cuenta 42000, tasa 29.5%."
        )

    if len(numeros) >= 1 and contiene(texto, ["calcula", "calcular", "cuanto", "monto", "total"]):
        return (
            "Puedo ayudarte a resolver el caso, pero necesito que me indiques qué deseas calcular.\n\n"
            "Ejemplos:\n"
            "- Calcula IGV de S/ 1000 más IGV.\n"
            "- Factura de S/ 1180 con IGV incluido.\n"
            "- Ventas 5000 y compras 2000, calcula IGV.\n"
            "- Detracción de S/ 1000 con 12%.\n"
            "- Deuda de S/ 1200 en 6 cuotas.\n"
            "- Ingresos 500000, costos 230000, gastos deducibles 80000, gastos no deducibles 15000, pagos a cuenta 42000."
        )

    return None


def detectar_pregunta_especifica(mensaje):
    texto = limpiar_texto(mensaje)

    for pregunta, respuesta in PREGUNTAS_ESPECIFICAS.items():
        pregunta_limpia = limpiar_texto(pregunta)

        if texto == pregunta_limpia:
            return respuesta

        if pregunta_limpia in texto:
            return respuesta

        similitud = difflib.SequenceMatcher(None, texto, pregunta_limpia).ratio()

        if similitud > 0.86:
            return respuesta

    reglas_cortas = [
        (["igv", "tasa"], "que es el igv y cual es su tasa actual"),
        (["igv", "calcula"], "como se calcula el igv de una factura"),
        (["igv", "factura"], "como se calcula el igv de una factura"),
        (["operaciones", "exoneradas"], "que operaciones estan exoneradas del igv"),
        (["exonerado", "inafecto"], "cual es la diferencia entre exonerado e inafecto"),
        (["credito", "fiscal"], "que es el credito fiscal y como se usa"),
        (["rentas", "categorias"], "cuales son las rentas de primera segunda tercera cuarta y quinta categoria"),
        (["renta", "tercera"], "como se calcula el impuesto a la renta de tercera categoria"),
        (["gastos", "deducibles"], "que gastos son deducibles para la renta empresarial"),
        (["pagos", "cuenta"], "cuales son los pagos a cuenta mensuales"),
        (["declaracion", "anual"], "que es la declaracion jurada anual"),
        (["factura", "boleta"], "cuando se emite una factura y cuando una boleta"),
        (["nota", "credito"], "que es una nota de credito y cuando se emite"),
        (["nota", "debito"], "que es una nota de debito"),
        (["comprobante", "retencion"], "que es el comprobante de retencion"),
        (["factura", "electronica"], "como funciona la factura electronica"),
        (["regimenes", "peru"], "cuales son los regimenes tributarios en peru"),
        (["rus", "rer", "rmt"], "cual es la diferencia entre rus rer rmt y regimen general"),
        (["limite", "ingresos", "regimen"], "que limite de ingresos tiene cada regimen"),
        (["cambio", "regimen"], "como me cambio de regimen tributario"),
        (["libros", "regimen"], "que libros contables lleva cada regimen"),
        (["vencen", "declaraciones"], "cuando vencen las declaraciones mensuales"),
        (["cronograma", "sunat"], "que es el cronograma de vencimientos de sunat"),
        (["no", "declaro"], "que pasa si no declaro a tiempo"),
        (["multa", "declarar"], "cuanto es la multa por no declarar"),
        (["regulariza", "deuda"], "como se regulariza una deuda tributaria"),
        (["deuda", "tributaria"], "como se regulariza una deuda tributaria"),
        (["sistema", "detracciones"], "que es el sistema de detracciones"),
        (["bienes", "servicios", "detraccion"], "que bienes y servicios estan sujetos a detraccion"),
        (["porcentaje", "detraccion"], "cual es el porcentaje de detraccion"),
        (["retencion", "igv"], "que es la retencion del igv"),
        (["agentes", "retencion"], "quienes son agentes de retencion"),
        (["libros", "obligado"], "que libros contables estoy obligado a llevar"),
        (["ple", "sunat"], "que es el ple de sunat"),
        (["registro", "ventas"], "como se lleva el registro de ventas"),
        (["registro", "compras"], "como se lleva el registro de compras"),
        (["atraso", "libros"], "cual es el atraso maximo permitido en los libros"),
        (["impuestos", "independiente"], "como calculo mis impuestos si soy independiente"),
        (["gastos", "casa"], "puedo deducir gastos de mi casa si trabajo desde ahi"),
        (["uit"], "que es la uit y para que sirve"),
        (["deuda", "sunat"], "como se si tengo deuda con sunat"),
        (["clave", "sol"], "como obtengo mi clave sol"),
    ]

    for palabras, clave_respuesta in reglas_cortas:
        if all(palabra in texto for palabra in palabras):
            return PREGUNTAS_ESPECIFICAS[clave_respuesta]

    return None


def detectar_tema(mensaje):
    texto = corregir_texto(mensaje)

    mejor_tema = None
    mejor_puntaje = 0

    for tema, data in TEMAS.items():
        puntaje = 0

        if tema in texto:
            puntaje += 20

        for alias in data["aliases"]:
            alias_limpio = limpiar_texto(alias)

            if alias_limpio == texto:
                puntaje += 30

            elif alias_limpio in texto:
                puntaje += len(alias_limpio.split()) * 6

            else:
                similitud = difflib.SequenceMatcher(None, texto, alias_limpio).ratio()

                if similitud > 0.84:
                    puntaje += int(similitud * 12)

        if puntaje > mejor_puntaje:
            mejor_puntaje = puntaje
            mejor_tema = tema

    if mejor_puntaje >= 5:
        return mejor_tema

    return None


def detectar_intencion(mensaje):
    texto = limpiar_texto(mensaje)

    if texto in RESPUESTAS_DIRECTAS:
        return "directa"

    if any(frase in texto for frase in ["para que sirve", "para q sirve", "sirve para que", "cual es su finalidad"]):
        return "para_que_sirve"

    if any(frase in texto for frase in ["que es", "q es", "que significa", "definicion", "concepto", "significado"]):
        return "que_es"

    if any(frase in texto for frase in ["como funciona", "funciona", "proceso", "mecanismo"]):
        return "como_funciona"

    if any(frase in texto for frase in ["como se calcula", "calcular", "calculo", "formula", "monto"]):
        return "como_se_calcula"

    if any(frase in texto for frase in ["ejemplo", "dame un ejemplo", "un ejemplo", "caso practico"]):
        return "ejemplo"

    if any(frase in texto for frase in ["mas informacion", "explicame mas", "amplia", "detalla", "mas detalle"]):
        return "extra"

    if any(frase in texto for frase in ["cuando se emite", "cuando se usa", "cuando usar", "en que caso"]):
        return "extra"

    return "que_es"


def es_pregunta_seguimiento(mensaje):
    texto = limpiar_texto(mensaje)

    frases = [
        "que es",
        "para que sirve",
        "como funciona",
        "como se calcula",
        "dame un ejemplo",
        "un ejemplo",
        "ejemplo",
        "mas informacion",
        "explicame mas",
        "cuando se usa",
        "cuando se emite",
        "en que caso",
        "y eso",
        "eso que significa",
        "por que",
        "cual es la diferencia",
        "que diferencia hay",
    ]

    if texto in frases:
        return True

    if len(texto.split()) <= 6 and any(
        palabra in texto
        for palabra in ["sirve", "ejemplo", "funciona", "calcula", "usa", "emite", "significa", "diferencia"]
    ):
        return True

    return False


def obtener_tema_historial(historial):
    if not historial:
        return None

    for item in reversed(historial[-8:]):
        usuario = item.get("usuario", "")
        bot = item.get("bot", "")

        tema_usuario = detectar_tema(usuario)

        if tema_usuario:
            return tema_usuario

        tema_bot = detectar_tema(bot)

        if tema_bot:
            return tema_bot

    return None


def responder_tema(tema, intencion="que_es"):
    if not tema or tema not in TEMAS:
        return None

    data = TEMAS[tema]

    if intencion in data:
        return data[intencion]

    return data["que_es"]


def buscar_respuesta_local(mensaje, historial=None):
    if historial is None:
        historial = []

    texto = limpiar_texto(mensaje)

    if detectar_pregunta_prohibida(mensaje):
        return respuesta_segura()

    if texto in RESPUESTAS_DIRECTAS:
        return RESPUESTAS_DIRECTAS[texto]

    caso = resolver_caso_practico(mensaje)

    if caso:
        return caso

    especifica = detectar_pregunta_especifica(mensaje)

    if especifica:
        return especifica

    tema_actual = detectar_tema(mensaje)
    intencion = detectar_intencion(mensaje)

    if tema_actual:
        return responder_tema(tema_actual, intencion)

    if es_pregunta_seguimiento(mensaje):
        tema_anterior = obtener_tema_historial(historial)

        if tema_anterior:
            return responder_tema(tema_anterior, intencion)

    return None


def construir_contexto(historial):
    if not historial:
        return ""

    partes = []

    for item in historial[-8:]:
        usuario = item.get("usuario", "")
        bot = item.get("bot", "")

        if usuario:
            partes.append(f"Usuario: {usuario}")

        if bot:
            partes.append(f"TribuTax: {bot}")

    return "\n".join(partes)


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

Instrucciones:
- Responde en español.
- Responde con enfoque tributario peruano.
- Si es un caso práctico con números, resuelve paso a paso.
- Si faltan datos, indica qué datos faltan y da la fórmula.
- Si menciona un tema nuevo, responde ese tema.
- Si es una pregunta corta como "para qué sirve", usa el historial.
- No ayudes a evadir impuestos, falsificar comprobantes ni ocultar ingresos.
- Si se necesitan datos vigentes exactos, recomienda verificar SUNAT o consultar con contador.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=900,
            ),
        )

        if response and response.text:
            return response.text.strip()

        return None

    except Exception as e:
        print("Gemini no disponible:", str(e))
        return None


def respuesta_fallback():
    return (
        "Soy TribuTax. Puedo ayudarte con muchos temas tributarios de Perú:\n\n"
        "📌 IGV: cálculo, crédito fiscal, débito fiscal, exonerado e inafecto.\n"
        "📌 RUC y SUNAT: inscripción, Clave SOL, consultas, deudas y declaraciones.\n"
        "📌 Comprobantes: factura, boleta, recibo por honorarios, guía de remisión, nota de crédito y nota de débito.\n"
        "📌 Facturación electrónica: XML, CDR, OSE, PSE y comprobantes electrónicos.\n"
        "📌 Impuesto a la Renta: primera, segunda, tercera, cuarta y quinta categoría.\n"
        "📌 Casos de renta: ingresos, costos, gastos deducibles, no deducibles, adiciones, renta neta e impuesto.\n"
        "📌 Regímenes: Nuevo RUS, RER, RMT y Régimen General.\n"
        "📌 Detracciones, retenciones y percepciones.\n"
        "📌 Libros contables: Registro de Ventas, Registro de Compras, PLE y SIRE.\n"
        "📌 Multas, deudas, fraccionamiento, cobranza coactiva y fiscalización.\n"
        "📌 Otros: UIT, ITAN, ITF, ISC, predial, alcabala, arbitrios, aduanas y drawback.\n\n"
        "También puedo resolver casos. Ejemplo:\n"
        "Ingresos 500000, costos 230000, gastos deducibles 80000, gastos no deducibles 15000, pagos a cuenta 42000, tasa 29.5%."
    )


def responder_chatbot(mensaje, historial=None):
    if historial is None:
        historial = []

    try:
        mensaje = mensaje.strip()

        if mensaje == "":
            return "Escribe tu consulta para poder ayudarte."

        respuesta_local = buscar_respuesta_local(mensaje, historial)

        if respuesta_local:
            return respuesta_local

        respuesta_gemini = responder_con_gemini(mensaje, historial)

        if respuesta_gemini:
            return respuesta_gemini

        return respuesta_fallback()

    except Exception as e:
        print("ERROR EN responder_chatbot:", str(e))
        return respuesta_fallback()