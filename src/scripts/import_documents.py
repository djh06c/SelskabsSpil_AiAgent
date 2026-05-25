from pathlib import Path
from neo4j import GraphDatabase


# --- Neo4j connection settings ---
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "Ballincat43"
NEO4J_DATABASE = "neo4j"


# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


# Maps file names to existing Game node names in Neo4j
FILE_TO_GAME_NAME = {
    "meyer.md": "Meyer",
    "fisk.md": "Fisk",
    "vandfald.md": "Vandfald",
    "beer-pong.md": "Beer Pong",
    "snyd.md": "Snyd",
}


def import_document(tx, file_name: str, game_name: str, text: str):
    query = """
    MATCH (g:Game {name: $game_name})
    MERGE (d:Document {fileName: $file_name})
    SET d.title = $game_name,
        d.text = $text,
        d.source = $file_name
    MERGE (g)-[:HAS_DOCUMENT]->(d)
    RETURN g.name AS game, d.fileName AS document
    """

    result = tx.run(
        query,
        game_name=game_name,
        file_name=file_name,
        text=text
    )

    return result.single()


def main():
    if not DATA_DIR.exists():
        raise FileNotFoundError(f"Data folder not found: {DATA_DIR}")

    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
    )

    with driver:
        with driver.session(database=NEO4J_DATABASE) as session:
            for file_path in DATA_DIR.glob("*.md"):
                file_name = file_path.name

                if file_name not in FILE_TO_GAME_NAME:
                    print(f"Skipping unknown file: {file_name}")
                    continue

                game_name = FILE_TO_GAME_NAME[file_name]
                text = file_path.read_text(encoding="utf-8")

                record = session.execute_write(
                    import_document,
                    file_name,
                    game_name,
                    text
                )

                if record:
                    print(f"Imported {record['document']} for game {record['game']}")
                else:
                    print(f"No matching Game node found for: {game_name}")

    print("Done importing documents.")


if __name__ == "__main__":
    main()