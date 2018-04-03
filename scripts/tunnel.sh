#!/bin/bash
ip='34.218.76.205'
autossh -f -M 20000 -N -R :48731:localhost:8080 webproxyuser@"$ip"
