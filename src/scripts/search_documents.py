from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from pathlib import Path
import os

env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)

model = SentenceTransformer(MODEL_NAME)


def search_documents(question, top_k=1):
    question_embedding = model.encode(question).tolist()

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


def main():
    question = input("Stil et regelspørgsmål: ")

    results = search_documents(question, top_k=1)

    if not results:
        print("Ingen relevante dokumenter fundet.")
        return

    best = results[0]

    print("\n--- Bedste match ---\n")
    print(f"Spørgsmål: {question}")
    print(f"Spil: {best['game']}")
    print(f"Dokument: {best['fileName']}")
    print(f"Score: {best['score']}")
    print("\n--- Kontekst-preview ---\n")
    print(best["text"][:500])


if __name__ == "__main__":
    main()
    driver.close()