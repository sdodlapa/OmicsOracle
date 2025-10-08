#!/bin/bash
# Start OmicsOracle with HTTP/1.1 only (no HTTP/2)

# Stop any running instances
pkill -f "uvicorn.*omics_oracle"
sleep 2

# Start with HTTP/1.1 only
cd /Users/sanjeevadodlapati/Downloads/Repos/OmicsOracle

# Option 1: Using uvicorn directly
uvicorn omics_oracle_v2.api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --no-http2 \
    --log-level info

# Option 2: If that doesn't work, use gunicorn with HTTP/1.1
# gunicorn omics_oracle_v2.api.main:app \
#     --workers 4 \
#     --worker-class uvicorn.workers.UvicornWorker \
#     --bind 0.0.0.0:8000 \
#     --log-level info
