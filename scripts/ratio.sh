#!/bin/bash
perc=$(mysql -u root -pPassword1! -e "SELECT SUM(password='Password1!')/COUNT(*) AS perc FROM scoring.credential")
echo $perc
perc=$(echo $perc | cut -d ' ' -f 2)
date=$(date +%H:%M:%S)
echo $date,$perc >> /home/dsu/default.csv
