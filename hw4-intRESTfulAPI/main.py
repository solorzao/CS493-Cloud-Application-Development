from google.cloud import datastore
from flask import Flask, request, Response, abort, jsonify
import json
import sys
import constants

app = Flask(__name__)
client = datastore.Client()


@app.route('/')
def index():
    return "This is the home page"


def get_results(resultType, cursor):
    query = client.query(kind=resultType)
    results = query.fetch(start_cursor=cursor, limit=3)
    page = next(results.pages)
    resultList = list(page)
    nextCursor = results.next_page_token
    return resultList, nextCursor


@app.route('/boats', methods=['POST', 'GET'])
def boats_get_post():
    if request.method == 'POST':
        try:
            content = request.get_json()
            new_boat = datastore.entity.Entity(key=client.key(constants.boats))
            new_boat.update({"name": content["name"], "type": content["type"],
                             "length": content["length"], "loads": None})
            client.put(new_boat)
            new_boat["id"] = new_boat.key.id
            new_boat["self"] = (
                f"{request.url}/" + str(new_boat["id"]))
            return (json.dumps(new_boat), 201)
        except:
            return (jsonify(Error="The request object is missing at least one of the required attributes"), 400)
    elif request.method == 'GET':
        cursor = None
        results, nextCursor = get_results(constants.boats, cursor)
        for result in results:
            if result["loads"] != None:
                loads = json.loads(result["loads"])
                for load in loads:
                    self_url = f"{request.url}/" + str(load["id"])
                    load["self"] = self_url.replace("boats", "loads")
                result["loads"] = loads
            result["id"] = result.key.id
            result["self"] = (
                f"{request.url}/" + str(result["id"]))
        if len(results) < 3:
            return (json.dumps(results), 200)
        else:
            if nextCursor != None:
                res = {}
                boats = json.dumps(results)
                res["boats"] = json.loads(boats)
                next_url = (f"{request.url}/results/" +
                            str(nextCursor, 'UTF-8'))
                res["next"] = next_url
                return (json.dumps(res), 200)
            else:
                return (json.dumps(results), 200)
    else:
        return 'Method not recognized'


@app.route('/boats/<id>', methods=['GET', 'DELETE'])
def boat_get_delete(id):
    if request.method == 'GET':
        boat_key = client.key(constants.boats, int(id))
        query = client.query(kind=constants.boats)
        query.key_filter(boat_key, '=')
        results = list(query.fetch())
        if len(results) == 0:
            return (jsonify(Error="No boat with this boat_id exists"), 404)
        else:
            for result in results:
                if result["loads"] != None:
                    loads = json.loads(result["loads"])
                    for load in loads:
                        self_url = f"{request.url}/" + str(load["id"])
                        load["self"] = self_url.replace(f"boats/{id}", "loads")
                    result["loads"] = loads
                result["id"] = result.key.id
                result["self"] = (
                    f"{request.url}")
        return (json.dumps(results[0]), 200)
    elif request.method == 'DELETE':
        boat_key = client.key(constants.boats, int(id))
        query = client.query(kind=constants.boats)
        query.key_filter(boat_key, '=')
        results = list(query.fetch())
        if len(results) == 0:
            return (jsonify(Error="No boat with this boat_id exists"), 404)
        else:
            for result in results:
                if result["loads"] != None:
                    loads = json.loads(result["loads"])
                    for load in loads:
                        load_key = client.key(constants.loads, load["id"])
                        load = client.get(key=load_key)
                        load["carrier"] = None
                        client.put(load)
                client.delete(boat_key)
        return ('', 204)


@app.route('/boats/<id>/loads', methods=['GET'])
def boat_loads_get(id):
    if request.method == 'GET':
        boat_key = client.key(constants.boats, int(id))
        query = client.query(kind=constants.boats)
        query.key_filter(boat_key, '=')
        results = list(query.fetch())
        if len(results) == 0:
            return (jsonify(Error="No boat with this boat_id exists"), 404)
        else:
            loads = {}
            loads = json.loads(results[0]['loads'])
            for load in loads:
                self_url = f"{request.url}/" + str(load["id"])
                load["self"] = self_url.replace(f"boats/{id}/", "")
            return (json.dumps(loads), 200)
    else:
        return 'Method not recognized'


@app.route('/boats/results/<cursor>', methods=['GET'])
def boats_get(cursor):
    if request.method == 'GET':
        if cursor != None:
            try:
                results, nextCursor = get_results(constants.boats, cursor)
                for result in results:
                    if result["loads"] != None:
                        loads = json.loads(result["loads"])
                        for load in loads:
                            self_url = f"{request.url}/" + str(load["id"])
                            self_url = self_url.replace("%3D%3D", "==")
                            load["self"] = self_url.replace(
                                f"boats/results/{cursor}", "loads")
                        result["loads"] = loads
                    result["id"] = result.key.id
                    self_url = (
                        f"{request.url}")
                    self_url = self_url.replace("%3D%3D", "==")
                    self_url = self_url.replace("/results", "")
                    self_url = self_url.replace(cursor, str(result.key.id))
                    result["self"] = self_url
                if len(results) < 3:
                    return (json.dumps(results), 200)
                else:
                    if nextCursor != None:
                        res = {}
                        boats = json.dumps(results)
                        res["boats"] = json.loads(boats)
                        next_url = f"{request.url}"
                        next_url = next_url.replace("%3D%3D", "==")
                        next_url = next_url.replace(
                            cursor, str(nextCursor, 'UTF-8'))
                        res["next"] = next_url
                        return (json.dumps(res), 200)
                    else:
                        return (json.dumps(results), 200)
            except:
                return (jsonify(Error="Invalid cursor provided"), 400)
        else:
            return (jsonify(Error="Cursor provided is null"), 400)
    else:
        return 'Method not recognized'


@app.route('/loads', methods=['POST', 'GET'])
def loads_get_post():
    if request.method == 'POST':
        try:
            content = request.get_json()
            new_load = datastore.entity.Entity(key=client.key(constants.loads))
            new_load.update({"weight": content["weight"], "carrier": None,
                             "content": content["content"], "delivery_date": content["delivery_date"]})
            client.put(new_load)
            new_load["id"] = new_load.key.id
            new_load["self"] = (
                f"{request.url}/" + str(new_load["id"]))
            return (json.dumps(new_load), 201)
        except:
            return (jsonify(Error="The request object is missing at least one of the required attributes"), 400)
    elif request.method == 'GET':
        cursor = None
        results, nextCursor = get_results(constants.loads, cursor)
        for result in results:
            if result["carrier"] != None:
                carrier = json.loads(result["carrier"])
                carrier_url = f"{request.url}/" + str(carrier["id"])
                carrier_url = carrier_url.replace("loads", "boats")
                carrier["self"] = carrier_url
                result["carrier"] = carrier
            result["id"] = result.key.id
            result["self"] = (
                f"{request.url}/" + str(result["id"]))
        if len(results) < 3:
            return (json.dumps(results), 200)
        else:
            if nextCursor != None:
                res = {}
                loads = json.dumps(results)
                res["loads"] = json.loads(loads)
                next_url = (f"{request.url}/results/" +
                            str(nextCursor, 'UTF-8'))
                res["next"] = next_url
                return (json.dumps(res), 200)
            else:
                return (json.dumps(results), 200)
    else:
        return 'Method not recognized'


@app.route('/loads/<id>', methods=['GET', 'DELETE'])
def load_get_delete(id):
    if request.method == 'GET':
        load_key = client.key(constants.loads, int(id))
        query = client.query(kind=constants.loads)
        query.key_filter(load_key, '=')
        results = list(query.fetch())
        if len(results) == 0:
            return (jsonify(Error="No load with this load_id exists"), 404)
        else:
            for result in results:
                if result["carrier"] != None:
                    carrier = json.loads(result["carrier"])
                    carrier_url = f"{request.url}/" + str(carrier["id"])
                    carrier_url = carrier_url.replace(f"loads/{id}", "boats")
                    carrier["self"] = carrier_url
                    result["carrier"] = carrier
                result["id"] = result.key.id
                result["self"] = (
                    f"{request.url}")
        return (json.dumps(results[0]), 200)
    elif request.method == 'DELETE':
        load_key = client.key(constants.loads, int(id))
        query = client.query(kind=constants.loads)
        query.key_filter(load_key, '=')
        results = list(query.fetch())
        if len(results) == 0:
            return (jsonify(Error="No load with this load_id exists"), 404)
        else:
            for result in results:
                if result["carrier"] != None:
                    carrier = json.loads(result["carrier"])
                    boat_key = client.key(constants.boats, carrier["id"])
                    boat = client.get(key=boat_key)
                    all_loads = json.loads(boat["loads"])
                    for load in all_loads:
                        if load["id"] == load_key.id:
                            all_loads.remove(load)

                    if len(all_loads) == 0:
                        boat.update({"loads": None})
                    else:
                        all_loads = json.dumps(all_loads)
                        boat.update({"loads": all_loads})

                    client.put(boat)
                client.delete(load_key)
        return ('', 204)


@app.route('/loads/results/<cursor>', methods=['GET'])
def loads_get(cursor):
    if request.method == 'GET':
        if cursor != None:
            try:
                results, nextCursor = get_results(constants.loads, cursor)
                for result in results:
                    if result["carrier"] != None:
                        carrier = json.loads(result["carrier"])
                        carrier_url = f"{request.url}/" + str(carrier["id"])
                        carrier_url = carrier_url.replace("%3D%3D", "==")
                        carrier_url = carrier_url.replace(
                            f"loads/results/{cursor}", "boats")
                        carrier["self"] = carrier_url
                        result["carrier"] = carrier
                        result["carrier"] = carrier
                    result["id"] = result.key.id
                    self_url = (
                        f"{request.url}")
                    self_url = self_url.replace("%3D%3D", "==")
                    self_url = self_url.replace("/results", "")
                    self_url = self_url.replace(cursor, str(result.key.id))
                    result["self"] = self_url
                if len(results) < 3:
                    return (json.dumps(results), 200)
                else:
                    if nextCursor != None:
                        res = {}
                        loads = json.dumps(results)
                        res["loads"] = json.loads(loads)
                        next_url = f"{request.url}"
                        next_url = next_url.replace("%3D%3D", "==")
                        next_url = next_url.replace(
                            cursor, str(nextCursor, 'UTF-8'))
                        res["next"] = next_url
                        return (json.dumps(res), 200)
                    else:
                        return (json.dumps(results), 200)
            except:
                return (jsonify(Error="Invalid cursor provided"), 400)
        else:
            return (jsonify(Error="Cursor provided is null"), 400)
    else:
        return 'Method not recognized'


@app.route('/boats/<boat_id>/loads/<load_id>', methods=['PUT', 'DELETE'])
def boats_loads_put_delete(boat_id, load_id):
    if request.method == 'PUT':
        boat_key = client.key(constants.boats, int(boat_id))
        boat = client.get(key=boat_key)
        if boat is not None:
            load_key = client.key(constants.loads, int(load_id))
            load = client.get(key=load_key)
            if load is None:
                return (jsonify(Error="The specified boat and/or load does not exist"), 404)
            query = client.query(kind=constants.loads)  # get load object
            query.key_filter(load_key, '=')
            load_entity = list(query.fetch())

            query = client.query(kind=constants.boats)  # get boat object
            query.key_filter(boat_key, '=')
            boat_entity = list(query.fetch())

            if load_entity[0]["carrier"] == None:
                boat_info = {}  # add boat info to load
                boat_info["name"] = boat_entity[0]["name"]
                boat_info["id"] = boat.key.id
                boat_info = json.dumps(boat_info)
                load_entity[0].update({"carrier": boat_info})
                client.put(load_entity[0])

                # add load info to boat
                if boat_entity[0]["loads"] != None:
                    all_loads = json.loads(boat_entity[0]["loads"])
                else:
                    all_loads = []

                load_info = {}
                load_info["id"] = load.key.id
                all_loads.append(load_info)
                all_loads = json.dumps(all_loads)
                boat_entity[0].update({"loads": all_loads})
                client.put(boat_entity[0])

                return ('', 204)
            else:
                return (jsonify(Error="The current load is already assigned to a boat"), 403)

        else:
            return (jsonify(Error="The specified boat and/or load does not exist"), 404)

    elif request.method == 'DELETE':
        boat_key = client.key(constants.boats, int(boat_id))
        boat = client.get(key=boat_key)
        if boat is not None:
            load_key = client.key(constants.loads, int(load_id))
            load = client.get(key=load_key)
            if load is None:
                return (jsonify(Error="The specified boat and/or load does not exist"), 404)
            query = client.query(kind=constants.loads)  # get load object
            query.key_filter(load_key, '=')
            load_entity = list(query.fetch())

            query = client.query(kind=constants.boats)  # get boat object
            query.key_filter(boat_key, '=')
            boat_entity = list(query.fetch())

            if load_entity[0]["carrier"] != None:
                try:
                    boat_info = {}  # remove boat info from load
                    boat_info["name"] = boat_entity[0]["name"]
                    boat_info["id"] = boat.key.id
                    boat_info = json.dumps(boat_info)
                    load_entity[0].update({"carrier": None})

                    # remove load info from boat
                    if boat_entity[0]["loads"] != None:
                        all_loads = json.loads(boat_entity[0]["loads"])
                    else:
                        all_loads = []

                    for load in all_loads:
                        if load["id"] == load_key.id:
                            all_loads.remove(load)

                    if len(all_loads) == 0:
                        boat_entity[0].update({"loads": None})
                    else:
                        all_loads = json.dumps(all_loads)
                        boat_entity[0].update({"loads": all_loads})

                    client.put(boat_entity[0])
                    client.put(load_entity[0])
                    return ('', 204)
                except:
                    return (jsonify(Error="The current load is not assigned to this boat"), 403)
            else:
                return (jsonify(Error="The specified boat and/or load does not exist"), 404)

        else:
            return (jsonify(Error="The specified boat and/or load does not exist"), 404)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
