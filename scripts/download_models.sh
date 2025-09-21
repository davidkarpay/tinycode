#!/bin/bash
# TinyCode Model Download Automation Script
# Downloads all required models for offline operation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 TinyCode Model Download Script${NC}"
echo "=========================================="

# Configuration
OLLAMA_HOST=${OLLAMA_HOST:-localhost}
OLLAMA_PORT=${OLLAMA_PORT:-11434}
OLLAMA_URL="http://${OLLAMA_HOST}:${OLLAMA_PORT}"

# Required models
OLLAMA_MODELS=("tinyllama:latest")
EMBEDDING_MODELS=("all-MiniLM-L6-v2")

# Optional models (can be enabled)
OPTIONAL_OLLAMA_MODELS=(
    "qwen2.5-coder:7b"
    "starcoder2:7b"
    "nomic-embed-text:latest"
)

# Functions
check_dependency() {
    local cmd=$1
    local package=$2

    if ! command -v "$cmd" &> /dev/null; then
        echo -e "${RED}❌ $cmd not found. Please install $package${NC}"
        return 1
    fi
    return 0
}

check_ollama_service() {
    echo -e "${YELLOW}📡 Checking Ollama service...${NC}"

    if curl -s "$OLLAMA_URL/api/tags" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Ollama service is running at $OLLAMA_URL${NC}"
        return 0
    else
        echo -e "${RED}❌ Ollama service not available at $OLLAMA_URL${NC}"
        echo "Please start Ollama service: ollama serve"
        return 1
    fi
}

download_ollama_model() {
    local model=$1
    echo -e "${YELLOW}📥 Downloading Ollama model: $model${NC}"

    if ollama pull "$model"; then
        echo -e "${GREEN}✅ Successfully downloaded $model${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to download $model${NC}"
        return 1
    fi
}

test_ollama_model() {
    local model=$1
    echo -e "${YELLOW}🧪 Testing Ollama model: $model${NC}"

    local response
    response=$(ollama run "$model" "Hello, respond with 'OK'" 2>/dev/null | head -1)

    if [[ "$response" == *"OK"* ]]; then
        echo -e "${GREEN}✅ Model $model is functional${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️ Model $model may not be fully functional${NC}"
        return 1
    fi
}

download_embedding_model() {
    local model=$1
    echo -e "${YELLOW}📥 Downloading embedding model: $model${NC}"

    python3 -c "
import sys
try:
    from sentence_transformers import SentenceTransformer
    print(f'Downloading {model}...')
    model_obj = SentenceTransformer('$model')
    # Test encoding
    embeddings = model_obj.encode(['test sentence'])
    print(f'✅ Model cached at: {model_obj.cache_folder}')
    print(f'✅ Embedding dimension: {embeddings.shape[1]}')
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Successfully downloaded and tested $model${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to download $model${NC}"
        return 1
    fi
}

show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --all                Download all models including optional ones"
    echo "  --no-test           Skip model testing after download"
    echo "  --embedding-only    Download only embedding models"
    echo "  --ollama-only       Download only Ollama models"
    echo "  --help, -h          Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  OLLAMA_HOST         Ollama host (default: localhost)"
    echo "  OLLAMA_PORT         Ollama port (default: 11434)"
}

main() {
    local download_all=false
    local skip_tests=false
    local embedding_only=false
    local ollama_only=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --all)
                download_all=true
                shift
                ;;
            --no-test)
                skip_tests=true
                shift
                ;;
            --embedding-only)
                embedding_only=true
                shift
                ;;
            --ollama-only)
                ollama_only=true
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    echo -e "${BLUE}Configuration:${NC}"
    echo "  Ollama URL: $OLLAMA_URL"
    echo "  Download all: $download_all"
    echo "  Skip tests: $skip_tests"
    echo "  Embedding only: $embedding_only"
    echo "  Ollama only: $ollama_only"
    echo ""

    # Check dependencies
    echo -e "${YELLOW}🔍 Checking dependencies...${NC}"

    if [ "$ollama_only" != "true" ]; then
        check_dependency "python3" "Python 3" || exit 1

        # Check Python packages
        if ! python3 -c "import sentence_transformers" 2>/dev/null; then
            echo -e "${RED}❌ sentence-transformers not found. Please run: pip install sentence-transformers${NC}"
            exit 1
        fi
    fi

    if [ "$embedding_only" != "true" ]; then
        check_dependency "ollama" "Ollama" || exit 1
        check_ollama_service || exit 1
    fi

    echo -e "${GREEN}✅ All dependencies satisfied${NC}"
    echo ""

    # Download Ollama models
    if [ "$embedding_only" != "true" ]; then
        echo -e "${BLUE}📦 Downloading Ollama models...${NC}"

        local models_to_download=("${OLLAMA_MODELS[@]}")

        if [ "$download_all" = "true" ]; then
            models_to_download+=("${OPTIONAL_OLLAMA_MODELS[@]}")
        fi

        for model in "${models_to_download[@]}"; do
            if download_ollama_model "$model"; then
                if [ "$skip_tests" != "true" ]; then
                    test_ollama_model "$model"
                fi
            else
                echo -e "${YELLOW}⚠️ Continuing with other models...${NC}"
            fi
            echo ""
        done

        echo -e "${BLUE}📋 Available Ollama models:${NC}"
        ollama list
        echo ""
    fi

    # Download embedding models
    if [ "$ollama_only" != "true" ]; then
        echo -e "${BLUE}🔤 Downloading embedding models...${NC}"

        for model in "${EMBEDDING_MODELS[@]}"; do
            download_embedding_model "$model"
            echo ""
        done
    fi

    # Final verification
    echo -e "${BLUE}🔍 Running final verification...${NC}"

    if [ -f "scripts/verify_offline_models.py" ]; then
        python3 scripts/verify_offline_models.py
    else
        echo -e "${YELLOW}⚠️ Verification script not found. Manual verification recommended.${NC}"
    fi

    echo ""
    echo -e "${GREEN}🎉 Model download process completed!${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Verify offline operation: python scripts/verify_offline_models.py"
    echo "2. Test the application: python tiny_code.py"
    echo "3. Check the offline setup guide: OFFLINE_SETUP_GUIDE.md"
    echo ""
    echo -e "${BLUE}Model locations:${NC}"
    echo "  Ollama models: ~/.ollama/"
    echo "  Embedding models: ~/.cache/huggingface/hub/"
    echo ""

    # Show storage usage
    echo -e "${BLUE}📊 Storage usage:${NC}"
    if [ -d "$HOME/.ollama" ]; then
        echo -n "  Ollama: "
        du -sh "$HOME/.ollama" 2>/dev/null || echo "Unknown"
    fi

    if [ -d "$HOME/.cache/huggingface" ]; then
        echo -n "  HuggingFace: "
        du -sh "$HOME/.cache/huggingface" 2>/dev/null || echo "Unknown"
    fi
}

# Handle script interruption
trap 'echo -e "\n${RED}❌ Download interrupted by user${NC}"; exit 130' INT

# Run main function
main "$@"