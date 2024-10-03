#!/bin/bash
# This script runs before the installation phase

# Update and upgrade the system packages
sudo apt-get update -y
sudo apt-get upgrade -y

# Install dependencies like Python, Pip, or any others needed
sudo apt-get install -y python3-pip
sudo apt-get install -y tmux

# Optional: Install Conda if needed
# wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh
# bash ~/miniconda.sh -b -p $HOME/miniconda
# eval "$($HOME/miniconda/bin/conda shell.bash hook)"

echo "Before Install phase is complete."

