# IT Helpdesk Chatbot 🤖  

An intelligent conversational assistant designed to provide automated IT support and help desk services using AI-powered responses and semantic search.

---

## ✨ Features

- **Smart Chat Interface** – Real-time AI-powered conversations  
- **Knowledge Base Integration** – Upload PDFs and add URLs for contextual responses  
- **Admin Dashboard** – Comprehensive management interface with analytics  
- **Session Management** – Track and manage user interactions  
- **API Key Management** – Secure key storage and rotation  
- **Vector Search** – Semantic similarity search using Pinecone  
- **Chat Logging** – Complete conversation history with performance metrics  

---

## 🚀 Quick Start

### ✅ Prerequisites

- Python 3.8+  
- [OpenRouter API key](https://openrouter.ai)  
- [Pinecone API key](https://www.pinecone.io)  

---

### 📦 Installation

#### 1. Clone the repository

```bash
git clone https://github.com/keerthanab2201/IT-Helpdesk-Chatbot.git
cd IT-Helpdesk-Chatbot
```
#### 2. Create conda environment

```bash
conda create -n chatbot python=3.10 -y
```
```bash
conda activate chatbot
```
#### 3. Install dependencies

```bash
pip install -r requirements.txt
```
#### 4. Configure environment  
Create a `.env` file:<br>
`OPENROUTER_API_KEY=your_openrouter_api_key`<br>
`PINECONE_API_KEY=your_pinecone_api_key`<br>
`PINECONE_INDEX_NAME=testbot`

#### 5. Run the application

```bash
python app.py
```
Visit http://localhost:5000 for the chat interface or http://localhost:5000/admin for the admin panel.

---

## 🛠️ Tech Stack

| Layer       | Tools / Libraries                    |
|-------------|--------------------------------------|
| **Backend** | Flask, Python                        |
| **Database**| SQLite, Pinecone (Vector DB)         |
| **AI/ML**   | OpenRouter API, SentenceTransformers |
| **Frontend**| Bootstrap, jQuery                    |
| **Parsing** | PyPDF2, BeautifulSoup4               |

---

## 🔧 Usage

### 💬 Chat Interface

- Navigate to `/`  
- Start chatting with the assistant  
- Ask IT-related questions  
- Get contextual responses based on uploaded documents and URLs  

### 🧑‍💼 Admin Panel

- Navigate to `/admin`  
- Upload PDF documents to the knowledge base  
- Add URLs for web content indexing  
- Monitor chat logs and user sessions  
- Manage API keys securely
