from flask import Flask, render_template, request, redirect, url_for, g, flash, jsonify
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
import secrets

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
        
        # Chat logs table - Create if not exists
        cursor.execute('''CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_message TEXT,
            bot_response TEXT
        )''')
        
        # Add new columns if they don't exist
        try:
            cursor.execute('ALTER TABLE chat_logs ADD COLUMN session_id TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute('ALTER TABLE chat_logs ADD COLUMN response_time REAL')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # API keys table
        cursor.execute('''CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_name TEXT,
            api_key TEXT,
            created_at TEXT,
            status TEXT DEFAULT 'active'
        )''')
        
        # Knowledge base table
        cursor.execute('''CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            name TEXT,
            content TEXT,
            added_at TEXT,
            status TEXT DEFAULT 'processing'
        )''')
        
        # Sessions table
        cursor.execute('''CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            started_at TEXT,
            last_activity TEXT,
            message_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active'
        )''')
        
        db.commit()

init_db()

# Function to get active API key from database
def get_active_api_key():
    """Get an active API key from the database, fallback to env variable"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT api_key FROM api_keys WHERE status = 'active' LIMIT 1")
        result = cursor.fetchone()
        if result:
            return result[0]
    except Exception as e:
        print(f"Error getting API key from database: {e}")
    
    # Fallback to environment variable
    return OPENROUTER_API_KEY
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

# API to get dashboard stats
@app.route("/api/stats")
def get_stats():
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Total chats
        cursor.execute("SELECT COUNT(*) FROM chat_logs")
        total_chats = cursor.fetchone()[0]
        
        # Active sessions
        cursor.execute("SELECT COUNT(*) FROM sessions WHERE status = 'active'")
        active_sessions = cursor.fetchone()[0]
        
        # Knowledge items
        cursor.execute("SELECT COUNT(*) FROM knowledge_base")
        knowledge_items = cursor.fetchone()[0]
        
        # API keys
        cursor.execute("SELECT COUNT(*) FROM api_keys WHERE status = 'active'")
        api_keys = cursor.fetchone()[0]
        
        return jsonify({
            "total_chats": total_chats,
            "active_sessions": active_sessions,
            "knowledge_items": knowledge_items,
            "api_keys": api_keys
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API to get chat logs
@app.route("/api/chat-logs")
def get_chat_logs():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT timestamp, session_id, user_message, bot_response, response_time 
            FROM chat_logs 
            ORDER BY timestamp DESC 
            LIMIT 50
        """)
        logs = cursor.fetchall()
        
        return jsonify([{
            "timestamp": log[0],
            "session_id": log[1],
            "user_message": log[2][:100] + "..." if len(log[2]) > 100 else log[2],
            "bot_response": log[3][:100] + "..." if len(log[3]) > 100 else log[3],
            "response_time": f"{log[4]:.1f}s" if log[4] else "N/A"
        } for log in logs])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API to get sessions
@app.route("/api/sessions")
def get_sessions():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT session_id, started_at, last_activity, message_count, status 
            FROM sessions 
            ORDER BY last_activity DESC
        """)
        sessions = cursor.fetchall()
        
        return jsonify([{
            "session_id": session[0],
            "started_at": session[1],
            "last_activity": session[2],
            "message_count": session[3],
            "status": session[4]
        } for session in sessions])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API to get knowledge base items
@app.route("/api/knowledge-base")
def get_knowledge_base():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT type, name, added_at, status FROM knowledge_base ORDER BY added_at DESC")
        items = cursor.fetchall()
        
        return jsonify([{
            "type": item[0],
            "name": item[1],
            "added_at": item[2],
            "status": item[3]
        } for item in items])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API to get API keys
@app.route("/api/api-keys")
def get_api_keys():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT key_name, api_key, created_at, status FROM api_keys WHERE status = 'active'")
        keys = cursor.fetchall()
        
        return jsonify([{
            "key_name": key[0],
            "api_key": key[1],
            "created_at": key[2],
            "status": key[3]
        } for key in keys])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API to add existing API key
@app.route("/api/add-api-key", methods=["POST"])
def add_api_key():
    try:
        key_name = request.json.get("key_name")
        api_key = request.json.get("api_key")
        
        if not key_name or not api_key:
            return jsonify({"error": "Key name and API key are required"}), 400
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO api_keys (key_name, api_key, created_at, status) 
            VALUES (?, ?, ?, 'active')
        """, (key_name, api_key, datetime.utcnow().isoformat()))
        db.commit()
        
        return jsonify({
            "key_name": key_name,
            "api_key": api_key,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API to delete API key
@app.route("/api/delete-api-key", methods=["POST"])
def delete_api_key():
    try:
        api_key = request.json.get("api_key")
        if not api_key:
            return jsonify({"error": "API key is required"}), 400
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE api_keys SET status = 'deleted' WHERE api_key = ?", (api_key,))
        db.commit()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Chat response
@app.route("/get", methods=["POST"])
def get_bot_response():
    try:
        start_time = datetime.now()
        user_message = request.form.get("msg")
        session_id = request.form.get("session_id", str(uuid.uuid4()))
        
        if not user_message.strip():
            return "Please enter a valid message."

        # Update or create session
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT session_id FROM sessions WHERE session_id = ?", (session_id,))
        if cursor.fetchone():
            cursor.execute("""
                UPDATE sessions 
                SET last_activity = ?, message_count = message_count + 1 
                WHERE session_id = ?
            """, (datetime.utcnow().isoformat(), session_id))
        else:
            cursor.execute("""
                INSERT INTO sessions (session_id, started_at, last_activity, message_count, status) 
                VALUES (?, ?, ?, 1, 'active')
            """, (session_id, datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))

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
            "Authorization": f"Bearer {get_active_api_key()}",
            "HTTP-Referer": "https://github.com/keerthanab2201/IT-Helpdesk-Chatbot",
            "X-Title": "IT Helpdesk Chatbot",
            "Content-Type": "application/json"
        }

        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        html_response = markdown.markdown(content)

        # Calculate response time
        response_time = (datetime.now() - start_time).total_seconds()

        # Store chat in logs
        cursor.execute("""
            INSERT INTO chat_logs (session_id, timestamp, user_message, bot_response, response_time) 
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, datetime.utcnow().isoformat(), user_message, content, response_time))
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
        
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        file.save(filepath)

        try:
            # Add to knowledge base
            db = get_db()
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO knowledge_base (type, name, content, added_at, status) 
                VALUES ('PDF', ?, ?, ?, 'processing')
            """, (filename, filepath, datetime.utcnow().isoformat()))
            db.commit()

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
                # Update status to failed
                cursor.execute("UPDATE knowledge_base SET status = 'failed' WHERE name = ?", (filename,))
                db.commit()
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

            # Update status to processed
            cursor.execute("UPDATE knowledge_base SET status = 'processed' WHERE name = ?", (filename,))
            db.commit()

            print("PDF processed and indexed successfully.")
            return redirect(url_for("admin"))

        except Exception as e:
            print("PDF processing error:", e)
            # Update status to failed
            db = get_db()
            cursor = db.cursor()
            cursor.execute("UPDATE knowledge_base SET status = 'failed' WHERE name = ?", (filename,))
            db.commit()
            return f"Error processing file: {e}", 500

    print("Invalid file type.")
    return "Invalid file type. Please upload a PDF.", 400

# Add URLs
@app.route("/add_url", methods=["POST"])
def add_url():
    try:
        url = request.form.get("url")
        title = request.form.get("title", url)
        
        if not url:
            return redirect(url_for("admin"))

        print(f"Received URL to add: {url}")

        # Add to knowledge base
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO knowledge_base (type, name, content, added_at, status) 
            VALUES ('URL', ?, ?, ?, 'processing')
        """, (title, url, datetime.utcnow().isoformat()))
        db.commit()

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
            embedding = embedding_model.encode(chunk).tolist()
            if embedding:
                index.upsert(vectors=[{
                    "id": str(uuid.uuid4()),
                    "values": embedding,
                    "metadata": {"text": chunk}
                }])

        # Update status to processed
        cursor.execute("UPDATE knowledge_base SET status = 'processed' WHERE name = ? AND content = ?", (title, url))
        db.commit()

        print("URL content successfully embedded and indexed.")
        return redirect(url_for("admin"))

    except Exception as e:
        print("Error processing URL:", e)
        # Update status to failed
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE knowledge_base SET status = 'failed' WHERE content = ?", (url,))
        db.commit()
        return redirect(url_for("admin"))

# API to get current active API key info
@app.route("/api/current-api-key")
def get_current_api_key():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT key_name, api_key FROM api_keys WHERE status = 'active' LIMIT 1")
        result = cursor.fetchone()
        
        if result:
            return jsonify({
                "source": "database",
                "key_name": result[0],
                "api_key": result[1][:20] + "..." if len(result[1]) > 20 else result[1],
                "full_key": result[1]
            })
        else:
            return jsonify({
                "source": "environment",
                "key_name": "Environment Variable",
                "api_key": OPENROUTER_API_KEY[:20] + "..." if OPENROUTER_API_KEY and len(OPENROUTER_API_KEY) > 20 else "Not Set",
                "full_key": OPENROUTER_API_KEY
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/end-session", methods=["POST"])
def end_session():
    try:
        session_id = request.json.get("session_id")
        if not session_id:
            return jsonify({"error": "Session ID is required"}), 400
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE sessions SET status = 'ended' WHERE session_id = ?", (session_id,))
        db.commit()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)