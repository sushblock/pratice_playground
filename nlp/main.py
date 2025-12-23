from ingestion_factory import IngestionFactory
from dotenv import load_dotenv
import os
import shutil

def ensure_dir(path: str):
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)

if __name__ == "__main__":
    # --------------------------------------------------
    # Load environment variables
    # --------------------------------------------------
    load_dotenv()

    DOCUMENT_FOLDER = os.getenv("DOCUMENT_FOLDER")

    if not DOCUMENT_FOLDER:
        raise EnvironmentError("DOCUMENT_FOLDER is not set in .env")

    RAW_DIR = os.path.join(DOCUMENT_FOLDER, "raw")
    PROCESSED_DIR = os.path.join(DOCUMENT_FOLDER, "processed")
    ERROR_DIR = os.path.join(DOCUMENT_FOLDER, "error")

    # Ensure required directories exist
    ensure_dir(RAW_DIR)
    ensure_dir(PROCESSED_DIR)
    ensure_dir(ERROR_DIR)

    # Initialize ingestion factory
    factory = IngestionFactory()

    print(f"\n--- Starting Automatic Ingestion Pipeline ---")
    print(f"Root Folder : {DOCUMENT_FOLDER}")
    print(f"Raw Folder  : {RAW_DIR}")

    all_rag_documents = []

    # --------------------------------------------------
    # Process only files in raw/
    # --------------------------------------------------
    for filename in os.listdir(RAW_DIR):
        file_path = os.path.join(RAW_DIR, filename)

        if not os.path.isfile(file_path):
            continue

        print(f"\nProcessing file: {file_path}")

        try:
            chunks = factory.process_file(file_path)
            all_rag_documents.extend(chunks)

            # Move to processed/
            shutil.move(
                file_path,
                os.path.join(PROCESSED_DIR, filename)
            )

            print(f"✔ Successfully created {len(chunks)} chunks.")

        except ValueError as e:
            # Unsupported MIME / registry mismatch
            print(f"✖ Skipping file (unsupported type): {e}")

            shutil.move(
                file_path,
                os.path.join(ERROR_DIR, filename)
            )

        except Exception as e:
            # Any unexpected processing failure
            print(f"✖ Error processing file: {e}")

            shutil.move(
                file_path,
                os.path.join(ERROR_DIR, filename)
            )

    print(
        f"\n--- Ingestion Complete. Total chunks ready for RAG: "
        f"{len(all_rag_documents)} ---"
    )

    # At this point:
    # - raw/       -> empty or contains unprocessed files
    # - processed/ -> successfully ingested source files
    # - error/     -> files requiring investigation
    # - all_rag_documents -> ready for vector DB ingestion
