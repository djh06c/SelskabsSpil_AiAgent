from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from pathlib import Path
import os

# Finder .env-filen i projektets rodmappe:
# SelskabsSpil_AiAgent/.env
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# Sikkerhedstjek, så fejl bliver lettere at forstå
if not env_path.exists():
    raise FileNotFoundError(f".env-filen blev ikke fundet her: {env_path}")

if not NEO4J_URI:
    raise ValueError("NEO4J_URI mangler i .env-filen.")

if not NEO4J_USER:
    raise ValueError("NEO4J_USER mangler i .env-filen.")

if not NEO4J_PASSWORD:
    raise ValueError("NEO4J_PASSWORD mangler i .env-filen.")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)

model = SentenceTransformer(MODEL_NAME)


def get_documents_without_embeddings(tx):
    query = """
    MATCH (d:Document)
    WHERE d.embedding IS NULL
    RETURN elementId(d) AS id, d.text AS text, d.fileName AS fileName
    """
    return list(tx.run(query))


def save_embedding(tx, document_id, embedding):
    query = """
    MATCH (d:Document)
    WHERE elementId(d) = $document_id
    SET d.embedding = $embedding
    RETURN d.fileName AS fileName
    """
    tx.run(query, document_id=document_id, embedding=embedding)


def main():
    print(f"Bruger .env-fil: {env_path}")
    print(f"Forbinder til Neo4j på: {NEO4J_URI}")
    print(f"Database: {NEO4J_DATABASE}")

    with driver.session(database=NEO4J_DATABASE) as session:
        documents = session.execute_read(get_documents_without_embeddings)

        if not documents:
            print("Ingen Document-noder mangler embeddings.")
            return

        print(f"Fandt {len(documents)} dokumenter uden embeddings.")

        for doc in documents:
            text = doc["text"]
            file_name = doc["fileName"]
            document_id = doc["id"]

            if not text or not text.strip():
                print(f"Springer tomt dokument over: {file_name}")
                continue

            embedding = model.encode(text).tolist()

            session.execute_write(save_embedding, document_id, embedding)

            print(f"Embedding gemt for: {file_name}")

    driver.close()
    print("Færdig.")


if __name__ == "__main__":
    main()