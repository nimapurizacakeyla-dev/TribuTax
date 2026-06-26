const chatPanel = document.getElementById("chat-panel");
const chatBox = document.getElementById("chat-box");
const input = document.getElementById("user-input");
const floatingChat = document.getElementById("floating-chat");
const clickText = document.getElementById("click-text");

// Historial temporal de la conversación
let historialConversacion = [];

// Borra historial al recargar
localStorage.clear();
sessionStorage.clear();

document.addEventListener("DOMContentLoaded", function () {
    reiniciarChat();
});

window.addEventListener("beforeunload", function () {
    localStorage.clear();
    sessionStorage.clear();
});

function reiniciarChat() {
    historialConversacion = [];

    chatBox.innerHTML = "";
    crearMensajeBot("¡Hola! Soy TribuTax. Escribe tu consulta.");

    input.value = "";

    chatPanel.classList.remove("active");
    floatingChat.classList.remove("oculto");

    if (clickText) {
        clickText.classList.remove("oculto");
    }
}

function abrirChat() {
    chatPanel.classList.add("active");
    floatingChat.classList.add("oculto");

    if (clickText) {
        clickText.classList.add("oculto");
    }
}

function cerrarChat() {
    chatPanel.classList.remove("active");
    floatingChat.classList.remove("oculto");

    if (clickText) {
        clickText.classList.remove("oculto");
    }
}

function crearMensajeUsuario(texto) {
    const fila = document.createElement("div");
    fila.className = "message-row user-row";

    const mensaje = document.createElement("div");
    mensaje.className = "user-message";
    mensaje.textContent = texto;

    const avatar = document.createElement("img");
    avatar.className = "message-avatar";
    avatar.src = "/static/uploads/persona.jpg";
    avatar.alt = "Usuario";

    fila.appendChild(mensaje);
    fila.appendChild(avatar);

    chatBox.appendChild(fila);
}

function crearMensajeBot(texto) {
    const fila = document.createElement("div");
    fila.className = "message-row bot-row";

    const avatar = document.createElement("img");
    avatar.className = "message-avatar";
    avatar.src = "/static/uploads/robot.jpg";
    avatar.alt = "TribuTax";

    const mensaje = document.createElement("div");
    mensaje.className = "bot-message";
    mensaje.textContent = texto;

    fila.appendChild(avatar);
    fila.appendChild(mensaje);

    chatBox.appendChild(fila);
}

function mostrarPuntosEscribiendo() {
    const burbuja = document.createElement("div");
    burbuja.className = "typing-bubble";
    burbuja.id = "typing-indicator";

    burbuja.innerHTML = `
        <span></span>
        <span></span>
        <span></span>
    `;

    chatBox.appendChild(burbuja);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function quitarPuntosEscribiendo() {
    const burbuja = document.getElementById("typing-indicator");

    if (burbuja) {
        burbuja.remove();
    }
}

async function enviarMensaje() {
    const mensaje = input.value.trim();

    if (mensaje === "") {
        return;
    }

    crearMensajeUsuario(mensaje);
    input.value = "";

    mostrarPuntosEscribiendo();

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                mensaje: mensaje,
                historial: historialConversacion.slice(-8)
            })
        });

        const data = await response.json();

        quitarPuntosEscribiendo();

        const respuestaBot = data.respuesta || "No pude generar una respuesta en este momento.";
        crearMensajeBot(respuestaBot);

        // Guardar conversación para que entienda preguntas de seguimiento
        historialConversacion.push({
            usuario: mensaje,
            bot: respuestaBot
        });

        // Evita que el historial crezca demasiado
        if (historialConversacion.length > 10) {
            historialConversacion = historialConversacion.slice(-10);
        }

        chatBox.scrollTop = chatBox.scrollHeight;

    } catch (error) {
        quitarPuntosEscribiendo();

        crearMensajeBot("Error: verifica que el servidor esté activo.");

        chatBox.scrollTop = chatBox.scrollHeight;
    }
}

function usarPregunta(pregunta) {
    abrirChat();
    input.value = pregunta;
    enviarMensaje();
}

function limpiarHistorial() {
    historialConversacion = [];
    reiniciarChat();
}

input.addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        enviarMensaje();
    }
});