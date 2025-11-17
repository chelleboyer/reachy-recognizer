#!/bin/bash
# Keep Ollama Model Loaded in Memory

MODEL=${1:-phi3:mini}

echo "🔥 Keeping Ollama model '$MODEL' warm in memory..."
echo "   This prevents the 30-second first-response delay."
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Keep the model loaded by sending a keepalive request every 5 minutes
while true; do
    echo "[$(date '+%H:%M:%S')] Pinging $MODEL to keep loaded..."
    
    curl -s -X POST http://localhost:11434/api/chat \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"$MODEL\",
            \"messages\": [{\"role\": \"user\", \"content\": \"ping\"}],
            \"stream\": false,
            \"keep_alive\": \"30m\",
            \"options\": {\"num_predict\": 1}
        }" > /dev/null
    
    if [ $? -eq 0 ]; then
        echo "   ✓ Model is warm and ready"
    else
        echo "   ✗ Failed to reach Ollama. Is it running?"
        echo "   Start with: ollama serve"
    fi
    
    # Wait 5 minutes before next ping
    sleep 300
done
