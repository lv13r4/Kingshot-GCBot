#!/bin/bash
if [ ! -d "venv" ]; then
    echo "Setup not found. Running setup..."
    chmod +x INSTALL_ON_LINUX.sh
    ./INSTALL_ON_LINUX.sh
fi

echo "Starting KS Bot..."
venv/bin/python ksapp.py
