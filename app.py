import dbcreds
import mariadb
from flask import Flask, request, Response
import json
import sys
import uuid
# x = uuid.uuid4()
# print(x)
# y = str(x)[:10]
# print(y)

#instantiate Flask object
app = Flask(__name__)
######################### Function List #######################################
class MariaDbConnection:    
    def __init__(self):
        self.conn = None
        self.cursor = None
    try:
        def connect(self):
            self.conn = mariadb.connect(
            user=dbcreds.user, 
            password=dbcreds.password, 
            host=dbcreds.host, 
            port=dbcreds.port, 
            database=dbcreds.database)
            self.cursor = self.conn.cursor()
            return True
    
        def endConn(self):
            if (self.cursor != None):
                self.cursor.close()
            else:
                print("Cursor was never opened, nothing to close here.")
                if (self.conn != None):
                    self.conn.close()
                else:
                    print("Connection was never opened, nothing to close here.")
    except mariadb.OperationalError:
        print("Something wrong with the connection")

def getallUsers():
    cnnct_to_db = MariaDbConnection()
    cnnct_to_db.connect()
    getParams = request.args.get("id")
    print("This is GET params", getParams)
    
    if (getParams is None):
        cnnct_to_db.cursor.execute("SELECT * FROM user")
        list = cnnct_to_db.cursor.fetchall()
        user_list = []
        content = {}
        for result in list:
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
        #Check if cursor opened and close all connections
        cnnct_to_db.endConn()
        return Response(json.dumps(user_list),
                                    mimetype="application/json",
                                    status=200)
    elif (getParams is not None):
        cnnct_to_db.cursor.execute("SELECT * FROM user WHERE id =?", [getParams])
        userIdMatch = cnnct_to_db.cursor.fetchone()
        print(userIdMatch)
        user_list = []
        content = {}
        birthday = userIdMatch[5]
        birthdate = birthday.strftime("%Y-%m-%d")
        content = { 'username': userIdMatch[1],
                    'email' : userIdMatch[3],
                    'bio' : userIdMatch[4],
                    'birthdate' : birthdate,
                    'imageUrl' : userIdMatch[6],
                    'bannerUrl' : userIdMatch[7]
                    }       
        user_list.append(content)
        #Check if cursor opened and close all connections
        cnnct_to_db.endConn()
        return Response(json.dumps(user_list),
                                mimetype="application/json",
                                status=200)
    else:
        print("Incorrect GET function called")

def createNewUser():
    cnnct_to_db = MariaDbConnection()
    cnnct_to_db.connect()
    data = request.json
    print("Retrieved client data", data)
    client_email = data.get('email')
    client_username = data.get('username')
    client_password = data.get('password')
    client_bio = data.get('bio')
    client_birthdate = data.get('birthdate')
    
    resp = {
        "email": client_email,
        "username": client_username,
        "password": client_password,
        "bio": client_bio,
        "birthdate": client_birthdate,
        "imageUrl": data.get('imageUrl'),
        "bannerUrl": data.get('bannerUrl')
    }

    try:
        cnnct_to_db.cursor.execute("INSERT INTO user(email, username, password, birthdate) VALUES(?,?,?,?)",[client_email, client_username, client_password, client_birthdate])
        if(cnnct_to_db.cursor.rowcount == 1):
            print("New user register sucessful")
            cnnct_to_db.conn.commit()
        else:
            print("Failed to update")     
    except mariadb.DataError:
        print("Something is wrong with your data inputs")
    #Check if cursor opened and close all connections
    finally:
        cnnct_to_db.endConn()
    return Response(json.dumps(resp),
                            mimetype="application/json",
                            status=200)

def updateUserInfo():
    cnnct_to_db = MariaDbConnection()
    cnnct_to_db.connect()
    data = request.json
    client_loginToken = data.get('loginToken')
    #Get the user id from query
    try:
        cnnct_to_db.cursor.execute("SELECT user.id, username, email, bio, birthdate FROM user INNER JOIN user_session ON user_session.userId = user.id WHERE user_session.loginToken =?", [client_loginToken])
        id_match = cnnct_to_db.cursor.fetchone()

        print("ID matching", id_match)
    except mariadb.DataError:
        print("Something is wrong with client data inputs")
    
    for key in data:
        result = data[key]
        print("The key and value are {} = {}".format(key, result))
        if (key != 'loginToken'):
            cnnct_to_db.cursor.execute("UPDATE user SET ?=? WHERE id =?", [key,result,id_match[0]])
            if(cnnct_to_db.cursor.rowcount == 1):
                print("User updated sucessfully")
                cnnct_to_db.conn.commit()
            else:
                print("Failed to update")
        else:
            continue
    return Response(
                    mimetype="application/json",
                    status=200)
    
def deleteUser():
    cnnct_to_db = MariaDbConnection()
    cnnct_to_db.connect()
    data = request.json
    client_loginToken = data.get('loginToken')
    client_password = data.get('password')
    try:
        #checks password and logintoken are in the same row
        cnnct_to_db.cursor.execute("SELECT user.id FROM user INNER JOIN user_session ON user_session.userId = user.id WHERE user.password =? and user_session.loginToken =?",[client_password, client_loginToken])
        id_match = cnnct_to_db.cursor.fetchone()
        id_match = id_match[0]
        cnnct_to_db.cursor.execute("DELETE FROM user WHERE id=?",[id_match])
    
    except mariadb.DataError:
        print("Something is wrong with client data inputs") 
        
    if(cnnct_to_db.cursor.rowcount == 1):
        print("User deleted sucessfully")
        cnnct_to_db.conn.commit()
    else:
        print("Failed to update")

    #Check if cursor opened and close all connections
    cnnct_to_db.endConn()

    return Response(
                    mimetype="application/json",
                    status=200)

################################  End of functions #################################################

@app.route('/')
def homepage():
    return "<h1>Hello World</h1>"

@app.route('/api/users', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def usersApi():
    if (request.method == 'GET'):
        return getallUsers()
    elif (request.method == 'POST'):
        return createNewUser()    
    elif (request.method == 'PATCH'):
        return updateUserInfo()
    elif (request.method == 'DELETE'):
        return deleteUser()
    else:
        print("Something went wrong.")

#Debug / production environments
if (len(sys.argv) > 1):
    mode = sys.argv[1]
    if (mode == "production"):
        import bjoern
        host = '0.0.0.0'
        port = 5000
        print("Server is running in production mode")
        bjoern.run(app, host, port)
    elif (mode == "testing"):
        from flask_cors import CORS
        CORS(app)
        print("Server is running in testing mode")
        app.run(debug=True)
        #Should not have CORS open in production
    else:
        print("Invalid mode arugement, exiting")
        exit()
else:
    print ("No arguement was provided")
    exit()

