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
        cnnct_to_db.cursor.execute("SELECT comment.id, tweet.id, comment.userId, username, comment.content, comment.createdAt, imageUrl, tweetImageUrl FROM comment INNER JOIN tweet ON comment.tweetId = tweet.id INNER JOIN user ON user.id=tweet.userId")
        list = cnnct_to_db.cursor.fetchall()
        comment_list = []
        content = {}
        for result in list:
            created_at = result[5]
            created_at_serialize = created_at.strftime("%Y-%m-%d %H:%M:%S")
            content = { 'commentId': result[0],
                        'userId' : result[2],
                        'tweetId' : result[1],
                        'username': result[3],
                        'content' : result[4],
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
            cnnct_to_db.cursor.execute("SELECT comment.id, tweet.id, comment.userId, username, comment.content, comment.createdAt, imageUrl, tweetImageUrl FROM comment INNER JOIN tweet ON comment.tweetId = tweet.id INNER JOIN user ON user.id=tweet.userId WHERE tweetId=?", [params_id])
            tweet_id_match = cnnct_to_db.cursor.fetchall()
            comment_list = []
            content = {}
            for result in tweet_id_match:
                created_at = result[4]
                created_at_serialize = created_at.strftime("%Y-%m-%d %H:%M:%S")
                content = { 'commentId': result[0],
                        'userId' : result[2],
                        'tweetId' : result[1],
                        'username': result[3],
                        'content' : result[4],
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
                'maxLength': 150,
                'required': True
            },
        ]
        validate_data(requirements,data)
        check_data_required(requirements,data)
        
    except InvalidData:
        return Response("Invalid data sent",
                                    mimetype="text/plain",
                                    status=400)

    client_loginToken = data.get('loginToken')

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
        requirements = [
                {   'name': 'loginToken',
                    'datatype': str,
                    'maxLength': 32,
                    'required': True
                },
                {   
                    'name': 'commentId',
                    'datatype': int,
                    'maxLength': 10,
                    'required': True
                },
                {   
                    'name': 'content',
                    'datatype': str,
                    'maxLength': 150,
                    'required': True
                },
            ]
        validate_data(requirements,data)
        check_data_required(requirements,data)

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
    cnnct_to_db.cursor.execute("SELECT content FROM comment WHERE id=?", [client_commentId])
    updated_comment = cnnct_to_db.cursor.fetchone()
    db_updated_comment = updated_comment[0]
    cnnct_to_db.endConn()
    
    resp = {
        "commentId": client_commentId,
        "tweetId": match_tweetId,
        "userId": match_userId,
        "username": match_username,
        "content": db_updated_comment,
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

    requirements = [
                {   'name': 'loginToken',
                    'datatype': str,
                    'maxLength': 32,
                    'required': True
                },
                {   
                    'name': 'commentId',
                    'datatype': int,
                    'maxLength': 10,
                    'required': True
                }
            ]
    validate_data(requirements,data)
    check_data_required(requirements,data)
    
    if type(data.get('commentId')) != int or data.get('commentId') is None:
        return Response("Please check your data input",
                    mimetype="text/plain",
                    status=400)

    client_loginToken = data.get('loginToken')
    client_commentId = data.get('commentId')

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