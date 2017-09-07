import pymysql

#connection = db.connect()
connection = pymysql.connect(host='localhost', user='root', password='toor')

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
   # Team Table
    cmd = ("CREATE TABLE team ( "
        "id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, "
        "name VARCHAR(255) NOT NULL UNIQUE, "
        "subnet VARCHAR(15) NOT NULL UNIQUE)")
    print(cmd)
    cursor.execute(cmd)

    # Service Table
    cmd = ("CREATE TABLE service ( "
        "id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, "
        "host INT NOT NULL, "
        "port INT NOT NULL)")
    print(cmd)
    cursor.execute(cmd)

    # Check Input Table
    cmd = ("CREATE TABLE service_check ( "
        "id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, "
        "check_function TEXT NOT NULL, "
        "poller TEXT NOT NULL, "
        "service_id INT NOT NULL, "
        "FOREIGN KEY (service_id) REFERENCES service(id) "
            "ON DELETE CASCADE)")
    print(cmd)
    cursor.execute(cmd)

    # Check Input Table
    cmd = ("CREATE TABLE check_input ( "
        "id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, "
        "input TEXT NOT NULL, "
        "expected TEXT NOT NULL, "
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
        "FOREIGN KEY (team_id) REFERENCES team(id) "
            "ON DELETE CASCADE)")
    print(cmd)
    cursor.execute(cmd)

    # Credential <-> CheckInput Relationship Table
    cmd = ("CREATE TABLE cred_input ( "
        "id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, "
        "cred_id INT NOT NULL, "
        "check_input_id INT NOT NULL, "
        "FOREIGN KEY (cred_id) REFERENCES credential(id) "
            "ON DELETE CASCADE, "
        "FOREIGN KEY (check_input_id) REFERENCES check_input(id) "
            "ON DELETE CASCADE)")
    print(cmd)
    cursor.execute(cmd)

    # Result Table
    cmd = ("CREATE TABLE result ( "
        "id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, "
        "check_id INT NOT NULL, "
        "team_id INT NOT NULL, "
        "time TIMESTAMP NOT NULL, "
        "result BOOL NOT NULL, "
        "FOREIGN KEY (check_id) REFERENCES service_check(id) "
            "ON DELETE CASCADE, "
        "FOREIGN KEY (team_id) REFERENCES team(id) "
            "ON DELETE CASCADE)")
    print(cmd)
    cursor.execute(cmd)

    connection.commit()
    connection.close()
