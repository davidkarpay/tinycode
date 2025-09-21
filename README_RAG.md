# Tiny Code RAG - Genetics-Enhanced Coding Assistant

A comprehensive RAG (Retrieval-Augmented Generation) system that enhances the Tiny Code agent with document summarization capabilities and genetics domain knowledge.

## 🎯 Overview

This system combines:
- **TinyLlama** for local AI processing (no external APIs)
- **RAG Infrastructure** for context-aware responses
- **Genetics Knowledge Base** with bioinformatics documentation
- **Document Summarization** for interactive document exploration
- **Hybrid Search** combining dense embeddings + BM25 sparse search

## 🏗️ Architecture

```
tiny_code_rag/
├── rag/                     # Core RAG infrastructure
│   ├── embeddings/          # Local sentence transformers
│   ├── vectorstore/         # FAISS vector database
│   ├── ingestion/           # Document loading & chunking
│   └── retrieval/           # Hybrid search system
├── genetics/                # Genetics knowledge crawler
├── summarizer/              # Document summarization
├── tiny_code/              # Enhanced coding agent
└── config/                 # Configuration files
```

## 🚀 Quick Start

### 1. Launch Interactive Mode
```bash
python tiny_code_rag.py
```

### 2. Set Up Genetics Knowledge Base
```bash
# Interactive mode
/setup_genetics

# Or command line
python tiny_code_rag.py setup-genetics --max-pages 30
```

### 3. Ingest Your Documents
```bash
# Interactive mode
/ingest /path/to/documents

# Or command line
python tiny_code_rag.py ingest /path/to/documents --kb general
```

### 4. Start Using RAG Features
```bash
# Search knowledge base
/rag "GATK best practices"

# Summarize documents
/summarize document.pdf

# Chat with documents
/chat "Explain VCF format specifications"

# Get genetics help
/genetics "SAM file format"
```

## 💡 Key Features

### 🔍 **Hybrid Search**
- Dense embeddings (sentence-transformers)
- Sparse search (BM25)
- Automatic index optimization
- Metadata filtering

### 📚 **Knowledge Bases**
- **General**: Any documents you ingest
- **Genetics**: Bioinformatics specs and documentation
- **Code**: Programming examples and patterns

### 🧬 **Genetics Corpus**
Pre-configured to crawl and index:
- HTS format specifications (SAM/BAM/VCF/BED)
- GATK best practices
- samtools/bcftools documentation
- NCBI RefSeq and ClinVar docs
- Bioinformatics tool manuals

### 📄 **Document Processing**
Supports 15+ file formats:
- PDF, DOCX, PPTX, Excel
- HTML, Markdown, plain text
- Code files (Python, JavaScript, etc.)
- JSON, XML, CSV

### 🤖 **Enhanced Coding**
- Context-aware code generation
- RAG-enhanced code explanation
- Genetics-specific coding help
- Memory of previous decisions

## 🎮 Interactive Commands

### RAG Commands
| Command | Description | Example |
|---------|-------------|---------|
| `/ingest <path>` | Add documents to RAG | `/ingest /docs/genetics/` |
| `/rag <query>` | Search knowledge base | `/rag "VCF file format"` |
| `/summarize <path>` | Summarize document | `/summarize paper.pdf` |
| `/chat <question>` | Chat with documents | `/chat "How does GATK work?"` |
| `/genetics <concept>` | Explain genetics concept | `/genetics "coordinate systems"` |
| `/knowledge <base>` | Switch knowledge base | `/knowledge genetics` |
| `/rag_stats` | Show system statistics | `/rag_stats` |

### Enhanced File Commands
| Command | Description |
|---------|-------------|
| `/analyze <file>` | RAG-enhanced code analysis |
| `/explain <file>` | Code explanation with context |
| `/review <file>` | Code review with best practices |

## 🛠️ Command Line Usage

### Document Operations
```bash
# Ingest documents
python tiny_code_rag.py ingest documents/ --kb general

# Search knowledge base
python tiny_code_rag.py search "machine learning" --kb general

# Summarize document
python tiny_code_rag.py summarize document.pdf --type extractive --length 300

# Ask questions
python tiny_code_rag.py ask "What is CRISPR?" --kb genetics
```

### System Setup
```bash
# Set up genetics knowledge (one-time)
python tiny_code_rag.py setup-genetics --max-pages 50

# Test system
python tiny_code_rag.py search "test query"
```

## ⚙️ Configuration

### Main Config (`config/rag_config.yaml`)
```yaml
embedding:
  model: "all-MiniLM-L6-v2"
  dimension: 384

retrieval:
  hybrid_alpha: 0.7  # Dense vs sparse weight
  top_k: 10

llm:
  primary_model: "tinyllama:latest"
  temperature: 0.7
```

### Genetics Corpus (`config/genetics_corpus.yaml`)
Configures sources for genetics knowledge:
- HTS specifications
- Tool documentation
- Reference databases
- Ontologies

## 📊 System Statistics

Use `/rag_stats` or check system status:
```python
# In Python
from tiny_code.rag_enhanced_agent import RAGEnhancedTinyCodeAgent
agent = RAGEnhancedTinyCodeAgent()
stats = agent.get_rag_stats()
```

## 🧪 Testing

The system includes comprehensive testing:

1. **Component Tests**: Each RAG component works independently
2. **Integration Tests**: End-to-end document processing
3. **CLI Tests**: All commands function correctly
4. **Knowledge Base Tests**: Genetics corpus ingestion

## 🔧 Troubleshooting

### Common Issues

**"No relevant documents found"**
- Make sure you've ingested documents first
- Check that you're searching the right knowledge base
- Try different search terms

**"Model not found"**
- Ensure TinyLlama is installed: `ollama pull tinyllama`
- Check Ollama is running: `ollama list`

**Memory Issues**
- Reduce batch sizes in config
- Use smaller embedding models
- Process documents in smaller chunks

**Import Errors**
- Make sure all dependencies are installed
- Check Python path includes the project directory

## 📈 Performance

### Benchmarks (on MacBook Air M1)
- **Document Ingestion**: ~100 docs/min
- **Embedding Generation**: ~1000 chunks/min
- **Search Latency**: <100ms for 10k documents
- **Summary Generation**: ~30 seconds per document

### Optimization Tips
- Use CPU-optimized FAISS for small datasets
- Cache embeddings to avoid recomputation
- Batch process large document sets
- Use appropriate chunk sizes (800-1000 tokens)

## 🔮 Advanced Usage

### Custom Knowledge Bases
```python
# Create specialized knowledge base
await agent.ingest_documents(
    "/path/to/domain/docs",
    knowledge_base="custom_domain"
)

# Search specific domain
results = agent.rag_search(
    "domain-specific query",
    knowledge_base="custom_domain"
)
```

### Genetics-Specific Features
```python
# Get genetics help
explanation = agent.explain_genetics_concept("GWAS")

# Code help with genetics context
help_text = agent.get_coding_help("parse VCF files in Python")
```

### Programmatic API
```python
from tiny_code.rag_enhanced_agent import RAGEnhancedTinyCodeAgent

agent = RAGEnhancedTinyCodeAgent()

# Document operations
summary = agent.summarize_document("paper.pdf")
response = agent.chat_with_documents("What is the main finding?")

# Code operations with RAG
code = agent.rag_enhanced_coding("Create a VCF parser")
```

## 🤝 Contributing

1. Add new document loaders in `rag/ingestion/`
2. Extend genetics corpus in `config/genetics_corpus.yaml`
3. Add new retrieval strategies in `rag/retrieval/`
4. Enhance CLI commands in `tiny_code_rag.py`

## 📝 License

MIT License - Build amazing genetics applications!

---

**Built with ❤️ for the genetics and bioinformatics community**

*Powered by TinyLlama, FAISS, and sentence-transformers - 100% local, no external APIs required*