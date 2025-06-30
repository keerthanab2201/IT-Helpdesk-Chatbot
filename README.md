# IT-Helpdesk-Chatbot
#how to run
### step 1- create a conda environment after opening the repository
```bash
conda create -n chatbot python=3.10 -y

```bash
conda activate chatbot

### step 2- install the requirements
```bash
pip install -r requirements.txt
```

### step 3- Create a .env file in the root directory and add your Pinecone & OpenAI credentials as follows:
```ini
PINECONE_API_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
OPENAI_API_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

```bash
### step 4 - Run the following command to store embeddings to Pinecone
python store_index.py
```
```bash
### finally run the following command
python app.py
```

Now,
```bash
open up localhost:xxxx
```

### Techstack Used:
- Python
- LangChain
- Flask
- GPT
- Pinecone
