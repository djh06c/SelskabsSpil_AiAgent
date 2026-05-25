This project runs locally. To start the system:

1. Start Neo4j Desktop instance: SelskabsspilsAgent
2. Start n8n
3. Start Ollama with hermes3
4. Start FastAPI:
   cd src/scripts
   uvicorn rag_api:app --reload --port 8000
5. Start MCP server:
   python mcp_server.py
6. Test Graph RAG:
   curl -X POST http://localhost:5678/webhook/recommend-games -H "Content-Type: application/json" -d '{"equipment":"Kort"}'
7. Test Vector RAG:
   curl -X POST http://localhost:5678/webhook/ask-rules -H "Content-Type: application/json" -d '{"question":"Hvad skal man bruge til Beer Pong?"}'
