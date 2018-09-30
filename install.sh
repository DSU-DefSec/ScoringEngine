#!/bin/bash

install_common() {
    sudo apt-get update
    echo "Installing common files..."
    sudo apt-get install -y python3 python3-pip python-dev
    sudo pip3 install -U pip
    echo "Common files installed"
    echo "Configuring logging to /var/log/scoring.log ..."
    sudo cp install/scoring.syslog.conf /etc/rsyslog.d/
    sudo systemctl restart rsyslog
}

install_engine() {
    install_common
    echo "Installing engine..."
    echo "Installing dependencies..."
    sudo apt-get install -y freetds-dev libssl-dev libffi-dev libldap2-dev libsasl2-dev freerdp2-x11 smbclient
    sudo pip3 install dnspython paramiko pymysql pymssql pyldap requests
    echo "Creating score user..."
    sudo useradd -s /bin/bash score
    echo "Creating systemd service..."
    sudo cp install/scoring_engine.service /etc/systemd/system/
    sudo systemctl daemon-reload
    echo 'Engine Installed! Run: `systemctl start scoring_engine` to start'
}

install_db() {
    echo "Installing DB..."
    sudo apt install -y mysql-server
    echo "DB Installed!"
}

install_web() {
    install_common
    install_engine
    echo "Installing Web..."
    sudo apt-get install -y python3-tk nginx
    sudo pip3 install Flask flask-login flask-wtf bcrypt uwsgi
    echo "Creating web server systemd service..."
    sudo cp install/scoring_web.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo chown -R :www-data /opt/scoring/scoring/
    sudo chmod -R g+w /opt/scoring/scoring/
    echo "Creating rsync systemd service..."
    sudo cp install/rsyncd.service /etc/systemd/system/
    sudo systemctl daemon-reload
    echo "Configuring nginx..."
    sudo cp install/scoring.site /etc/nginx/sites-available/
    sudo ln -s /etc/nginx/sites-available/scoring.site /etc/nginx/sites-enabled/
    sudo rm /etc/nginx/sites-enabled/default
    sudo nginx -t
    sudo systemctl restart nginx
    echo 'Web Installed! Run :`systemctl start scoring_web` to start'
}

role=$1

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
