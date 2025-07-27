#!/bin/bash
cd "$(dirname "$0")"
cd ../../..
source venv/bin/activate
python3 src/main.py
