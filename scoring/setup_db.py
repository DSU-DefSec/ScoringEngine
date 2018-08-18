#!/usr/bin/python3
import db

if __name__ == '__main__':
    connection = db.connect()
    
    with connection.cursor() as cursor:
        # Delete old db
        cmd = "DROP DATABASE IF EXISTS scoring"
        print(cmd)
        cursor.execute(cmd)
    
        # Create new db
        cmd = "CREATE DATABASE scoring"
        print(cmd)
        cursor.execute(cmd)
    
        # Use db
        cmd = "USE scoring"
        print(cmd)
        cursor.execute(cmd)
    
        ## Create tables
        # Settings table
        cmd = ("CREATE TABLE settings ( "
               "id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, "
               "skey VARCHAR(255) NOT NULL, "
               "value VARCHAR(255) NOT NULL)")
        print(cmd)
        cursor.execute(cmd)
    
        # Team Table
        cmd = ("CREATE TABLE team ( "
               "id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, "
               "name VARCHAR(255) NOT NULL UNIQUE, "
               "subnet VARCHAR(15) NOT NULL, "
               "netmask VARCHAR(15) NOT NULL)")
        print(cmd)
        cursor.execute(cmd)
    
        # Users table
        cmd = ("CREATE TABLE users ( "
           "id INT AUTO_INCREMENT PRIMARY KEY, "
           "username VARCHAR(255), "
           "password CHAR(60) NOT NULL, "
           "team_id INT, "
           "is_admin BOOL NOT NULL, "
           "FOREIGN KEY (team_id) REFERENCES team(id) "
               "ON DELETE CASCADE)")
        print(cmd)
        cursor.execute(cmd)
    
        # Service Table
        cmd = ("CREATE TABLE service ( "
            "id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, "
            "host INT NOT NULL, "
            "port INT NOT NULL)")
        print(cmd)
        cursor.execute(cmd)
    
        # Check Table
        cmd = ("CREATE TABLE service_check ( "
            "id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, "
            "name VARCHAR(255) NOT NULL UNIQUE, "
            "check_function VARCHAR(255) NOT NULL, "
            "poller VARCHAR(255) NOT NULL, "
            "service_id INT NOT NULL, "
            "FOREIGN KEY (service_id) REFERENCES service(id) "
                "ON DELETE CASCADE)")
        print(cmd)
        cursor.execute(cmd)
    
        # Domain Table
        cmd = ("CREATE TABLE domain ( "
            "id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, "
            "fqdn VARCHAR(256) NOT NULL UNIQUE)")
        print(cmd)
        cursor.execute(cmd)
    
        # Check Input Table
        cmd = ("CREATE TABLE check_io ( "
            "id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, "
            "input VARCHAR(4095) NOT NULL, "
            "expected VARCHAR(4095) NOT NULL, "
            "check_id INT NOT NULL, "
            "FOREIGN KEY (check_id) REFERENCES service_check(id) "
                "ON DELETE CASCADE)")
        print(cmd)
        cursor.execute(cmd)
    
        # Credential Table
        cmd = ("CREATE TABLE credential ( "
            "id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, "
            "username VARCHAR(255) NOT NULL, "
            "password VARCHAR(255) NOT NULL, "
            "team_id INT NOT NULL, " 
            "service_id INT NOT NULL, "
            "domain_id INT, "
            "FOREIGN KEY (team_id) REFERENCES team(id) "
                "ON DELETE CASCADE, "
            "FOREIGN KEY (service_id) REFERENCES service(id) "
                "ON DELETE CASCADE, "
            "FOREIGN KEY (domain_id) REFERENCES domain(id) "
                "ON DELETE CASCADE)")
        print(cmd)
        cursor.execute(cmd)
    
        # Credential <-> Check IO Relationship Table
        cmd = ("CREATE TABLE cred_input ( "
            "id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, "
            "cred_id INT NOT NULL, "
            "check_io_id INT NOT NULL, "
            "FOREIGN KEY (cred_id) REFERENCES credential(id) "
                "ON DELETE CASCADE, "
            "FOREIGN KEY (check_io_id) REFERENCES check_io(id) "
                "ON DELETE CASCADE)")
        print(cmd)
        cursor.execute(cmd)
    
        # Result Table
        cmd = ("CREATE TABLE result ( "
            "id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, "
            "check_id INT NOT NULL, "
            "check_io_id INT NOT NULL, "
            "team_id INT NOT NULL, "
            "time TIMESTAMP NOT NULL, "
            "poll_input VARCHAR(4095) NOT NULL, "
            "poll_result VARCHAR(4095) NOT NULL, "
            "result BOOL NOT NULL, "
            "FOREIGN KEY (check_id) REFERENCES service_check(id) "
                "ON DELETE CASCADE, "
            "FOREIGN KEY (check_io_id) REFERENCES check_io(id) "
                "ON DELETE CASCADE, "
            "FOREIGN KEY (team_id) REFERENCES team(id) "
                "ON DELETE CASCADE)")
        print(cmd)
        cursor.execute(cmd)

        # Password change request table
        cmd = ("CREATE TABLE pcr ( "
            "id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, "
            "team_id INT NOT NULL, "
            "service_id INT, "
            "domain_id INT, "
            "submitted TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
            "completed TIMESTAMP NULL, "
            "status INT NOT NULL, "
            "creds TEXT NOT NULL, "
            "team_comment VARCHAR(4095) DEFAULT '', "
            "admin_comment VARCHAR(4095) DEFAULT '', "
            "FOREIGN KEY (team_id) REFERENCES team(id) "
                "ON DELETE CASCADE, "
            "FOREIGN KEY (service_id) REFERENCES service(id) "
                "ON DELETE CASCADE, "
            "FOREIGN KEY (domain_id) REFERENCES domain(id) "
                "ON DELETE CASCADE)")
        print(cmd)
        cursor.execute(cmd)
    
        connection.commit()
        connection.close()
