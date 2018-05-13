#!/bin/bash

export FLASK_APP=web/server.py
python3 -m flask run --host 0.0.0.0 --port 8000
