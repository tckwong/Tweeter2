import dbcreds
import mariadb
from flask import Flask, request, Response
import json
import sys

#instantiate Flask object
app = Flask(__name__)
######################### Function List #######################################

class connectMariaDb:    
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
        return True

def endCursor(db):
    if (db.cursor != None):
        db.cursor.close()
    else:
        print("Cursor was never opened, nothing to close here.")
        if (db.conn != None):
            db.conn.close()
        else:
            print("Connection was never opened, nothing to close here.")
# class endCursor(connectMariaDb):
#     def __init__(self):
#         super().__init__()
#     def checkCursorConn(self):
#         if (self.cursor != None):
#             self.cursor.close()
#         else:
#             print("Cursor was never opened, nothing to close here.")
#         if (self.conn != None):
#             self.conn.close()
#         else:
#             print("Connection was never opened, nothing to close here.")
        
def getallUsers():
    cnnct_to_db = connectMariaDb()
    cnnct_to_db.connect()
    getParams = request.args.get("id")
    print("This is GET params", getParams)
    
    if (getParams is None):
        cnnct_to_db.cursor.execute("SELECT * FROM user")
        list = cnnct_to_db.cursor.fetchall()
        user_list = []
        content = {}
        for result in list:
            birthday = result[5]
            birthdate = birthday.strftime("%Y-%m-%d")
            content = {'username': result[1],
                        'email' : result[3],
                        'bio' : result[4],
                        'birthdate' : birthdate,
                        'imageUrl' : result[6],
                        'bannerUrl' : result[7]
                        }       
            user_list.append(content)
        #Check if cursor opened and close all connections
        endCursor(cnnct_to_db)
        return Response(json.dumps(user_list),
                                    mimetype="application/json",
                                    status=200)
    else:
        print("Incorrect GET function called")

def getUniqueUser(userID):
    cnnct_to_db = connectMariaDb()
    cnnct_to_db.cursor.execute("SELECT * FROM user WHERE id=?",[userID])
    userIdMatch = cnnct_to_db.cursor.fetchone()
    print(userIdMatch)
    user_list = []
    content = {}
    birthday = userIdMatch[5]
    birthdate = birthday.strftime("%Y-%m-%d")
    content = {'username': userIdMatch[1],
                'email' : userIdMatch[3],
                'bio' : userIdMatch[4],
                'birthdate' : birthdate,
                'imageUrl' : userIdMatch[6],
                'bannerUrl' : userIdMatch[7]
                }       
    user_list.append(content)
    #Check if cursor opened and close all connections
    #####################
    return Response(json.dumps(user_list),
                            mimetype="application/json",
                            status=200)

def createNewUser():
    cnnct_to_db = connectMariaDb()
    cnnct_to_db.connect()
    data = request.json
    print("This is client data", data)
    client_username = data.get('username')
    client_email = data.get('email')
    client_birthdate = data.get('birthdate')
    client_password = data.get('password')
    
    resp = {
        "email": data.get('email'),
        "username": data.get('username'),
        "password": data.get('password'),
        "bio": data.get('bio'),
        "birthdate": data.get('birthdate'),
        "imageUrl": data.get('imageUrl'),
        "bannerUrl": data.get('bannerUrl')
    }

    #cnnct_to_db.cursor.execute("INSERT INTO user(email, username, password, bio, birthdate, imageUrl, bannerUrl) VALUES(?,?,?,?,?,?,?)",[resp['email'],resp['username'],resp['password'],resp['bio'],resp['birthdate'],resp['imageUrl'],resp['bannerUrl']])
    try:
        cnnct_to_db.cursor.execute("INSERT INTO user(email, username, password, birthdate) VALUES(?,?,?,?)",[client_email, client_username, client_password, client_birthdate])
    except mariadb.DataError:
        print("Something wrong with your inputs")
    except mariadb.OperationalError:
            print("Operational error on query")
    if(cnnct_to_db.cursor.rowcount == 1):
        print("New user register sucessful")
        cnnct_to_db.conn.commit()
    else:
        print("Failed to update")        
    #Check if cursor opened and close all connections
    endCursor(cnnct_to_db)
    return Response(json.dumps(resp),
                            mimetype="application/json",
                            status=200)

################################  End of functions #################################################

@app.route('/')
def homepage():
    return "<h1>Hello World</h1>"

@app.route('/api/users', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def usersApi():
    if (request.method == 'GET'):
        return getallUsers()
    # elif (getParams != None):
    #     # getUniqueUser(getParams)

    elif (request.method == 'POST'):
        return createNewUser()
        
       
    # elif (request.method == 'PATCH'):
    #     data = request.json
    #     print("This is client data", data)

    #     animal_list[1] = data
    #     return Response(json.dumps(animal_list),
    #                             mimetype="application/json",
    #                             status=200)
    # elif (request.method == 'DELETE'):
    #     data = request.json
    #     print("This is client data", data)
    #     animal_selection = data["animal"]
        
    #     resp = {
    #         "animal": animal_selection
    #     }
    
    #     return Response(json.dumps(resp),
    #                             mimetype="application/json",
    #                             status=200)
    # else:
    #     print("Something went wrong")

# except mariadb.DataError:
#     print("Something wrong with your data")
# except mariadb.OperationalError: #Creating already existing table falls under OperationalError
#     print("Something wrong with the connection")
# except mariadb.ProgrammingError:
#     print("Your query was wrong")
# except mariadb.IntegrityError:
#     print("Your query would have broken the database")
# except ValueError:
#     print("Please input a username")
# except:
#     print("Something went wrong")

# finally:
#     if (cursor != None):
#         cursor.close()
#     else:
#         print("Cursor was never opened, nothing to close here.")
#     if (conn != None):
#         conn.close()
#     else:
#         print("Connection was never opened, nothing to close here.")

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
    print ("No arguement was provided")
    exit()

