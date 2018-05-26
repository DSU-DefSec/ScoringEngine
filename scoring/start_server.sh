#!/bin/bash

if [ ! -f /var/run/rsyncd.pid ]; then
    sudo rsync --daemon --config rsyncd.conf
fi

export FLASK_APP=web/server.py
python3 -m flask run --host 0.0.0.0 --port 8000
