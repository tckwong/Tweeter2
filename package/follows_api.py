from package import app
from flask import request, Response
import mariadb
import json
import dbcreds

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

def validate_token(token_input):
    try:
        if not (len(token_input) == 32):
            raise InvalidToken()
    except InvalidToken as error:
        raise error

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

def get_follows():
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
    if not validate_client_data(checklist, params):
        return Response("Incorrect data keys received",
                            mimetype="text/plain",
                            status=400)
    if (params_id is None):
        return Response(json.dumps("Please provide a 'userId'"),
                                mimetype="text/plain",
                                status=400)
    
    elif (params_id is not None):
        try:
            params_id = int(request.args.get("userId"))
        except ValueError:
            return Response("Incorrect datatype received",
                                        mimetype="text/plain",
                                        status=400)
        if ((0< params_id<99999999)):
            try:
                cnnct_to_db.cursor.execute("SELECT followed,email,username,bio,birthdate,imageUrl,bannerUrl FROM follow INNER JOIN user ON follow.followed = user.id WHERE follower=?", [params_id])
                follower_match = cnnct_to_db.cursor.fetchall()
                print(follower_match)
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
            follow_list = []
            content = {}
            for result in follower_match:
                birthdate_serialized = result[4].strftime("%Y-%m-%d")
                content = { 'userId': result[0],
                            'email' : result[1],
                            'username' : result[2],
                            'bio' : result[3],
                            'birthdate' : birthdate_serialized,
                            'imageUrl' : result[5],
                            'bannerUrl' : result[6]
                            }
                follow_list.append(content)
            cnnct_to_db.endConn()
        else:
            cnnct_to_db.endConn()
            return Response(json.dumps("Incorrect data type received"),
                                mimetype="text/plain",
                                status=200)

        return Response(json.dumps(follow_list),
                                    mimetype="application/json",
                                    status=200)

def post_follow():
    try:
        data = request.json
        checklist = ["loginToken", "followId"]
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
                'name': 'followId',
                'datatype': int,
                'maxLength': 10,
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
    client_followId = data.get('followId')

    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()

        #check loginToken if exists
        cnnct_to_db.cursor.execute("SELECT user.id,loginToken FROM user INNER JOIN user_session ON user_session.userId = user.id WHERE user_session.loginToken =?", [client_loginToken])
        info_match = cnnct_to_db.cursor.fetchone()
        #check for a row match
        if info_match == None:
            return Response("No matching results were found",
                                mimetype="text/plain",
                                status=400)

        follower_user_id = info_match[0]
        
        cnnct_to_db.cursor.execute("SELECT id FROM user WHERE id=?",[client_followId])
        user_id_match = cnnct_to_db.cursor.fetchall()
        if(user_id_match == None):
            return Response("Failed to update",
                            mimetype="text/plain",
                            status=400)

        cnnct_to_db.cursor.execute("INSERT INTO follow(follower,followed) VALUES(?,?)",[follower_user_id,client_followId])
        if(cnnct_to_db.cursor.rowcount == 1):
            cnnct_to_db.conn.commit()
        else:
            return Response("Failed to update",
                                mimetype="text/plain",
                                status=400)

        return Response("Follow sucessful",
                                mimetype="text/plain",
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

def delete_follow():
    try:
        data = request.json
        checklist = ["loginToken", "followId"]
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
                'name': 'followId',
                'datatype': int,
                'maxLength': 10,
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
    client_followId = data.get('followId')

    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()

        #check loginToken if exists
        cnnct_to_db.cursor.execute("SELECT user.id,loginToken FROM user INNER JOIN user_session ON user_session.userId = user.id WHERE user_session.loginToken =?", [client_loginToken])
        info_match = cnnct_to_db.cursor.fetchone()
        #check for a row match
        if info_match == None:
            return Response("No matching results were found",
                                mimetype="text/plain",
                                status=400)

        follower_user_id = info_match[0]
        
        cnnct_to_db.cursor.execute("SELECT id FROM user WHERE id=?",[client_followId])
        user_id_match = cnnct_to_db.cursor.fetchall()
        if(user_id_match == None):
            return Response("Failed to update",
                            mimetype="text/plain",
                            status=400)

        cnnct_to_db.cursor.execute("DELETE FROM follow WHERE follower=? AND followed=?",[follower_user_id,client_followId])
        if(cnnct_to_db.cursor.rowcount == 1):
            cnnct_to_db.conn.commit()
        else:
            return Response("Failed to update",
                                mimetype="text/plain",
                                status=400)

        return Response("Follow delete sucessful",
                                mimetype="text/plain",
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

@app.route('/api/follows', methods=['GET', 'POST', 'DELETE'])
def follows_api():
    if (request.method == 'GET'):
        return get_follows()
    elif (request.method == 'POST'):
        return post_follow()
    elif (request.method == 'DELETE'):
        return delete_follow()
    else:
        print("Something went wrong.")