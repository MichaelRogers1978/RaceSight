async function sendMessage() {
    const input = document.getElementById("input").value;
    const output = document.getElementById("output");

    output.textContent += `\n\nYou: ${input}\n`;

    const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input })
    });

    const data = await response.json();

    output.textContent += `RaceSight: ${data.response}\n`;
    output.scrollTop = output.scrollHeight;
}
