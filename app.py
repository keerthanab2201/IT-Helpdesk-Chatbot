# app.py
from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
import os
import requests
import markdown
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Environment Variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "it-helpdesk-index")

# Embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

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
        return markdown.markdown(content)

    except Exception as e:
        print("Chat error:", e)
        return "Sorry, I encountered an error."

# Upload documents
@app.route("/upload_document", methods=["POST"])
def upload_document():
    return redirect(url_for("admin"))

# Add URLs
@app.route("/add_url", methods=["POST"])
def add_url():
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
