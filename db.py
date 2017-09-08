import pymysql

def connect():
    connection = pymysql.connect(host='localhost', 
            user='root', password='toor')
    return connection

def get(cmd):
    connection = connect()
    with connection.cursor() as cursor:
        cursor.execute('USE scoring')
        cursor.execute(cmd)
        rows = cursor.fetchall()
    connection.close()
    return rows

def execute(cmd):
    connection = connect()
    with connection.cursor() as cursor:
        cursor.execute('USE scoring')
        cursor.execute(cmd)
        lid = cursor.lastrowid
    connection.commit()
    connection.close()
    return lid
