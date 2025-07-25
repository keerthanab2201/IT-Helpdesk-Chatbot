IT Helpdesk Chatbot 🤖

An intelligent conversational assistant designed to provide automated IT support and help desk services using AI-powered responses and semantic search.

✨ Features
Smart Chat Interface - Real-time AI-powered conversations
Knowledge Base Integration - Upload PDFs and add URLs for contextual responses
Admin Dashboard - Comprehensive management interface with analytics
Session Management - Track and manage user interactions
API Key Management - Secure key storage and rotation
Vector Search - Semantic similarity search using Pinecone
Chat Logging - Complete conversation history with performance metrics

🚀 Quick Start
Prerequisites:
Python 3.8+
OpenRouter API key
Pinecone API key

Installation:

Clone the repository

bashgit clone https://github.com/keerthanab2201/IT-Helpdesk-Chatbot.git
cd IT-Helpdesk-Chatbot

Create virtual environment

bashpython -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install dependencies

bashpip install -r requirements.txt

Configure environment
Create a .env file:

envOPENROUTER_API_KEY=your_openrouter_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=testbot

Run the application

bashpython app.py
Visit http://localhost:5000 for the chat interface or http://localhost:5000/admin for the admin panel.
🛠️ Tech Stack

Backend: Flask, Python
Database: SQLite, Pinecone (Vector DB)
AI/ML: OpenRouter API, SentenceTransformers
Frontend: Bootstrap, jQuery
File Processing: PyPDF2, BeautifulSoup4

📁 Project Structure
├── app.py                 # Main Flask application
├── templates/
│   ├── chat.html         # Chat interface
│   ├── admin.html        # Admin dashboard
│   └── logs.html         # Chat logs view
├── static/               # CSS and static files
├── data/                 # Uploaded documents
├── requirements.txt      # Python dependencies
└── .env                  # Environment variables
🔧 Usage
Chat Interface

Navigate to / to start chatting
Ask IT-related questions
Get contextual responses based on uploaded knowledge

Admin Panel:
Access /admin for management
Upload PDF documents to knowledge base
Add URLs for web content extraction
Monitor chat logs and sessions
Manage API keys
