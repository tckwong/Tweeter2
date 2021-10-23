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

class InvalidData(Exception):
    def __init__(self):
        super().__init__("Invalid data passed")

def validate_date(date_input):
    try:
        datetime.datetime.strptime(date_input, '%Y-%m-%d %H:%M:%S')
        raise TypeError()
    except:
        return False
    return True

def validate_misc_data(list, data):
    #Checks for invalid params/data
    for key in data.keys():
        if key in list:
            continue
        else:
            return False
    return True
    
def check_data_required(mydict, data):
    #Check if required
    checklist=[]
    for item in mydict:
        if(item.get('required') == True):
            checklist.append(item.get('name'))
    
    #Check data against required list
    for key in checklist:
        if key not in data.keys():
            raise ValueError("Required data was not found")
        else:
            continue
    return True

def validate_data(mydict, data):
    for item in data.keys():
        newlst = []
        for obj in mydict:
            x = obj.get('name')
            newlst.append(x)
            
        found_index = newlst.index(item)
        
        if item in mydict[found_index]['name']:
            #Check for correct datatype
            data_value = data.get(item)
            chk = isinstance(data_value, mydict[found_index]["datatype"])
            if not chk:
                raise ValueError("Please check your inputs. Type error was found.")

            #Check for max char length
            maxLen = mydict[found_index]['maxLength']
            if(type(data.get(item)) == str and maxLen != None):
                if(len(data.get(item)) > maxLen):
                    raise ValueError("Please check your inputs. Data is out of bounds")
        else:
            raise ValueError("Please check your inputs. An error was found with your data")

def get_tweets():
    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()
    
    except ConnectionError:
        cnnct_to_db.endConn()
        return Response("Error while attempting to connect to the database",
                                    mimetype="text/plain",
                                    status=400)
    params = request.args
    params_id = request.args.get("userId")
    checklist = ["userId"]
    if not validate_misc_data(checklist, params):
        return Response("Incorrect data keys received",
                            mimetype="text/plain",
                            status=400)
    if (params_id is None):
        cnnct_to_db.cursor.execute("SELECT tweet.id, user.id, username, content, createdAt, imageUrl, tweetImageUrl FROM tweet INNER JOIN user ON tweet.userId = user.id")
        list = cnnct_to_db.cursor.fetchall()
        print(list)
        tweet_list = []
        content = {}
        for result in list:
            created_at = result[4]
            print(created_at)
            created_at_serialize = created_at.strftime("%Y-%m-%d %H:%M:%S")
            print(created_at_serialize)
            content = { 'tweetId': result[0],
                        'userId' : result[1],
                        'username': result[2],
                        'content' : result[3],
                        'createdAt' : created_at_serialize,
                        'userImageUrl': result[5],
                        'tweetImageUrl' : result[6]
                        }
            tweet_list.append(content)
        #Check if cursor opened and close all connections
        cnnct_to_db.endConn()
        return Response(json.dumps(tweet_list),
                                    mimetype="application/json",
                                    status=200)
    elif (params_id is not None):
        try:
            params_id = int(request.args.get("userId"))
        except ValueError:
            return Response("Incorrect datatype received",
                                mimetype="text/plain",
                                status=200)
        if ((0< params_id<99999999)):
            try:
                cnnct_to_db.cursor.execute("SELECT tweet.id, user.id, username, content, createdAt, imageUrl, tweetImageUrl FROM tweet INNER JOIN user ON tweet.userId = user.id WHERE userId=?", [params_id])
                tweet_id_match = cnnct_to_db.cursor.fetchall()
                print(tweet_id_match)            
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
            tweet_list = []
            content = {}
            for result in tweet_id_match:
                created_at = result[4]
                created_at_serialize = created_at.strftime("%Y-%m-%d %H:%M:%S")
                content = { 'tweetId': result[0],
                        'userId' : result[1],
                        'username': result[2],
                        'content' : result[3],
                        'createdAt' : created_at_serialize,
                        'userImageUrl': result[5],
                        'tweetImageUrl' : result[6]
                        }
                tweet_list.append(content)
            cnnct_to_db.endConn()
        else:
            cnnct_to_db.endConn()
            return Response(json.dumps("Incorrect data type received"),
                                mimetype="text/plain",
                                status=200)

        return Response(json.dumps(tweet_list),
                                    mimetype="application/json",
                                    status=200)

def post_tweet():
    try:
        data = request.json
        checklist = ["loginToken", "content", "imageUrl"]
        if not validate_misc_data(checklist,data):
            return Response("Incorrect data keys received",
                                mimetype="text/plain",
                                status=400)
        
        requirements = [
            {   'name': 'loginToken',
                'datatype': str,
                'maxLength': 32,
                'required': True
            },
            {   
                'name': 'content',
                'datatype': str,
                'maxLength': 200,
                'required': True
            },
            {   
                'name': 'imageUrl',
                'datatype': str,
                'maxLength': 150,
                'required': False
            },
        ]

        validate_data(requirements,data)
        check_data_required(requirements,data)
        
    except InvalidData:
        return Response("Invalid data sent",
                                    mimetype="text/plain",
                                    status=400)

    client_loginToken = data.get('loginToken')
    client_content = data.get('content')
    client_imageUrl = data.get('imageUrl')

    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()

        #checkloginToken and get user Id
        cnnct_to_db.cursor.execute("SELECT user.id, username, imageUrl FROM user INNER JOIN user_session ON user_session.userId = user.id WHERE user_session.loginToken =?", [client_loginToken])
        user_id_match = cnnct_to_db.cursor.fetchone()
        #check for a row match
        if user_id_match == None:
            return Response("No matching results were found",
                                mimetype="text/plain",
                                status=400)
        
        #retrieve user information from DB
        db_id = user_id_match[0]
        db_username = user_id_match[1]
        db_imageUrl = user_id_match[2]
        
        #get current date and time
        cur_datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cnnct_to_db.cursor.execute("INSERT INTO tweet(content,createdAt,tweetImageUrl,userId) VALUES(?,?,?,?)",[client_content,cur_datetime,client_imageUrl,user_id_match[0]])
        if(cnnct_to_db.cursor.rowcount == 1):
            print("Tweet posted sucessfully")
            cnnct_to_db.conn.commit()
        else:
            return Response("Failed to update",
                                mimetype="text/plain",
                                status=400)
        cnnct_to_db.cursor.execute("SELECT * from tweet INNER JOIN user ON user.id = tweet.userId ORDER BY tweet.id DESC LIMIT 1")
        new_tweet_result = cnnct_to_db.cursor.fetchone()

        result_created_serialize = new_tweet_result[2].strftime('%Y-%m-%d %H:%M:%S')
        resp = {
                "tweetId" : new_tweet_result[0],
                "userId" : db_id,
                "username" : db_username,
                "userImageUrl" : db_imageUrl,
                "content" : new_tweet_result[1],
                "createdAt" : result_created_serialize,
                "imageUrl" : new_tweet_result[3]
        }

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

def update_tweet():
    try:
        data = request.json
        checklist = ["loginToken", "tweetId", "content"]
        if not validate_misc_data(checklist,data):
            return Response("Incorrect data keys received",
                                mimetype="text/plain",
                                status=400)
    except ValueError:
        return Response("Invalid data sent",
                                    mimetype="text/plain",
                                    status=400)
    requirements = [
            {   'name': 'loginToken',
                'datatype': str,
                'maxLength': 32,
                'required': True
            },  
            {   
                'name': 'tweetId',
                'datatype': int,
                'maxLength': 10,
                'required': True
            },
            {   
                'name': 'content',
                'datatype': str,
                'maxLength': 200,
                'required': True
            },
        ]

    validate_data(requirements,data)
    check_data_required(requirements,data)

    if type(data.get('tweetId')) != int or data.get('content') == None:
        return Response("Please check your data input",
                    mimetype="plain/text",
                    status=400)
    else:
        client_loginToken = data.get('loginToken')
        client_tweetId = data.get('tweetId')
        client_content = data.get('content')
    
    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()
        #Check for tweet ownership
        cnnct_to_db.cursor.execute("SELECT tweet.id, tweet.userId, content, loginToken FROM tweet INNER JOIN user ON user.id = tweet.userId INNER JOIN user_session ON tweet.userId = user_session.userId WHERE loginToken =? and tweet.id =?",[client_loginToken,client_tweetId])
        
        info_match = cnnct_to_db.cursor.fetchone()
        if not info_match:
            raise ValueError("No matching data found")
        print("Matching info", info_match)
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
    
    cnnct_to_db.cursor.execute("UPDATE tweet SET content =? WHERE id=?",[client_content,client_tweetId])
    
    if(cnnct_to_db.cursor.rowcount == 1):
        cnnct_to_db.conn.commit()  
    else:
        return Response("Failed to update",
                                mimetype="text/plain",
                                status=400)
    cnnct_to_db.endConn()
    
    resp = {
        "tweetId" : client_tweetId,
        "content" : client_content
    }

    return Response(json.dumps(resp),
                    mimetype="application/json",
                    status=200)

def delete_tweet():
    data = request.json
    checklist = ["loginToken", "tweetId"]
    if not validate_misc_data(checklist,data):
        return Response("Incorrect data keys received",
                            mimetype="text/plain",
                            status=400)
    requirements = [
            {   'name': 'loginToken',
                'datatype': str,
                'maxLength': 32,
                'required': True
            },  
            {   
                'name': 'tweetId',
                'datatype': int,
                'maxLength': 10,
                'required': True
            },
        ]

    validate_data(requirements,data)
    check_data_required(requirements,data)

    client_loginToken = data.get('loginToken')
    client_tweetId = data.get('tweetId')
    
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
                cnnct_to_db.conn.commit()
            else:
                return Response("Failed to update",
                                mimetype="text/plain",
                                status=400)
        else:
            raise ValueError("No matching results found")
            
    except ConnectionError:
        cnnct_to_db.endConn()
        print("Error while attempting to connect to the database")
        return Response("Error while attempting to connect to the database",
                        mimetype="text/plain",
                        status=444)  
    except mariadb.DataError:
        print("Something wrong with your data")
        return Response("Something wrong with your data",
                        mimetype="text/plain",
                        status=400)
        
    #Check if cursor opened and close all connections
    cnnct_to_db.endConn()
    return Response("Sucessfully deleted tweet",
                    mimetype="text/plain",
                    status=204)

@app.route('/api/tweets', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def tweet_api():
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