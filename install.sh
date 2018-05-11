#!/bin/bash

install_common() {
    echo "Installing common files..."
    sudo apt-get install -y python3 python3-pip python-dev
    sudo pip3 install -U pip
    echo "Common files installed"
}

install_engine() {
    install_common
    echo "Installing engine..."
    sudo apt-get install -y freetds-dev libssl-dev libffi-dev libldap2-dev libsasl2-dev freerdp
    sudo pip3 install dnspython paramiko pysmb pymysql pymssql pyldap requests
    echo "Engine Installed!"
}

install_db() {
    echo "Installing DB..."
    sudo apt install -y mysql-server
    echo "DB Installed!"
}

install_web() {
    install_common
    echo "Installing Web..."
    sudo apt-get install -y python3-tk
    sudo pip3 install Flask flask-login flask-wtf matplotlib bcrypt
    echo "Web Installed!"
}

role=$1
sudo apt-get update

if [ "$role" == "engine" ]; then
    install_engine
elif [ "$role" == "db" ]; then
    install_db
elif [ "$role" == "web" ]; then
    install_web
elif [ "$role" == "all" ]; then
    install_engine
    install_db
    install_web
else
    echo "Usage: ./install [engine | db | web | all]"
fi
