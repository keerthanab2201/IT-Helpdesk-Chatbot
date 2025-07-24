from flask import Flask, render_template, request, redirect, url_for, g, flash
from dotenv import load_dotenv
import os
import requests
import markdown
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
import uuid
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup  
import urllib.request
import urllib.parse



# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Environment Variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "testbot")

# Embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# SQLite config
DATABASE = 'chat_logs.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_message TEXT,
            bot_response TEXT
        )''')
        db.commit()

init_db()

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
try:
    if PINECONE_INDEX_NAME not in pc.list_indexes().names():
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        print(f"Created new Pinecone index: {PINECONE_INDEX_NAME}")
    else:
        print(f"Using existing Pinecone index: {PINECONE_INDEX_NAME}")
except Exception as e:
    print(f"Error initializing Pinecone: {e}")

# Home route
@app.route("/")
def home():
    return render_template("chat.html")

# Admin Panel
@app.route("/admin")
def admin():
    return render_template("admin.html")

# Chat response
@app.route("/get", methods=["POST"])
def get_bot_response():
    try:
        user_message = request.form.get("msg")
        if not user_message.strip():
            return "Please enter a valid message."

        embedding = embedding_model.encode(user_message).tolist()
        index = pc.Index(PINECONE_INDEX_NAME)
        query_response = index.query(vector=embedding, top_k=3, include_metadata=True)

        context = "\n".join([m.metadata.get("text", "") for m in query_response.matches])

        payload = {
            "model": "qwen/qwen3-30b-a3b:free",
            "messages": [
                {"role": "system", "content": f"You are an IT helpdesk assistant. Use this context if relevant:\n{context}"},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://github.com/keerthanab2201/IT-Helpdesk-Chatbot",
            "X-Title": "IT Helpdesk Chatbot",
            "Content-Type": "application/json"
        }

        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        html_response = markdown.markdown(content)

        # Store chat in logs
        db = get_db()
        db.execute("INSERT INTO chat_logs (timestamp, user_message, bot_response) VALUES (?, ?, ?)",
                   (datetime.utcnow().isoformat(), user_message, content))
        db.commit()

        return html_response

    except Exception as e:
        print("Chat error:", e)
        return "Sorry, I encountered an error."

# Upload documents
ALLOWED_EXTENSIONS = {"pdf"}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload_document", methods=["POST"])
def upload_document():
    print("Received upload_document request...")

    if 'pdf_file' not in request.files:
        print("No file part found.")
        return "No file part in the request.", 400

    file = request.files['pdf_file']
    print("Uploaded file:", file.filename)

    if file.filename == '':
        print("No selected file.")
        return "No selected file.", 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join("data", filename)
        print("Saving file to:", filepath)
        file.save(filepath)

        try:
            reader = PdfReader(filepath)
            full_text = ""

            # Extract text safely
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                except Exception as e:
                    print(f"Error reading page {page_num}: {e}")

            if not full_text.strip():
                print("No readable text found in the PDF.")
                return "Uploaded PDF has no readable text.", 400

            # Chunk and index into Pinecone
            chunks = [full_text[i:i+500] for i in range(0, len(full_text), 500)]
            index = pc.Index(PINECONE_INDEX_NAME)

            for chunk in chunks:
                try:
                    embedding = embedding_model.encode(chunk).tolist()
                    index.upsert(vectors=[{
                        "id": str(uuid.uuid4()),
                        "values": embedding,
                        "metadata": {"text": chunk}
                    }])
                except Exception as e:
                    print(f"Error embedding chunk: {e}")

            print("PDF processed and indexed successfully.")
            return redirect(url_for("admin"))

        except Exception as e:
            print("PDF processing error:", e)
            return f"Error processing file: {e}", 500

    print("Invalid file type.")
    return "Invalid file type. Please upload a PDF.", 400


# Add URLs
@app.route("/add_url", methods=["POST"])
def add_url():
    try:
        url = request.form.get("url")
        if not url:
            return redirect(url_for("admin"))

        print(f"Received URL to add: {url}")

        # Fetch page content
        with urllib.request.urlopen(url) as response:
            html_content = response.read()

        # Extract text using BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)

        # Chunk text
        chunks = [text[i:i + 500] for i in range(0, len(text), 500)]

        # Embed and index
        index = pc.Index(PINECONE_INDEX_NAME)
        for chunk in chunks:
            embedding = get_embedding(chunk)
            if embedding:
                index.upsert(vectors=[{
                    "id": str(uuid.uuid4()),
                    "values": embedding,
                    "metadata": {"text": chunk}
                }])

        print("URL content successfully embedded and indexed.")
        return redirect(url_for("admin"))

    except Exception as e:
        print("Error processing URL:", e)
        return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)