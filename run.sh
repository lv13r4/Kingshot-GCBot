#!/bin/bash
if [ ! -d "venv" ]; then
    echo "Setup not found. Running setup..."
    chmod +x setup_pi.sh
    ./setup_pi.sh
fi

echo "Starting KS Bot..."
venv/bin/python ksapp.py
