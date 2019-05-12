#!/bin/bash

sudo systemctl stop scoring_web scoring_engine
mysql -u root -p < schema.sql
./load_config.py configs/short-config.yaml
sudo systemctl start scoring_web scoring_engine
