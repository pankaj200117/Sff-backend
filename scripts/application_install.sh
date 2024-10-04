#!/bin/bash

# Navigate to the application directory
cd /var/www/html/Sff-backend

# Activate the virtual environment
source venv/bin/activate

# Kill any existing process on port 5011 (optional)
fuser -k 5011/tcp

# Start the Python API using Uvicorn
echo "Starting the Python API..."
uvicorn src.api:app --host 0.0.0.0 --port 5011 &

# Create a tmux session for the Gradio app
tmux new-session -d -s gradio_session
tmux send-keys -t gradio_session "source venv/bin/activate && cd /var/www/html/Sff-backend && python -m src.app" C-m

# Create a tmux session for the Suno API
tmux new-session -d -s suno_session
tmux send-keys -t suno_session "cd /var/www/html/suno-api && npm run dev" C-m

echo "All applications are now running in their respective tmux sessions."

