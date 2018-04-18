#!/bin/bash
for team in {1..4}; do
    perc=$(mysql -u root -pPassword1! -e "SELECT SUM(password='Password1!' AND team_id=$team)/SUM(team_id=$team) AS perc FROM scoring.credential")
    perc=$(echo $perc | cut -d ' ' -f 2)
    date=$(date +%H:%M:%S)
    echo $date,$perc >> /home/dsu/team_"$team"_default.csv
done
