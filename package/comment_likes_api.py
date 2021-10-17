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

def get_comment_likes():
    params = request.args
    params_id = request.args.get("commentId")
    checklist = ["commentId"]
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
        cnnct_to_db.cursor.execute("SELECT comment_like.id, comment_like.userId, username FROM comment_like INNER JOIN user ON comment_like.userId = user.id")
        list = cnnct_to_db.cursor.fetchall()
        
        comment_like_list = []
        content = {}
    
        for result in list:
            content = { 'commentId': result[0],
                        'userId': result[1],
                        'username' : result[2],
                        }
            comment_like_list.append(content)
        #Check if cursor opened and close all connections
        cnnct_to_db.endConn()
        return Response(json.dumps(comment_like_list),
                                    mimetype="application/json",
                                    status=200)
    
    elif (params_id is not None):
        try:
            params_id = int(request.args.get("commentId"))
        except ValueError:
            return Response("Incorrect datatype received",
                                        mimetype="text/plain",
                                        status=400)
        if ((0< params_id<99999999)):
            try:
                cnnct_to_db.cursor.execute("SELECT comment_like.id, comment_like.userId, username FROM comment_like INNER JOIN user ON comment_like.userId = user.id WHERE commentId=? ", [params_id])
                tweet_id_match = cnnct_to_db.cursor.fetchall()

                if(cnnct_to_db.cursor.rowcount == 0):
                    return Response("No results found",
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
            user_list = []
            content = {}
            
            for result in tweet_id_match:
                content = { 'commentId': result[0],
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

def post_comments_likes():
    try:
        data = request.json
        checklist = ["loginToken", "commentId"]
        if not validate_client_data(checklist,data):
            return Response("Incorrect data keys received",
                                mimetype="text/plain",
                                status=400)
    except ValueError:
        return Response("Invalid data sent",
                                    mimetype="text/plain",
                                    status=400)
    dict={  
        'loginToken' : str,
        'commentId' : int,
        }
    check_type(dict,data)

    client_loginToken = data.get('loginToken')
    client_commentId = data.get('commentId')
    validate_token(client_loginToken)

    #Checks for required data in DB
    if(type(client_commentId) == int and client_commentId == None):
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
        cnnct_to_db.cursor.execute("INSERT INTO comment_like (commentId, userId) VALUES(?,?)",[client_commentId, user_match[0]])
        
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
        print("You cannot like more than once/ commentId does not exist")
        return Response("You cannot like more than once/ commentId does not exist",
                                mimetype="text/plain",
                                status=400)
    finally:
        cnnct_to_db.endConn()

def delete_comment_likes():
    try:
        data = request.json
        checklist = ["loginToken", "commentId"]
        if not validate_client_data(checklist,data):
            return Response("Incorrect data keys received",
                                mimetype="text/plain",
                                status=400)
    except ValueError:
        return Response("Invalid data sent",
                                    mimetype="text/plain",
                                    status=400)
    
    client_loginToken = data.get('loginToken')
    client_commentId = data.get('commentId')
    validate_token(client_loginToken)
    
    #Checks for required data in DB
    if(type(client_commentId) != int or client_commentId == None):
        return Response("Error! Missing required data",
                        mimetype="text/plain",
                        status=400)

    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()
        cnnct_to_db.cursor.execute("SELECT comment_like.id, loginToken FROM comment_like INNER JOIN user ON comment_like.userId = user.id INNER JOIN user_session ON user_session.userId = user.id WHERE loginToken=?",[client_loginToken])
        match = cnnct_to_db.cursor.fetchone()
        if match == None:
            return Response("No matching results were found",
                                mimetype="text/plain",
                                status=400)

        cnnct_to_db.cursor.execute("DELETE FROM comment_like WHERE comment_like.id=?", [match[0]])
        
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

@app.route('/api/comment-likes', methods=['GET', 'POST', 'DELETE'])
def comment_likes_api():
    if (request.method == 'GET'):
        return get_comment_likes()
    elif (request.method == 'POST'):
        return post_comments_likes()    
    elif (request.method == 'DELETE'):
        return delete_comment_likes()
    else:
        print("Something went wrong.")