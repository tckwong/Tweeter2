#Not catching no content
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

class InvalidToken(Exception):
    def __init__(self, token, message="Invalid loginToken sent"):
        self.token = token
        self.message = message
        super().__init__(self.message)

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

def get_tweet_likes():
    params = request.args
    params_id = request.args.get("id")
    checklist = ["id"]
    if not validate_client_data(checklist,params):
        return Response("Incorrect data keys received",
                            mimetype="text/plain",
                            status=400)
    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()    
        
    except ConnectionError:
        cnnct_to_db.endConn()
        return Response("Error while attempting to connect to the database",
                                    mimetype="text/plain",
                                    status=400)
    if (params_id is None):
        cnnct_to_db.cursor.execute("SELECT tweet_like.tweetId, tweet_like.id, username FROM tweet_like INNER JOIN user ON tweet_like.userId = user.id")
        list = cnnct_to_db.cursor.fetchall()
        tweet_like_list = []
        content = {}
    
        for result in list:
            content = { 'tweetId': result[0],
                        'userId': result[1],
                        'username' : result[2],
                        }
            tweet_like_list.append(content)
        #Check if cursor opened and close all connections
        cnnct_to_db.endConn()
        return Response(json.dumps(tweet_like_list),
                                    mimetype="application/json",
                                    status=200)
    
    elif (params_id is not None):
        try:
            params_id = int(request.args.get("id"))
        except ValueError:
            return Response("Incorrect datatype received",
                                        mimetype="text/plain",
                                        status=400)
        if (type(params_id) == int and params_id > 0):    
            cnnct_to_db.cursor.execute("SELECT tweet_like.tweetId, tweet_like.id, username FROM tweet_like INNER JOIN user ON tweet_like.userId = user.id WHERE tweetId=? ", [params_id])
            tweet_id_match = cnnct_to_db.cursor.fetchall()

            if(cnnct_to_db.cursor.rowcount == 0):
                return Response("No results found",
                                mimetype="plain/text",
                                status=400)
            user_list = []
            content = {}
            
            for result in tweet_id_match:
                content = { 'tweetId': result[0],
                        'userId': result[1],
                        'username' : result[2],
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
def post_tweet_like():
    try:
        data = request.json
        checklist = ["loginToken", "tweetId"]
        if not validate_client_data(checklist,data):
            return Response("Incorrect data keys received",
                                mimetype="text/plain",
                                status=400)
    except ValueError:
        return Response("Invalid data sent",
                                    mimetype="text/plain",
                                    status=400)
    
    client_loginToken = data.get('loginToken')
    client_tweetId = data.get('tweetId')
    validate_token(client_loginToken)
    #Checks for required data in DB
    if(type(client_tweetId) == int and client_tweetId == None):
        return Response("Error! Missing required data",
                        mimetype="text/plain",
                        status=400)

    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()
        cnnct_to_db.cursor.execute("SELECT user.id from user INNER JOIN user_session ON user_session.userId = user.id WHERE loginToken=?",[client_loginToken])
        user_match = cnnct_to_db.cursor.fetchone()
        if user_match == None:
            return Response("No matching results were found",
                                mimetype="text/plain",
                                status=400)
        cnnct_to_db.cursor.execute("INSERT INTO tweet_like (tweetId, userId) VALUES(?,?)",[client_tweetId, user_match[0]])
        
        if(cnnct_to_db.cursor.rowcount == 1):
            cnnct_to_db.conn.commit()
        else:
            return Response("Failed to update",
                                mimetype="text/plain",
                                status=400)
        return Response(mimetype="application/json",
                        status=204)  
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

def delete_tweet_like():
    try:
        data = request.json
        checklist = ["loginToken", "tweetId"]
        if not validate_client_data(checklist,data):
            return Response("Incorrect data keys received",
                                mimetype="text/plain",
                                status=400)
    except ValueError:
        return Response("Invalid data sent",
                                    mimetype="text/plain",
                                    status=400)
    
    client_loginToken = data.get('loginToken')
    client_tweetId = data.get('tweetId')
    validate_token(client_loginToken)
    #Checks for required data in DB
    if(type(client_tweetId) != int or client_tweetId == None):
        return Response("Error! Missing required data",
                        mimetype="text/plain",
                        status=400)

    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()
        cnnct_to_db.cursor.execute("SELECT tweet_like.id, tweet_like.tweetId, loginToken FROM tweet_like INNER JOIN user ON tweet_like.userId = user.id INNER JOIN user_session ON user_session.userId = user.id WHERE loginToken=?",[client_loginToken])
        match = cnnct_to_db.cursor.fetchone()
        if match == None:
            return Response("No matching results were found",
                                mimetype="text/plain",
                                status=400)

        cnnct_to_db.cursor.execute("DELETE FROM tweet_like WHERE tweet_like.id=?", [match[0]])
        
        if(cnnct_to_db.cursor.rowcount == 1):
            cnnct_to_db.conn.commit()
        else:
            return Response("Failed to update",
                                mimetype="text/plain",
                                status=400)
        return Response(mimetype="application/json",
                        status=204)  
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

@app.route('/api/tweet-likes', methods=['GET', 'POST', 'DELETE'])
def tweet_likes_api():
    if (request.method == 'GET'):
        return get_tweet_likes()
    elif (request.method == 'POST'):
        return post_tweet_like()
    elif (request.method == 'DELETE'):
        return delete_tweet_like()
    else:
        print("Something went wrong.")

