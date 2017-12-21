#!/bin/bash
sudo apt-get update
sudo apt-get install -y mysql-server python3 python3-pip python-dev python3-tk freetds-dev libssl-dev libffi-dev libldap2-dev libsasl2-dev freerdp
sudo pip3 install -U pip
sudo pip3 install dnspython paramiko pysmb pymysql pymssql pyldap requests Flask flask-login flask-wtf matplotlib bcrypt
