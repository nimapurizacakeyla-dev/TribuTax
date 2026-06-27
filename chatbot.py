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

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
client = None

if GEMINI_API_KEY and genai is not None:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception:
        client = None


# ============================================================
# BASE GENERAL DEL CHATBOT
# ============================================================

BASE_TRIBUTARIA = """
Eres TribuTax, un asistente virtual especializado en tributación peruana.

Tu objetivo es responder consultas tributarias de manera clara, completa, concreta y útil.
Respondes como orientador tributario educativo, no como asesor legal definitivo.

Tu respuesta debe ser más desarrollada, no demasiado corta. Debe explicar:
1. Concepto.
2. Explicación sencilla.
3. Cómo funciona.
4. Ejemplo.
5. Recomendación.

Cuando el usuario pegue un caso práctico con números, debes resolver paso a paso:
1. Datos del caso.
2. Tema tributario identificado.
3. Desarrollo.
4. Fórmula.
5. Resultado.
6. Conclusión.
7. Recomendación.

Temas que dominas:
- Derecho Tributario.
- Código Tributario peruano.
- Actividad financiera del Estado.
- Ingresos públicos e ingresos tributarios.
- Tributo, impuesto, contribución y tasa.
- Arbitrios, derechos y licencias.
- Potestad tributaria.
- Principio de legalidad.
- Reserva de ley.
- Igualdad tributaria.
- Capacidad contributiva.
- No confiscatoriedad.
- Seguridad jurídica.
- Buena fe.
- Norma VIII sobre interpretación tributaria.
- Norma XVI, elusión, simulación y economía de opción.
- Obligación tributaria.
- Nacimiento y exigibilidad de la obligación tributaria.
- Acreedor tributario.
- Deudor tributario.
- Contribuyente.
- Responsable.
- Responsable solidario.
- Agentes de retención y percepción.
- Domicilio fiscal.
- Domicilio procesal.
- Notificaciones tributarias.
- Buzón electrónico.
- SUNAT.
- Facultades de recaudación, fiscalización, determinación y sanción.
- Obligaciones de la Administración Tributaria.
- Obligaciones de los administrados.
- Derechos de los administrados.
- Fiscalización tributaria.
- Verificación.
- Carta inductiva.
- Esquela.
- Requerimiento.
- Resolución de Determinación.
- Orden de Pago.
- Resolución de Multa.
- Procedimiento de cobranza coactiva.
- Deuda exigible coactivamente.
- Resolución de Ejecución Coactiva.
- Ejecutor Coactivo.
- Auxiliar Coactivo.
- Embargos.
- Suspensión y conclusión de cobranza coactiva.
- Reclamación.
- Apelación.
- Queja.
- Tribunal Fiscal.
- Procedimiento contencioso tributario.
- Procedimiento no contencioso.
- Demanda contencioso administrativa.
- Infracciones tributarias.
- Sanciones tributarias.
- Multas.
- Gradualidad.
- Comiso.
- Cierre temporal.
- Internamiento temporal de vehículos.
- Delito tributario.
- Defraudación tributaria.
- IGV.
- Crédito fiscal.
- Débito fiscal.
- IGV incluido.
- IGV por pagar.
- Operaciones gravadas, exoneradas e inafectas.
- Exportaciones.
- Detracciones.
- Retenciones.
- Percepciones.
- Impuesto a la Renta.
- Rentas de primera, segunda, tercera, cuarta y quinta categoría.
- Renta bruta.
- Renta neta.
- Renta neta imponible.
- Costos computables.
- Gastos deducibles.
- Gastos no deducibles.
- Adiciones tributarias.
- Deducciones tributarias.
- Pagos a cuenta.
- Declaración jurada anual.
- Saldo por pagar.
- Saldo a favor.
- Nuevo RUS.
- RER.
- RMT.
- Régimen General.
- Factura.
- Boleta.
- Recibo por honorarios.
- Nota de crédito.
- Nota de débito.
- Guía de remisión.
- Factura electrónica.
- XML.
- CDR.
- OSE.
- PSE.
- Libros contables.
- Registro de Ventas.
- Registro de Compras.
- Libro Diario.
- Libro Mayor.
- PLE.
- SIRE.
- RVIE.
- RCE.
- UIT.
- ITAN.
- ITF.
- ISC.
- Impuesto predial.
- Alcabala.
- Arbitrios.
- Licencia de funcionamiento.
- Aduanas.
- Importación.
- Exportación.
- Drawback.
- Tributos aduaneros.

Reglas:
- No ayudes a evadir impuestos.
- No ayudes a ocultar ingresos.
- No ayudes a falsificar comprobantes.
- No ayudes a engañar a SUNAT.
- Si el usuario pregunta algo ilegal, rechaza esa parte y ofrece alternativas legales.
- Si se necesitan tasas, límites, cronogramas o montos vigentes exactos, recomienda verificar SUNAT, El Peruano, MEF, municipalidad o consultar con un contador.
- No inventes normas actuales si no tienes confirmación.
- No digas que eres Gemini.
- Siempre responde como TribuTax.
"""


# ============================================================
# RESPUESTAS DIRECTAS
# ============================================================

RESPUESTAS_DIRECTAS = {
    "hola": (
        "¡Hola! Soy TribuTax, tu asistente virtual tributario.\n\n"
        "Puedo ayudarte con IGV, RUC, SUNAT, comprobantes de pago, Impuesto a la Renta, "
        "regímenes tributarios, detracciones, retenciones, libros contables, multas, deudas, "
        "cobranza coactiva, reclamaciones, apelaciones y casos prácticos.\n\n"
        "Puedes escribirme una consulta corta o pegar un caso completo con montos."
    ),
    "buenos dias": (
        "¡Buenos días! Soy TribuTax. Escríbeme tu consulta tributaria o pega tu caso práctico "
        "y te ayudo a resolverlo paso a paso."
    ),
    "buenas tardes": (
        "¡Buenas tardes! Soy TribuTax. Puedo ayudarte con teoría tributaria, cálculos prácticos "
        "y orientación sobre SUNAT."
    ),
    "buenas noches": (
        "¡Buenas noches! Soy TribuTax. Estoy listo para ayudarte con tus dudas tributarias."
    ),
    "quien eres": (
        "Soy TribuTax, un asistente virtual tributario creado para responder consultas sobre "
        "tributación peruana y resolver casos prácticos."
    ),
    "que eres": (
        "Soy TribuTax, un chatbot de orientación tributaria del Perú. Puedo ayudarte con temas "
        "como IGV, Renta, SUNAT, RUC, comprobantes, regímenes, libros, multas y procedimientos."
    ),
    "que es tributax": (
        "TribuTax es un chatbot de ayuda tributaria. Responde sobre IGV, RUC, SUNAT, comprobantes, "
        "Impuesto a la Renta, regímenes tributarios, detracciones, retenciones, libros contables, "
        "cobranza coactiva, infracciones, sanciones y casos prácticos."
    ),
    "ayuda": (
        "Puedo ayudarte con:\n\n"
        "1. IGV: cálculo, crédito fiscal, débito fiscal e IGV incluido.\n"
        "2. Renta: categorías, gastos deducibles, pagos a cuenta y declaración anual.\n"
        "3. Comprobantes: factura, boleta, nota de crédito y nota de débito.\n"
        "4. SUNAT: RUC, Clave SOL, deudas, multas y declaraciones.\n"
        "5. Código Tributario: obligación tributaria, fiscalización, cobranza coactiva y reclamaciones.\n"
        "6. Casos prácticos: puedes pegar un caso con montos y lo resuelvo."
    ),
    "gracias": "¡De nada! Si tienes otra consulta tributaria o un caso práctico, escríbeme.",
    "ok": "Perfecto. Puedes hacerme otra consulta tributaria o pegar un caso para resolverlo.",
    "adios": "Hasta luego. Recuerda que TribuTax puede ayudarte con consultas tributarias y casos prácticos.",
}


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


# ============================================================
# DICCIONARIO AMPLIO DE TEMAS
# ============================================================

TEMAS = {
    "derecho tributario": {
        "aliases": ["derecho tributario", "tributacion", "tributación", "materia tributaria"],
        "concepto": "El Derecho Tributario es la rama del Derecho que regula la creación, aplicación, recaudación y control de los tributos.",
        "explicacion": "Su función es ordenar la relación entre el Estado, que necesita recursos públicos, y los contribuyentes, que deben cumplir obligaciones tributarias cuando realizan hechos previstos en la ley.",
        "funcion": "Sirve para establecer reglas claras sobre quién paga, cuánto paga, cuándo paga, cómo declara y qué derechos tiene frente a la Administración Tributaria.",
        "ejemplo": "Cuando una empresa vende productos gravados con IGV, debe emitir comprobantes, registrar la operación y declarar el impuesto ante SUNAT.",
        "recomendacion": "Toda obligación tributaria debe revisarse con base legal, porque los tributos, sanciones y beneficios no pueden crearse libremente sin norma."
    },
    "tributo": {
        "aliases": ["tributo", "tributos", "que es tributo"],
        "concepto": "El tributo es una prestación normalmente en dinero que el Estado exige por ley para financiar el gasto público.",
        "explicacion": "El Código Tributario considera como tributos a los impuestos, contribuciones y tasas. Estos permiten sostener servicios públicos, infraestructura, administración estatal y políticas públicas.",
        "funcion": "Su función principal es recaudar recursos, aunque también puede tener fines extrafiscales, como desincentivar ciertas conductas o promover actividades.",
        "ejemplo": "El IGV es un impuesto; los arbitrios son tasas municipales; algunas aportaciones pueden funcionar como contribuciones.",
        "recomendacion": "Para saber qué tributo corresponde pagar, primero se debe identificar el hecho generador, el sujeto obligado, la base imponible y la tasa aplicable."
    },
    "impuesto": {
        "aliases": ["impuesto", "impuestos", "que es impuesto"],
        "concepto": "El impuesto es el tributo cuyo pago no genera una contraprestación directa a favor del contribuyente.",
        "explicacion": "Se paga porque se realiza un hecho gravado previsto en la ley, no porque el Estado entregue un servicio individualizado al contribuyente.",
        "funcion": "Permite financiar gastos generales del Estado, como salud, educación, seguridad, justicia e infraestructura.",
        "ejemplo": "El IGV y el Impuesto a la Renta son impuestos. Si una empresa vende bienes gravados, paga IGV; si obtiene utilidad, puede pagar Impuesto a la Renta.",
        "recomendacion": "Para calcular un impuesto se debe revisar la base imponible, la tasa y las deducciones o créditos permitidos."
    },
    "contribucion": {
        "aliases": ["contribucion", "contribución", "contribuciones"],
        "concepto": "La contribución es el tributo cuyo hecho generador está vinculado con beneficios derivados de obras públicas o actividades estatales.",
        "explicacion": "A diferencia del impuesto, en la contribución existe una relación más directa entre una actividad estatal y un beneficio para el contribuyente.",
        "funcion": "Busca financiar o recuperar el costo de actividades públicas que generan beneficios identificables.",
        "ejemplo": "Algunas aportaciones a entidades públicas o contribuciones especiales pueden tener esta naturaleza.",
        "recomendacion": "No debe confundirse contribución con impuesto, porque su justificación está asociada a un beneficio o actividad estatal."
    },
    "tasa": {
        "aliases": ["tasa", "tasas", "arbitrio", "arbitrios", "derecho", "derechos", "licencia", "licencias"],
        "concepto": "La tasa es el tributo que se paga por la prestación efectiva de un servicio público individualizado en el contribuyente.",
        "explicacion": "Las tasas pueden ser arbitrios, derechos o licencias. No son iguales a los impuestos porque se vinculan a un servicio o autorización concreta.",
        "funcion": "Sirven para cubrir el costo de servicios administrativos, municipales o autorizaciones.",
        "ejemplo": "Los arbitrios municipales por limpieza pública y serenazgo son tasas. Una licencia de funcionamiento también puede estar vinculada a una tasa.",
        "recomendacion": "Si el cobro corresponde a un servicio contractual privado, no es tasa tributaria."
    },
    "potestad tributaria": {
        "aliases": ["potestad tributaria", "poder tributario", "poder del estado para crear tributos"],
        "concepto": "La potestad tributaria es la facultad del Estado para crear, modificar, suprimir o exonerar tributos dentro de los límites constitucionales.",
        "explicacion": "No es un poder ilimitado. Debe respetar principios como legalidad, reserva de ley, igualdad, capacidad contributiva, no confiscatoriedad y derechos fundamentales.",
        "funcion": "Permite que el Estado obtenga recursos para financiar sus fines públicos.",
        "ejemplo": "El Congreso puede crear impuestos mediante ley. Los gobiernos locales pueden crear arbitrios, derechos y licencias dentro de su jurisdicción y límites legales.",
        "recomendacion": "Si una entidad cobra un tributo, debe existir una norma válida que lo sustente."
    },
    "principio de legalidad": {
        "aliases": ["principio de legalidad", "legalidad tributaria", "reserva de ley", "principio de reserva de ley"],
        "concepto": "El principio de legalidad exige que los elementos esenciales del tributo estén establecidos por ley o norma con rango equivalente.",
        "explicacion": "Esto significa que no se puede crear un tributo, sanción, exoneración o beneficio tributario sin una norma válida.",
        "funcion": "Protege al contribuyente frente a cobros arbitrarios y limita el poder tributario del Estado.",
        "ejemplo": "Para cobrar un impuesto debe existir una ley que indique el hecho gravado, sujeto obligado, base imponible y tasa.",
        "recomendacion": "Si se cuestiona un cobro, revisa primero si existe base legal y si la entidad tiene competencia para exigirlo."
    },
    "capacidad contributiva": {
        "aliases": ["capacidad contributiva", "principio de capacidad contributiva"],
        "concepto": "La capacidad contributiva es el principio según el cual los tributos deben guardar relación con la aptitud económica del contribuyente.",
        "explicacion": "La idea es que quien tiene mayor capacidad económica puede contribuir en mayor medida al sostenimiento del Estado.",
        "funcion": "Busca justicia y razonabilidad en la imposición tributaria.",
        "ejemplo": "El Impuesto a la Renta grava ingresos o utilidades porque estos revelan capacidad económica.",
        "recomendacion": "Un tributo puede ser cuestionable si resulta desproporcionado o no guarda relación con una manifestación de riqueza."
    },
    "no confiscatoriedad": {
        "aliases": ["no confiscatoriedad", "principio de no confiscatoriedad", "confiscatorio"],
        "concepto": "El principio de no confiscatoriedad impide que un tributo absorba una parte irrazonable o excesiva del patrimonio o renta del contribuyente.",
        "explicacion": "Los tributos pueden afectar la riqueza, pero no deben destruirla ni vaciar el derecho de propiedad.",
        "funcion": "Sirve como límite constitucional al poder tributario.",
        "ejemplo": "Un impuesto que consume casi toda la utilidad de una empresa podría ser cuestionado por posible efecto confiscatorio.",
        "recomendacion": "La confiscatoriedad se analiza caso por caso, considerando la carga tributaria y la situación concreta."
    },
    "fuentes del derecho tributario": {
        "aliases": ["fuentes del derecho tributario", "fuentes tributarias", "fuentes de derecho tributario"],
        "concepto": "Las fuentes del Derecho Tributario son los medios que producen o interpretan normas tributarias válidas.",
        "explicacion": "Incluyen la Constitución, tratados, leyes tributarias, normas de rango equivalente, decretos supremos, reglamentos, jurisprudencia, resoluciones generales de la Administración y doctrina.",
        "funcion": "Permiten identificar qué norma debe aplicarse y con qué jerarquía.",
        "ejemplo": "Una resolución del Tribunal Fiscal de observancia obligatoria puede orientar la interpretación de una norma tributaria.",
        "recomendacion": "Cuando exista conflicto, debe revisarse la jerarquía normativa y si la norma está vigente."
    },
    "interpretacion tributaria": {
        "aliases": ["interpretacion tributaria", "interpretación tributaria", "norma viii", "interpretacion de normas tributarias"],
        "concepto": "La interpretación tributaria consiste en determinar el sentido de una norma tributaria usando métodos admitidos por el Derecho.",
        "explicacion": "La Norma VIII permite usar métodos de interpretación, pero prohíbe crear tributos, sanciones o exoneraciones mediante interpretación.",
        "funcion": "Ayuda a aplicar correctamente normas tributarias cuando existe duda sobre su alcance.",
        "ejemplo": "Si una norma no incluye expresamente un supuesto, no se puede extender por analogía para crear una sanción.",
        "recomendacion": "En tributación, la interpretación debe ser cuidadosa porque afecta obligaciones económicas y derechos del contribuyente."
    },
    "norma xvi": {
        "aliases": ["norma xvi", "elusion", "elusión", "simulacion", "simulación", "clausula antielusiva", "cláusula antielusiva"],
        "concepto": "La Norma XVI permite a SUNAT calificar la verdadera naturaleza de los actos y combatir supuestos de elusión o simulación.",
        "explicacion": "La economía de opción es elegir una alternativa legal válida. La elusión, en cambio, usa actos artificiosos para evitar o reducir indebidamente tributos. La simulación aparenta actos distintos a los realmente efectuados.",
        "funcion": "Evita que se usen formas legales aparentes para obtener ventajas tributarias indebidas.",
        "ejemplo": "Crear operaciones sin sustancia económica solo para reducir impuestos puede ser observado por SUNAT.",
        "recomendacion": "La planificación tributaria debe ser real, sustentada y con propósito económico válido. No debe basarse en simulaciones."
    },
    "obligacion tributaria": {
        "aliases": ["obligacion tributaria", "obligación tributaria", "nacimiento de la obligacion", "exigibilidad de la obligacion"],
        "concepto": "La obligación tributaria es el vínculo jurídico entre el acreedor tributario y el deudor tributario, establecido por ley, cuyo objeto es cumplir una prestación tributaria.",
        "explicacion": "Nace cuando se realiza el hecho previsto por la ley como generador del tributo. Puede ser exigible desde el vencimiento del plazo legal o desde la notificación de la resolución correspondiente.",
        "funcion": "Permite exigir el pago del tributo y el cumplimiento de obligaciones formales.",
        "ejemplo": "Si una empresa vende bienes gravados con IGV, nace la obligación de declarar y pagar el impuesto según el periodo correspondiente.",
        "recomendacion": "Para analizar una obligación, identifica hecho generador, sujeto obligado, base imponible, tasa, plazo y forma de declaración."
    },
    "acreedor tributario": {
        "aliases": ["acreedor tributario", "acreedor"],
        "concepto": "El acreedor tributario es la entidad pública a favor de la cual debe realizarse la prestación tributaria.",
        "explicacion": "Puede ser el Gobierno Central, gobiernos regionales, gobiernos locales u otra entidad pública cuando la ley le otorgue esa calidad.",
        "funcion": "Tiene derecho a exigir el cumplimiento de la obligación tributaria.",
        "ejemplo": "SUNAT administra tributos del Gobierno Central como IGV e Impuesto a la Renta.",
        "recomendacion": "No siempre quien administra el tributo es quien finalmente recibe el recurso, por eso debe revisarse la norma aplicable."
    },
    "deudor tributario": {
        "aliases": ["deudor tributario", "deudor", "contribuyente", "responsable"],
        "concepto": "El deudor tributario es la persona obligada al cumplimiento de la prestación tributaria como contribuyente o responsable.",
        "explicacion": "El contribuyente realiza el hecho generador. El responsable, aunque no realice directamente el hecho generador, debe cumplir la obligación atribuida por ley.",
        "funcion": "Determina quién debe declarar, pagar o cumplir obligaciones tributarias.",
        "ejemplo": "Una empresa que vende bienes gravados es contribuyente del IGV. Un agente de retención puede ser responsable de retener y pagar un tributo.",
        "recomendacion": "Es importante distinguir contribuyente, responsable y representante legal porque sus obligaciones y riesgos no siempre son iguales."
    },
    "responsabilidad solidaria": {
        "aliases": ["responsabilidad solidaria", "responsable solidario", "representante responsable"],
        "concepto": "La responsabilidad solidaria permite exigir una deuda tributaria a un tercero responsable, además del contribuyente principal, cuando la ley lo establece.",
        "explicacion": "Puede alcanzar a representantes legales, administradores, liquidadores u otros sujetos cuando incumplen deberes o actúan con dolo, negligencia grave o abuso de facultades.",
        "funcion": "Busca asegurar el cobro de la deuda tributaria y evitar que el incumplimiento quede sin responsable.",
        "ejemplo": "Un representante legal que no declara ni paga tributos de la empresa podría ser evaluado como responsable solidario si se cumplen los supuestos legales.",
        "recomendacion": "Los representantes deben conservar documentación, llevar contabilidad, declarar oportunamente y actuar con diligencia."
    },
    "domicilio fiscal": {
        "aliases": ["domicilio fiscal", "domicilio procesal", "cambio de domicilio fiscal"],
        "concepto": "El domicilio fiscal es el lugar fijado por el contribuyente para efectos tributarios.",
        "explicacion": "SUNAT puede notificar actos en el domicilio fiscal. Se considera válido mientras no se comunique el cambio conforme a las reglas aplicables.",
        "funcion": "Permite ubicar al contribuyente para notificaciones, verificaciones, fiscalizaciones y cobranza.",
        "ejemplo": "Si SUNAT notifica una orden de pago en el domicilio fiscal declarado, la notificación puede surtir efectos aunque el contribuyente no revise oportunamente.",
        "recomendacion": "Mantén actualizado tu domicilio fiscal y revisa tu buzón electrónico para evitar perder plazos."
    },
    "sunat": {
        "aliases": ["sunat", "administracion tributaria", "administración tributaria"],
        "concepto": "SUNAT es la Superintendencia Nacional de Aduanas y de Administración Tributaria.",
        "explicacion": "Administra tributos internos y aduaneros, registra contribuyentes, recauda, fiscaliza, sanciona y controla el cumplimiento tributario.",
        "funcion": "Permite al Estado recaudar ingresos tributarios y controlar obligaciones de contribuyentes.",
        "ejemplo": "SUNAT puede fiscalizar una empresa, solicitar libros contables, emitir resoluciones de determinación o iniciar cobranza coactiva.",
        "recomendacion": "Todo contribuyente debe revisar periódicamente su buzón electrónico, declaraciones, deudas y obligaciones pendientes."
    },
    "facultad de fiscalizacion": {
        "aliases": ["fiscalizacion", "fiscalización", "facultad de fiscalizacion", "auditoria sunat", "verificacion", "verificación"],
        "concepto": "La facultad de fiscalización permite a SUNAT revisar si el contribuyente declaró y pagó correctamente sus tributos.",
        "explicacion": "Puede solicitar libros, comprobantes, contratos, sustentos bancarios, registros contables y otra documentación vinculada a las obligaciones tributarias.",
        "funcion": "Sirve para verificar la correcta determinación de tributos y detectar omisiones, reparos o infracciones.",
        "ejemplo": "SUNAT puede revisar si el crédito fiscal usado por una empresa tiene comprobantes válidos y relación con operaciones gravadas.",
        "recomendacion": "Guarda tus comprobantes, registros contables, contratos y medios de pago. Responde los requerimientos dentro del plazo."
    },
    "carta inductiva": {
        "aliases": ["carta inductiva", "esquela", "requerimiento", "comunicacion sunat", "comunicación sunat"],
        "concepto": "La carta inductiva o esquela es una comunicación de SUNAT que alerta al contribuyente sobre posibles inconsistencias.",
        "explicacion": "No siempre implica una fiscalización definitiva, pero debe revisarse con cuidado porque puede anticipar observaciones de SUNAT.",
        "funcion": "Busca que el contribuyente revise, sustente o corrija voluntariamente su situación tributaria.",
        "ejemplo": "SUNAT puede enviar una carta indicando diferencias entre ventas declaradas y comprobantes electrónicos emitidos.",
        "recomendacion": "No ignores estas comunicaciones. Revisa la información, contrasta tus registros y regulariza si corresponde."
    },
    "notificacion tributaria": {
        "aliases": ["notificacion", "notificación", "notificacion tributaria", "buzon electronico", "buzón electrónico"],
        "concepto": "La notificación tributaria es el acto mediante el cual la Administración comunica formalmente una resolución, requerimiento u otro acto al contribuyente.",
        "explicacion": "Puede realizarse por domicilio fiscal, buzón electrónico, constancia administrativa, publicación u otros medios previstos por ley.",
        "funcion": "Permite que el contribuyente conozca el acto y se computen plazos para responder, reclamar o apelar.",
        "ejemplo": "Una resolución de multa notificada en el buzón electrónico puede iniciar el plazo para impugnar.",
        "recomendacion": "Revisa constantemente el buzón electrónico de SUNAT porque las notificaciones pueden generar plazos importantes."
    },
    "cobranza coactiva": {
        "aliases": ["cobranza coactiva", "procedimiento de cobranza coactiva", "ejecucion coactiva", "ejecución coactiva", "rec"],
        "concepto": "La cobranza coactiva es el procedimiento administrativo mediante el cual la Administración Tributaria cobra deudas exigibles usando su facultad coercitiva.",
        "explicacion": "Se inicia normalmente con una Resolución de Ejecución Coactiva. En este procedimiento pueden dictarse medidas como embargos para asegurar el cobro.",
        "funcion": "Sirve para hacer efectiva la recaudación cuando el contribuyente no paga voluntariamente una deuda exigible.",
        "ejemplo": "Si una orden de pago queda exigible y no se cancela, SUNAT puede iniciar cobranza coactiva y ordenar embargo en cuentas bancarias.",
        "recomendacion": "Revisa si la deuda es exigible, si la notificación fue válida, si existe recurso pendiente o causal de suspensión o conclusión."
    },
    "ejecutor coactivo": {
        "aliases": ["ejecutor coactivo", "auxiliar coactivo", "funcionario coactivo"],
        "concepto": "El Ejecutor Coactivo es el funcionario responsable de dirigir el procedimiento de cobranza coactiva.",
        "explicacion": "Puede ordenar medidas de coerción, como embargos o remates, para cobrar deudas tributarias exigibles.",
        "funcion": "Garantiza la ejecución de la deuda dentro del procedimiento administrativo.",
        "ejemplo": "El Ejecutor Coactivo puede ordenar embargo en forma de retención sobre cuentas bancarias del deudor.",
        "recomendacion": "Si recibes una Resolución de Ejecución Coactiva, revisa plazos y causales de suspensión de inmediato."
    },
    "embargo": {
        "aliases": ["embargo", "embargo en retencion", "embargo en forma de retencion", "embargo en inscripcion", "embargo en deposito"],
        "concepto": "El embargo es una medida de cobranza que afecta bienes, cuentas, créditos o derechos del deudor para asegurar el pago de una deuda exigible.",
        "explicacion": "Puede ser en forma de retención, inscripción, depósito, intervención u otras modalidades permitidas por la norma.",
        "funcion": "Busca garantizar que la deuda tributaria pueda ser cobrada.",
        "ejemplo": "SUNAT puede ordenar a un banco retener fondos de una cuenta del contribuyente deudor.",
        "recomendacion": "Antes de cuestionar un embargo, verifica la deuda, la notificación, el estado del procedimiento y si existe causal de suspensión."
    },
    "reclamacion": {
        "aliases": ["reclamacion", "reclamación", "reclamo tributario", "procedimiento contencioso"],
        "concepto": "La reclamación es un recurso que permite cuestionar actos tributarios ante la propia Administración Tributaria.",
        "explicacion": "Puede presentarse contra resoluciones de determinación, resoluciones de multa, órdenes de pago y otros actos impugnables según corresponda.",
        "funcion": "Sirve para que la Administración revise su propio acto antes de que el caso llegue al Tribunal Fiscal.",
        "ejemplo": "Una empresa puede reclamar una resolución de multa si considera que SUNAT aplicó incorrectamente una infracción.",
        "recomendacion": "Revisa el plazo, requisitos, pruebas y si debes pagar o garantizar previamente según el tipo de acto."
    },
    "apelacion": {
        "aliases": ["apelacion", "apelación", "tribunal fiscal", "rtf"],
        "concepto": "La apelación es el recurso que permite llevar una controversia tributaria ante el Tribunal Fiscal.",
        "explicacion": "Se presenta cuando el contribuyente no está conforme con lo resuelto en reclamación o cuando corresponde impugnar directamente ciertos actos.",
        "funcion": "Permite que un órgano administrativo independiente resuelva la controversia en segunda instancia administrativa.",
        "ejemplo": "Si SUNAT declara infundada una reclamación, el contribuyente puede apelar ante el Tribunal Fiscal dentro del plazo aplicable.",
        "recomendacion": "Sustenta la apelación con argumentos, pruebas y normas aplicables. Revisa cuidadosamente los plazos."
    },
    "queja": {
        "aliases": ["queja", "recurso de queja", "queja tributaria"],
        "concepto": "La queja es un mecanismo para cuestionar actuaciones o procedimientos indebidos de la Administración Tributaria o del Tribunal Fiscal.",
        "explicacion": "No sirve para discutir el fondo del tributo, sino defectos en el procedimiento, demoras o actuaciones que afecten derechos.",
        "funcion": "Protege al administrado frente a irregularidades procedimentales.",
        "ejemplo": "Puede presentarse queja si la Administración continúa una cobranza coactiva pese a existir una causal de suspensión.",
        "recomendacion": "Identifica claramente el acto procedimental cuestionado y adjunta sustento."
    },
    "infraccion tributaria": {
        "aliases": ["infraccion", "infracción", "infraccion tributaria", "sancion tributaria", "sanción tributaria"],
        "concepto": "La infracción tributaria es toda acción u omisión que viola normas tributarias y está tipificada como infracción.",
        "explicacion": "No basta con que una conducta sea incorrecta; debe estar prevista legalmente como infracción para que pueda sancionarse.",
        "funcion": "Permite sancionar incumplimientos como no declarar, declarar fuera de plazo, no emitir comprobantes o no llevar libros.",
        "ejemplo": "No presentar una declaración dentro del plazo puede generar una infracción sancionada con multa.",
        "recomendacion": "Revisa la tabla de infracciones aplicable, el régimen tributario y la gradualidad para reducir la sanción si corresponde."
    },
    "multa tributaria": {
        "aliases": ["multa", "multas", "multa tributaria", "gradualidad"],
        "concepto": "La multa tributaria es una sanción económica por cometer una infracción tributaria.",
        "explicacion": "Su monto puede depender de la UIT, ingresos, tributo omitido, régimen tributario o tipo de infracción.",
        "funcion": "Busca sancionar e incentivar el cumplimiento de obligaciones tributarias.",
        "ejemplo": "Declarar fuera de plazo puede generar multa, aunque puede aplicarse gradualidad si se subsana voluntariamente.",
        "recomendacion": "Antes de pagar una multa, revisa si existe rebaja por gradualidad, subsanación o pago voluntario."
    },
    "delito tributario": {
        "aliases": ["delito tributario", "defraudacion tributaria", "defraudación tributaria"],
        "concepto": "El delito tributario es una conducta grave que busca defraudar al Estado mediante engaño, ocultamiento o maniobras fraudulentas.",
        "explicacion": "A diferencia de una infracción administrativa, puede tener consecuencias penales.",
        "funcion": "Protege la recaudación fiscal frente a conductas fraudulentas graves.",
        "ejemplo": "Usar comprobantes falsos para reducir impuestos puede generar consecuencias administrativas y penales.",
        "recomendacion": "Si existe riesgo de delito tributario, se debe buscar asesoría profesional y regularizar legalmente. No se debe continuar la conducta."
    },
    "igv": {
        "aliases": ["igv", "impuesto general a las ventas", "base imponible", "igv incluido", "precio con igv", "precio sin igv"],
        "concepto": "El IGV es el Impuesto General a las Ventas que grava principalmente la venta de bienes, prestación de servicios, contratos de construcción, primera venta de inmuebles por constructores e importaciones.",
        "explicacion": "En Perú la tasa general del IGV es 18%, compuesta por 16% de IGV y 2% de Impuesto de Promoción Municipal.",
        "funcion": "Grava el consumo y se declara normalmente de forma mensual.",
        "ejemplo": "Si vendes S/ 1,000 más IGV, el IGV es S/ 180 y el total es S/ 1,180.",
        "recomendacion": "Para calcular correctamente el IGV identifica si el monto está incluido o si se debe agregar."
    },
    "credito fiscal": {
        "aliases": ["credito fiscal", "crédito fiscal", "igv compras", "credito de compras"],
        "concepto": "El crédito fiscal es el IGV pagado en compras que puede descontarse del IGV generado por ventas.",
        "explicacion": "Para usarlo, la compra debe estar vinculada al negocio, tener comprobante válido, estar registrada y cumplir requisitos sustanciales y formales.",
        "funcion": "Reduce el IGV por pagar.",
        "ejemplo": "Si tu IGV de ventas es S/ 900 y tu IGV de compras aceptado es S/ 400, pagas S/ 500.",
        "recomendacion": "No uses crédito fiscal de gastos personales, comprobantes inválidos o compras no vinculadas al giro del negocio."
    },
    "debito fiscal": {
        "aliases": ["debito fiscal", "débito fiscal", "igv ventas"],
        "concepto": "El débito fiscal es el IGV generado por las ventas o servicios gravados realizados por el contribuyente.",
        "explicacion": "Se compara con el crédito fiscal para determinar si existe IGV por pagar.",
        "funcion": "Representa el IGV que el vendedor debe declarar por sus operaciones gravadas.",
        "ejemplo": "Ventas gravadas S/ 10,000 generan débito fiscal de S/ 1,800.",
        "recomendacion": "Registra correctamente tus comprobantes emitidos para evitar diferencias con SUNAT."
    },
    "exonerado e inafecto": {
        "aliases": ["exonerado", "inafecto", "exoneracion", "exoneración", "inafectacion", "inafectación"],
        "concepto": "Una operación exonerada está dentro del campo del tributo, pero una norma libera del pago. Una operación inafecta está fuera del campo de aplicación del tributo.",
        "explicacion": "La diferencia es importante porque afecta la declaración, el crédito fiscal y la forma de sustentar la operación.",
        "funcion": "Permite identificar si una operación está gravada, liberada o fuera del impuesto.",
        "ejemplo": "Una operación puede estar gravada por naturaleza, pero exonerada por una norma especial. En cambio, una operación inafecta nunca ingresa al ámbito del impuesto.",
        "recomendacion": "Verifica la norma vigente antes de tratar una operación como exonerada o inafecta."
    },
    "detraccion": {
        "aliases": ["detraccion", "detracción", "detracciones", "spot", "sistema de detracciones"],
        "concepto": "La detracción es un mecanismo por el cual el comprador deposita un porcentaje del pago en una cuenta del Banco de la Nación del proveedor.",
        "explicacion": "Ese dinero sirve para que el proveedor pague obligaciones tributarias.",
        "funcion": "Asegura fondos para el pago de tributos.",
        "ejemplo": "Si un servicio de S/ 1,000 está sujeto a detracción del 12%, se deposita S/ 120 y se paga al proveedor S/ 880.",
        "recomendacion": "Verifica siempre si el bien o servicio está sujeto a detracción y qué porcentaje aplica."
    },
    "retencion": {
        "aliases": ["retencion", "retención", "retenciones", "agente de retencion"],
        "concepto": "La retención es un mecanismo por el cual un agente designado retiene parte del pago al proveedor y lo entrega al fisco.",
        "explicacion": "Puede aplicarse en determinados supuestos, como retenciones del IGV o renta.",
        "funcion": "Facilita la recaudación adelantada del impuesto.",
        "ejemplo": "Si una operación es de S/ 2,000 y se aplica retención del 3%, se retiene S/ 60.",
        "recomendacion": "Verifica si el cliente es agente de retención y si la operación está sujeta al régimen."
    },
    "percepcion": {
        "aliases": ["percepcion", "percepción", "percepciones"],
        "concepto": "La percepción es un cobro adicional que realiza un agente al comprador como adelanto del impuesto.",
        "explicacion": "A diferencia de la retención, la percepción se suma al importe que paga el comprador.",
        "funcion": "Permite adelantar recaudación tributaria.",
        "ejemplo": "Si una operación es de S/ 1,000 y hay percepción del 2%, el comprador paga S/ 1,020.",
        "recomendacion": "El comprador puede usar la percepción como crédito o saldo según corresponda."
    },
    "impuesto a la renta": {
        "aliases": ["impuesto a la renta", "renta", "ir", "renta empresarial"],
        "concepto": "El Impuesto a la Renta grava ingresos, rentas o utilidades obtenidas por personas naturales o empresas.",
        "explicacion": "Se clasifica en rentas de primera, segunda, tercera, cuarta y quinta categoría.",
        "funcion": "Permite gravar manifestaciones de capacidad económica.",
        "ejemplo": "Una empresa paga renta de tercera categoría por sus utilidades. Un trabajador independiente genera renta de cuarta categoría.",
        "recomendacion": "Para calcularlo correctamente identifica la categoría, ingresos, deducciones, gastos permitidos, pagos a cuenta y tasa aplicable."
    },
    "renta de primera categoria": {
        "aliases": ["renta de primera", "primera categoria", "primera categoría", "alquiler", "alquileres"],
        "concepto": "La renta de primera categoría proviene principalmente del alquiler de bienes muebles o inmuebles.",
        "explicacion": "La genera el propietario o poseedor que recibe ingresos por arrendamiento.",
        "funcion": "Permite tributar los ingresos por alquiler.",
        "ejemplo": "Si alquilas un departamento y recibes una mensualidad, generas renta de primera categoría.",
        "recomendacion": "Declara el alquiler y conserva contratos, pagos y constancias."
    },
    "renta de segunda categoria": {
        "aliases": ["renta de segunda", "segunda categoria", "segunda categoría", "dividendos", "intereses", "ganancia de capital"],
        "concepto": "La renta de segunda categoría comprende ingresos de capital como intereses, regalías, dividendos y ganancias de capital.",
        "explicacion": "Puede originarse por inversiones, cesión de derechos o venta de ciertos bienes.",
        "funcion": "Grava rendimientos del capital.",
        "ejemplo": "Recibir dividendos de una empresa puede generar renta de segunda categoría.",
        "recomendacion": "Verifica si corresponde retención o declaración directa."
    },
    "renta de tercera categoria": {
        "aliases": ["renta de tercera", "tercera categoria", "tercera categoría", "renta empresarial", "empresa"],
        "concepto": "La renta de tercera categoría corresponde a actividades empresariales.",
        "explicacion": "Se determina considerando ingresos, costos, gastos deducibles, adiciones, deducciones y pagos a cuenta.",
        "funcion": "Grava las utilidades empresariales.",
        "ejemplo": "Una tienda que compra y vende mercadería genera renta de tercera categoría.",
        "recomendacion": "Lleva contabilidad ordenada y sustenta costos y gastos con comprobantes válidos."
    },
    "renta de cuarta categoria": {
        "aliases": ["renta de cuarta", "cuarta categoria", "cuarta categoría", "honorarios", "recibo por honorarios", "independiente"],
        "concepto": "La renta de cuarta categoría corresponde al trabajo independiente.",
        "explicacion": "Se genera cuando una persona presta servicios sin relación laboral dependiente y emite recibos por honorarios.",
        "funcion": "Grava ingresos de profesionales u oficios independientes.",
        "ejemplo": "Un diseñador independiente que emite recibo por honorarios genera renta de cuarta categoría.",
        "recomendacion": "Revisa si corresponde retención, pago a cuenta o suspensión de retenciones."
    },
    "renta de quinta categoria": {
        "aliases": ["renta de quinta", "quinta categoria", "quinta categoría", "planilla", "sueldo", "trabajador en planilla"],
        "concepto": "La renta de quinta categoría corresponde al trabajo dependiente en planilla.",
        "explicacion": "El empleador calcula y retiene el impuesto si los ingresos superan los límites aplicables.",
        "funcion": "Grava remuneraciones de trabajadores dependientes.",
        "ejemplo": "Un trabajador contratado en planilla genera renta de quinta categoría.",
        "recomendacion": "Revisa tus boletas de pago y retenciones anuales si tienes más de un empleador."
    },
    "gastos deducibles": {
        "aliases": ["gastos deducibles", "gasto deducible", "gastos no deducibles", "gasto no deducible", "principio de causalidad"],
        "concepto": "Los gastos deducibles son aquellos que pueden restarse para determinar la renta neta porque están vinculados a generar renta o mantener la fuente productora.",
        "explicacion": "Deben cumplir causalidad, razonabilidad, fehaciencia, sustento documentario, registro contable y bancarización cuando corresponda.",
        "funcion": "Reducen legalmente la base imponible del Impuesto a la Renta.",
        "ejemplo": "Alquiler del local, servicios del negocio, sueldos, compras vinculadas al giro y publicidad pueden ser deducibles si cumplen requisitos.",
        "recomendacion": "No registres gastos personales como gastos del negocio. SUNAT puede repararlos y generar adiciones tributarias."
    },
    "adiciones tributarias": {
        "aliases": ["adiciones", "adiciones tributarias", "reparos tributarios", "gastos reparables"],
        "concepto": "Las adiciones tributarias son importes que se suman a la utilidad contable para determinar la renta neta imponible.",
        "explicacion": "Generalmente corresponden a gastos contabilizados que no son aceptados tributariamente.",
        "funcion": "Corrigen la diferencia entre resultado contable y resultado tributario.",
        "ejemplo": "Una multa tributaria registrada como gasto contable puede adicionarse porque no es deducible.",
        "recomendacion": "Identifica cada gasto no deducible al cierre del ejercicio para evitar errores en la declaración anual."
    },
    "pagos a cuenta": {
        "aliases": ["pagos a cuenta", "pago a cuenta", "adelanto de renta"],
        "concepto": "Los pagos a cuenta son adelantos mensuales del Impuesto a la Renta.",
        "explicacion": "Se realizan durante el ejercicio y luego se descuentan del impuesto anual determinado.",
        "funcion": "Permiten adelantar recaudación y reducir el saldo final por pagar.",
        "ejemplo": "Si el impuesto anual es S/ 35,000 y los pagos a cuenta son S/ 42,000, existe saldo a favor de S/ 7,000.",
        "recomendacion": "Controla tus pagos a cuenta mensualmente para evitar errores en la declaración anual."
    },
    "nuevo rus": {
        "aliases": ["nuevo rus", "rus", "regimen unico simplificado", "régimen único simplificado"],
        "concepto": "El Nuevo RUS es un régimen tributario simplificado para pequeños negocios de personas naturales.",
        "explicacion": "Permite pagar una cuota mensual fija según ingresos o compras, pero tiene limitaciones sobre actividades, comprobantes y montos.",
        "funcion": "Facilita el cumplimiento tributario de pequeños contribuyentes.",
        "ejemplo": "Una pequeña bodega puede estar en Nuevo RUS si cumple los requisitos vigentes.",
        "recomendacion": "Verifica límites actuales, actividades permitidas y si necesitas emitir factura, porque el Nuevo RUS tiene restricciones."
    },
    "rer": {
        "aliases": ["rer", "regimen especial", "régimen especial", "regimen especial de renta"],
        "concepto": "El RER es el Régimen Especial de Renta para ciertos negocios que cumplen requisitos y límites.",
        "explicacion": "Tiene obligaciones simplificadas frente al Régimen General, pero no todas las actividades pueden acogerse.",
        "funcion": "Permite tributar de manera más simple a determinados contribuyentes.",
        "ejemplo": "Un pequeño negocio comercial que emite facturas podría estar en RER si cumple límites y actividad permitida.",
        "recomendacion": "Antes de acogerte, revisa ingresos, compras, activos, trabajadores y actividad económica."
    },
    "rmt": {
        "aliases": ["rmt", "regimen mype tributario", "régimen mype tributario", "mype tributario"],
        "concepto": "El RMT es el Régimen MYPE Tributario, orientado a micro y pequeñas empresas.",
        "explicacion": "Permite determinar el impuesto según utilidad, con reglas específicas y obligaciones contables según ingresos.",
        "funcion": "Busca adecuar la carga tributaria al tamaño de la empresa.",
        "ejemplo": "Una pequeña empresa formal puede tributar en RMT si cumple los requisitos.",
        "recomendacion": "Lleva control de ingresos, gastos y libros para determinar correctamente el impuesto."
    },
    "regimen general": {
        "aliases": ["regimen general", "régimen general", "general"],
        "concepto": "El Régimen General es el régimen tributario con obligaciones completas para empresas.",
        "explicacion": "Permite realizar todo tipo de actividades, pero exige contabilidad más completa y determinación anual de renta.",
        "funcion": "Grava la utilidad empresarial bajo reglas generales.",
        "ejemplo": "Una empresa grande o con actividades excluidas de regímenes simplificados suele estar en Régimen General.",
        "recomendacion": "Requiere contabilidad ordenada, control de gastos deducibles y cumplimiento mensual y anual."
    },
    "factura": {
        "aliases": ["factura", "factura electronica", "factura electrónica"],
        "concepto": "La factura es un comprobante de pago que sustenta una operación y permite al comprador usar gasto, costo o crédito fiscal si corresponde.",
        "explicacion": "Se emite normalmente cuando el cliente tiene RUC o necesita sustentar tributariamente la operación.",
        "funcion": "Sirve para acreditar ventas, compras, IGV, costos y gastos.",
        "ejemplo": "Una empresa vende mercadería a otra empresa y emite factura electrónica.",
        "recomendacion": "Verifica RUC, descripción, importe, IGV, fecha y validez del comprobante."
    },
    "boleta": {
        "aliases": ["boleta", "boleta de venta"],
        "concepto": "La boleta es un comprobante de pago emitido generalmente a consumidores finales.",
        "explicacion": "No suele otorgar derecho a crédito fiscal para el comprador.",
        "funcion": "Acredita una venta o servicio a una persona que no requiere sustento tributario empresarial.",
        "ejemplo": "Una tienda vende un producto a una persona natural y emite boleta.",
        "recomendacion": "Emite boleta cuando corresponda y registra correctamente las ventas."
    },
    "recibo por honorarios": {
        "aliases": ["recibo por honorarios", "recibo honorarios", "honorarios electronicos", "honorarios electrónicos"],
        "concepto": "El recibo por honorarios es el comprobante que emite una persona natural por servicios independientes.",
        "explicacion": "Está vinculado a rentas de cuarta categoría.",
        "funcion": "Sustenta el pago de servicios profesionales o independientes.",
        "ejemplo": "Un abogado independiente emite recibo por honorarios por una asesoría.",
        "recomendacion": "Verifica si corresponde retención o suspensión de cuarta categoría."
    },
    "nota de credito": {
        "aliases": ["nota de credito", "nota de crédito", "nota credito", "devolucion", "devolución", "descuento", "anulacion", "anulación"],
        "concepto": "La nota de crédito es un comprobante que reduce, corrige o anula total o parcialmente una factura o boleta.",
        "explicacion": "Se emite por devoluciones, descuentos posteriores, errores en el comprobante o anulación de operaciones.",
        "funcion": "Disminuye el importe de una operación ya emitida.",
        "ejemplo": "Factura S/ 1,500 y devolución S/ 300: corresponde emitir nota de crédito y el nuevo monto queda en S/ 1,200.",
        "recomendacion": "Relaciona siempre la nota de crédito con el comprobante original."
    },
    "nota de debito": {
        "aliases": ["nota de debito", "nota de débito", "nota debito", "aumento", "recargo", "interes"],
        "concepto": "La nota de débito es un comprobante que aumenta el valor de una factura o boleta ya emitida.",
        "explicacion": "Se usa por intereses, penalidades, recargos, diferencias de precio o gastos adicionales.",
        "funcion": "Incrementa el importe de una operación previa.",
        "ejemplo": "Factura S/ 2,000 y recargo por transporte S/ 250: corresponde nota de débito y el nuevo monto es S/ 2,250.",
        "recomendacion": "Debe vincularse al comprobante original y explicar el motivo del aumento."
    },
    "facturacion electronica": {
        "aliases": ["facturacion electronica", "facturación electrónica", "xml", "cdr", "ose", "pse", "see"],
        "concepto": "La facturación electrónica es la emisión digital de comprobantes con validez tributaria.",
        "explicacion": "Incluye documentos como XML y CDR, y puede emitirse mediante sistemas autorizados, OSE, PSE o SEE.",
        "funcion": "Permite registrar operaciones electrónicamente y facilitar el control tributario.",
        "ejemplo": "Una empresa emite una factura electrónica y recibe un CDR que acredita su validación.",
        "recomendacion": "Conserva XML, CDR y representación impresa cuando corresponda."
    },
    "libros contables": {
        "aliases": ["libros", "libros contables", "contabilidad", "registro de ventas", "registro de compras", "libro diario", "libro mayor"],
        "concepto": "Los libros contables son registros donde se anotan operaciones económicas y tributarias del contribuyente.",
        "explicacion": "Permiten sustentar ventas, compras, gastos, ingresos, inventarios y declaraciones.",
        "funcion": "Sirven para determinar impuestos y demostrar la realidad de las operaciones.",
        "ejemplo": "El Registro de Ventas permite controlar comprobantes emitidos y débito fiscal. El Registro de Compras sustenta crédito fiscal.",
        "recomendacion": "Lleva tus libros dentro del plazo y de acuerdo con tu régimen tributario."
    },
    "ple": {
        "aliases": ["ple", "programa de libros electronicos", "programa de libros electrónicos"],
        "concepto": "El PLE es el Programa de Libros Electrónicos de SUNAT.",
        "explicacion": "Permite validar y enviar libros electrónicos con estructuras determinadas.",
        "funcion": "Facilita el cumplimiento de obligaciones contables electrónicas.",
        "ejemplo": "Una empresa puede validar su Registro de Compras electrónico mediante PLE.",
        "recomendacion": "Revisa formato, periodo y consistencia antes de presentar."
    },
    "sire": {
        "aliases": ["sire", "rvie", "rce", "registro de ventas electronico", "registro de compras electronico"],
        "concepto": "El SIRE es el Sistema Integrado de Registros Electrónicos de SUNAT.",
        "explicacion": "Incluye registros electrónicos como el RVIE y RCE, permitiendo usar información propuesta por SUNAT.",
        "funcion": "Ayuda a llevar registros de ventas y compras de forma electrónica.",
        "ejemplo": "SUNAT puede proponer comprobantes electrónicos para el Registro de Compras Electrónico.",
        "recomendacion": "Revisa y ajusta la información antes de aceptar o presentar."
    },
    "uit": {
        "aliases": ["uit", "unidad impositiva tributaria"],
        "concepto": "La UIT es la Unidad Impositiva Tributaria, un valor de referencia usado en normas tributarias.",
        "explicacion": "Sirve para determinar bases imponibles, deducciones, límites, sanciones, obligaciones contables y otros aspectos.",
        "funcion": "Uniformiza cálculos tributarios y administrativos.",
        "ejemplo": "Una multa puede calcularse como porcentaje de una UIT.",
        "recomendacion": "Verifica el valor vigente de la UIT para el año que estás analizando."
    },
    "deuda tributaria": {
        "aliases": ["deuda tributaria", "deuda sunat", "deuda", "regularizar deuda"],
        "concepto": "La deuda tributaria está compuesta por tributo, multas e intereses cuando corresponda.",
        "explicacion": "Puede originarse por declaraciones omitidas, pagos fuera de plazo, tributos no pagados o sanciones.",
        "funcion": "Representa el monto pendiente de cumplimiento frente al acreedor tributario.",
        "ejemplo": "Si no pagas IGV declarado, se genera deuda con intereses.",
        "recomendacion": "Consulta tu deuda en SUNAT con Clave SOL y evalúa pago, fraccionamiento o reclamación si no estás conforme."
    },
    "fraccionamiento": {
        "aliases": ["fraccionamiento", "fraccionar", "cuotas", "aplazamiento"],
        "concepto": "El fraccionamiento permite pagar una deuda tributaria en cuotas, si se cumplen requisitos.",
        "explicacion": "SUNAT puede aprobar un cronograma de pago, normalmente con intereses y condiciones.",
        "funcion": "Facilita regularizar deudas sin pagarlas en una sola cuota.",
        "ejemplo": "Una deuda de S/ 6,000 dividida en 12 cuotas sería S/ 500 mensuales sin considerar intereses.",
        "recomendacion": "El cálculo real puede incluir intereses. Verifica condiciones antes de solicitarlo."
    },
    "bancarizacion": {
        "aliases": ["bancarizacion", "bancarización", "medios de pago", "pago bancarizado"],
        "concepto": "La bancarización es el uso de medios de pago financieros para sustentar operaciones.",
        "explicacion": "Cuando corresponde, pagar sin medio bancario puede impedir usar gasto, costo o crédito fiscal.",
        "funcion": "Permite trazabilidad de operaciones y combate informalidad.",
        "ejemplo": "Pagar una factura mediante transferencia bancaria ayuda a sustentar la operación.",
        "recomendacion": "Usa medios de pago válidos cuando el monto y la norma lo exijan."
    },
    "planilla": {
        "aliases": ["planilla", "essalud", "onp", "afp", "trabajador dependiente"],
        "concepto": "La planilla registra trabajadores dependientes y sus remuneraciones.",
        "explicacion": "Incluye aportes, retenciones, beneficios laborales y obligaciones del empleador.",
        "funcion": "Formaliza la relación laboral y permite cumplir obligaciones tributarias y laborales.",
        "ejemplo": "Un trabajador en planilla puede generar renta de quinta categoría.",
        "recomendacion": "Registra correctamente a tus trabajadores para evitar contingencias laborales y tributarias."
    },
    "predial": {
        "aliases": ["impuesto predial", "predial", "autovaluo", "autoavaluo"],
        "concepto": "El impuesto predial es un tributo municipal que grava la propiedad de predios urbanos y rústicos.",
        "explicacion": "Lo administra la municipalidad donde se ubica el inmueble.",
        "funcion": "Financia servicios y funciones municipales.",
        "ejemplo": "Tener una casa o terreno puede generar obligación de pagar impuesto predial.",
        "recomendacion": "Consulta la municipalidad para el cálculo exacto y fechas de vencimiento."
    },
    "alcabala": {
        "aliases": ["alcabala", "impuesto de alcabala", "compra de inmueble"],
        "concepto": "La alcabala grava la transferencia de propiedad de bienes inmuebles.",
        "explicacion": "Generalmente la paga el comprador, según las reglas municipales aplicables.",
        "funcion": "Grava la adquisición de inmuebles.",
        "ejemplo": "Comprar un departamento puede generar impuesto de alcabala.",
        "recomendacion": "Antes de comprar un inmueble, calcula costos notariales, registrales y tributarios."
    },
    "aduanas": {
        "aliases": ["aduanas", "importacion", "importación", "exportacion", "exportación", "tributos aduaneros"],
        "concepto": "Aduanas controla el ingreso y salida de mercancías del país.",
        "explicacion": "En importaciones pueden aplicarse derechos arancelarios, IGV, ISC, percepciones u otros conceptos.",
        "funcion": "Controla comercio exterior y recauda tributos aduaneros.",
        "ejemplo": "Importar mercadería puede generar IGV de importación y aranceles.",
        "recomendacion": "Para operaciones reales, revisa partida arancelaria, valor en aduana y régimen aplicable."
    },
    "drawback": {
        "aliases": ["drawback", "restitucion arancelaria", "restitución arancelaria"],
        "concepto": "El drawback es un mecanismo de restitución de derechos arancelarios para ciertos exportadores.",
        "explicacion": "Busca devolver parte de derechos vinculados a insumos importados incorporados en bienes exportados.",
        "funcion": "Promueve exportaciones y reduce costos tributarios asociados a insumos importados.",
        "ejemplo": "Una empresa exportadora puede solicitar drawback si cumple requisitos documentarios y materiales.",
        "recomendacion": "Conserva documentos de importación, producción y exportación para sustentar la solicitud."
    },
}


# ============================================================
# UTILIDADES
# ============================================================

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


def extraer_numeros(mensaje):
    texto = str(mensaje).lower()
    texto = texto.replace(",", "")
    numeros = re.findall(r"\d+(?:\.\d+)?", texto)
    return [float(numero) for numero in numeros]


def formato_soles(numero):
    return f"S/ {numero:,.2f}"


def contiene(texto, palabras):
    return any(palabra in texto for palabra in palabras)


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
        "Eso podría generar infracciones tributarias, multas, fiscalizaciones e incluso consecuencias penales si se trata de una conducta fraudulenta.\n\n"
        "Sí puedo ayudarte con alternativas legales:\n\n"
        "1. Elegir correctamente el régimen tributario.\n"
        "2. Usar gastos deducibles reales y sustentados.\n"
        "3. Aplicar correctamente crédito fiscal.\n"
        "4. Regularizar declaraciones pendientes.\n"
        "5. Solicitar fraccionamiento si tienes deuda.\n"
        "6. Revisar gradualidad para reducir multas legalmente.\n"
        "7. Ordenar libros contables y comprobantes.\n\n"
        "Ejemplo de consulta legal: ¿Qué gastos puedo deducir correctamente en mi empresa?"
    )


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
            r"gastos?\s*(?:deducibles|aceptados|permitidos|administrativos|ventas|operativos)\s*(?:por|de|:)?\s*s?/?\s*([\d,]+(?:\.\d+)?)",
        ],
        "gastos_no_deducibles": [
            r"gastos?\s*(?:no deducibles|reparables|no aceptados)\s*(?:por|de|:)?\s*s?/?\s*([\d,]+(?:\.\d+)?)",
            r"multas?\s*(?:sunat|tributarias|administrativas)?\s*(?:por|de|:)?\s*s?/?\s*([\d,]+(?:\.\d+)?)",
            r"gastos?\s*personales\s*(?:por|de|:)?\s*s?/?\s*([\d,]+(?:\.\d+)?)",
        ],
        "pagos_a_cuenta": [
            r"pagos?\s*a\s*cuenta\s*(?:del impuesto a la renta|de renta)?\s*(?:por|de|:)?\s*s?/?\s*([\d,]+(?:\.\d+)?)",
        ],
        "impuesto_calculado": [
            r"impuesto\s*a\s*la\s*renta\s*(?:determinado|calculado)?\s*(?:por|de|:)?\s*s?/?\s*([\d,]+(?:\.\d+)?)",
            r"impuesto\s*(?:determinado|calculado)\s*(?:por|de|:)?\s*s?/?\s*([\d,]+(?:\.\d+)?)",
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


# ============================================================
# CASOS PRÁCTICOS
# ============================================================

def resolver_caso_saldo_renta(mensaje):
    texto = limpiar_texto(mensaje)
    montos = extraer_montos_con_etiquetas(mensaje)
    numeros = extraer_numeros(mensaje)

    if not contiene(texto, ["saldo por pagar", "saldo a favor", "pagos a cuenta", "impuesto a la renta"]):
        return None

    impuesto = montos.get("impuesto_calculado")
    pagos = montos.get("pagos_a_cuenta")

    if impuesto is None and contiene(texto, ["impuesto a la renta", "impuesto determinado", "impuesto calculado"]) and len(numeros) >= 1:
        impuesto = numeros[0]

    if pagos is None and contiene(texto, ["pagos a cuenta"]) and len(numeros) >= 2:
        pagos = numeros[1]

    if impuesto is not None and pagos is not None:
        saldo = impuesto - pagos

        if saldo > 0:
            resultado = f"Existe saldo por pagar de {formato_soles(saldo)}."
        elif saldo < 0:
            resultado = f"Existe saldo a favor de {formato_soles(abs(saldo))}."
        else:
            resultado = "No existe saldo por pagar ni saldo a favor."

        return (
            "Caso práctico: saldo por pagar o saldo a favor del Impuesto a la Renta\n\n"
            "1. Datos del caso\n"
            f"Impuesto a la Renta determinado: {formato_soles(impuesto)}\n"
            f"Pagos a cuenta realizados: {formato_soles(pagos)}\n\n"
            "2. Tema tributario identificado\n"
            "Se trata de la comparación entre el Impuesto a la Renta anual determinado y los pagos a cuenta realizados durante el ejercicio.\n\n"
            "3. Fórmula\n"
            "Saldo = Impuesto determinado - Pagos a cuenta\n\n"
            "4. Desarrollo\n"
            f"Saldo = {formato_soles(impuesto)} - {formato_soles(pagos)}\n"
            f"Saldo = {formato_soles(saldo)}\n\n"
            "5. Resultado\n"
            f"{resultado}\n\n"
            "6. Conclusión\n"
            "Si el impuesto determinado es mayor que los pagos a cuenta, hay saldo por pagar. "
            "Si los pagos a cuenta son mayores que el impuesto, hay saldo a favor del contribuyente.\n\n"
            "7. Recomendación\n"
            "El saldo debe verificarse en la declaración jurada anual y contrastarse con los pagos registrados en SUNAT."
        )

    return None


def resolver_caso_renta_empresarial_avanzado(mensaje):
    texto = limpiar_texto(mensaje)

    palabras_caso = [
        "ingresos tributarios",
        "costos computables",
        "gastos deducibles",
        "gastos no deducibles",
        "adiciones tributarias",
        "renta neta imponible",
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
            "6. Tasa del impuesto.\n\n"
            "Fórmula general:\n"
            "Renta neta imponible = ingresos - costos - gastos deducibles + adiciones - deducciones.\n"
            "Impuesto a la Renta = renta neta imponible x tasa.\n"
            "Saldo = impuesto calculado - pagos a cuenta.\n\n"
            "Ejemplo de cómo escribirlo:\n"
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
        "Resolución del caso práctico de Impuesto a la Renta empresarial\n\n"
        "1. Datos identificados\n"
        f"Ingresos tributarios: {formato_soles(ingresos)}\n"
        f"Costos computables: {formato_soles(costos)}\n"
        f"Gastos deducibles: {formato_soles(gastos_deducibles)}\n"
        f"Gastos no deducibles: {formato_soles(gastos_no_deducibles)}\n"
        f"Adiciones adicionales: {formato_soles(adiciones)}\n"
        f"Deducciones: {formato_soles(deducciones)}\n"
        f"Pagos a cuenta: {formato_soles(pagos_a_cuenta)}\n"
        f"Tasa aplicada: {tasa}%\n\n"
        "2. Tema tributario identificado\n"
        "Este caso corresponde a la determinación de la renta neta imponible de tercera categoría "
        "y el cálculo del Impuesto a la Renta empresarial.\n\n"
        "3. Identificación de gastos\n"
        "Los gastos deducibles se restan porque están vinculados a la generación de renta o mantenimiento "
        "de la fuente productora. Los gastos no deducibles se adicionan porque no son aceptados tributariamente.\n\n"
        "4. Fórmula\n"
        "Renta neta imponible = ingresos - costos - gastos deducibles + adiciones - deducciones\n\n"
        "5. Desarrollo\n"
        f"Renta neta imponible = {formato_soles(ingresos)} - {formato_soles(costos)} - {formato_soles(gastos_deducibles)} + {formato_soles(gastos_no_deducibles + adiciones)} - {formato_soles(deducciones)}\n"
        f"Renta neta imponible = {formato_soles(renta_neta)}\n\n"
        "6. Impuesto a la Renta\n"
        f"Impuesto a la Renta = {formato_soles(renta_neta)} x {tasa}%\n"
        f"Impuesto a la Renta = {formato_soles(impuesto)}\n\n"
        "7. Saldo final\n"
        f"Saldo = {formato_soles(impuesto)} - {formato_soles(pagos_a_cuenta)}\n"
        f"{resultado_saldo}\n\n"
        "8. Conclusión\n"
        "Si el impuesto calculado supera los pagos a cuenta, la empresa debe pagar la diferencia. "
        "Si los pagos a cuenta son mayores, se genera saldo a favor.\n\n"
        "9. Recomendación\n"
        "Verifica que los gastos deducibles tengan comprobantes válidos, causalidad, fehaciencia, registro contable "
        "y bancarización cuando corresponda."
    )


def resolver_caso_practico(mensaje):
    texto = limpiar_texto(mensaje)
    numeros = extraer_numeros(mensaje)

    caso_saldo = resolver_caso_saldo_renta(mensaje)
    if caso_saldo:
        return caso_saldo

    caso_renta = resolver_caso_renta_empresarial_avanzado(mensaje)
    if caso_renta:
        return caso_renta

    if "igv" in texto and contiene(texto, ["mas igv", "sin igv", "agregar igv", "adicionar igv", "sumar igv"]):
        if len(numeros) >= 1:
            base = numeros[0]
            igv = base * 0.18
            total = base + igv

            return (
                "Caso práctico de IGV sin incluir\n\n"
                "1. Datos del caso\n"
                f"Base imponible: {formato_soles(base)}\n"
                "Tasa del IGV: 18%\n\n"
                "2. Fórmula\n"
                "IGV = base imponible x 18%\n"
                "Total = base imponible + IGV\n\n"
                "3. Desarrollo\n"
                f"IGV = {formato_soles(base)} x 18% = {formato_soles(igv)}\n"
                f"Total = {formato_soles(base)} + {formato_soles(igv)} = {formato_soles(total)}\n\n"
                "4. Resultado\n"
                f"IGV: {formato_soles(igv)}\n"
                f"Total a cobrar: {formato_soles(total)}\n\n"
                "5. Conclusión\n"
                "Si el precio indicado no incluye IGV, debes agregar el 18% para obtener el total facturado."
            )

    if "igv" in texto and contiene(texto, ["incluido", "incluye", "con igv", "ya tiene igv", "precio final"]):
        if len(numeros) >= 1:
            total = numeros[0]
            base = total / 1.18
            igv = total - base

            return (
                "Caso práctico de IGV incluido\n\n"
                "1. Datos del caso\n"
                f"Total con IGV: {formato_soles(total)}\n"
                "Tasa del IGV: 18%\n\n"
                "2. Fórmula\n"
                "Base imponible = total / 1.18\n"
                "IGV = total - base imponible\n\n"
                "3. Desarrollo\n"
                f"Base imponible = {formato_soles(total)} / 1.18 = {formato_soles(base)}\n"
                f"IGV = {formato_soles(total)} - {formato_soles(base)} = {formato_soles(igv)}\n\n"
                "4. Resultado\n"
                f"Base imponible: {formato_soles(base)}\n"
                f"IGV: {formato_soles(igv)}\n"
                f"Total: {formato_soles(total)}\n\n"
                "5. Conclusión\n"
                "Cuando el precio ya incluye IGV, no se multiplica por 18%; se divide entre 1.18 para hallar la base."
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
                "Caso práctico de IGV mensual\n\n"
                "1. Datos del caso\n"
                f"Ventas gravadas: {formato_soles(ventas)}\n"
                f"Compras gravadas: {formato_soles(compras)}\n\n"
                "2. Tema tributario identificado\n"
                "Se debe calcular el débito fiscal por ventas, el crédito fiscal por compras y luego comparar ambos.\n\n"
                "3. Fórmulas\n"
                "IGV de ventas = ventas x 18%\n"
                "IGV de compras = compras x 18%\n"
                "IGV por pagar = IGV de ventas - IGV de compras\n\n"
                "4. Desarrollo\n"
                f"IGV de ventas = {formato_soles(ventas)} x 18% = {formato_soles(igv_ventas)}\n"
                f"IGV de compras = {formato_soles(compras)} x 18% = {formato_soles(igv_compras)}\n"
                f"Diferencia = {formato_soles(igv_ventas)} - {formato_soles(igv_compras)} = {formato_soles(igv_pagar)}\n\n"
                "5. Resultado\n"
                f"{resultado}\n\n"
                "6. Recomendación\n"
                "Para usar el crédito fiscal, las compras deben estar vinculadas al negocio, sustentadas con comprobantes válidos y registradas correctamente."
            )

    if contiene(texto, ["nota de debito", "nota debito", "aumentar factura", "incrementar factura", "cobrar adicional", "aumentar monto", "recargo"]):
        if len(numeros) >= 2:
            original = numeros[0]
            adicional = numeros[1]
            nuevo_total = original + adicional

            return (
                "Caso práctico de nota de débito\n\n"
                "1. Datos del caso\n"
                f"Factura original: {formato_soles(original)}\n"
                f"Monto adicional: {formato_soles(adicional)}\n\n"
                "2. Tema tributario identificado\n"
                "Corresponde analizar si se debe aumentar el valor de una operación ya facturada.\n\n"
                "3. Comprobante que corresponde emitir\n"
                "Corresponde emitir una nota de débito.\n\n"
                "4. Fórmula\n"
                "Nuevo monto = factura original + monto adicional\n\n"
                "5. Desarrollo\n"
                f"Nuevo monto = {formato_soles(original)} + {formato_soles(adicional)} = {formato_soles(nuevo_total)}\n\n"
                "6. Resultado\n"
                f"Nuevo monto de la operación: {formato_soles(nuevo_total)}\n\n"
                "7. Conclusión\n"
                "La nota de débito se usa cuando aumenta el valor de una operación ya facturada, por ejemplo por intereses, penalidades, recargos o diferencias de precio."
            )

    if contiene(texto, [
        "nota de credito",
        "nota credito",
        "devolucion",
        "devolvio",
        "devuelve",
        "devolver",
        "mercaderia",
        "descuento",
        "rebaja",
        "anular parte",
        "disminuir factura",
    ]):
        if len(numeros) >= 2:
            original = numeros[0]
            descuento = numeros[1]
            nuevo_total = original - descuento

            if nuevo_total < 0:
                nuevo_total = 0

            return (
                "Caso práctico de nota de crédito\n\n"
                "1. Datos del caso\n"
                f"Factura original: {formato_soles(original)}\n"
                f"Monto devuelto, descontado o corregido: {formato_soles(descuento)}\n\n"
                "2. Tema tributario identificado\n"
                "El caso trata de una reducción del valor de una operación ya facturada.\n\n"
                "3. Comprobante que corresponde emitir\n"
                "Corresponde emitir una nota de crédito.\n\n"
                "4. Motivo\n"
                "La nota de crédito se emite cuando hay devolución de mercadería, descuento posterior, anulación parcial o corrección que reduce el monto de la operación.\n\n"
                "5. Fórmula\n"
                "Nuevo monto = factura original - monto devuelto o descontado\n\n"
                "6. Desarrollo\n"
                f"Nuevo monto = {formato_soles(original)} - {formato_soles(descuento)} = {formato_soles(nuevo_total)}\n\n"
                "7. Resultado\n"
                f"Nuevo monto de la operación: {formato_soles(nuevo_total)}\n\n"
                "8. Conclusión\n"
                "La empresa debe emitir una nota de crédito vinculada a la factura original para disminuir correctamente el valor de la operación."
            )

    if contiene(texto, ["detraccion", "detracciones"]):
        if len(numeros) >= 2:
            monto = numeros[0]
            porcentaje = numeros[1]

            detraccion = monto * (porcentaje / 100)
            saldo = monto - detraccion

            return (
                "Caso práctico de detracción\n\n"
                "1. Datos del caso\n"
                f"Monto de la operación: {formato_soles(monto)}\n"
                f"Porcentaje de detracción: {porcentaje}%\n\n"
                "2. Tema tributario identificado\n"
                "Se trata del Sistema de Pago de Obligaciones Tributarias, conocido como detracciones.\n\n"
                "3. Fórmula\n"
                "Detracción = monto de la operación x porcentaje\n"
                "Saldo a pagar al proveedor = monto - detracción\n\n"
                "4. Desarrollo\n"
                f"Detracción = {formato_soles(monto)} x {porcentaje}% = {formato_soles(detraccion)}\n"
                f"Saldo = {formato_soles(monto)} - {formato_soles(detraccion)} = {formato_soles(saldo)}\n\n"
                "5. Resultado\n"
                f"Monto a depositar en Banco de la Nación: {formato_soles(detraccion)}\n"
                f"Saldo a pagar directamente al proveedor: {formato_soles(saldo)}\n\n"
                "6. Recomendación\n"
                "Verifica en SUNAT si el bien o servicio está sujeto a detracción y cuál es el porcentaje vigente."
            )

    if contiene(texto, ["retencion", "retenciones"]):
        if len(numeros) >= 2:
            monto = numeros[0]
            porcentaje = numeros[1]

            retencion = monto * (porcentaje / 100)
            neto = monto - retencion

            return (
                "Caso práctico de retención\n\n"
                "1. Datos del caso\n"
                f"Monto de la operación: {formato_soles(monto)}\n"
                f"Porcentaje de retención: {porcentaje}%\n\n"
                "2. Fórmula\n"
                "Retención = monto x porcentaje\n"
                "Neto a pagar = monto - retención\n\n"
                "3. Desarrollo\n"
                f"Retención = {formato_soles(monto)} x {porcentaje}% = {formato_soles(retencion)}\n"
                f"Neto a pagar = {formato_soles(monto)} - {formato_soles(retencion)} = {formato_soles(neto)}\n\n"
                "4. Resultado\n"
                f"Monto retenido: {formato_soles(retencion)}\n"
                f"Neto a pagar al proveedor: {formato_soles(neto)}\n\n"
                "5. Recomendación\n"
                "Confirma si el comprador es agente de retención y si la operación está sujeta al régimen."
            )

    if contiene(texto, ["percepcion", "percepciones"]):
        if len(numeros) >= 2:
            monto = numeros[0]
            porcentaje = numeros[1]

            percepcion = monto * (porcentaje / 100)
            total = monto + percepcion

            return (
                "Caso práctico de percepción\n\n"
                "1. Datos del caso\n"
                f"Monto de la operación: {formato_soles(monto)}\n"
                f"Porcentaje de percepción: {porcentaje}%\n\n"
                "2. Fórmula\n"
                "Percepción = monto x porcentaje\n"
                "Total a pagar = monto + percepción\n\n"
                "3. Desarrollo\n"
                f"Percepción = {formato_soles(monto)} x {porcentaje}% = {formato_soles(percepcion)}\n"
                f"Total = {formato_soles(monto)} + {formato_soles(percepcion)} = {formato_soles(total)}\n\n"
                "4. Resultado\n"
                f"Monto de percepción: {formato_soles(percepcion)}\n"
                f"Total a pagar: {formato_soles(total)}\n\n"
                "5. Conclusión\n"
                "La percepción se cobra como un adicional al comprador y puede ser usada según las reglas tributarias aplicables."
            )

    if contiene(texto, ["fraccionar", "fraccionamiento", "cuotas", "dividir deuda"]):
        if len(numeros) >= 2:
            deuda = numeros[0]
            cuotas = int(numeros[1])

            if cuotas <= 0:
                return "El número de cuotas debe ser mayor a cero."

            cuota = deuda / cuotas

            return (
                "Caso práctico de fraccionamiento de deuda\n\n"
                "1. Datos del caso\n"
                f"Deuda tributaria: {formato_soles(deuda)}\n"
                f"Número de cuotas: {cuotas}\n\n"
                "2. Fórmula referencial\n"
                "Cuota aproximada = deuda / número de cuotas\n\n"
                "3. Desarrollo\n"
                f"Cuota aproximada = {formato_soles(deuda)} / {cuotas} = {formato_soles(cuota)}\n\n"
                "4. Resultado\n"
                f"Cuota mensual aproximada sin intereses: {formato_soles(cuota)}\n\n"
                "5. Recomendación\n"
                "Este cálculo es referencial. SUNAT puede aplicar intereses, requisitos y condiciones para aprobar el fraccionamiento."
            )

    if contiene(texto, ["descuento", "rebaja"]) and len(numeros) >= 2:
        monto = numeros[0]
        descuento = numeros[1]

        if descuento <= 100 and contiene(texto, ["%", "por ciento"]):
            descuento_monto = monto * (descuento / 100)
            total = monto - descuento_monto

            return (
                "Caso práctico de descuento porcentual\n\n"
                f"Monto inicial: {formato_soles(monto)}\n"
                f"Descuento: {descuento}%\n"
                f"Monto descontado: {formato_soles(descuento_monto)}\n"
                f"Total final: {formato_soles(total)}\n\n"
                "Conclusión: el descuento porcentual reduce el valor de la operación. Si ya existía comprobante emitido, podría corresponder nota de crédito."
            )

        total = monto - descuento

        if total < 0:
            total = 0

        return (
            "Caso práctico de descuento fijo\n\n"
            f"Monto inicial: {formato_soles(monto)}\n"
            f"Descuento: {formato_soles(descuento)}\n"
            f"Total final: {formato_soles(total)}\n\n"
            "Conclusión: si el descuento ocurre después de emitida la factura, normalmente corresponde emitir nota de crédito."
        )

    if contiene(texto, ["interes", "mora", "moratorio"]) and len(numeros) >= 3:
        deuda = numeros[0]
        tasa = numeros[1]
        periodos = numeros[2]

        interes = deuda * (tasa / 100) * periodos
        total = deuda + interes

        return (
            "Caso práctico de interés simple referencial\n\n"
            f"Deuda: {formato_soles(deuda)}\n"
            f"Tasa aplicada: {tasa}%\n"
            f"Periodos: {periodos}\n\n"
            "Fórmula:\n"
            "Interés = deuda x tasa x periodos\n\n"
            f"Interés aproximado: {formato_soles(interes)}\n"
            f"Total aproximado: {formato_soles(total)}\n\n"
            "Recomendación: para intereses tributarios reales, verifica la tasa vigente aplicable en SUNAT."
        )

    if contiene(texto, ["gasto deducible", "gastos deducibles", "gasto no deducible", "gastos no deducibles", "deducible"]):
        return (
            "Análisis de gastos deducibles y no deducibles\n\n"
            "1. Concepto\n"
            "Un gasto deducible es aquel que puede restarse para determinar la renta neta porque está vinculado a generar ingresos o mantener la fuente productora.\n\n"
            "2. Requisitos principales\n"
            "- Causalidad: relación con el negocio.\n"
            "- Fehaciencia: operación real.\n"
            "- Sustento: comprobante válido.\n"
            "- Razonabilidad: monto coherente.\n"
            "- Registro contable: anotado correctamente.\n"
            "- Bancarización: cuando corresponda.\n\n"
            "3. Ejemplos de gastos deducibles\n"
            "- Alquiler del local.\n"
            "- Sueldos del personal.\n"
            "- Servicios básicos del negocio.\n"
            "- Compras vinculadas al giro.\n"
            "- Publicidad del negocio.\n\n"
            "4. Ejemplos de gastos no deducibles\n"
            "- Gastos personales del dueño.\n"
            "- Multas tributarias.\n"
            "- Comprobantes falsos o inválidos.\n"
            "- Gastos sin sustento.\n"
            "- Gastos no vinculados al negocio.\n\n"
            "5. Conclusión\n"
            "Si un gasto no cumple requisitos tributarios, puede ser reparado por SUNAT y adicionarse para calcular la renta neta imponible."
        )

    if contiene(texto, ["cobranza coactiva", "ejecucion coactiva", "ejecución coactiva", "embargo"]):
        return (
            "Orientación sobre cobranza coactiva\n\n"
            "1. Concepto\n"
            "La cobranza coactiva es un procedimiento administrativo mediante el cual SUNAT u otra Administración Tributaria cobra deudas exigibles.\n\n"
            "2. Cómo funciona\n"
            "Normalmente se inicia con una Resolución de Ejecución Coactiva. Luego el Ejecutor Coactivo puede ordenar medidas como embargos para asegurar el pago.\n\n"
            "3. Qué se revisa\n"
            "- Si la deuda es exigible.\n"
            "- Si la notificación fue válida.\n"
            "- Si existe reclamación, apelación u otro recurso pendiente.\n"
            "- Si existe causal de suspensión o conclusión.\n\n"
            "4. Ejemplo\n"
            "Si una empresa no paga una Orden de Pago exigible, SUNAT puede iniciar cobranza coactiva y ordenar embargo en cuentas bancarias.\n\n"
            "5. Recomendación\n"
            "Revisa inmediatamente la notificación, el detalle de la deuda, los plazos y si corresponde presentar escrito de suspensión, reclamación, apelación o queja."
        )

    if len(numeros) >= 1 and contiene(texto, ["calcula", "calcular", "cuanto", "cuánto", "monto", "total"]):
        return (
            "Puedo ayudarte a resolver el caso, pero necesito que me indiques qué deseas calcular exactamente.\n\n"
            "Puedes escribirlo así:\n\n"
            "- Calcula IGV de S/ 1000 más IGV.\n"
            "- Factura de S/ 1180 con IGV incluido.\n"
            "- Ventas S/ 5000 y compras S/ 2000. Calcula IGV por pagar.\n"
            "- Detracción de S/ 1000 con 12%.\n"
            "- Retención de S/ 3000 con 3%.\n"
            "- Deuda S/ 1200 en 6 cuotas.\n"
            "- Factura S/ 1500 y devolución de mercadería S/ 300.\n"
            "- Impuesto a la Renta S/ 35000 y pagos a cuenta S/ 42000.\n"
            "- Ingresos S/ 500000, costos S/ 230000, gastos deducibles S/ 80000, gastos no deducibles S/ 15000, pagos a cuenta S/ 42000."
        )

    return None


# ============================================================
# DETECCIÓN DE TEMAS
# ============================================================

def obtener_aliases():
    aliases = []

    for tema, data in TEMAS.items():
        aliases.append(tema)
        aliases.extend(data["aliases"])

    aliases.extend(RESPUESTAS_DIRECTAS.keys())

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
        "deito": "nota de debito",
        "notadebito": "nota de debito",
        "notacredito": "nota de credito",
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
        "devolvio": "devolucion",
        "devuelve": "devolucion",
        "devolver": "devolucion",
        "mercadería": "mercaderia",
        "coactiva": "cobranza coactiva",
        "embargaron": "embargo",
        "sunat": "sunat",
    }

    palabras = texto_limpio.split()
    texto_corregido = " ".join([correcciones.get(p, p) for p in palabras])

    aliases = obtener_aliases()
    match = difflib.get_close_matches(texto_corregido, aliases, n=1, cutoff=0.84)

    if match:
        return match[0]

    return texto_corregido


def detectar_tema(mensaje):
    texto = corregir_texto(mensaje)

    mejor_tema = None
    mejor_puntaje = 0

    for tema, data in TEMAS.items():
        puntaje = 0

        if tema in texto:
            puntaje += 25

        for alias in data["aliases"]:
            alias_limpio = limpiar_texto(alias)

            if alias_limpio == texto:
                puntaje += 35

            elif alias_limpio in texto:
                puntaje += len(alias_limpio.split()) * 8

            else:
                similitud = difflib.SequenceMatcher(None, texto, alias_limpio).ratio()

                if similitud > 0.84:
                    puntaje += int(similitud * 14)

        if puntaje > mejor_puntaje:
            mejor_puntaje = puntaje
            mejor_tema = tema

    if mejor_puntaje >= 6:
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

    return "general"


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

def responder_tema(tema, intencion="general"):
    if not tema or tema not in TEMAS:
        return None

    data = TEMAS[tema]

    if tema == "igv":
        return (
            "El IGV es el Impuesto General a las Ventas. En Perú grava principalmente la venta de bienes, "
            "la prestación de servicios, los contratos de construcción, la primera venta de inmuebles realizada "
            "por constructores y las importaciones.\n\n"
            "Su tasa general actual es 18%, compuesta por 16% de IGV y 2% de Impuesto de Promoción Municipal.\n\n"
            "Ejemplo: si una venta es de S/ 1,000 sin IGV, el impuesto será S/ 180 y el total a pagar será S/ 1,180."
        )

    if intencion == "que_es":
        return (
            f"{data['concepto']}\n\n"
            f"{data['explicacion']}\n\n"
            f"Ejemplo: {data['ejemplo']}"
        )

    if intencion == "para_que_sirve":
        return (
            f"{data['funcion']}\n\n"
            f"{data['explicacion']}"
        )

    if intencion == "como_funciona":
        return (
            f"{data['explicacion']}\n\n"
            f"En la práctica: {data['funcion']}\n\n"
            f"Ejemplo: {data['ejemplo']}"
        )

    if intencion == "ejemplo":
        return (
            f"Ejemplo: {data['ejemplo']}\n\n"
            f"Esto se relaciona con: {data['concepto']}"
        )

    return (
        f"{data['concepto']}\n\n"
        f"{data['explicacion']}\n\n"
        f"Ejemplo: {data['ejemplo']}\n\n"
        f"Recomendación: {data['recomendacion']}"
    )

def detectar_pregunta_especifica(mensaje):
    texto = limpiar_texto(mensaje)

    reglas = [
        {
            "palabras": ["igv", "tasa"],
            "respuesta": responder_tema("igv")
        },
        {
            "palabras": ["credito", "fiscal"],
            "respuesta": responder_tema("credito fiscal")
        },
        {
            "palabras": ["debito", "fiscal"],
            "respuesta": responder_tema("debito fiscal")
        },
        {
            "palabras": ["exonerado", "inafecto"],
            "respuesta": responder_tema("exonerado e inafecto")
        },
        {
            "palabras": ["obligacion", "tributaria"],
            "respuesta": responder_tema("obligacion tributaria")
        },
        {
            "palabras": ["cobranza", "coactiva"],
            "respuesta": responder_tema("cobranza coactiva")
        },
        {
            "palabras": ["ejecutor", "coactivo"],
            "respuesta": responder_tema("ejecutor coactivo")
        },
        {
            "palabras": ["reclamacion"],
            "respuesta": responder_tema("reclamacion")
        },
        {
            "palabras": ["apelacion"],
            "respuesta": responder_tema("apelacion")
        },
        {
            "palabras": ["tribunal", "fiscal"],
            "respuesta": responder_tema("apelacion")
        },
        {
            "palabras": ["multa"],
            "respuesta": responder_tema("multa tributaria")
        },
        {
            "palabras": ["infraccion"],
            "respuesta": responder_tema("infraccion tributaria")
        },
        {
            "palabras": ["nota", "credito"],
            "respuesta": responder_tema("nota de credito")
        },
        {
            "palabras": ["nota", "debito"],
            "respuesta": responder_tema("nota de debito")
        },
        {
            "palabras": ["renta", "tercera"],
            "respuesta": responder_tema("renta de tercera categoria")
        },
        {
            "palabras": ["renta", "cuarta"],
            "respuesta": responder_tema("renta de cuarta categoria")
        },
        {
            "palabras": ["renta", "quinta"],
            "respuesta": responder_tema("renta de quinta categoria")
        },
        {
            "palabras": ["nuevo", "rus"],
            "respuesta": responder_tema("nuevo rus")
        },
        {
            "palabras": ["rmt"],
            "respuesta": responder_tema("rmt")
        },
        {
            "palabras": ["rer"],
            "respuesta": responder_tema("rer")
        },
        {
            "palabras": ["regimen", "general"],
            "respuesta": responder_tema("regimen general")
        },
    ]

    for regla in reglas:
        if all(palabra in texto for palabra in regla["palabras"]):
            return regla["respuesta"]

    return None


# ============================================================
# BÚSQUEDA LOCAL
# ============================================================

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


# ============================================================
# GEMINI
# ============================================================

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

def responder_con_gemini(mensaje, historial=None, respuesta_local=None):
    if client is None or types is None:
        return None

    contexto = construir_contexto(historial or [])

    prompt = f"""
Eres TribuTax, un asistente virtual especializado en tributación peruana.

Responde SOLO lo que el usuario pregunta.
No saludes en cada respuesta.
No repitas listas fijas como "concepto, explicación, ejemplo, recomendación" salvo que el usuario pida una explicación amplia.
No digas "soy TribuTax" en cada respuesta.
Responde de forma clara, directa y concreta.
Si la pregunta es simple, responde en 1 a 3 párrafos.
Si es un caso práctico con números, resuelve paso a paso.
Si el usuario pregunta algo fuera de tributación, indica amablemente que solo atiendes consultas tributarias.
Si se requieren montos, tasas, límites o cronogramas vigentes, recomienda verificar SUNAT o la norma vigente.
No ayudes a evadir impuestos, ocultar ingresos, falsificar comprobantes ni engañar a SUNAT.

Temas que puedes responder:
IGV, Impuesto a la Renta, SUNAT, RUC, Clave SOL, comprobantes de pago, factura, boleta,
recibo por honorarios, nota de crédito, nota de débito, detracciones, retenciones, percepciones,
regímenes tributarios, Nuevo RUS, RER, RMT, Régimen General, libros contables, PLE, SIRE,
declaraciones mensuales, multas, gradualidad, deuda tributaria, cobranza coactiva, reclamación,
apelación, Tribunal Fiscal, obligación tributaria, Código Tributario, infracciones, sanciones,
UIT, impuesto predial, alcabala, arbitrios, aduanas, importación y exportación.

Historial reciente:
{contexto}

Pregunta del usuario:
{mensaje}

Respuesta:
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
            print("Gemini respondió correctamente.")
            return response.text.strip()

        return None

    except Exception as e:
        print("ERROR GEMINI:", str(e))
        return None
        
# ============================================================
# FALLBACK
# ============================================================

def respuesta_fallback():
    return (
        "Soy TribuTax, tu asistente virtual tributario. Puedo ayudarte con teoría, orientación y casos prácticos de tributación peruana.\n\n"
        "Puedo responder sobre:\n\n"
        "1. IGV\n"
        "Cálculo del IGV, IGV incluido, crédito fiscal, débito fiscal, operaciones gravadas, exoneradas e inafectas.\n\n"
        "2. Impuesto a la Renta\n"
        "Rentas de primera, segunda, tercera, cuarta y quinta categoría, gastos deducibles, gastos no deducibles, pagos a cuenta, declaración anual, renta neta imponible y saldo a favor o por pagar.\n\n"
        "3. Comprobantes de pago\n"
        "Factura, boleta, recibo por honorarios, nota de crédito, nota de débito, guía de remisión, factura electrónica, XML, CDR, OSE y PSE.\n\n"
        "4. Regímenes tributarios\n"
        "Nuevo RUS, RER, Régimen MYPE Tributario y Régimen General.\n\n"
        "5. SUNAT y Código Tributario\n"
        "RUC, Clave SOL, domicilio fiscal, obligación tributaria, acreedor, deudor, contribuyente, responsable, notificaciones, fiscalización y procedimientos tributarios.\n\n"
        "6. Cobranza coactiva\n"
        "Deuda exigible, Resolución de Ejecución Coactiva, Ejecutor Coactivo, embargos, suspensión y conclusión del procedimiento.\n\n"
        "7. Infracciones y sanciones\n"
        "Multas, gradualidad, tipicidad, legalidad, proporcionalidad, no concurrencia de infracciones y regularización.\n\n"
        "8. Libros contables\n"
        "Registro de Ventas, Registro de Compras, Libro Diario, Libro Mayor, PLE, SIRE, RVIE y RCE.\n\n"
        "9. Detracciones, retenciones y percepciones\n"
        "Cálculos, porcentajes, aplicación, comprobantes y efectos en el pago.\n\n"
        "10. Casos prácticos\n"
        "Puedes escribirme casos como:\n"
        "- Ventas S/ 50,000 y compras S/ 20,000. Calcular IGV por pagar.\n"
        "- Factura S/ 1,500 y devolución de mercadería S/ 300.\n"
        "- Impuesto a la Renta S/ 35,000 y pagos a cuenta S/ 42,000.\n"
        "- Ingresos S/ 500,000, costos S/ 230,000, gastos deducibles S/ 80,000, gastos no deducibles S/ 15,000 y pagos a cuenta S/ 42,000.\n\n"
        "Escríbeme tu consulta con el mayor detalle posible y te ayudo a resolverla paso a paso."
    )

def es_consulta_tributaria(mensaje):
    texto = limpiar_texto(mensaje)

    palabras_tributarias = [
        "tributo", "tributario", "tributaria", "impuesto", "igv", "renta",
        "sunat", "ruc", "clave sol", "factura", "boleta", "recibo",
        "honorarios", "nota de credito", "nota de debito", "detraccion",
        "retencion", "percepcion", "declaracion", "declarar", "multa",
        "deuda", "fraccionamiento", "cobranza", "coactiva", "embargo",
        "fiscalizacion", "requerimiento", "esquela", "carta inductiva",
        "libros", "registro de ventas", "registro de compras", "ple", "sire",
        "nuevo rus", "rer", "rmt", "regimen general", "uit", "predial",
        "alcabala", "arbitrios", "aduanas", "importacion", "exportacion",
        "drawback", "credito fiscal", "debito fiscal", "obligacion tributaria",
        "codigo tributario", "reclamacion", "apelacion", "tribunal fiscal",
        "sancion", "infraccion", "gasto deducible", "gasto no deducible",
        "pagos a cuenta", "renta neta", "base imponible"
    ]

    if any(palabra in texto for palabra in palabras_tributarias):
        return True

    if extraer_numeros(mensaje) and any(
        palabra in texto
        for palabra in ["ventas", "compras", "ingresos", "costos", "gastos", "cuotas", "saldo"]
    ):
        return True

    return False
# ============================================================
# FUNCIÓN PRINCIPAL QUE USA main.py
# ============================================================

def responder_chatbot(mensaje, historial=None):
    if historial is None:
        historial = []

    try:
        mensaje = mensaje.strip()

        if mensaje == "":
            return "Escribe tu consulta tributaria o pega tu caso práctico para poder ayudarte."

        texto = limpiar_texto(mensaje)

        if detectar_pregunta_prohibida(mensaje):
            return respuesta_segura()

        if texto in RESPUESTAS_DIRECTAS:
            return RESPUESTAS_DIRECTAS[texto]

        if not es_consulta_tributaria(mensaje):
            return (
                "Tu consulta no parece estar relacionada con tributación.\n\n"
                "Puedo ayudarte con IGV, SUNAT, RUC, comprobantes de pago, Impuesto a la Renta, "
                "regímenes tributarios, detracciones, retenciones, libros contables, multas, deudas, "
                "cobranza coactiva y casos prácticos tributarios."
            )

        # Primero consulta a Gemini
        respuesta_gemini = responder_con_gemini(
            mensaje=mensaje,
            historial=historial,
            respuesta_local=None
        )

        if respuesta_gemini:
            return respuesta_gemini

        # Si Gemini falla por cuota, error o API, recién responde local
        respuesta_local = buscar_respuesta_local(mensaje, historial)

        if respuesta_local:
            return respuesta_local

        return respuesta_fallback()

    except Exception as e:
        print("ERROR EN responder_chatbot:", str(e))
        return respuesta_fallback()