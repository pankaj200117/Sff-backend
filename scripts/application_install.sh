#!/bin/bash
# This script runs to start the applications

# Start the API app in tmux
tmux new-session -d -s app
tmux send-keys -t app "conda activate demo_api_env" C-m
tmux send-keys -t app "cd /var/www/html/Sff-backend" C-m
tmux send-keys -t app "python -m src.api" C-m

# Start the Gradio app in a new tmux window
tmux new-window -t app -n gradio
tmux send-keys -t app:gradio "conda activate demo_api_env" C-m
tmux send-keys -t app:gradio "cd /var/www/html/Sff-backend" C-m
tmux send-keys -t app:gradio "python -m src.app" C-m

# Start the Suno API in a new tmux window
tmux new-window -t app -n suno
tmux send-keys -t app:suno "cd /var/www/html/Sff-backend/suno-api" C-m
tmux send-keys -t app:suno "npm run dev" C-m

echo "ApplicationStart phase is complete, all apps are running."

