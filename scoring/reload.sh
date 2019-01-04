#!/bin/bash
service scoring_engine stop
./load_config.py configs/CyberConquest_18-11-18.yaml
service scoring_engine start
