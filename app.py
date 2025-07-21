from flask import Flask, render_template, request
from dotenv import load_dotenv
import os
import requests
import markdown
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer


# Load environment variables
load_dotenv()

app = Flask(__name__)

# Load environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "it-helpdesk-index")

# Load HuggingFace embedding model (384-dim)
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

try:
    if PINECONE_INDEX_NAME not in pc.list_indexes().names():
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=384,  # Must match embedding model
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        print(f"Created new Pinecone index: {PINECONE_INDEX_NAME}")
    else:
        print(f"Using existing Pinecone index: {PINECONE_INDEX_NAME}")
except Exception as e:
    print(f"Error initializing Pinecone: {e}")

@app.route("/")
def home():
    return render_template("chat.html")

@app.route("/get", methods=["POST"])
def get_bot_response():
    try:
        user_message = request.form.get("msg")
        if not user_message or not user_message.strip():
            return "Please enter a valid message."

        print("User message:", user_message)

        # Get embedding
        embedding = get_embedding(user_message)
        if not embedding:
            return "Error generating embedding. Try again."

        # Query Pinecone
        index = pc.Index(PINECONE_INDEX_NAME)
        query_response = index.query(
            vector=embedding,
            top_k=3,
            include_metadata=True
        )

        # Construct context from top matches
        context = "\n".join(
            [match.metadata.get("text", "") for match in query_response.matches]
        )

        # Prepare OpenRouter chat payload
        payload = {
            "model": "qwen/qwen3-30b-a3b:free",  # ✅ correct model name
            "messages": [
                {"role": "system", "content": f"You are an IT helpdesk assistant. Use this context if relevant:\n{context}"},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }

        print("Payload:", payload)

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://github.com/keerthanab2201/IT-Helpdesk-Chatbot",
            "X-Title": "IT Helpdesk Chatbot",
            "Content-Type": "application/json"
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )

        response.raise_for_status()
        raw_markdown = response.json()["choices"][0]["message"]["content"]
        html_response = markdown.markdown(raw_markdown)
        return html_response


    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        if e.response is not None:
            print("Status Code:", e.response.status_code)
            print("Response Text:", e.response.text)
        return "Our helpdesk service is currently unavailable. Please try again later."

    except Exception as e:
        print(f"Unexpected Error: {e}")
        return "Sorry, I encountered an unexpected error."

def get_embedding(text):
    try:
        return embedding_model.encode(text).tolist()
    except Exception as e:
        print(f"HuggingFace Embedding Error: {e}")
        return None

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)