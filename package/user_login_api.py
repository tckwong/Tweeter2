from package import app
from flask import request, Response
import mariadb
import dbcreds

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

class InvalidToken(Exception):
    def __init__(self):
        super().__init__("Invalid loginToken sent")

def validate_client_data(list, data):
    for key in data.keys():
        if key in list:
            continue
        else:
            return False
    return True

def validate_token(token_input):
    try:
        if not (len(token_input) == 32):
            raise InvalidToken()
    except InvalidToken as error:
        raise error

def login_user():
    data = request.json
    check_data_lst = ["email", "password"]
    if not validate_client_data(check_data_lst,data):
        return Response("Incorrect data keys received",
                                    mimetype="text/plain",
                                    status=400)
    client_email = data.get('email')
    client_password = data.get('password')

    try:
        if type(client_email) != str or type(client_password) != str:
            raise TypeError()
    except TypeError:
        return Response("Invalid data sent!",
                        mimetype="text/plain",
                        status=400)
    
    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()

        cnnct_to_db.cursor.execute("SELECT id, email, password FROM user WHERE email=? and password=?",[client_email,client_password])
    except ConnectionError:
        print("Error while attempting to connect to the database")
        return Response("Error while attempting to connect to the database",
                        mimetype="text/plain",
                        status=444)  
    except mariadb.DataError:
        print("Something wrong with your data")
        return Response("Something wrong with your data",
                        mimetype="text/plain",
                        status=400)
    except mariadb.IntegrityError:
        print("Something wrong with your data")
        return Response("Something wrong with your data",
                        mimetype="text/plain",
                        status=400)
    
    id_match = cnnct_to_db.cursor.fetchone()
    #Only returns one row, so only one combination is valid
    if id_match == None:
        return Response("No matching login combination",
                        mimetype="plain/text",
                        status=400)
    else:
        id_match = id_match[0]
    
    #create unique login token
    import uuid
    generateUuid = uuid.uuid4().hex
    str(generateUuid)

    try:
        cnnct_to_db.cursor.execute("INSERT INTO user_session (userId, loginToken) VALUES(?, ?)",[id_match, generateUuid])
        cnnct_to_db.conn.commit()
    
    except mariadb.DataError:
        print("Something wrong with your data")
        return Response("Something wrong with your data",
                        mimetype="text/plain",
                        status=400)
    except mariadb.IntegrityError:
            print("Something wrong with your data")
            return Response("Something wrong with your data",
                            mimetype="text/plain",
                            status=400)
    finally:
        cnnct_to_db.endConn()

    return Response("Log in posted",
                    mimetype="text/plain",
                    status=200)

def logout_user():
    try:
        data = request.json
        checklist = ["password","loginToken"]
        if not validate_client_data(checklist,data):
            return Response("Incorrect data keys received",
                                    mimetype="text/plain",
                                    status=400)
                                    
        client_loginToken = data.get('loginToken')
        client_password = data.get('password')
        validate_token(client_loginToken)
        for item in checklist:
            if item is None:
                return Response("Error! Missing required data",
                            mimetype="text/plain",
                            status=400)
    except ValueError:
        return Response("Invalid data sent",
                                    mimetype="text/plain",
                                    status=400)
    except TypeError:
        return Response("Invalid data type sent",
                                    mimetype="text/plain",
                                    status=400)
    
    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()

        cnnct_to_db.cursor.execute("SELECT user.id, password, loginToken FROM user INNER JOIN user_session ON user_session.userId = user.id WHERE password=? and loginToken=?",[client_password,client_loginToken])
    except ConnectionError:
        print("Error while attempting to connect to the database")
        return Response("Error while attempting to connect to the database",
                        mimetype="text/plain",
                        status=444)  
    except mariadb.DataError:
        print("Something wrong with your data")
        return Response("Something wrong with your data",
                        mimetype="text/plain",
                        status=400)
    except mariadb.IntegrityError:
        print("Something wrong with your data")
        return Response("Something wrong with your data",
                        mimetype="text/plain",
                        status=400)
    
    match = cnnct_to_db.cursor.fetchone()
    #Only returns one row, so only one combination is valid
    if match == None:
        return Response("Incorrect data was received",
                        mimetype="plain/text",
                        status=400)

    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()
        cnnct_to_db.cursor.execute("DELETE FROM user_session WHERE userId=?", [match[0]])
        cnnct_to_db.conn.commit()
        return Response("Logged out successfully",
                        mimetype="text/plain",
                        status=200)
    except ConnectionError:
        print("Error while attempting to connect to the database")
        return Response("Error while attempting to connect to the database",
                        mimetype="text/plain",
                        status=444)  
    except mariadb.DataError:
        print("Something wrong with your data")
        return Response("Something wrong with your data",
                        mimetype="text/plain",
                        status=400)
    except mariadb.IntegrityError:
        print("Something wrong with your data")
        return Response("Something wrong with your data",
                        mimetype="text/plain",
                        status=400)
    finally:
        cnnct_to_db.endConn()

@app.route('/api/login', methods=['POST', 'DELETE'])
def login_api():
    if (request.method == 'POST'):
        return login_user()
        
    elif (request.method == 'DELETE'):
        return logout_user()
    else:
        print("Something went wrong.")
