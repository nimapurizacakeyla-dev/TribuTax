from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from chatbot import responder_chatbot

app = FastAPI(title="TribuTax")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def inicio(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    mensaje_usuario = data.get("mensaje", "")

    respuesta = responder_chatbot(mensaje_usuario)

    return {"respuesta": respuesta}