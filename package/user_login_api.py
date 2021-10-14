from package import app
from flask import request, Response
import mariadb
import dbcreds
import json

class MariaDbConnection:    
    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self):
        self.conn = mariadb.connect(
        user=dbcreds.user, 
        password=dbcreds.password, 
        host=dbcreds.host,
        port=dbcreds.port, 
        database=dbcreds.database)
        self.cursor = self.conn.cursor()

    def endConn(self):
        #Check if cursor opened and close all connections
        if (self.cursor != None):
            self.cursor.close()
        if (self.conn != None):
            self.conn.close()


def login_user():
    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()
    except ConnectionError:
        print("Error while attempting to connect to the database")

    #retrieve data from api call
    try:
        data = request.json
    except ValueError:
        print("ERROR, MISSING REQUIRED INPUTS")

    client_email = data.get('email')
    client_password = data.get('password')

    cnnct_to_db.cursor.execute("SELECT id, email, password FROM user WHERE email=? and password=?",[client_email,client_password])
    id_match = cnnct_to_db.cursor.fetchone()
    id_match = id_match[0]
    
    import uuid
    generateUuid = uuid.uuid4().hex
    str(generateUuid)

    try:
        cnnct_to_db.cursor.execute("INSERT INTO user_session (userId, loginToken) VALUES(?, ?)",[id_match, generateUuid])
        
        if(cnnct_to_db.cursor.rowcount == 1):
            cnnct_to_db.conn.commit()
        else:
            print("Failed to update")
        return Response("Logged in successfully",
                        mimetype="plain/text",
                        status=200)
    except mariadb.DataError:
        print("Something wrong with your data")
    except mariadb.IntegrityError:
        print("Your query would have broken the database and we stopped it")
    finally:
        cnnct_to_db.endConn()
    
def logout_user():
    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()
    except ConnectionError:
        print("Error while attempting to connect to the database")

    data = request.json
    client_loginToken = data.get('loginToken')

    cnnct_to_db.cursor.execute("DELETE FROM user_session WHERE loginToken=?", [client_loginToken])
    cnnct_to_db.endConn()

    return Response("Logged out successfully",
                        mimetype="plain/text",
                        status=200)
@app.route('/api/login', methods=['POST', 'DELETE'])
def loginApi():
    if (request.method == 'POST'):
        return login_user()
        
    elif (request.method == 'DELETE'):
        return logout_user()
    else:
        print("Something went wrong.")
