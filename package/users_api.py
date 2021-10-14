from flask import request, Response
import mariadb
import json
import dbcreds
from package import app
import datetime

class CustomError(Exception):
    pass
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

def validate_date(date_input):
    try:
        datetime.datetime.strptime(date_input, '%Y-%m-%d')
    except CustomError:
        print("Invalid date format")
        return Response("Invalid date format",
                                    mimetype="text/plain",
                                    status=400)
def validate_token(token_input):
    try:
        len(token_input) == 32
    except CustomError:
        return Response("Invalid LoginToken",
                                    mimetype="text/plain",
                                    status=403)                  
def get_users():
    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()
    
    except ConnectionError:
        cnnct_to_db.endConn()
        return Response("Error while attempting to connect to the database",
                                    mimetype="text/plain",
                                    status=400)

    try:    
        getParams = request.args.get("id")
    except CustomError:
        return Response("Invalid data sent",
                                    mimetype="text/plain",
                                    status=400)         
    #data input check        
    if (getParams is None):
        cnnct_to_db.cursor.execute("SELECT * FROM user")
        list = cnnct_to_db.cursor.fetchall()
        user_list = []
        content = {}
        for result in list:
            birthday = result[5]
            birthdate = birthday.strftime("%Y-%m-%d")
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
    elif (getParams is not None):
        try:
            getParams = int(getParams)
        except CustomError:
            return Response("Invalid parameters. Must be an integer, and a valid id",
                                    mimetype="text/plain",
                                    status=400)

        if (type(getParams) == int and getParams > 0):    
            cnnct_to_db.cursor.execute("SELECT * FROM user WHERE id =?", [getParams])
            userIdMatch = cnnct_to_db.cursor.fetchall()
    
            user_list = []
            content = {}
            for result in userIdMatch:
                birthday = result[5]
                birthdate = birthday.strftime("%Y-%m-%d")
                content = { 'username': result[1],
                            'email' : result[3],
                            'bio' : result[4],
                            'birthdate' : birthdate,
                            'imageUrl' : result[6],
                            'bannerUrl' : result[7]
                            }
            user_list.append(content)
            cnnct_to_db.endConn()
        else:
            cnnct_to_db.endConn()
            return Response("Invalid data input",
                                    mimetype="text/plain",
                                    status=400)

        return Response(json.dumps(user_list),
                                    mimetype="application/json",
                                    status=200)

def create_new_user():
    try:
        data = request.json
    except CustomError:
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

    if (client_email is None or client_username is None or client_password is None or client_birthdate is None):
        return Response("Error! Missing required data",
                        mimetype="text/plain",
                        status=400)
    validate_date(client_birthdate)
    
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
            print("New user register sucessful")
            cnnct_to_db.conn.commit()
        else:
            print("Failed to update") 
        
        return Response(json.dumps(resp),
                                mimetype="application/json",
                                status=200)    
    except ConnectionError:
        print("Error while attempting to connect to the database")
    except mariadb.DataError:
        print("Something wrong with your data")
    except mariadb.IntegrityError:
        print("Your query would have broken the database and we stopped it")
    finally:
        cnnct_to_db.endConn()


def update_user_info():
    data = request.json
    print(data)
    client_loginToken = data.get('loginToken')
    validate_token(client_loginToken)
    print("should not show")

    content= {
        "pie" : "good"
    }

    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()
        cnnct_to_db.cursor.execute("SELECT user.id FROM user INNER JOIN user_session ON user_session.userId = user.id WHERE user_session.loginToken =?", [client_loginToken])
        id_match = cnnct_to_db.cursor.fetchone()

        print("ID matching?", id_match)
    except mariadb.DataError:
        print("Something is wrong with client data inputs")
    
    try:
        for key in data:
            result = data[key]
            if (key != 'loginToken'):
                print("this is the raw result",result)
                print("this is the raw key",key)
                if (key == "email"):
                    cnnct_to_db.cursor.execute("UPDATE user SET email =? WHERE user.id=?",[result,id_match[0]])
                elif (key == "username"):
                    cnnct_to_db.cursor.execute("UPDATE user SET username =? WHERE user.id=?",[result,id_match[0]])
                elif (key == "bio"):
                    cnnct_to_db.cursor.execute("UPDATE user SET bio =? WHERE user.id=?",[result,id_match[0]])
                else:
                    print("Error happened with inputs")
                if(cnnct_to_db.cursor.rowcount == 1):
                    print("User updated sucessfully")
                    cnnct_to_db.conn.commit()
                else:
                    print("Failed to update")
            else:
                continue
            #Check if cursor opened and close all connections
            cnnct_to_db.endConn()
            
            return Response(json.dumps(content),
                            mimetype="application/json",
                            status=200)
    except ConnectionError:
        return Response(json.dumps("Error while attempting to connect to the database"),
                                    mimetype="text/plain",
                                    status=400)
    except mariadb.DataError:
        print("Something is wrong with client data inputs")
    finally:
        cnnct_to_db.endConn()
    
def delete_user():
    
    data = request.json
    client_loginToken = data.get('loginToken')
    client_password = data.get('password')
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
                print("Failed to update")
        else:
            raise ValueError("Incorrect loginToken and password combination")
            
    except ConnectionError:
        print("Error while attempting to connect to the database")
        cnnct_to_db.endConn()
    except mariadb.DataError:
        print("Something is wrong with client data inputs") 
        
    #Check if cursor opened and close all connections
    cnnct_to_db.endConn()
    return Response(
                    mimetype="plain/text",
                    status=200)
    

@app.route('/api/users', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def usersApi():
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