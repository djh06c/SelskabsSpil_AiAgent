from fastapi import FastAPI
from pydantic import BaseModel
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from pathlib import Path
import requests
import os

env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
OLLAMA_MODEL = "hermes3"
OLLAMA_URL = "http://localhost:11434/api/chat"

app = FastAPI()

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)

embedding_model = SentenceTransformer(MODEL_NAME)


class QuestionRequest(BaseModel):
    question: str


def search_documents(question, top_k=1):
    question_embedding = embedding_model.encode(question).tolist()

    query = """
    CALL db.index.vector.queryNodes(
        'document_embedding_index',
        $top_k,
        $question_embedding
    )
    YIELD node, score

    OPTIONAL MATCH (g:Game)-[:HAS_DOCUMENT]->(node)

    RETURN
        g.name AS game,
        node.fileName AS fileName,
        node.text AS text,
        score
    ORDER BY score DESC
    """

    with driver.session(database=NEO4J_DATABASE) as session:
        result = session.run(
            query,
            top_k=top_k,
            question_embedding=question_embedding
        )

        return [record.data() for record in result]


def ask_hermes(question, context):
    system_prompt = """
Du er en dansk selskabsspils-agent.

Du må kun svare ud fra den kontekst, du får.
Hvis svaret ikke står i konteksten, skal du sige:
"Det kan jeg ikke finde information om i min knowledge base."

Svar kort, konkret og let forståeligt.
"""

    user_prompt = f"""
Brugerens spørgsmål:
{question}

Kontekst fra knowledge base:
{context}

Svar på dansk:
"""

    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }

    response = requests.post(OLLAMA_URL, json=payload)

    if response.status_code != 200:
        raise Exception(f"Fejl fra Ollama: {response.status_code} - {response.text}")

    data = response.json()
    return data["message"]["content"]


@app.post("/ask-rules")
def ask_rules(request: QuestionRequest):
    results = search_documents(request.question, top_k=1)

    if not results:
        return {
            "answer": "Jeg kunne ikke finde noget relevant i knowledge basen.",
            "source": None
        }

    best = results[0]
    answer = ask_hermes(request.question, best["text"])

    return {
        "question": request.question,
        "answer": answer,
        "source": {
            "game": best["game"],
            "document": best["fileName"],
            "score": best["score"]
        }
    }