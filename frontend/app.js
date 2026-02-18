async function sendMessage() {
    const messageInput = document.getElementById("message");
    const chatBox = document.getElementById("chatBox");

    const apiKey = localStorage.getItem("gemini_api_key");
    const message = messageInput.value;

    chatBox.innerHTML += `<div><b>Tú:</b> ${message}</div>`;

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
        chatBox.innerHTML += `<div><b>IA:</b> ${data.reply}</div>`;
    } else {
        chatBox.innerHTML += `<div style="color:red;">Error: ${data.error}</div>`;
    }

    messageInput.value = "";
}
