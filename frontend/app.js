function saveKey() {
    const key = document.getElementById("apiKey").value;
    if (!key) {
        alert("Ingresa una API Key");
        return;
    }
    localStorage.setItem("gemini_api_key", key);
    window.location.href = "chat.html";
}

async function sendMessage() {
    const apiKey = localStorage.getItem("gemini_api_key");
    const message = document.getElementById("message").value;

    if (!message) return;

    addMessage("Tú", message, "user");
    document.getElementById("message").value = "";

    const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            api_key: apiKey,
            message: message
        })
    });

    const data = await response.json();

    if (data.reply) {
        addMessage("Gemini", data.reply, "bot");
    } else {
        addMessage("Error", "No se pudo conectar con la API", "bot");
    }
}

function addMessage(sender, text, cssClass) {
    const chatBox = document.getElementById("chatBox");
    const div = document.createElement("div");
    div.className = cssClass;
    div.innerHTML = `<strong>${sender}:</strong> ${text}`;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}
