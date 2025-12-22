from dataclasses import dataclass

@dataclass
class RAGConfig:
    """Centralized configuration for the ingestion pipeline."""
    chunk_size: int = 1000
    chunk_overlap: int = 100
    # Add 2025-specific settings here
    ocr_enabled: bool = True
    embedding_model: str = "text-embedding-3-small"
