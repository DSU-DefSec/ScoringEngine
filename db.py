import pymysql

host='127.0.0.1'
user='root'
password='toor'

def connect():
    connection = pymysql.connect(host=host, 
            user=user, password=password)
    return connection

def get(cmd, args=None):
    connection = connect()
    with connection.cursor() as cursor:
        cursor.execute('USE scoring')
        cursor.execute(cmd, args)
        rows = cursor.fetchall()
    connection.close()
    return rows

def execute(cmd, args=None):
    print(cmd)
    connection = connect()
    with connection.cursor() as cursor:
        cursor.execute('USE scoring')
        cursor.execute(cmd, args)
        lid = cursor.lastrowid
    connection.commit()
    connection.close()
    return lid
