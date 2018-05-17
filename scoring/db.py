import pymysql

host='192.168.2.3'
user='root'
password='Password1!'

def connect():
    """
    Connect to the MySQL database with the globally defined
    credentials and host.

    Returns:
        Connection: A connection to the database
    """
    connection = pymysql.connect(host=host, 
            user=user, password=password)
    return connection

def get(table, columns, where=None, orderby=None, args=None):
    """
    Execute a SELECT statement on the database and return the matching columns.

    Arguments:
        table (str): Table to SELECT data from
        columns (str): Columns to get
        where (str): Optional, MySQL WHERE statement
        orderby (str): Optional, MySQL ORDER BY statement
        args (Tuple(str)): Optional, arguments for a prepared statement

    Returns:
        List(List(object)): List of rows which match the SELECT statement
    """
    # Build command
    columns = ','.join(columns)
    cmd = 'SELECT %s FROM %s' % (columns, table)
    if where is not None:
        cmd += ' WHERE ' + where
    if orderby is not None:
        cmd += ' ORDER BY ' + orderby

    # Execute command
    connection = connect()
    with connection.cursor() as cursor:
        cursor.execute('USE scoring')
        cursor.execute(cmd, args)
        rows = cursor.fetchall()
    connection.close()
    return rows

def getall(table):
    """
    Get all rows from the given table.

    Arguments:
        table (str): The table to get rows from

    Returns:
        List(List(object)): List of all rows in the table
    """
    rows = get(table, ['*'])
    return rows

def execute(cmd, args=None):
    """
    Execute a MySQL command on the database.

    Arguments:
        cmd (str): MySQL command to execute
        args (Tuple(str)): Optional, arguments for a prepared statement

    Returns:
        int: The ID of the last row created or modified by the command
    """
    connection = connect()
    with connection.cursor() as cursor:
        cursor.execute('USE scoring')
        cursor.execute(cmd, args)
        lid = cursor.lastrowid
    connection.commit()
    connection.close()
    return lid

def reset_table(table):
    """
    Delete all rows from the given table.

    Arguments:
        table (str): Table to delete all data from
    """
    execute('DELETE FROM %s' % table)

def reset_all_tables():
    """
    Delete all data from all tables in the database.
    """
    reset_table('settings')
    reset_table('team')
    reset_table('users')
    reset_table('domain')
    reset_table('service')
    reset_table('service_check')
    reset_table('check_io')
    reset_table('credential')
    reset_table('result')

def insert(table, columns, args):
    """
    Insert data into the given table.

    Arguments:
        table (str): The table to insert data into
        columns (List(str)): List of columns identifying the data
        args (List(str)): List of pieces of data corresponding to the columns

    Returns:
        int: The ID of the inserted row 
    """
    columns = ','.join(columns)
    vals = ', '.join(['%s']*len(args))
    cmd = 'INSERT INTO %s (%s)' % (table, columns)
    cmd += ' VALUES (%s)' % vals
    id = execute(cmd, args)
    return id

def modify(table, set, args, where=None):
    """
    Modify the given columns in the given table matching the given criteria.

    Arguments:
        table (str): The table to modify
        set (str): The fields to modify (field1=%s, field2=%s)
        where (str): The matching criteria
    """
    cmd = 'UPDATE %s SET %s' % (table, set)
    if where is not None:
        cmd += ' WHERE %s' % where
    execute(cmd, args)

def set_credential_password(username, password, team_id, service_id=None, domain_id=None):
    """
    Set the password for the credentials matching the given criteria.

    Arguments:
        username (str): The username of the credentials
        password (str): The password to change to
        team_id (str): The ID of the team of the credentials
        service_id (str): Optional, the ID of the service of the credentials. service_id and domain_id cannot both be None
        domain_id (str): Optional, the ID of the domain of the credentials. service_id and domain_id cannot both be None
    """
    if service_id is None and domain_id is None:
        raise Exception('service_id and domain_id cannot both be None.')
    cmd = 'UPDATE credential SET password=%s WHERE username=%s AND team_id=%s'
    if service_id is not None:
        cmd += ' AND service_id=%s'
        execute(cmd, (password, username, team_id, service_id))
    else:
        cmd += ' AND domain_id=%s'
        execute(cmd, (password, username, team_id, domain_id))
