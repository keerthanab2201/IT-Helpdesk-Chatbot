from src.helper import load_pdf_file, text_split, download_hugging_face_embeddings
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
import os

load_dotenv()

PINECONE_API_KEY= os.environ.get('PINECONE_API_KEY')
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY

extracted_data= load_pdf_file(data='data/')
text_chunks= text_split(extracted_data)
embeddings= download_hugging_face_embeddings()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Check if index exists, if not create it
if "my_index" not in pc.list_indexes().names():
    pc.create_index(
        name="my_index",
        dimension=1536,  # Must match your embedding model's dimension
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-west-2"
        )
    )

#embed each chunk and upsert the embeddings into your Pinecone index
docsearch= PineconeVectorStore.from_documents(
    documents= text_chunks,
    embedding= embeddings,
    index_name= index_name
)
