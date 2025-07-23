# app.py (Prompt-based job application chatbot)

from flask import Flask, request, jsonify, render_template
import os, sqlite3, json, requests
from datetime import datetime
from extract_utils import extract_text_from_pdf, extract_text_from_image, extract_details

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Store latest user interaction info
user_context = {"email": "", "date": "", "time": ""}
OPENROUTER_API_KEY = "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"  # Replace with actual key

# ---------- Utilities ----------
def save_chat(sender, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT, message TEXT, timestamp TEXT
            )""")
        cursor.execute("INSERT INTO chat_history (sender, message, timestamp) VALUES (?, ?, ?)",
                       (sender, message, timestamp))
        conn.commit()


def detect_prompt_reply(message):
    prompt = f"""
You are a smart job application chatbot.
Respond casually and help the user with:
- Applying for a job
- Uploading a resume (PDF or image)
- Scheduling or canceling an interview
- Friendly chitchat (hello, how are you, thanks, etc.)

Also, ask the next question when needed (e.g., after resume, ask for date/time).

User: {message}
Chatbot:
"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost"
    }
    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        result = res.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print("OpenRouter Error:", e)
        return "⚠️ Sorry, I couldn't process that."

# ---------- Routes ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get_response", methods=["POST"])
def get_response():
    msg = request.get_json().get("message", "")
    save_chat("user", msg)

    if msg.lower() in ["no", "nope"] and user_context["email"]:
        reply = f"✅ Your interview is confirmed for {user_context['email']} on {user_context['date']} at {user_context['time']}. All the best! 🎯"
    else:
        reply = detect_prompt_reply(msg)

    save_chat("bot", reply)
    return jsonify({"response": reply})

@app.route("/upload_resume", methods=["POST"])
def upload_resume():
    file = request.files.get("file")
    if not file:
        return jsonify({"response": "⚠️ No file uploaded."})
    filename = file.filename
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(path)
    ext = filename.split(".")[-1].lower()
    text = extract_text_from_pdf(path) if ext == "pdf" else extract_text_from_image(path)
    details = extract_details(text)

    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, email TEXT, phone TEXT, skills TEXT, resume_file TEXT
            )""")
        cursor.execute("INSERT INTO applications (name, email, phone, skills, resume_file) VALUES (?, ?, ?, ?, ?)",
                       (details["name"], details["email"], details["phone"], details["skills"], filename))
        conn.commit()

    return jsonify({"response": f"✅ Resume uploaded for {details['name']} ({details['email']}). Please schedule your interview."})

@app.route("/schedule_interview", methods=["POST"])
def schedule():
    data = request.get_json()
    date, time, email = data.get("date"), data.get("time"), data.get("email")
    if not date or not time or not email:
        return jsonify({"response": "⚠️ Please provide date, time, and email."})

    user_context.update({"date": date, "time": time, "email": email})

    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interview_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT, time TEXT, email TEXT
            )""")
        cursor.execute("SELECT * FROM interview_slots WHERE date = ? AND time = ?", (date, time))
        if cursor.fetchone():
            return jsonify({"response": "❌ Slot already booked. Try another."})
        cursor.execute("INSERT INTO interview_slots (date, time, email) VALUES (?, ?, ?)", (date, time, email))
        conn.commit()

    return jsonify({"response": f"✅ Interview scheduled on {date} at {time}. Do you want to cancel this appointment?"})

@app.route("/cancel_interview", methods=["POST"])
def cancel():
    email = user_context["email"]
    if not email:
        return jsonify({"response": "⚠️ No scheduled interview found."})

    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM interview_slots WHERE email = ?", (email,))
        conn.commit()

    user_context.update({"email": "", "date": "", "time": ""})
    return jsonify({"response": "🗑️ Interview appointment cancelled."})

@app.route("/admin/chat_history")
def history():
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT sender, message, timestamp FROM chat_history ORDER BY id ASC")
        rows = cursor.fetchall()
    html = "<h2>Chat History</h2><table border='1'><tr><th>Sender</th><th>Message</th><th>Time</th></tr>"
    for s, m, t in rows:
        html += f"<tr><td>{s}</td><td>{m}</td><td>{t}</td></tr>"
    html += "</table>"
    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
