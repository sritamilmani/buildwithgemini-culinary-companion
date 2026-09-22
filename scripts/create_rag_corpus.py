"""Script to create a serverless Vertex AI RAG corpus for Culinary Companion."""

import vertexai
from vertexai.preview import rag
from vertexai.preview.rag.utils import resources as rr

PROJECT_ID = "qwiklabs-gcp-03-f55cf09067a8"
LOCATION = "us-central1"  # Serverless RAG is us-central1 only
GCS_PATH = "gs://culinary-companion-media-qwiklabs-gcp-03-f55cf09067a8/rag/pg49513.txt"

PARSING_PROMPT = (
    "Extract the individual useful facts, herbs, spices, culinary recipes, and medicinal uses described in this text. "
    "Ignore and omit all Gutenberg metadata, licenses, and boilerplate text. "
    "Output clean, self-contained informative prose."
)


def main():
    print(f"Initializing Vertex AI RAG in {LOCATION} for project {PROJECT_ID}...")
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    print("Setting RAG Engine configuration to Serverless mode...")
    cfg = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragEngineConfig"
    try:
        rag.update_rag_engine_config(
            rag_engine_config=rag.RagEngineConfig(
                name=cfg,
                rag_managed_db_config=rag.RagManagedDbConfig(mode=rr.Serverless()),
            )
        )
        print("✅ Serverless mode configured.")
    except Exception as e:
        print(f"Note on serverless config update: {e}")

    print("Creating serverless RAG corpus...")
    corpus = rag.create_corpus(
        display_name="complete-herbal-corpus",
        vector_db=rr.RagManagedVertexVectorSearch(),
        embedding_model_config=rag.EmbeddingModelConfig(
            publisher_model="publishers/google/models/text-embedding-005"
        ),
    )
    print(f"✅ RAG Corpus created successfully! Corpus Name: {corpus.name}")

    print(f"Importing and indexing document from {GCS_PATH}...")
    resp = rag.import_files(
        corpus_name=corpus.name,
        paths=[GCS_PATH],
        transformation_config=rag.TransformationConfig(
            chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
        ),
        llm_parser=rag.LlmParserConfig(
            model_name="gemini-2.0-flash-001",
            custom_parsing_prompt=PARSING_PROMPT,
        ),
    )
    print(f"✅ Imported {resp.imported_rag_files_count} file(s) into RAG corpus.")
    
    # Save corpus name to a local file for tool reference
    with open(".rag_corpus_name", "w") as f:
        f.write(corpus.name)
    print(f"Saved corpus name to .rag_corpus_name: {corpus.name}")


if __name__ == "__main__":
    main()
