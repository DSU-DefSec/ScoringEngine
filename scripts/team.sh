#!/bin/bash
for team in {1..3}; do
    team_id=$((109+$team))
    perc=$(mysql -u root -pUnderWaterBlowFish -e "SELECT SUM(password='Password1!' OR password='password' OR password='bae' OR password='blade' AND team_id=$team_id)/COUNT(*) FROM scoring.credential")
    perc=$(echo $perc | cut -d ' ' -f 10)
    echo $team,$perc
done
