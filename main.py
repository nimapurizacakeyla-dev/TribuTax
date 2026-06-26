from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from chatbot import responder_chatbot

app = FastAPI(title="TribuTax")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def inicio(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()

        mensaje_usuario = data.get("mensaje", "")
        historial = data.get("historial", [])

        if not mensaje_usuario.strip():
            return JSONResponse(content={
                "respuesta": "Escribe una consulta para poder ayudarte."
            })

        respuesta = responder_chatbot(
            mensaje=mensaje_usuario,
            historial=historial
        )

        return JSONResponse(content={
            "respuesta": respuesta
        })

    except Exception as e:
        print("ERROR EN /chat:", str(e))

        return JSONResponse(content={
            "respuesta": "Soy TribuTax. En este momento puedo ayudarte con IGV, SUNAT, RUC, comprobantes, renta, regímenes tributarios, detracciones, retenciones, libros contables y Clave SOL."
        })