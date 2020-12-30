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


@app.route('/boats', methods=['POST', 'GET'])
def boats_get_post():
    if request.method == 'POST':
        try:
            content = request.get_json()
            new_boat = datastore.entity.Entity(key=client.key(constants.boats))
            new_boat.update({"name": content["name"], "type": content["type"],
                             "length": content["length"]})
            client.put(new_boat)
            new_boat["id"] = new_boat.key.id
            new_boat["self"] = (
                f"{request.url}/" + str(new_boat["id"]))
            return (json.dumps(new_boat), 201)
        except:
            return (jsonify(Error="The request object is missing at least one of the required attributes"), 400)
    elif request.method == 'GET':
        query = client.query(kind=constants.boats)
        results = list(query.fetch())
        for e in results:
            e["id"] = e.key.id
            e["self"] = (
                f"{request.url}/" + str(e["id"]))
        return (json.dumps(results), 200)
    else:
        return 'Method not recognized'


@app.route('/slips', methods=['POST', 'GET'])
def slips_get_post():
    if request.method == 'POST':
        try:
            content = request.get_json()
            new_slip = datastore.entity.Entity(key=client.key(constants.slips))
            new_slip.update(
                {"number": content["number"], "current_boat": None})
            client.put(new_slip)
            new_slip["id"] = new_slip.key.id
            new_slip["self"] = (
                f"{request.url}/" + str(new_slip["id"]))
            return (json.dumps(new_slip), 201)
        except:
            return (jsonify(Error="The request object is missing the required number"), 400)
    elif request.method == 'GET':
        query = client.query(kind=constants.slips)
        results = list(query.fetch())
        for e in results:
            e["id"] = e.key.id
            e["self"] = (
                f"{request.url}/" + str(e["id"]))
        return (json.dumps(results), 200)

    else:
        return 'Method not recognized'


@app.route('/boats/<id>', methods=['PATCH', 'GET', 'DELETE'])
def boat_patch_get_delete(id):
    if request.method == 'GET':
        boat_key = client.key(constants.boats, int(id))
        query = client.query(kind=constants.boats)
        query.key_filter(boat_key, '=')
        results = list(query.fetch())
        if len(results) == 0:
            return (jsonify(Error="No boat with this boat_id exists"), 404)
        else:
            for e in results:
                e["id"] = e.key.id
                e["self"] = (
                    f"{request.url}")
        return (json.dumps(results[0]), 200)
    elif request.method == 'PATCH':
        content = request.get_json()
        boat_key = client.key(constants.boats, int(id))
        boat = client.get(key=boat_key)
        if boat is None:
            return (jsonify(Error="No boat with this boat_id exists"), 404)
        else:
            try:
                boat.update({"name": content["name"], "type": content["type"],
                             "length": content["length"]})
                client.put(boat)
                boat["id"] = boat.key.id
                boat["self"] = (
                    f"{request.url}")
                return (json.dumps(boat), 200)
            except:
                return (jsonify(Error="The request object is missing at least one of the required attributes"), 400)
    elif request.method == 'DELETE':
        boat_key = client.key(constants.boats, int(id))
        boat = client.get(key=boat_key)
        if boat is not None:
            query = client.query(kind=constants.slips)
            results = list(query.fetch())
            for e in results:
                if e["current_boat"] == boat_key.id:
                    e.update({"current_boat": None})
                    client.put(e)
            client.delete(boat_key)
            return ('', 204)
        else:
            return (jsonify(Error="No boat with this boat_id exists"), 404)
    else:
        return 'Method not recognized'


@app.route('/slips/<id>', methods=['GET', 'DELETE'])
def slips_get_delete(id):
    if request.method == 'GET':
        slip_key = client.key(constants.slips, int(id))
        query = client.query(kind=constants.slips)
        query.key_filter(slip_key, '=')
        results = list(query.fetch())
        if len(results) == 0:
            return (jsonify(Error="No slip with this slip_id exists"), 404)
        else:
            for e in results:
                e["id"] = e.key.id
                e["self"] = (
                    f"{request.url}")
        return (json.dumps(results[0]), 200)
    elif request.method == 'DELETE':
        slip_key = client.key(constants.slips, int(id))
        slip = client.get(key=slip_key)
        if slip is not None:
            client.delete(slip_key)
            return ('', 204)
        else:
            return (jsonify(Error="No slip with this slip_id exists"), 404)
    else:
        return 'Method not recognized'


@app.route('/slips/<slip_id>/<boat_id>', methods=['PUT', 'DELETE'])
def slips_boats_put_delete(slip_id, boat_id):
    if request.method == 'PUT':
        slip_key = client.key(constants.slips, int(slip_id))
        slip = client.get(key=slip_key)
        if slip is not None:
            boat_key = client.key(constants.boats, int(boat_id))
            boat = client.get(key=boat_key)
            if boat is None:
                return (jsonify(Error="The specified boat and/or slip does not exist"), 404)
            query = client.query(kind=constants.slips)
            query.key_filter(slip_key, '=')
            results = list(query.fetch())
            for e in results:
                if e["current_boat"] == None:
                    slip.update({"current_boat": boat_key.id})
                    client.put(slip)
                    return ('', 204)
                else:
                    return (jsonify(Error="The slip is not empty"), 403)
        else:
            return (jsonify(Error="The specified boat and/or slip does not exist"), 404)

    elif request.method == 'DELETE':
        slip_key = client.key(constants.slips, int(slip_id))
        slip = client.get(key=slip_key)
        if slip is not None:
            boat_key = client.key(constants.boats, int(boat_id))
            boat = client.get(key=boat_key)
            if boat is None:
                return (jsonify(Error="No boat with this boat_id is at the slip with this slip_id"), 404)
            query = client.query(kind=constants.slips)
            query.key_filter(slip_key, '=')
            results = list(query.fetch())
            for e in results:
                if e["current_boat"] == boat_key.id:
                    slip.update({"current_boat": None})
                    client.put(slip)
                    return ('', 204)
                else:
                    return (jsonify(Error="No boat with this boat_id is at the slip with this slip_id"), 404)
        else:
            return (jsonify(Error="No boat with this boat_id is at the slip with this slip_id"), 404)
    else:
        return 'Method not recognized'


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
