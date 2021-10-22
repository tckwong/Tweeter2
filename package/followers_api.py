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

def get_followers():
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
                cnnct_to_db.cursor.execute("SELECT id,email,username,bio,birthdate,imageUrl,bannerUrl FROM user INNER JOIN follow ON user.id = follower WHERE followed =?", [params_id])
                follower_id_match = cnnct_to_db.cursor.fetchall()
                
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
            for result in follower_id_match:
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
@app.route('/api/followers', methods=['GET'])
def followers_api():
    if (request.method == 'GET'):
        return get_followers()
    else:
        print("Something went wrong.")