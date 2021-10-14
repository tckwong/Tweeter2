from package import app
from flask import request, Response
import mariadb
import json
import dbcreds
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
        # raise ConnectionError("Failed to connect to the database")
class CustomError(Exception):
    pass

def validate_date(date_input):
    try:
        datetime.datetime.strptime(date_input, '%Y-%m-%d')
    except CustomError:
        print("Invalid date format")
        return Response("Invalid date format",
                                    mimetype="text/plain",
                                    status=400)
    return True

def validate_token(token_input):
    try:
        len(token_input) == 32
    except CustomError:
        return Response("Invalid LoginToken",
                                    mimetype="text/plain",
                                    status=403)

def get_tweets():
    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()
    except ConnectionError:
        cnnct_to_db.endConn()
        return Response("Error while attempting to connect to the database",
                                    mimetype="text/plain",
                                    status=400)
    
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
    try:
        data = request.json
    except CustomError:
        return Response("Invalid data sent",
                                    mimetype="text/plain",
                                    status=400) 
    client_loginToken = data.get('loginToken')
    if(data.get('content') == None):
        print("Content cannot be none")
        return Response("Content cannot be none",
                                mimetype="text/plain",
                                status=400)
    else:
        client_content = data.get('content')
        client_imageUrl = data.get('imageUrl')

    validate_token(client_loginToken)
    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()

        #checkloginToken and get Id
        cnnct_to_db.cursor.execute("SELECT user.id, username, imageUrl FROM user INNER JOIN user_session ON user_session.userId = user.id WHERE user_session.loginToken =?", [client_loginToken])
        user_login_match = cnnct_to_db.cursor.fetchone()
        #check data inputs
        if (user_login_match != None):
            print("successfully found match")
        else:
            return Response("Invalid data sent",
                                mimetype="text/plain",
                                status=400)
        dict_keys = ("userId", "username", "userImageUrl")
        
        result_dict = dict(zip(dict_keys,user_login_match))
        print(result_dict)
        db_id = result_dict["userId"]
        db_username = result_dict["username"]
        db_imageUrl = result_dict["userImageUrl"]
        
        #get current date and time
        cur_datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(cur_datetime)
        cnnct_to_db.cursor.execute("INSERT INTO tweet(content,createdAt,tweetImageUrl,userId) VALUES(?,?,?,?)",[client_content,cur_datetime,client_imageUrl,user_login_match[0]])
        if(cnnct_to_db.cursor.rowcount == 1):
            print("Tweet posted sucessfully")
            cnnct_to_db.conn.commit()
        else:
            print("Failed to update")
        cnnct_to_db.cursor.execute("SELECT * FROM tweet")
        new_tweet_result = cnnct_to_db.cursor.fetchone()
        client_dict_keys = ("id", "content", "createdAt", "tweetImageUrl","userId")
        
        result_tweet_dict = dict(zip(client_dict_keys,new_tweet_result))
        print(result_tweet_dict)
        resp = {
                "tweetId" : user_login_match[0],
                "userId" : db_id,
                "username" : db_username,
                "userImageUrl" : db_imageUrl,
                "content" : result_tweet_dict["content"],
                "createdAt" : result_tweet_dict["createdAt"],
                "imageUrl" : result_tweet_dict["tweetImageUrl"]
        }

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

def update_tweet():
    data = request.json

    if type(data.get('tweetId')) != int:
        print("Incorrect data input")
        return Response("Please check your data input",
                    mimetype="plain/text",
                    status=400)
    else:
        client_loginToken = data.get('loginToken')
        client_tweetId = data.get('tweetId')
        client_content = data.get('content')
    
    validate_token(client_loginToken)
    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()
        #Check for tweet ownership
        cnnct_to_db.cursor.execute("SELECT tweet.id, tweet.userId, content, loginToken FROM tweet INNER JOIN user ON user.id = tweet.userId INNER JOIN user_session ON tweet.userId = user_session.userId WHERE loginToken =? and tweet.id =?",[client_loginToken,client_tweetId])
        
        info_match = cnnct_to_db.cursor.fetchone()
                
        print("Matching info", info_match)
    except ConnectionError:
        print("Error while attempting to connect to the database")
    except mariadb.DataError:
        print("Something is wrong with client data inputs")
    except mariadb.IntegrityError:
        print("Your query would have broken the database and we stopped it")
    
    cnnct_to_db.cursor.execute("UPDATE tweet SET content =? WHERE id=?",[client_content,client_tweetId])
    
    if(cnnct_to_db.cursor.rowcount == 1):
        cnnct_to_db.conn.commit()
        print("Tweet updated sucessfully")         
    else:
        print("Failed to update")
            
    #Check if cursor opened and close all connections
    cnnct_to_db.endConn()
    
    resp = {
        "tweetId" : client_tweetId,
        "content" : client_content
    }

    return Response(json.dumps(resp),
                    mimetype="application/json",
                    status=200)
    # except mariadb.DataError:
    #     print("Something is wrong with client data inputs")
    # except mariadb.IntegrityError:
    #     print("Your query would have broken the database and we stopped it")
    # except mariadb.OperationalError:
    #     print("Something wrong with the operation of your query")
    # except mariadb.ProgrammingError:
    #     print("Your query was wrong")


def delete_tweet():
    data = request.json
    if type(data.get('tweetId')) != int:
        print("Incorrect data input (tweetId)")
        return Response("Please check your data input",
                    mimetype="plain/text",
                    status=400)
    client_loginToken = data.get('loginToken')
    client_tweetId = data.get('tweetId')
    
    validate_token(client_loginToken)
    
    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()
        #checks password and logintoken are in the same row
        cnnct_to_db.cursor.execute("SELECT tweet.id, tweet.userId, content, loginToken FROM tweet INNER JOIN user ON user.id = tweet.userId INNER JOIN user_session ON tweet.userId = user_session.userId WHERE loginToken =? and tweet.id =?",[client_loginToken,client_tweetId])
        id_match = cnnct_to_db.cursor.fetchone()
        if id_match != None:
            id_match = id_match[0]
            cnnct_to_db.cursor.execute("DELETE FROM tweet WHERE id=?",[client_tweetId])
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
    return Response("Sucessfully deleted tweet",
                    mimetype="plain/text",
                    status=200)

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