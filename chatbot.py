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

Tu función es orientar de forma clara, rápida y sencilla sobre:
IGV, SUNAT, RUC, comprobantes de pago, factura, boleta, recibo por honorarios,
notas de crédito, notas de débito, Impuesto a la Renta, regímenes tributarios,
detracciones, retenciones, percepciones, libros contables, PLE, SIRE, UIT,
Clave SOL, multas, declaraciones, deudas tributarias y obligaciones fiscales.

Tus respuestas son orientativas. Para fechas, tasas específicas actualizadas,
cronogramas, multas exactas o decisiones formales, recomienda verificar SUNAT
o consultar con un contador.
"""


RESPUESTAS = {
    # SALUDOS E IDENTIDAD
    "hola": "¡Hola! Soy TribuTax, tu asistente virtual tributario. Puedo ayudarte con IGV, SUNAT, RUC, comprobantes de pago, Impuesto a la Renta, regímenes tributarios, detracciones, retenciones, libros contables, UIT y Clave SOL.",
    "buenos dias": "¡Buenos días! Soy TribuTax. ¿En qué consulta tributaria puedo ayudarte hoy?",
    "buenas tardes": "¡Buenas tardes! Soy TribuTax. Escríbeme tu consulta y te orientaré de forma clara.",
    "buenas noches": "¡Buenas noches! Soy TribuTax. Estoy listo para ayudarte con tus dudas tributarias.",
    "quien eres": "Soy TribuTax, un asistente virtual tributario creado para responder consultas sobre IGV, SUNAT, RUC, comprobantes de pago, renta, regímenes tributarios y obligaciones fiscales.",
    "que eres": "Soy TribuTax, un chatbot de orientación tributaria para ayudarte con consultas sobre impuestos y obligaciones en Perú.",
    "que es tributax": "TribuTax es un chatbot de ayuda tributaria. Responde consultas sobre IGV, RUC, SUNAT, comprobantes de pago, renta, regímenes tributarios, detracciones, retenciones, libros contables y Clave SOL.",
    "tributax": "Soy TribuTax, tu asistente virtual tributario.",
    "ayuda": "Puedo ayudarte con IGV, RUC, SUNAT, comprobantes, facturas, boletas, notas de crédito, notas de débito, renta, regímenes tributarios, detracciones, retenciones, libros contables, UIT y Clave SOL.",
    "gracias": "¡De nada! Soy TribuTax. Si tienes otra consulta tributaria, escríbeme.",
    "ok": "Perfecto. Puedes hacerme otra consulta sobre IGV, SUNAT, RUC, comprobantes, renta o regímenes tributarios.",
    "adios": "Hasta luego. Recuerda que TribuTax puede ayudarte con tus consultas tributarias cuando lo necesites.",

    # IGV
    "que es el igv": "El IGV es el Impuesto General a las Ventas. En Perú grava principalmente la venta de bienes, la prestación de servicios, contratos de construcción, primera venta de inmuebles realizada por constructores e importaciones. Su tasa general es 18%, compuesta por 16% de IGV y 2% de Impuesto de Promoción Municipal.",
    "que es el igv y cual es su tasa actual": "El IGV es el Impuesto General a las Ventas. Su tasa general actual en Perú es 18%, formada por 16% de IGV y 2% de Impuesto de Promoción Municipal.",
    "cual es la tasa del igv": "La tasa general del IGV en Perú es 18%. Está compuesta por 16% de IGV y 2% de Impuesto de Promoción Municipal.",
    "como se calcula el igv": "El IGV se calcula aplicando el 18% sobre la base imponible. Ejemplo: si la base es S/ 100, el IGV es S/ 18 y el total es S/ 118. Si el monto ya incluye IGV, divides el total entre 1.18 para hallar la base.",
    "como se calcula el igv de una factura": "Para calcular el IGV de una factura: si el precio no incluye IGV, multiplica la base por 18%. Ejemplo: base S/ 100, IGV S/ 18, total S/ 118. Si el total incluye IGV, divide el total entre 1.18.",
    "que operaciones estan exoneradas del igv": "Las operaciones exoneradas del IGV son aquellas que están dentro del ámbito del impuesto, pero una norma las libera del pago. Pueden incluir ciertos bienes o servicios señalados por ley. Como la lista puede cambiar, se recomienda verificar en SUNAT.",
    "que es el credito fiscal": "El crédito fiscal es el IGV pagado en compras que puede descontarse del IGV generado por las ventas, siempre que la compra esté vinculada al negocio, tenga comprobante válido y esté registrada correctamente.",
    "que es el credito fiscal y como se usa": "El crédito fiscal es el IGV que una empresa paga en sus compras y puede usar para descontarlo del IGV de sus ventas. Para usarlo, la compra debe estar relacionada al negocio, sustentada con comprobante válido y registrada correctamente.",
    "cual es la diferencia entre exonerado e inafecto": "Una operación exonerada sí está dentro del campo del IGV, pero una norma la libera del pago. Una operación inafecta no está dentro del campo de aplicación del impuesto.",
    "igv incluido": "Cuando un precio tiene IGV incluido, significa que el monto total ya contiene el 18%. Para hallar la base imponible, se divide el total entre 1.18.",
    "precio con igv": "Si el precio ya incluye IGV, la base se calcula dividiendo el total entre 1.18. Luego el IGV se obtiene restando la base al total.",
    "precio sin igv": "Si el precio no incluye IGV, se calcula multiplicando la base por 18%. Luego se suma el IGV a la base para obtener el total.",
    "base imponible igv": "La base imponible del IGV es el valor sobre el cual se calcula el impuesto. Por ejemplo, si el valor de venta es S/ 100, esa es la base imponible.",
    "igv por pagar": "El IGV por pagar se calcula restando el crédito fiscal del débito fiscal. Es decir: IGV de ventas menos IGV de compras.",
    "debito fiscal": "El débito fiscal es el IGV que una empresa cobra en sus ventas y que debe declarar ante SUNAT.",
    "requisitos del credito fiscal": "Para usar crédito fiscal, la compra debe estar vinculada al negocio, estar sustentada con comprobante válido, estar registrada correctamente y cumplir las normas tributarias.",
    "que compras dan credito fiscal": "Dan crédito fiscal las compras vinculadas a la actividad del negocio, sustentadas con comprobantes válidos y registradas correctamente.",
    "cuando no puedo usar credito fiscal": "No puedes usar crédito fiscal si la compra no está relacionada con el negocio, no tiene comprobante válido, no está registrada correctamente o corresponde a gastos no aceptados tributariamente.",

    # RUC Y SUNAT
    "que es el ruc": "El RUC es el Registro Único de Contribuyentes. Es el número que identifica a una persona natural o empresa ante SUNAT para realizar actividades económicas y cumplir obligaciones tributarias.",
    "para que sirve el ruc": "El RUC sirve para identificarte ante SUNAT, emitir comprobantes de pago, declarar impuestos, realizar actividades económicas formales y cumplir obligaciones tributarias.",
    "quienes deben tener ruc": "Deben tener RUC las personas o empresas que realizan actividades económicas, prestan servicios, venden bienes, alquilan inmuebles o generan ingresos sujetos a obligaciones tributarias.",
    "como sacar ruc": "Puedes obtener tu RUC en SUNAT de forma virtual o presencial. Debes validar tu identidad, registrar tu domicilio fiscal, actividad económica y datos del contribuyente.",
    "que es sunat": "SUNAT es la Superintendencia Nacional de Aduanas y de Administración Tributaria. Administra tributos, fiscaliza obligaciones y permite realizar trámites como RUC, declaraciones, pagos y consulta de deudas.",
    "que es domicilio fiscal": "El domicilio fiscal es la dirección registrada ante SUNAT donde el contribuyente realiza sus actividades o recibe notificaciones tributarias.",
    "que significa domicilio habido": "La condición de domicilio habido significa que SUNAT reconoce que el contribuyente puede ser ubicado en su domicilio fiscal declarado.",
    "que significa no habido": "No habido significa que SUNAT no pudo ubicar al contribuyente en su domicilio fiscal. Esto puede generar restricciones para emitir comprobantes o realizar trámites.",

    # CLAVE SOL
    "que es clave sol": "La Clave SOL es la contraseña que permite ingresar a SUNAT Operaciones en Línea. Sirve para declarar impuestos, pagar tributos, consultar deudas, emitir comprobantes y realizar trámites virtuales.",
    "que es la clave sol": "La Clave SOL es la contraseña que permite ingresar a SUNAT Operaciones en Línea. Sirve para declarar impuestos, pagar tributos, consultar deudas, emitir comprobantes y realizar trámites virtuales.",
    "para que sirve clave sol": "La Clave SOL sirve para acceder a los servicios virtuales de SUNAT, como declarar impuestos, pagar deudas, consultar RUC, emitir comprobantes electrónicos y revisar notificaciones.",
    "como obtengo mi clave sol": "Puedes obtener tu Clave SOL desde SUNAT, por canales virtuales o presenciales, validando tu identidad y datos del contribuyente.",
    "como recuperar clave sol": "Puedes recuperar tu Clave SOL desde la plataforma de SUNAT, siguiendo el proceso de recuperación con tus datos de identidad y validación.",
    "como cambiar clave sol": "Puedes cambiar tu Clave SOL ingresando a SUNAT Operaciones en Línea y modificando tus credenciales desde las opciones de seguridad.",

    # COMPROBANTES
    "que es comprobante de pago": "Un comprobante de pago es un documento que acredita la transferencia de bienes, la entrega en uso o la prestación de servicios. Puede ser factura, boleta, recibo por honorarios, nota de crédito, nota de débito, entre otros.",
    "tipos de comprobantes de pago": "Los principales comprobantes de pago son factura, boleta de venta, recibo por honorarios, nota de crédito, nota de débito, liquidación de compra, ticket y comprobantes electrónicos.",
    "diferencia entre factura y boleta": "La factura se emite cuando el comprador necesita sustentar gasto, costo o crédito fiscal. La boleta se emite normalmente a consumidores finales y no permite usar crédito fiscal.",
    "cuando se emite una factura y cuando una boleta": "Se emite factura cuando el comprador necesita sustentar crédito fiscal, gasto o costo tributario, normalmente empresas o personas con RUC. Se emite boleta cuando la venta es para un consumidor final.",
    "cuando se emite factura": "La factura se emite cuando el comprador necesita sustentar crédito fiscal, gasto o costo tributario. Generalmente se entrega a empresas o personas con RUC.",
    "cuando se emite boleta": "La boleta se emite normalmente a consumidores finales que no necesitan usar crédito fiscal.",
    "factura": "La factura es un comprobante de pago que permite sustentar una operación comercial. Sirve para respaldar crédito fiscal, gasto o costo tributario cuando corresponde.",
    "boleta": "La boleta es un comprobante que se emite generalmente a consumidores finales. Acredita la venta o servicio, pero normalmente no permite usar crédito fiscal.",
    "recibo por honorarios": "El recibo por honorarios es el comprobante que emiten los trabajadores independientes por la prestación de servicios profesionales u oficios.",
    "que es recibo por honorarios": "El recibo por honorarios es un comprobante usado por personas que prestan servicios independientes. Está relacionado con rentas de cuarta categoría.",
    "cuando emito recibo por honorarios": "Debes emitir recibo por honorarios cuando prestas un servicio independiente y no estás en planilla por esa actividad.",
    "factura electronica": "La factura electrónica es un comprobante digital con validez tributaria. Se emite a través de sistemas autorizados por SUNAT y queda registrada electrónicamente.",
    "boleta electronica": "La boleta electrónica es un comprobante digital emitido a consumidores finales. Tiene validez tributaria y se registra electrónicamente.",
    "comprobante electronico": "Un comprobante electrónico es un documento digital autorizado por SUNAT que acredita operaciones comerciales y tributarias.",
    "que es el comprobante de retencion": "El comprobante de retención acredita que un agente de retención designado por SUNAT retuvo parte del pago, generalmente relacionado con el IGV.",
    "como funciona la factura electronica": "La factura electrónica es un comprobante digital con validez tributaria. Se emite mediante sistemas autorizados por SUNAT y sirve para sustentar operaciones.",

    # NOTAS
    "nota de debito": "La nota de débito se emite para aumentar el valor de una operación ya facturada, por ejemplo, por intereses, penalidades, diferencia de precio, gastos adicionales o ajustes.",
    "que es nota de debito": "La nota de débito es un comprobante que sirve para aumentar el valor de una operación ya facturada. Se usa, por ejemplo, por intereses, penalidades, diferencia de precio, gastos adicionales o ajustes.",
    "que es una nota de debito": "La nota de débito es un comprobante que aumenta el valor de una factura o boleta ya emitida. Se utiliza cuando hay recargos, intereses, penalidades o diferencias de precio.",
    "para que sirve nota de debito": "La nota de débito sirve para aumentar el valor de una operación ya facturada. Se usa por intereses, penalidades, diferencia de precio, gastos adicionales o ajustes.",
    "cuando se emite nota de debito": "La nota de débito se emite cuando se necesita incrementar el monto de una factura o boleta ya emitida.",
    "ejemplo de nota de debito": "Ejemplo: emitiste una factura por S/ 500, pero luego debes cobrar S/ 50 adicionales por transporte. Entonces emites una nota de débito por S/ 50.",
    "nota de credito": "La nota de crédito es un comprobante que sirve para disminuir, corregir o anular total o parcialmente una factura o boleta ya emitida.",
    "que es nota de credito": "La nota de crédito es un comprobante que se emite para reducir, corregir o anular una operación ya facturada. Se usa por devoluciones, descuentos, errores o anulaciones.",
    "que es una nota de credito": "La nota de crédito sirve para disminuir, corregir o anular una factura o boleta ya emitida.",
    "para que sirve nota de credito": "La nota de crédito sirve para disminuir, corregir o anular total o parcialmente una factura o boleta ya emitida.",
    "cuando se emite nota de credito": "La nota de crédito se emite por devoluciones, descuentos posteriores, errores en el comprobante o anulación de una operación.",
    "ejemplo de nota de credito": "Ejemplo: emitiste una factura por S/ 300 y el cliente devolvió mercadería por S/ 80. Entonces emites una nota de crédito por S/ 80.",

    # IMPUESTO A LA RENTA
    "que es impuesto a la renta": "El Impuesto a la Renta grava los ingresos obtenidos por personas naturales y empresas. En Perú se clasifica en rentas de primera, segunda, tercera, cuarta y quinta categoría.",
    "cuales son las rentas de primera segunda tercera cuarta y quinta categoria": "Primera categoría: alquileres. Segunda categoría: intereses, dividendos, regalías y ganancias de capital. Tercera categoría: actividades empresariales. Cuarta categoría: trabajo independiente con recibos por honorarios. Quinta categoría: trabajo dependiente en planilla.",
    "renta de primera categoria": "La renta de primera categoría proviene principalmente del alquiler de bienes muebles o inmuebles, como casas, departamentos, locales o vehículos.",
    "renta de segunda categoria": "La renta de segunda categoría proviene de intereses, regalías, dividendos, ganancias de capital y venta de valores, según corresponda.",
    "renta de tercera categoria": "La renta de tercera categoría corresponde a ingresos empresariales generados por negocios, comercios, empresas o actividades productivas.",
    "renta de cuarta categoria": "La renta de cuarta categoría corresponde al trabajo independiente, como servicios profesionales prestados mediante recibos por honorarios.",
    "renta de quinta categoria": "La renta de quinta categoría corresponde al trabajo dependiente, es decir, sueldos, salarios y remuneraciones de trabajadores en planilla.",
    "diferencia entre cuarta y quinta categoria": "La cuarta categoría corresponde al trabajo independiente con recibo por honorarios. La quinta categoría corresponde al trabajo dependiente en planilla.",
    "como se calcula el impuesto a la renta de tercera categoria": "El Impuesto a la Renta de tercera categoría se calcula restando a los ingresos empresariales los costos y gastos deducibles para obtener la renta neta. Luego se aplica la tasa correspondiente y se descuentan los pagos a cuenta realizados.",
    "que gastos son deducibles para la renta empresarial": "Son deducibles los gastos necesarios para producir renta o mantener la fuente del negocio, siempre que sean razonables, estén sustentados con comprobantes válidos y cumplan las normas tributarias.",
    "cuales son los pagos a cuenta mensuales": "Los pagos a cuenta mensuales son adelantos del Impuesto a la Renta que las empresas realizan durante el año. Luego se descuentan del impuesto anual.",
    "que es la declaracion jurada anual": "La declaración jurada anual es la declaración donde el contribuyente informa sus ingresos, costos, gastos, pagos a cuenta y determina si tiene impuesto por pagar o saldo a favor.",
    "que es renta neta": "La renta neta es el resultado de restar a los ingresos los costos, gastos o deducciones permitidas por la norma tributaria.",
    "que es renta bruta": "La renta bruta es el ingreso obtenido antes de aplicar deducciones, costos o gastos permitidos.",
    "que es pago a cuenta": "El pago a cuenta es un adelanto mensual del Impuesto a la Renta que luego se descuenta del impuesto anual.",
    "declaracion anual": "La declaración anual es la presentación ante SUNAT donde se informa el resultado tributario del año, pagos a cuenta, impuesto por pagar o saldo a favor.",
    "saldo a favor": "El saldo a favor ocurre cuando el contribuyente pagó más impuesto del que correspondía. Puede aplicarse contra futuras obligaciones o solicitar devolución si corresponde.",

    # REGÍMENES
    "cuales son los regimenes tributarios en peru": "En Perú existen principalmente cuatro regímenes tributarios: Nuevo RUS, Régimen Especial de Renta o RER, Régimen MYPE Tributario o RMT y Régimen General.",
    "nuevo rus": "El Nuevo RUS es un régimen tributario para pequeños negocios de personas naturales. Tiene pagos mensuales fijos y obligaciones simplificadas.",
    "que es nuevo rus": "El Nuevo RUS es un régimen para pequeños negocios que venden a consumidores finales. No permite emitir facturas y tiene pagos mensuales fijos según categoría.",
    "rer": "El RER es el Régimen Especial de Renta. Está dirigido a ciertos negocios con límites de ingresos y obligaciones tributarias simplificadas.",
    "que es rer": "El RER es un régimen tributario para negocios que cumplen ciertos requisitos. Permite emitir facturas y declarar IGV y renta mensual.",
    "rmt": "El RMT es el Régimen MYPE Tributario. Está orientado a micro y pequeñas empresas, con una tributación más gradual según la utilidad.",
    "que es rmt": "El Régimen MYPE Tributario está dirigido a micro y pequeñas empresas. Permite emitir comprobantes y llevar obligaciones según ingresos.",
    "regimen general": "El Régimen General es para empresas con operaciones más amplias. No tiene límites pequeños de ingresos y exige obligaciones contables más completas.",
    "cual es la diferencia entre rus rer rmt y regimen general": "Nuevo RUS: pequeños negocios de personas naturales. RER: régimen especial con límites. RMT: micro y pequeñas empresas. Régimen General: empresas con obligaciones contables completas.",
    "que limite de ingresos tiene cada regimen": "Los límites de ingresos dependen del régimen tributario y pueden actualizarse. Para montos exactos vigentes, se recomienda revisar SUNAT.",
    "como me cambio de regimen tributario": "El cambio de régimen tributario depende del régimen actual, ingresos, actividad y régimen al que deseas pasar. Puede realizarse mediante declaraciones o trámites en SUNAT, según el caso.",
    "que libros contables lleva cada regimen": "Nuevo RUS usualmente no lleva libros formales. RER lleva Registro de Compras y Registro de Ventas. RMT y Régimen General llevan libros según ingresos y obligaciones.",
    "que regimen me conviene": "El régimen que te conviene depende de tus ingresos, tipo de negocio, clientes, gastos, necesidad de emitir factura y obligaciones contables. Para elegir correctamente, conviene revisar SUNAT o consultar a un contador.",
    "puedo cambiar de regimen": "Sí, puedes cambiar de régimen tributario si cumples las condiciones del régimen al que deseas ingresar. El procedimiento depende de tu situación y debe revisarse en SUNAT.",

    # DECLARACIONES, MULTAS Y DEUDAS
    "que es declaracion mensual": "La declaración mensual es la presentación que realiza el contribuyente ante SUNAT para informar ventas, compras, IGV, renta mensual u otras obligaciones del periodo.",
    "cuando vencen las declaraciones mensuales": "Las declaraciones mensuales vencen según el cronograma de SUNAT, el periodo tributario y el último dígito del RUC.",
    "que es el cronograma de vencimientos de sunat": "Es el calendario oficial de SUNAT que indica las fechas límite para declarar y pagar impuestos según el último dígito del RUC.",
    "que pasa si no declaro a tiempo": "Si no declaras a tiempo, puedes generar multas, intereses moratorios, deuda tributaria y posibles restricciones. Lo recomendable es regularizar cuanto antes.",
    "cuanto es la multa por no declarar": "La multa por no declarar depende del régimen, tipo de obligación y tributo omitido. Puede reducirse si regularizas voluntariamente, según corresponda.",
    "como se regulariza una deuda tributaria": "Para regularizar una deuda tributaria debes ingresar a SUNAT con RUC y Clave SOL, revisar la deuda, declarar lo pendiente, pagar o solicitar fraccionamiento si corresponde.",
    "como se si tengo deuda con sunat": "Puedes consultar si tienes deuda ingresando a SUNAT Operaciones en Línea con tu RUC, usuario y Clave SOL.",
    "que es pdt": "El PDT es un Programa de Declaración Telemática usado para presentar ciertas declaraciones tributarias ante SUNAT.",
    "que es declara facil": "Declara Fácil es una plataforma de SUNAT que permite presentar declaraciones y pagos de manera virtual.",
    "que pasa si no pago impuestos": "Si no pagas impuestos, puedes generar intereses, multas, cobranza coactiva, embargos o restricciones tributarias. Lo recomendable es regularizar cuanto antes.",
    "que pasa si declaro fuera de plazo": "Declarar fuera de plazo puede generar multa e intereses. En algunos casos puede haber gradualidad o reducción si regularizas voluntariamente.",
    "interes moratorio": "El interés moratorio es el interés que se genera cuando una deuda tributaria no se paga dentro del plazo establecido.",
    "cobranza coactiva": "La cobranza coactiva es el procedimiento mediante el cual SUNAT exige el pago de deudas tributarias vencidas, pudiendo aplicar medidas como embargos.",
    "fraccionamiento tributario": "El fraccionamiento tributario permite pagar una deuda tributaria en cuotas, siempre que se cumplan los requisitos establecidos por SUNAT.",
    "aplazamiento tributario": "El aplazamiento permite postergar el pago de una deuda tributaria por un tiempo determinado, según las condiciones de SUNAT.",
    "que es una multa tributaria": "Una multa tributaria es una sanción aplicada por incumplir obligaciones tributarias, como no declarar, declarar fuera de plazo, no emitir comprobantes o llevar libros con atraso.",
    "gradualidad": "La gradualidad es un régimen que puede permitir reducir multas si el contribuyente regulariza voluntariamente o cumple ciertas condiciones.",
    "multa por no emitir comprobante": "No emitir comprobante de pago puede generar sanciones como multa o cierre temporal, según la infracción y la normativa aplicable.",
    "multa por libros atrasados": "Llevar libros contables con atraso puede generar multa. El monto depende del tipo de infracción y la norma vigente.",

    # DETRACCIONES, RETENCIONES Y PERCEPCIONES
    "que es el sistema de detracciones": "El sistema de detracciones consiste en depositar un porcentaje del pago en una cuenta del Banco de la Nación a nombre del proveedor, para asegurar el cumplimiento de obligaciones tributarias.",
    "detraccion": "La detracción es un sistema donde una parte del pago se deposita en una cuenta del Banco de la Nación para asegurar el cumplimiento de obligaciones tributarias.",
    "para que sirve la detraccion": "La detracción sirve para asegurar que el proveedor tenga fondos destinados al pago de tributos administrados por SUNAT.",
    "cuenta de detracciones": "La cuenta de detracciones es una cuenta del Banco de la Nación donde se depositan los montos detraídos por operaciones sujetas al sistema.",
    "que bienes y servicios estan sujetos a detraccion": "Los bienes y servicios sujetos a detracción están definidos por SUNAT y pueden variar. Se recomienda revisar la tabla vigente de detracciones.",
    "cual es el porcentaje de detraccion": "El porcentaje de detracción depende del bien o servicio. No existe un solo porcentaje para todos los casos. Debe revisarse la tabla vigente de SUNAT.",
    "que es la retencion del igv": "La retención del IGV es un mecanismo donde un agente designado por SUNAT retiene parte del IGV al proveedor y luego lo entrega al fisco.",
    "retencion": "La retención es un mecanismo donde un agente designado retiene parte del impuesto y luego lo entrega a SUNAT.",
    "quienes son agentes de retencion": "Los agentes de retención son contribuyentes designados por SUNAT para retener parte del IGV en determinadas operaciones.",
    "percepcion": "La percepción es un mecanismo mediante el cual se cobra por adelantado una parte del impuesto que corresponderá pagar en una operación futura.",
    "diferencia entre retencion detraccion y percepcion": "La detracción separa parte del pago y lo deposita en el Banco de la Nación. La retención descuenta parte del impuesto al proveedor. La percepción cobra un adelanto adicional al comprador.",

    # LIBROS CONTABLES
    "que libros contables estoy obligado a llevar": "Los libros contables dependen del régimen tributario, nivel de ingresos y tipo de contribuyente. Pueden incluir Registro de Ventas, Registro de Compras, Libro Diario, Libro Mayor e Inventarios.",
    "que es el ple de sunat": "El PLE es el Programa de Libros Electrónicos de SUNAT. Sirve para validar y presentar libros contables electrónicos.",
    "como se lleva el registro de ventas": "El Registro de Ventas se lleva anotando los comprobantes emitidos por ventas o servicios, como facturas, boletas, notas de crédito y notas de débito.",
    "como se lleva el registro de compras": "El Registro de Compras se lleva anotando comprobantes recibidos por compras, gastos y servicios vinculados al negocio.",
    "cual es el atraso maximo permitido en los libros": "El atraso máximo depende del tipo de libro contable y la norma vigente. Para evitar sanciones, se recomienda revisar los plazos oficiales de SUNAT.",
    "registro de ventas": "El Registro de Ventas contiene los comprobantes emitidos por ventas o servicios. Permite sustentar ingresos y determinar el débito fiscal del IGV.",
    "registro de compras": "El Registro de Compras contiene los comprobantes recibidos por compras y gastos del negocio. Sirve para sustentar crédito fiscal, costos y gastos.",
    "libro diario": "El Libro Diario registra cronológicamente las operaciones económicas de una empresa mediante asientos contables.",
    "libro mayor": "El Libro Mayor organiza las operaciones por cuentas contables, permitiendo conocer movimientos y saldos.",
    "libro de inventarios y balances": "El Libro de Inventarios y Balances muestra información sobre activos, pasivos, patrimonio, inventarios y estados financieros del negocio.",
    "libros electronicos": "Los libros electrónicos son registros contables llevados en formato digital y presentados o validados según las disposiciones de SUNAT.",
    "sire sunat": "El SIRE es el Sistema Integrado de Registros Electrónicos de SUNAT, relacionado con registros de ventas y compras electrónicos.",

    # INDEPENDIENTES Y PRÁCTICAS
    "como calculo mis impuestos si soy independiente": "Si eres independiente, normalmente generas renta de cuarta categoría y emites recibos por honorarios. Debes revisar tus ingresos, retenciones, pagos a cuenta y obligación de declarar.",
    "soy independiente que debo pagar": "Si eres independiente, normalmente generas renta de cuarta categoría. Debes emitir recibos por honorarios y revisar si corresponde retención, pago a cuenta o declaración según tus ingresos.",
    "trabajador independiente": "Un trabajador independiente presta servicios por cuenta propia y normalmente emite recibos por honorarios. Sus ingresos corresponden a renta de cuarta categoría.",
    "suspension de cuarta categoria": "La suspensión de cuarta categoría permite evitar retenciones o pagos a cuenta cuando tus ingresos proyectados no superan los límites establecidos por SUNAT.",
    "retencion cuarta categoria": "La retención de cuarta categoría se aplica a recibos por honorarios cuando corresponde, según el monto y condiciones establecidas por SUNAT.",
    "recibo por honorarios electronico": "El recibo por honorarios electrónico es el comprobante digital que emite un trabajador independiente por sus servicios.",
    "puedo deducir gastos de mi casa si trabajo desde ahi": "Depende de si el gasto está vinculado directamente con la generación de ingresos y si cumple los requisitos tributarios. Los gastos personales no suelen ser deducibles.",
    "que es la uit": "La UIT es la Unidad Impositiva Tributaria. Sirve como valor de referencia para calcular impuestos, multas, deducciones, límites de ingresos, sanciones y obligaciones tributarias.",
    "que es la uit y para que sirve": "La UIT es la Unidad Impositiva Tributaria. Sirve como valor de referencia para calcular impuestos, multas, deducciones, límites de ingresos, sanciones y obligaciones tributarias.",

    # GASTOS Y EMPRESA
    "gastos deducibles": "Los gastos deducibles son aquellos necesarios para generar renta o mantener la fuente productora, siempre que estén sustentados, sean razonables y cumplan la norma tributaria.",
    "gastos no deducibles": "Los gastos no deducibles son aquellos que la norma tributaria no permite descontar para calcular el Impuesto a la Renta, como gastos personales o sin sustento válido.",
    "principio de causalidad": "El principio de causalidad indica que un gasto debe estar relacionado con la generación de ingresos o el mantenimiento de la fuente productora para ser deducible.",
    "bancarizacion": "La bancarización consiste en usar medios de pago del sistema financiero para sustentar ciertas operaciones y permitir su reconocimiento tributario.",
    "comprobante valido": "Un comprobante válido debe cumplir los requisitos establecidos por SUNAT y estar correctamente emitido para sustentar una operación.",
    "sustento tributario": "El sustento tributario es la documentación que respalda una operación, como comprobantes de pago, contratos, medios de pago, registros contables y evidencias.",

    # ADUANAS
    "exportacion": "La exportación es la venta de bienes o servicios hacia el exterior. En materia tributaria puede tener tratamiento especial, como saldo a favor del exportador en ciertos casos.",
    "importacion": "La importación es el ingreso de bienes desde el exterior al país. Puede estar sujeta a tributos aduaneros, IGV y otras obligaciones.",
    "drawback": "El drawback es un mecanismo de restitución de derechos arancelarios para ciertos exportadores que cumplen requisitos.",
    "aduanas": "Aduanas es el área encargada del control de ingreso y salida de mercancías del país, administrada por SUNAT.",
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

    for pregunta, respuesta in RESPUESTAS.items():
        pregunta_limpia = limpiar_texto(pregunta)

        if texto == pregunta_limpia:
            return respuesta

        if pregunta_limpia in texto:
            return respuesta

        if texto in pregunta_limpia and len(texto) > 4:
            return respuesta

    claves = {
        "hola": RESPUESTAS["hola"],
        "buenos dias": RESPUESTAS["buenos dias"],
        "buenas tardes": RESPUESTAS["buenas tardes"],
        "buenas noches": RESPUESTAS["buenas noches"],
        "quien eres": RESPUESTAS["quien eres"],
        "tributax": RESPUESTAS["que es tributax"],

        "igv": RESPUESTAS["que es el igv"],
        "impuesto general a las ventas": RESPUESTAS["que es el igv"],
        "credito fiscal": RESPUESTAS["que es el credito fiscal"],
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
        "y como funciona",
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
        "por que",
        "y por que",
        "para que",
        "y eso",
        "eso que significa",
        "cual es la diferencia",
        "que diferencia hay",
    ]

    if texto in frases:
        return True

    if len(texto.split()) <= 6 and any(
        palabra in texto
        for palabra in [
            "sirve",
            "ejemplo",
            "funciona",
            "usa",
            "emite",
            "calcula",
            "diferencia",
            "significa",
        ]
    ):
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
        if "emite" in pregunta or "usa" in pregunta:
            return "La nota de crédito se emite por devoluciones, descuentos posteriores, errores en el comprobante o anulación de una operación."
        return "Sobre la nota de crédito: se usa para reducir, corregir o anular una operación ya emitida."

    if "igv" in tema:
        if "sirve" in pregunta:
            return "El IGV sirve para gravar el consumo de bienes y servicios en Perú. Las empresas lo cobran en sus ventas y luego lo declaran ante SUNAT."
        if "calcula" in pregunta:
            return "El IGV se calcula aplicando el 18% sobre la base imponible. Si la base es S/ 100, el IGV es S/ 18 y el total S/ 118."
        if "ejemplo" in pregunta:
            return "Ejemplo: si vendes un producto con base de S/ 200, el IGV será S/ 36 y el total será S/ 236."
        return "Sobre el IGV: es el Impuesto General a las Ventas y su tasa general en Perú es 18%."

    if "factura" in tema:
        if "sirve" in pregunta:
            return "La factura sirve para sustentar una venta o servicio. También permite al comprador sustentar gasto, costo o crédito fiscal cuando corresponde."
        if "ejemplo" in pregunta:
            return "Ejemplo: una empresa vende mercadería a otra empresa por S/ 1,000 más IGV y emite una factura para que el comprador pueda sustentar la compra."
        return "Sobre la factura: es un comprobante de pago usado cuando el comprador necesita sustentar crédito fiscal, gasto o costo tributario."

    if "boleta" in tema:
        if "sirve" in pregunta:
            return "La boleta sirve para acreditar una venta o servicio realizado a un consumidor final. Generalmente no permite usar crédito fiscal."
        if "ejemplo" in pregunta:
            return "Ejemplo: una tienda vende un producto a una persona natural para consumo personal y emite una boleta de venta."
        return "Sobre la boleta: se emite normalmente a consumidores finales."

    if "ruc" in tema:
        if "sirve" in pregunta:
            return "El RUC sirve para identificar a una persona o empresa ante SUNAT, emitir comprobantes, declarar impuestos y realizar actividades económicas formales."
        return "Sobre el RUC: es el Registro Único de Contribuyentes usado para identificarte ante SUNAT."

    if "clave sol" in tema:
        if "sirve" in pregunta:
            return "La Clave SOL sirve para ingresar a SUNAT Operaciones en Línea y realizar trámites como declarar, pagar, consultar deudas y emitir comprobantes."
        return "Sobre la Clave SOL: es la contraseña para acceder a los servicios virtuales de SUNAT."

    if "uit" in tema:
        if "sirve" in pregunta:
            return "La UIT sirve como valor de referencia para calcular impuestos, multas, deducciones, límites de ingresos, sanciones y obligaciones tributarias."
        return "Sobre la UIT: es la Unidad Impositiva Tributaria usada como referencia en normas tributarias y administrativas."

    if "detraccion" in tema:
        if "sirve" in pregunta:
            return "La detracción sirve para asegurar que parte del pago se destine al cumplimiento de obligaciones tributarias del proveedor."
        if "ejemplo" in pregunta:
            return "Ejemplo: si un servicio está sujeto a detracción, el comprador deposita un porcentaje del pago en la cuenta de detracciones del proveedor en el Banco de la Nación."
        return "Sobre la detracción: es un sistema donde parte del pago se deposita en el Banco de la Nación para obligaciones tributarias."

    if "retencion" in tema:
        if "sirve" in pregunta:
            return "La retención sirve para que un agente designado descuente parte del impuesto y lo entregue a SUNAT."
        return "Sobre la retención: es un mecanismo mediante el cual un agente retiene parte del impuesto al proveedor."

    if "renta" in tema:
        if "sirve" in pregunta:
            return "El Impuesto a la Renta sirve para gravar los ingresos obtenidos por personas naturales y empresas."
        if "ejemplo" in pregunta:
            return "Ejemplo: una empresa que obtiene utilidades paga Impuesto a la Renta de tercera categoría; un trabajador en planilla tributa renta de quinta categoría."
        return "Sobre el Impuesto a la Renta: grava los ingresos de personas y empresas."

    if "libro" in tema or "ple" in tema or "sire" in tema:
        if "sirve" in pregunta:
            return "Los libros contables sirven para registrar las operaciones económicas del negocio y sustentar información tributaria ante SUNAT."
        return "Sobre libros contables: permiten registrar compras, ventas, operaciones y obligaciones contables del contribuyente."

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

Instrucciones:
- Responde en el mismo idioma del usuario.
- Si la pregunta actual es corta como "para qué sirve", "dame un ejemplo" o "cómo funciona",
  usa el historial para entender a qué tema se refiere.
- Si el usuario cambia de tema, responde el nuevo tema.
- Responde claro, directo y sin mencionar errores técnicos.
- Si se necesitan datos exactos vigentes, recomienda verificar SUNAT.
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
        "Soy TribuTax. Puedo ayudarte con muchos temas tributarios de Perú, por ejemplo:\n\n"
        " IGV: tasa, cálculo, crédito fiscal, operaciones exoneradas e inafectas.\n"
        " RUC y SUNAT: inscripción, domicilio fiscal, Clave SOL, deudas y declaraciones.\n"
        " Comprobantes: factura, boleta, recibo por honorarios, nota de crédito y nota de débito.\n"
        " Impuesto a la Renta: primera, segunda, tercera, cuarta y quinta categoría.\n"
        " Regímenes tributarios: Nuevo RUS, RER, RMT y Régimen General.\n"
        " Detracciones, retenciones y percepciones.\n"
        " Libros contables: Registro de Ventas, Registro de Compras, PLE y SIRE.\n"
        "Multas, fraccionamiento, intereses, UIT y obligaciones tributarias.\n\n"
        "Escríbeme tu pregunta de forma específica, por ejemplo: ¿Qué es el crédito fiscal?"
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