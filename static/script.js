const chatPanel = document.getElementById("chat-panel");
const chatBox = document.getElementById("chat-box");
const input = document.getElementById("user-input");
const floatingChat = document.getElementById("floating-chat");
const clickText = document.getElementById("click-text");

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
    chatBox.innerHTML = `
        <div class="bot-message">
    ¡Hola! Soy TribuTax. Escribe tu consulta.
        </div>
    `;

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
    const mensaje = document.createElement("div");
    mensaje.className = "user-message";
    mensaje.textContent = texto;
    chatBox.appendChild(mensaje);
}

function crearMensajeBot(texto) {
    const mensaje = document.createElement("div");
    mensaje.className = "bot-message";
    mensaje.textContent = texto;
    chatBox.appendChild(mensaje);
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
            body: JSON.stringify({ mensaje: mensaje })
        });

        const data = await response.json();

        quitarPuntosEscribiendo();
        crearMensajeBot(data.respuesta);

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
    reiniciarChat();
}

input.addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        enviarMensaje();
    }
});