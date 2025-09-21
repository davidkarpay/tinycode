#!/bin/bash
# TinyCode Offline Container Startup Script

set -e

echo "🚀 Starting TinyCode in offline mode..."

# Start Ollama service in background
echo "📡 Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama service..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama service is ready"
        break
    fi

    if [ $i -eq 30 ]; then
        echo "❌ Ollama service failed to start"
        exit 1
    fi

    sleep 2
done

# Verify models are available
echo "🔍 Verifying models..."
if ollama list | grep -q "tinyllama:latest"; then
    echo "✅ tinyllama:latest model available"
else
    echo "❌ tinyllama:latest model not found"
    exit 1
fi

# Test embedding models
echo "🔤 Testing embedding models..."
python -c "
from sentence_transformers import SentenceTransformer
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(['test'])
    print('✅ Embedding models functional')
except Exception as e:
    print(f'❌ Embedding model error: {e}')
    exit(1)
"

# Run model verification if available
if [ -f "/app/scripts/verify_offline_models.py" ]; then
    echo "🧪 Running offline model verification..."
    python /app/scripts/verify_offline_models.py || {
        echo "⚠️ Model verification had issues, but continuing..."
    }
fi

echo "🎉 TinyCode offline environment ready!"

# Start the application
echo "🚀 Starting TinyCode API server..."

# Check if we should start the API server or CLI
if [ "${START_MODE:-api}" = "api" ]; then
    exec python api_server.py
elif [ "${START_MODE}" = "cli" ]; then
    exec python tiny_code.py
else
    # Default to API server
    exec python api_server.py
fi