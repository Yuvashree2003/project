function addMessage(message, from = "user") {
    const chatbox = document.getElementById("chatbox");
    const msgDiv = document.createElement("div");
    msgDiv.className = from;
    msgDiv.innerText = message;
    chatbox.appendChild(msgDiv);
    chatbox.scrollTop = chatbox.scrollHeight;
}

function sendMessage() {
    const input = document.getElementById("userInput");
    const message = input.value.trim();
    if (!message) return;
    addMessage(message, "user");
    input.value = "";

    fetch("/get_response", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message })
    })
    .then(res => res.json())
    .then(data => handleBotResponse(data.response))
    .catch(err => {
        console.error("Error:", err);
        addMessage("⚠️ Failed to get response from server.", "bot");
    });
}

function handleBotResponse(responseText) {
    addMessage(responseText, "bot");

    const lower = responseText.toLowerCase();
    if (lower.includes("upload")) document.getElementById("uploadBox").style.display = "block";
    if (lower.includes("schedule")) document.getElementById("calendarBox").style.display = "block";
    if (lower.includes("cancel")) cancelAppointment();
}

function uploadResume() {
    const fileInput = document.getElementById("resumeInput");
    const file = fileInput.files[0];
    if (!file) return alert("Please select a file.");

    const formData = new FormData();
    formData.append("file", file);

    fetch("/upload_resume", {
        method: "POST",
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        addMessage(data.response, "bot");
        document.getElementById("uploadBox").style.display = "none";
    })
    .catch(err => {
        console.error("Upload error:", err);
        addMessage("⚠️ Failed to upload resume.", "bot");
    });
}

function submitInterviewDate() {
    const date = document.getElementById("interviewDate").value;
    const time = document.getElementById("interviewTime").value;
    const email = document.getElementById("interviewEmail").value;

    if (!date || !time || !email) {
        return addMessage("⚠️ Please fill all fields.", "bot");
    }

    fetch("/schedule_interview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ date, time, email })
    })
    .then(res => res.json())
    .then(data => {
        addMessage(data.response, "bot");
        if (!data.response.includes("already booked")) {
            document.getElementById("calendarBox").style.display = "none";
        }
    })
    .catch(err => {
        console.error("Error:", err);
        addMessage("⚠️ Failed to schedule interview.", "bot");
    });
}

function cancelAppointment() {
    fetch("/cancel_interview", {
        method: "POST"
    })
    .then(res => res.json())
    .then(data => {
        addMessage(data.response, "bot");
    })
    .catch(err => {
        console.error("Cancel error:", err);
        addMessage("⚠️ Failed to cancel appointment.", "bot");
    });
}

function startMic() {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();

    recognition.lang = 'en-IN';  // Try 'en-US' if this fails
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    console.log("🎤 Mic started");

    recognition.onstart = () => {
        console.log("🎙️ Voice recognition started. Speak now.");
    };

    recognition.onspeechend = () => {
        console.log("🛑 Speech ended.");
        recognition.stop();
    };

    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        console.log("📝 Recognized text:", transcript);
        document.getElementById("userInput").value = transcript;
        sendMessage();
    };

    recognition.onerror = function(event) {
        console.error("🚫 Speech recognition error:", event.error);
        alert("Speech recognition error: " + event.error);
    };

    recognition.start();
}


// Attach event listeners
window.onload = () => {
    document.getElementById("sendBtn").onclick = sendMessage;
    document.getElementById("micBtn").onclick = startMic;
    document.getElementById("uploadBtn").onclick = uploadResume;
    document.getElementById("submitBtn").onclick = submitInterviewDate;
};
