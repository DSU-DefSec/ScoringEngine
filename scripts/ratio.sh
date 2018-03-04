#!/bin/bash
perc=$(mysql -u root -pUnderWaterBlowFish -e "SELECT SUM(password='Password1!' OR password='password' OR password='bae' OR password='blade')/COUNT(*) FROM scoring.credential")
perc=$(echo $perc | cut -d ' ' -f 8)
date=$(date +%H:%M:%S)
echo $date,$perc >> /root/default.csv
