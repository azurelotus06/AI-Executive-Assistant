#!/bin/bash
echo "Starting backend tunnel..."
cd "$(dirname "$0")"
echo "Current directory: $(pwd)"
echo ""
echo "Starting localtunnel on port 8000..."
lt --port 8000 --subdomain zoom-backend-1 --print-requests
