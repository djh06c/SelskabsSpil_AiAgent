# Arkitektur

Projektet består af to RAG-flows.

## Graph RAG
Bruges til at anbefale spil ud fra udstyr.
n8n modtager udstyr via webhook og spørger Neo4j efter spil, der har relationen USES til udstyret.

## Vector RAG
Bruges til regelspørgsmål.
n8n modtager et spørgsmål via webhook og sender det til FastAPI.
FastAPI laver embedding af spørgsmålet, søger i Neo4j vector index og sender den relevante dokumenttekst til Hermes via Ollama.
Svaret returneres til n8n og videre til brugeren.

## Teknologier
- n8n til automatisering
- FastAPI som lokalt API
- Neo4j som graph database og vector database
- SentenceTransformers til embeddings
- Ollama/Hermes som lokal LLM
- 