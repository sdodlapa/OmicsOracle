#!/bin/bash
# Start test server with SQLite configuration

# Load test environment
export $(grep -v '^#' test_environment.env | xargs)

# Start server
cd "$(dirname "$0")"
python -m omics_oracle_v2.api.main
