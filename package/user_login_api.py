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
    def __init__(self):
        super().__init__("Invalid loginToken sent")

def validate_misc_data(list, data):
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

def login_user():
    data = request.json
    check_data_lst = ["email", "password"]
    if not validate_misc_data(check_data_lst,data):
        return Response("Incorrect data keys received",
                                    mimetype="text/plain",
                                    status=400)
    requirements = [
            {   'name': 'email',
                'datatype': str,
                'maxLength': 20,
                'required': True
            },
            {   'name': 'password',
                'datatype': str,
                'maxLength': 20,
                'required': True
            },
        ]

    validate_data(requirements,data)
    check_data_required(requirements,data)
    
    client_email = data.get('email')
    client_password = data.get('password')

    try:
        if type(client_email) != str or type(client_password) != str:
            raise TypeError()
    except TypeError:
        return Response("Invalid data sent!",
                        mimetype="text/plain",
                        status=400)
    
    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()

        cnnct_to_db.cursor.execute("SELECT id, email, username, bio, birthdate, imageUrl, bannerUrl FROM user WHERE email=? and password=?",[client_email,client_password])
        match = cnnct_to_db.cursor.fetchone()
        #Only returns one row, so only one combination is valid
        if match == None:
            return Response("No matching login combination",
                            mimetype="plain/text",
                            status=400)
        else:
            client_id = match[0]
            client_email = match[1]
            client_username = match[2]
            client_bio = match[3]
            birthdate_serialized = match[4].strftime("%Y-%m-%d")
            client_birthdate=birthdate_serialized
            client_imageUrl = match[5]
            client_bannerUrl = match[6]
        
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
    
    #create unique login token
    import uuid
    generateUuid = uuid.uuid4().hex
    str(generateUuid)

    try:
        cnnct_to_db.cursor.execute("INSERT INTO user_session (userId, loginToken) VALUES(?,?)",[client_id, generateUuid])
        cnnct_to_db.conn.commit()
        cnnct_to_db.cursor.execute("SELECT loginToken FROM user_session  WHERE userId =? ORDER BY id DESC LIMIT 1",[client_id])
        get_token = cnnct_to_db.cursor.fetchone()
        client_token = get_token[0]
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

    resp = {
        "userId": client_id,
        "email": client_email,
        "username": client_username,
        "bio": client_bio,
        "birthdate": client_birthdate,
        "loginToken": client_token,
        "imageUrl": client_imageUrl,
        "bannerUrl": client_bannerUrl
    }
    return Response(json.dumps(resp),
                                mimetype="application/json",
                                status=201)

def logout_user():
    try:
        data = request.json
        checklist = ["username","loginToken"]
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
            {   'name': 'username',
                'datatype': str,
                'maxLength': 30,
                'required': True
            },
        ]
        validate_data(requirements,data)
        check_data_required(requirements,data)

        client_loginToken = data.get('loginToken')
        client_username = data.get('username')

        for item in checklist:
            if item is None:
                return Response("Error! Missing required data",
                            mimetype="text/plain",
                            status=400)
    except ValueError:
        return Response("Invalid data sent",
                                    mimetype="text/plain",
                                    status=400)
    except TypeError:
        return Response("Invalid data type sent",
                                    mimetype="text/plain",
                                    status=400)
    
    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()

        cnnct_to_db.cursor.execute("SELECT user.id, password, loginToken, username FROM user INNER JOIN user_session ON user_session.userId = user.id WHERE username=? and loginToken=?",[client_username,client_loginToken])
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
    
    match = cnnct_to_db.cursor.fetchone()
    #Only returns one row, so only one combination is valid
    if match == None:
        return Response("Incorrect data was received",
                        mimetype="plain/text",
                        status=400)

    try:
        cnnct_to_db = MariaDbConnection()
        cnnct_to_db.connect()
        cnnct_to_db.cursor.execute("DELETE FROM user_session WHERE userId=?", [match[0]])
        cnnct_to_db.conn.commit()
        return Response("Logged out successfully",
                        mimetype="text/plain",
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

@app.route('/api/login', methods=['POST', 'DELETE'])
def login_api():
    if (request.method == 'POST'):
        return login_user()
        
    elif (request.method == 'DELETE'):
        return logout_user()
    else:
        print("Something went wrong.")
