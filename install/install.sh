#!/bin/bash

################################################
# DSU-DefSecClub Scoring Engine Install Script #
################################################

# Color codes
plus="\033[1;32m[+]\e[m"
warn="\033[1;33m[!]\e[m"
err="\033[1;31m{!]\e[m"

# Root check
if ! [[ $EUID -eq 0 ]]; then
   echo -e "${err} Install script must be run with sudo (sudo ./install.sh)"
   exit 1
fi

if ! [ -z ${1+x} ]; then
    echo "Usage: ./install.sh"
fi

INSTALL_DIR=$(dirname $PWD)

# Update package list and set list to check if package needs updating
echo -e "$plus Updating package list..."
apt update
NEEDS_UPGRADE=$(/usr/lib/update-notifier/apt-check -p 2>&1 >/dev/null | grep "^$1$" | wc -l)


# Check if a package is installed before trying to install it
install_package() {
    if ! (dpkg -l $1 > /dev/null 2>&1); then    
        apt install -y $1  > /dev/null 2>&1 && echo -e "\t$plus Successfully installed $1." || echo -e "\t$err Installing $1 failed!"
    else
        if (echo $NEEDS_UPGRADE 2>&1 >/dev/null | grep -q "^$1$"); then
            apt install -y $1 && echo -e "\t$plus Successfully upgraded $1." || echo -e "\t$err Upgrading $1 failed!"
        else
            echo -e "\t$plus Package $1 is already installed and upgraded."
        fi
    fi
}

echo -e "\n$plus Installing dependencies..."
    install_package python3
    install_package python3-pip
    install_package python3-dev
    install_package libsasl2-dev
    install_package freetds-dev
    install_package libssl-dev
    install_package libffi-dev
    install_package libldap2-dev
    install_package freerdp2-x11
    install_package smbclient
    pip3 install -U dnspython paramiko pymysql pymssql pyldap requests timeout-decorator bs4
    echo -e "$plus Common files installed"

echo -e "$plus Installing database (mysql-server)..."
    install_package mysql-server
echo -e "$plus Configuring database..."
    mysql -u root < schema.sql
    while true; do
        read -s -p "New password for database user 'scoring': " mysqlpass
	echo
        read -s -p "Confirm password for database user 'scoring': " mysqlpassconf
	echo
        if [[ $mysqlpass == $mysqlpassconf ]]; then
            break
        else
    	echo "Passwords did not match. Please try again."
        fi
    done
    mysql -u root -e "CREATE USER scoring@'localhost' IDENTIFIED BY '$mysqlpass'"
    mysql -u root -e "GRANT ALL PRIVILEGES ON scoring.* to scoring@'localhost'"
    sed -i "s/PASSWORD_HERE/$mysqlpass/" $INSTALL_DIR/etc/db.yaml

echo -e "$plus Installing web software..."
    install_package python3-tk
    install_package nginx
    pip3 install Flask flask-login flask-wtf bcrypt uwsgi
    sed -i "s.INSTALL_DIR.$INSTALL_DIR.g" $INSTALL_DIR/etc/uwsgi.ini

echo -e "$plus Configuring nginx..."
    cp scoring.site /etc/nginx/sites-available/
    sed -i "s.INSTALL_DIR.$INSTALL_DIR.g" /etc/nginx/sites-available/scoring.site
    rm /etc/nginx/sites-enabled/scoring.site
    ln -s /etc/nginx/sites-available/scoring.site /etc/nginx/sites-enabled/
    if [ -f /etc/nginx/sites-enabled/default ]; then rm /etc/nginx/sites-enabled/default; fi 

echo -e "$plus Creating services..."
    cp scoring_web.service /etc/systemd/system/
    sed -i "s.INSTALL_DIR.$INSTALL_DIR.g" /etc/systemd/system/scoring_web.service
    cp scoring_engine.service /etc/systemd/system/
    sed -i "s.INSTALL_DIR.$INSTALL_DIR.g" /etc/systemd/system/scoring_engine.service
    chown -R :www-data $INSTALL_DIR/
    chmod -R g+w $INSTALL_DIR

echo -e "$plus Configuring logging to /var/log/scoring.log..."
    cp scoring.syslog.conf /etc/rsyslog.d/
    if ! (grep -q "score" /etc/passwd); then
        echo -e "$plus Creating score user..."
        useradd -s /bin/bash score && echo -e "$plus Created user." || echo -e "$err Failed to create user!"
    fi

# Start all the services
echo -e "$plus Starting services..."
systemctl daemon-reload
systemctl restart rsyslog
systemctl restart nginx

echo -e "\n$plus ScoringEngine set up! To start, run:"
echo -e "\t ./load_config.py config_file"
echo -e "\t systemctl start scoring_engine scoring_web\n"
echo -e "$plus To interact or view the engine, navigate to:"
echo -e "\t http://127.0.0.1\n"
