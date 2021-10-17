from flask import request, Response
import mariadb
import json
import dbcreds
from package import app
import datetime

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
        super().__init__("Invalid loginToken received")

def validate_client_data(list, data):
    for key in data.keys():
        if key in list:
            continue
        else:
            return False
    return True

def validate_date(date_input):
    try:
        datetime.datetime.strptime(date_input, '%Y-%m-%d')
    except ValueError:
        return False
    return True

def validate_token(token_input):
    try:
        if not (len(token_input) == 32):
            raise InvalidToken()
    except InvalidToken as error:
        raise error

def check_type(mydict, data):
    for x in data.keys():
        found_key = mydict.get(x)
        if x != 'birthdate':
            chk = isinstance(data.get(x), found_key)
        if not chk:
            raise ValueError("Please check your inputs. Type error was found.")

def check_char_len(mydict, data):
    for item in data.keys():
        found_key = mydict.get(item)
        if(type(data.get(item)) == str and found_key != None):
            if(len(data.get(item)) > found_key):
                raise ValueError("Please check your inputs. Data is out of bounds")
def get_users():
    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()
    
    except ConnectionError:
        cnnct_to_db.endConn()
        return Response("Error while attempting to connect to the database",
                                    mimetype="text/plain",
                                    status=400)

    params = request.args
    params_id = request.args.get("id")
    checklist = ["id"]
    if not validate_client_data(checklist,params):
        return Response("Incorrect data keys received",
                            mimetype="text/plain",
                            status=400)

    if (params_id is None):
        cnnct_to_db.cursor.execute("SELECT * FROM user")
        list = cnnct_to_db.cursor.fetchall()
        user_list = []
        content = {}
        for result in list:
            birthdate = result[5].strftime("%Y-%m-%d")
            content = { 'id': result[0],
                        'username': result[1],
                        'email' : result[3],
                        'bio' : result[4],
                        'birthdate' : birthdate,
                        'imageUrl' : result[6],
                        'bannerUrl' : result[7]
                        }
            user_list.append(content)
        #Check if cursor opened and close all connections
        cnnct_to_db.endConn()
        return Response(json.dumps(user_list),
                                    mimetype="application/json",
                                    status=200)
    elif (params_id is not None):
        try:
            params_id = int(request.args.get("id"))
        except ValueError:
            return Response("Incorrect datatype received",
                                        mimetype="text/plain",
                                        status=400)
    
        if ((0< params_id<99999999)):
            cnnct_to_db.cursor.execute("SELECT * FROM user WHERE id =?", [params_id])
            userIdMatch = cnnct_to_db.cursor.fetchall()
            user_list = []
            content = {}
            for result in userIdMatch:
                birthdate_serialized = result[5].strftime("%Y-%m-%d")
                content = { 'username': result[1],
                            'email' : result[3],
                            'bio' : result[4],
                            'birthdate' : birthdate_serialized,
                            'imageUrl' : result[6],
                            'bannerUrl' : result[7]
                            }
            user_list.append(content)
            cnnct_to_db.endConn()
        else:
            cnnct_to_db.endConn()
            return Response("Invalid parameters. ID Must be an integer",
                                    mimetype="text/plain",
                                    status=400)

        return Response(json.dumps(user_list),
                                    mimetype="application/json",
                                    status=200)

def create_new_user():
    try:
        data = request.json
        checklist = ["email", "username","password","bio","birthdate","imageUrl","bannerUrl"]
        if not validate_client_data(checklist,data):
            return Response("Incorrect data keys received",
                                mimetype="text/plain",
                                status=400)
        dict={
            'email' : str,
            'username' : str,
            'password' : str,
            'bio' : str,
            'imageUrl' : str,
            'bannerUrl': str,
            }
        char_limit_dict = {
            'username': 20,
            'password':20,
            'email':20,
            'imageUrl' : 100,
            'bannerUrl' : 100
        }
        check_type(dict,data)
        check_char_len(char_limit_dict,data)
        
    except ValueError:
        return Response("Invalid data sent",
                                    mimetype="text/plain",
                                    status=400)
    client_email = data.get('email')
    client_username = data.get('username')
    client_password = data.get('password')
    client_bio = data.get('bio')
    client_birthdate = data.get('birthdate')
    client_imageUrl = data.get('imageUrl')
    client_bannerUrl = data.get('bannerUrl')

    #Checks for required data in DB
    if (client_email is None or client_username is None or client_password is None or client_birthdate is None):
        return Response("Error! Missing required data",
                        mimetype="text/plain",
                        status=400)
    #Checks birthdate format
    if not validate_date(client_birthdate):
        return Response("Invalid date format. Please check data inputs",
                        mimetype="text/plain",
                        status=400)
    resp = {
        "email": client_email,
        "username": client_username,
        "password": client_password,
        "bio": client_bio,
        "birthdate": client_birthdate,
        "imageUrl": client_imageUrl,
        "bannerUrl": client_bannerUrl
    }

    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()
        cnnct_to_db.cursor.execute("INSERT INTO user(email, username, password, birthdate, bio, imageUrl, bannerUrl) VALUES(?,?,?,?,?,?,?)",[client_email,client_username,client_password,client_birthdate,client_bio,client_imageUrl,client_bannerUrl])
        if(cnnct_to_db.cursor.rowcount == 1):
            cnnct_to_db.conn.commit()
        else:
            return Response("Failed to update",
                                mimetype="text/plain",
                                status=400)
        return Response(json.dumps(resp),
                                mimetype="application/json",
                                status=201)  
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

def update_user_info():
    data = request.json
    dict={  
            'loginToken':str,
            'email' : str,
            'username' : str,
            'password' : str,
            'bio' : str,
            'imageUrl' : str,
            'bannerUrl': str,
            }
    char_limit_dict = {
        'username': 20,
        'password':20,
        'email':20,
        'imageUrl' : 100,
        'bannerUrl' : 100
    }

    check_type(dict,data)
    check_char_len(char_limit_dict,data)
    client_loginToken = data.get('loginToken')
    validate_token(client_loginToken)

    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()
        cnnct_to_db.cursor.execute("SELECT user.id FROM user INNER JOIN user_session ON user_session.userId = user.id WHERE user_session.loginToken =?", [client_loginToken])
        id_match = cnnct_to_db.cursor.fetchone()
        if id_match == None:
            raise ValueError

    except ConnectionError:
        cnnct_to_db.endConn()
        print("Error while attempting to connect to the database")
        return Response("Error while attempting to connect to the database",
                                mimetype="text/plain",
                                status=444)  
    except mariadb.DataError:
        cnnct_to_db.endConn()
        print("Something wrong with your data")
        return Response("Something wrong with your data",
                                mimetype="text/plain",
                                status=400)
    except ValueError as error:
        cnnct_to_db.endConn()
        return Response("No match was found"+str(error),
                                mimetype="text/plain",
                                status=400)
    try:
        for key in data:
            result = data[key]
            if (key != 'loginToken'):
                if (key == "email"):
                    cnnct_to_db.cursor.execute("UPDATE user SET email =? WHERE user.id=?",[result,id_match[0]])
                elif (key == "username"):
                    cnnct_to_db.cursor.execute("UPDATE user SET username =? WHERE user.id=?",[result,id_match[0]])
                elif (key == "bio"):
                    cnnct_to_db.cursor.execute("UPDATE user SET bio =? WHERE user.id=?",[result,id_match[0]])
                else:
                    print("Error happened with inputs")

                if(cnnct_to_db.cursor.rowcount == 1):
                    cnnct_to_db.conn.commit()
                else:
                    return Response("Failed to update",
                                    mimetype="text/plain",
                                    status=400)
            else:
                continue
        
        cnnct_to_db.cursor.execute("SELECT * FROM user WHERE id=?", [id_match[0]])
        updated_user = cnnct_to_db.cursor.fetchone()
        resp =  {'id': updated_user[0],
                'username': updated_user[1],
                'email' : updated_user[3],
                'bio' : updated_user[4],
                'imageUrl' : updated_user[6],
                'bannerUrl' : updated_user[7]
                }
        cnnct_to_db.endConn()
        return Response(json.dumps(resp),
                        mimetype="application/json",
                        status=200)
    except ConnectionError:
        cnnct_to_db.endConn()
        return Response(json.dumps("Error while attempting to connect to the database"),
                                    mimetype="text/plain",
                                    status=400)
    except mariadb.DataError:
        cnnct_to_db.endConn()
        print("Something wrong with your data")
        return Response("Something wrong with your data",
                        mimetype="text/plain",
                        status=400)
    except mariadb.IntegrityError:
        cnnct_to_db.endConn()
        print("Something wrong with your data")
        return Response("Something wrong with your data",
                        mimetype="text/plain",
                        status=400)

def delete_user():
    try:                                
        data = request.json
        checklist = ["password","loginToken"]
        if not validate_client_data(checklist,data):
            return Response("Incorrect data keys received",
                                mimetype="text/plain",
                                status=400)
        
        char_limit_dict = {
            'password': 20,
        }
        check_char_len(char_limit_dict,data)
        
        client_loginToken = data.get('loginToken')
        validate_token(client_loginToken)
        client_password = data.get('password')
    except ValueError:
        return Response("Invalid data sent",
                                    mimetype="text/plain",
                                    status=400)
    for item in checklist:
        if item is None:
            return Response("Error! Missing required data",
                        mimetype="text/plain",
                        status=400)
    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()
        #checks password and logintoken are in the same row
        cnnct_to_db.cursor.execute("SELECT user.id FROM user INNER JOIN user_session ON user_session.userId = user.id WHERE user.password =? and user_session.loginToken =?",[client_password, client_loginToken])
        id_match = cnnct_to_db.cursor.fetchone()
        if id_match != None:
            id_match = id_match[0]
            cnnct_to_db.cursor.execute("DELETE FROM user WHERE id=?",[id_match])
            if(cnnct_to_db.cursor.rowcount == 1):
                print("User deleted sucessfully")
                cnnct_to_db.conn.commit()
            else:
                return Response("Failed to update",
                                mimetype="text/plain",
                                status=400)
        else:
            raise ValueError("Incorrect loginToken and password combination")
        cnnct_to_db.endConn()
        return Response("Sucessfully deleted",
                            mimetype="text/plain",
                            status=204)
    except ConnectionError:
        cnnct_to_db.endConn()
        print("Error while attempting to connect to the database")
        return Response("Error while attempting to connect to the database",
                        mimetype="text/plain",
                        status=444)
    except mariadb.DataError:
        cnnct_to_db.endConn()
        print("Something wrong with your data")
        return Response("Something wrong with your data",
                        mimetype="text/plain",
                        status=400)

@app.route('/api/users', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def users_api():
    if (request.method == 'GET'):
        return get_users()
    elif (request.method == 'POST'):
        return create_new_user()    
    elif (request.method == 'PATCH'):
        return update_user_info()
    elif (request.method == 'DELETE'):
        return delete_user()
    else:
        print("Something went wrong.")