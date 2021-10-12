import dbcreds
import mariadb
from flask import Flask, request, Response
import json
import sys

#instantiate Flask object
app = Flask(__name__)
######################### Function List #######################################
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
        # raise ConnectionError("Failed to connect to the database")
                
def get_users():
    cnnct_to_db = MariaDbConnection()
    cnnct_to_db.connect()
    getParams = int(request.args.get("id"))
    #data input check        
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
        if (type(getParams) == int and getParams > 0):    
            cnnct_to_db.cursor.execute("SELECT * FROM user WHERE id =?", [getParams])
            userIdMatch = cnnct_to_db.cursor.fetchall()
            print(userIdMatch)
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
            print(content)
            cnnct_to_db.endConn()
        else:
            print("Something went wrong")
            cnnct_to_db.endConn()
            return Response(json.dumps("Invalid data input"),
                                    mimetype="text/plain",
                                    status=400)

        return Response(json.dumps(user_list),
                                    mimetype="application/json",
                                    status=200)

def create_new_user():
    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()
        data = request.json
        
        client_email = data.get('email')
        client_username = data.get('username')
        client_password = data.get('password')
        client_bio = data.get('bio')
        client_birthdate = data.get('birthdate')
        client_imageUrl = data.get('imageUrl')
        client_bannerUrl = data.get('bannerUrl')

        resp = {
            "email": client_email,
            "username": client_username,
            "password": client_password,
            "bio": client_bio,
            "birthdate": client_birthdate,
            "imageUrl": client_imageUrl,
            "bannerUrl": client_bannerUrl
        }

        if (resp["email"] is None or resp["username"] is None or resp["password"] is None or resp["bio"] is None or resp["birthdate"] is None):
            return Response("Error! Missing required data",
                            mimetype="text/plain",
                            status=400)

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
    cnnct_to_db = MariaDbConnection()
    cnnct_to_db.connect()
    data = request.json
    client_loginToken = data.get('loginToken')
    #Get the user id from query
    try:
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
            return Response(
                            mimetype="application/json",
                            status=200)
    except mariadb.DataError:
        print("Something is wrong with client data inputs")
    finally:
        if (cnnct_to_db.cursor != None):
            cnnct_to_db.cursor.close()

        if (cnnct_to_db.conn != None):
            cnnct_to_db.conn.rollback()
            cnnct_to_db.conn.close()
    
def delete_user():
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
######### #########Login API ############################
# def login_user():
#     cnnct_to_db = MariaDbConnection()
#     cnnct_to_db.connect()

#     data = request.json
#     client_email = data.get('email')
#     client_password = data.get('password')
#     if not client_email or not client_password:
#         raise ValueError("ERROR, MISSING REQUIRED INPUTS")
        
#     cnnct_to_db.cursor.execute("SELECT id, email, password FROM user WHERE email=? and password=?",[client_email,client_password])
#     id_match = cnnct_to_db.cursor.fetchone()
#     id_match = id_match[0]
#     print("id is", id_match)
    
#     import uuid
#     generateUuid = uuid.uuid4().hex
#     str(generateUuid)

#     try:
#         cnnct_to_db.cursor.execute("INSERT INTO user_session (userId, loginToken) VALUES(?, ?)",[id_match, generateUuid])
        
#         if(cnnct_to_db.cursor.rowcount == 1):
#             cnnct_to_db.conn.commit()
#         else:
#             print("Failed to update")
#         return Response("Logged in successfully",
#                         mimetype="plain/text",
#                         status=200)
#     except mariadb.DataError:
#         print("Something wrong with your data")
#     except mariadb.IntegrityError:
#         print("Your query would have broken the database and we stopped it")
#     finally:
#         cnnct_to_db.endConn()

# from package import user_login_mod
# user_login_mod.login_user()


################################################################################
######Tweet API functions#############
def get_tweets():
    cnnct_to_db = MariaDbConnection()
    cnnct_to_db.connect()
    getParams = request.args.get("id")
    #data input check
    if (getParams is None):
        cnnct_to_db.cursor.execute("SELECT * FROM tweet")
        list = cnnct_to_db.cursor.fetchall()
        tweet_list = []
        content = {}
        for result in list:
            created_at = result[2]
            created_at_serialize = created_at.strftime("%Y-%m-%d")
            content = { 'tweetId': result[0],
                        'userId' : result[4],
                        'content' : result[1],
                        'createdAt' : created_at_serialize,
                        'tweetImageUrl' : result[3]
                        }
            tweet_list.append(content)
        #Check if cursor opened and close all connections
        cnnct_to_db.endConn()
        return Response(json.dumps(tweet_list),
                                    mimetype="application/json",
                                    status=200)
    elif (getParams is not None):
        if ((type(getParams) == str) and (getParams>0)):    
            cnnct_to_db.cursor.execute("SELECT * FROM user WHERE id =?", [getParams])
            userIdMatch = cnnct_to_db.cursor.fetchone()
            tweet_list = []
            content = {}
            for result in userIdMatch:
                created_at = result[2]
                created_at_serialize = created_at.strftime("%Y-%m-%d")
                content = { 'tweetId': result[0],
                            'userId' : result[4],
                            'content' : result[1],
                            'createdAt' : created_at_serialize,
                            'tweetImageUrl' : result[3]
                            }
            tweet_list.append(content)
            cnnct_to_db.endConn()
        else:
            print("Something went wrong")
            cnnct_to_db.endConn()
            return

        return Response(json.dumps(tweet_list),
                                    mimetype="application/json",
                                    status=200)

def post_tweet():
    pass
def update_tweet():
    pass
def delete_tweet():
    pass
################################  End of functions #################################################

@app.route('/')
def homepage():
    return "<h1>Hello World</h1>"

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



@app.route('/api/tweets', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def tweetApi():
    if (request.method == 'GET'):
        return get_tweets()
    elif (request.method == 'POST'):
        return post_tweet()    
    elif (request.method == 'PATCH'):
        return update_tweet()
    elif (request.method == 'DELETE'):
        return delete_tweet()
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
    print ("No argument was provided")
    exit()

