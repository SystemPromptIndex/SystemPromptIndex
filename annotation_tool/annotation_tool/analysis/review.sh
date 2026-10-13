#!/bin/bash
# One-click: start server and open review tool in browser
DIR="$(cd "$(dirname "$0")" && pwd)"
PORT=8080

# Kill any existing server on this port
lsof -ti:$PORT 2>/dev/null | xargs kill 2>/dev/null

echo "Starting review tool at http://localhost:$PORT/review_negative_spans.html"
cd "$DIR"
python3 -m http.server $PORT &
SERVER_PID=$!
sleep 1
open "http://localhost:$PORT/review_negative_spans.html"

echo "Press Ctrl+C to stop the server."
trap "kill $SERVER_PID 2>/dev/null; exit" INT
wait $SERVER_PID
