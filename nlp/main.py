from ingestion_factory import IngestionFactory

factory = IngestionFactory()

# Automatically detects PDF, Markdown, or Text and processes accordingly
final_rag_documents = factory.process_file("data_source_2025.txt")

for doc in final_rag_documents:
    print(f"Content: {doc['text'][:50]}... | Type: {doc['metadata']['format']}")
