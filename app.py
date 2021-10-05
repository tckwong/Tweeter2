import dbcreds
import mariadb
from flask import Flask, request, Response
import json

#instantiate Flask object
app = Flask(__name__)

conn = None
cursor = None

try:
    animal_list = [
                {'animal': "snake"},
                {'animal': "giraffe"},
                {'animal': "tiger"}
            ]
    @app.route('/animals', methods=['GET', 'POST', 'PATCH', 'DELETE'])
    def animals():
        if (request.method == 'GET'):
            conn = mariadb.connect(
                user=dbcreds.user, password=dbcreds.password, host=dbcreds.host, port=dbcreds.port, database=dbcreds.database)
            cursor = conn.cursor()
            args = request.args
            print("This is GET params", args)
            cursor.execute("SELECT name FROM my_animals")
            list = cursor.fetchall()
            animal_list_new = []
            content = {}
            for result in list:
                content = {'animal': result[0]}
                animal_list_new.append(content)
            
            #Check if cursor opened and close all connections
            if (cursor != None):
                cursor.close()
            else:
                print("Cursor was never opened, nothing to close here.")
            if (conn != None):
                conn.close()
            else:
                print("Connection was never opened, nothing to close here.")
            
            return Response(json.dumps(animal_list_new),
                                    mimetype="application/json",
                                    status=200)
        
        elif (request.method == 'POST'):
            data = request.json
            print("This is client data", data)
        
            return Response(json.dumps(animal_list),
                                    mimetype="application/json",
                                    status=200) 
        elif (request.method == 'PATCH'):
            data = request.json
            print("This is client data", data)

            animal_list[1] = data
            return Response(json.dumps(animal_list),
                                    mimetype="application/json",
                                    status=200) 
        elif (request.method == 'DELETE'):
            data = request.json
            print("This is client data", data)
            animal_selection = data["animal"]
            
            resp = {
                "animal": animal_selection
            }
        
            return Response(json.dumps(resp),
                                    mimetype="application/json",
                                    status=200)
        else:
            print("Something went wrong")

except mariadb.DataError:
    print("Something wrong with your data")
except mariadb.OperationalError: #Creating already existing table falls under OperationalError
    print("Something wrong with the connection")
except mariadb.ProgrammingError:
    print("Your query was wrong")
except mariadb.IntegrityError:
    print("Your query would have broken the database")
except ValueError:
    print("Please input a username")
except:
    print("Something went wrong")

finally:
    if (cursor != None):
        cursor.close()
    else:
        print("Cursor was never opened, nothing to close here.")
    if (conn != None):
        conn.close()
    else:
        print("Connection was never opened, nothing to close here.")



