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
        datetime.datetime.strptime(date_input, '%Y-%m-%d %H:%M:%S')
        raise TypeError()
    except:
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
        chk = isinstance(data.get(x), found_key)
        if not chk:
            raise ValueError("Please check your inputs. Type error was found.")

def check_char_len(mydict, data):
    for item in data.keys():
        found_key = mydict.get(item)
        if(type(data.get(item)) == str and found_key != None):
            if(len(data.get(item)) > found_key):
                raise ValueError("Please check your inputs. Data is out of bounds")

def get_comments():
    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()
    
    except ConnectionError:
        cnnct_to_db.endConn()
        return Response("Error while attempting to connect to the database",
                                    mimetype="text/plain",
                                    status=400)
    params = request.args
    params_id = request.args.get("tweetId")
    checklist = ["tweetId"]
    if not validate_client_data(checklist, params):
        return Response("Incorrect data keys received",
                            mimetype="text/plain",
                            status=400)
    if (params_id is None):
        cnnct_to_db.cursor.execute("SELECT * FROM comment")
        list = cnnct_to_db.cursor.fetchall()
        comment_list = []
        content = {}
        for result in list:
            created_at = result[4]
            created_at_serialize = created_at.strftime("%Y-%m-%d %H:%M:%S")
            content = { 'commentId': result[0],
                        'userId' : result[1],
                        'tweetId' : result[2],
                        'content' : result[3],
                        'createdAt': created_at_serialize
                        }
            comment_list.append(content)
        #Check if cursor opened and close all connections
        cnnct_to_db.endConn()
        return Response(json.dumps(comment_list),
                                    mimetype="application/json",
                                    status=200)
    elif (params_id is not None):
        try:
            params_id = int(request.args.get("tweetId"))
        except ValueError:
            return Response(json.dumps("Incorrect datatype received"),
                                mimetype="text/plain",
                                status=200)
        if ((0< params_id<99999999)):
            cnnct_to_db.cursor.execute("SELECT * FROM comment WHERE tweetId=?", [params_id])
            tweet_id_match = cnnct_to_db.cursor.fetchall()
            comment_list = []
            content = {}
            for result in tweet_id_match:
                created_at = result[4]
                created_at_serialize = created_at.strftime("%Y-%m-%d %H:%M:%S")
                content = { 'commentId': result[0],
                        'userId' : result[1],
                        'tweetId' : result[2],
                        'content' : result[3],
                        'createdAt': created_at_serialize
                        }
            comment_list.append(content)
            cnnct_to_db.endConn()
        else:
            cnnct_to_db.endConn()
            return Response(json.dumps("Incorrect data type received"),
                                mimetype="text/plain",
                                status=200)

        return Response(json.dumps(comment_list),
                                    mimetype="application/json",
                                    status=200)

def post_comments():
    try:
        data = request.json
        checklist = ["loginToken", "tweetId", "content"]
        if not validate_client_data(checklist,data):
            return Response("Incorrect data keys received",
                                mimetype="text/plain",
                                status=400)
        dict={
            'tweetId' : int,
            'loginToken' : str,
            'content' : str,
            }
        check_type(dict,data)
        char_limit_dict = {
            'content': 150,
            'imageUrl':100
        }
        check_char_len(char_limit_dict,data)
    except InvalidData:
        return Response("Invalid data sent",
                                    mimetype="text/plain",
                                    status=400)

    client_loginToken = data.get('loginToken')
    validate_token(client_loginToken)

    if(data.get('content') == None or data.get('tweetId') == None):
        return Response("Required data missing",
                                mimetype="text/plain",
                                status=400)
    else:
        client_content = data.get('content')
        client_tweetId = data.get('tweetId')

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
        
        db_id = user_id_match[0]
        db_username = user_id_match[1]

        #get current date and time
        cur_datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cnnct_to_db.cursor.execute("INSERT INTO comment(userId,tweetId,content,createdAt) VALUES(?,?,?,?)",[db_id,client_tweetId,client_content,cur_datetime])
        if(cnnct_to_db.cursor.rowcount == 1):
            cnnct_to_db.conn.commit()
        else:
            return Response("Failed to update",
                                mimetype="text/plain",
                                status=400)
        cnnct_to_db.cursor.execute("SELECT * FROM comment")
        new_comment_result = cnnct_to_db.cursor.fetchone()

        resp = {
                "commentId": new_comment_result[0],
                "tweetId" : client_tweetId,
                "userId" : db_id,
                "username" : db_username,
                "content" : new_comment_result[3],
                "createdAt" : cur_datetime
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

def update_comments():
    try:
        data = request.json
        checklist = ["loginToken", "commentId", "content"]
        if not validate_client_data(checklist,data):
            return Response("Incorrect data keys received",
                                mimetype="text/plain",
                                status=400)
        dict={
            'loginToken' : str,
            'content' : str,
            'commentId' : int
            }
        char_limit_dict = {
            'content': 150
        }
        check_type(dict,data)
        check_char_len(char_limit_dict,data)

        
    except ValueError:
        return Response("Invalid data sent",
                                    mimetype="text/plain",
                                    status=400)

    if type(data.get('commentId')) != int or data.get('content') == None:
        return Response("Please check your data input",
                    mimetype="plain/text",
                    status=400)
    else:
        client_loginToken = data.get('loginToken')
        client_commentId = data.get('commentId')
        client_content = data.get('content')
    validate_token(client_loginToken)
    
    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()
        
        #Check for tweet ownership
        cnnct_to_db.cursor.execute("SELECT comment.createdAt, comment.userId, comment.tweetId, content, username FROM comment INNER JOIN user ON user.id = comment.userId INNER JOIN user_session ON user.id = user_session.userId WHERE loginToken =? and comment.id =?",[client_loginToken,client_commentId])
        
        info_match = cnnct_to_db.cursor.fetchone()
        if not info_match:
            raise ValueError("No matching data found")
        birthdate_serialized = info_match[0].strftime('%Y-%m-%d %H:%M:%S')
        match_createdAt = birthdate_serialized
        match_userId = info_match[1]
        match_tweetId = info_match[2]
        match_content = info_match[3]
        match_username = info_match[4]
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

    cnnct_to_db.cursor.execute("UPDATE comment SET content =? WHERE id=?",[client_content,client_commentId])
    
    if(cnnct_to_db.cursor.rowcount == 1):
        cnnct_to_db.conn.commit()  
    else:
        return Response("Failed to update",
                                mimetype="text/plain",
                                status=400)
    cnnct_to_db.endConn()
    
    resp = {
        "commentId": client_commentId,
        "tweetId": match_tweetId,
        "userId": match_userId,
        "username": match_username,
        "content": match_content,
        "createdAt": match_createdAt
    }
    return Response(json.dumps(resp),
                    mimetype="application/json",
                    status=200)

def delete_comments():
    data = request.json
    checklist = ["loginToken", "commentId"]
    if not validate_client_data(checklist,data):
            return Response("Incorrect data keys received",
                                mimetype="text/plain",
                                status=400)
    dict={
        'commentId' : int,
        'loginToken' : str
        }

    check_type(dict,data)
    
    if type(data.get('commentId')) != int or data.get('commentId') is None:
        return Response("Please check your data input",
                    mimetype="text/plain",
                    status=400)

    client_loginToken = data.get('loginToken')
    client_commentId = data.get('commentId')
    validate_token(client_loginToken)
    
    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()
        #checks password and logintoken are in the same row
        cnnct_to_db.cursor.execute("SELECT comment.userId, content FROM comment INNER JOIN user ON user.id = comment.userId INNER JOIN user_session ON user.id = user_session.userId WHERE loginToken =? and comment.id =?",[client_loginToken,client_commentId])
        id_match = cnnct_to_db.cursor.fetchone()
        if id_match != None:
            id_match = id_match[0]
            cnnct_to_db.cursor.execute("DELETE FROM comment WHERE id=?",[client_commentId])
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
    #Check if cursor opened and close all connections
    cnnct_to_db.endConn()
    return Response("Sucessfully deleted comment",
                    mimetype="text/plain",
                    status=204)

@app.route('/api/comments', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def comment_api():
    if (request.method == 'GET'):
        return get_comments()
    elif (request.method == 'POST'):
        return post_comments()    
    elif (request.method == 'PATCH'):
        return update_comments()
    elif (request.method == 'DELETE'):
        return delete_comments()
    else:
        print("Something went wrong.")