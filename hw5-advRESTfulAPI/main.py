from google.cloud import datastore
from flask import Flask, request, make_response, abort, jsonify
import json
import sys
import constants

app = Flask(__name__)
client = datastore.Client()


def unique_check(boat_name):
    query = client.query(kind=constants.boats)
    results = list(query.fetch())
    for e in results:
        if e['name'] == boat_name:
            return "not unique"
    return "unique"


def validate_input(client_input, type):
    if type == "name":
        if isinstance(client_input, str):
            if all(x.isalnum() or x.isspace() for x in client_input):
                if len(client_input) < 1 or len(client_input) > 30:
                    return (jsonify(Error="The name of the boat must be greater than 1, but less than 30 char"), 400)
            else:
                return (jsonify(Error="The name of the boat must be a alphanumeric string only"), 400)
        else:
            return (jsonify(Error="The name of the boat must be a alphanumeric string only"), 400)
    elif type == "type":
        if isinstance(client_input, str):
            if all(x.isalpha() or x.isspace() for x in client_input):
                if len(client_input) < 1 or len(client_input) > 30:
                    return (jsonify(Error="The type of the boat must be greater than 1, but less than 30 char"), 400)
            else:
                return (jsonify(Error="The type of the boat must be a alphabetic string only"), 400)
        else:
            return (jsonify(Error="The type of the boat must be a alphabetic string only"), 400)
    elif type == "length":
        if isinstance(client_input, int):
            if client_input < 1 or client_input > 1000:
                return (jsonify(Error="The length of the boat must be greater than 1, but less than 1000"), 400)
        else:
            return (jsonify(Error="The length of the boat must be an integer"), 400)
    return "ok"


@app.route('/')
def index():
    return "This is the home page"


@app.route('/boats', methods=['POST', 'GET'])
def boats_get_post():
    if request.method == 'POST':
        if request.content_type == 'application/json':
            try:
                content = request.get_json()
                new_boat = datastore.entity.Entity(
                    key=client.key(constants.boats))
                name_check = unique_check(content["name"])
                if name_check == "unique":

                    input_status = validate_input(content["name"], "name")
                    if input_status != "ok":
                        return input_status
                    input_status = validate_input(content["type"], "type")
                    if input_status != "ok":
                        return input_status
                    input_status = validate_input(content["length"], "length")
                    if input_status != "ok":
                        return input_status

                    new_boat.update({"name": content["name"], "type": content["type"],
                                     "length": content["length"]})
                    client.put(new_boat)
                    new_boat["id"] = new_boat.key.id
                    new_boat["self"] = (
                        f"{request.url}/" + str(new_boat["id"]))
                else:
                    return (jsonify(Error="That name is currently in use, please provide a different name"), 403)
                if 'application/json' in request.accept_mimetypes or '*/*' in request.accept_mimetypes:
                    return (json.dumps(new_boat), 201)
                else:
                    return (jsonify(Error="Response not acceptable"), 406)
            except:
                return (jsonify(Error="The request object is missing at least one of the required attributes"), 400)
        else:
            return (jsonify(Error="Bad request, data must be in JSON format"), 415)
    elif request.method == 'GET':
        query = client.query(kind=constants.boats)
        results = list(query.fetch())
        for e in results:
            e["id"] = e.key.id
            e["self"] = (
                f"{request.url}/" + str(e["id"]))
        if 'application/json' in request.accept_mimetypes or '*/*' in request.accept_mimetypes:
            return (json.dumps(results), 200)
        else:
            return (jsonify(Error="Response not acceptable"), 406)
    else:
        return (jsonify(Error="Method not allowed"), 405)


@app.route('/boats/<id>', methods=['GET', 'PUT', 'PATCH', 'DELETE'])
def boat_get_put_patch_delete(id):
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
        if 'application/json' in request.accept_mimetypes:
            return (json.dumps(results[0]), 200)
        elif 'text/html' in request.accept_mimetypes:
            html_res = '<ul>' + \
                f'<li>id: {results[0]["id"]}</li>' + \
                f'<li>name: {results[0]["name"]}</li>' + \
                f'<li>type: {results[0]["type"]}</li>' + \
                f'<li>length: {results[0]["length"]}</li>' + \
                f'<li>self: {results[0]["self"]}</li>' + '</ul>'
            return html_res
        else:
            return (jsonify(Error="Response not acceptable"), 406)
    elif request.method == 'PUT':
        if request.content_type == 'application/json':
            content = request.get_json()
            boat_key = client.key(constants.boats, int(id))
            boat = client.get(key=boat_key)
            if boat is None:
                return (jsonify(Error="No boat with this boat_id exists"), 404)
            else:
                try:
                    name_check = unique_check(content["name"])
                    if name_check == "unique":
                        input_status = validate_input(content["name"], "name")
                        if input_status != "ok":
                            return input_status
                        input_status = validate_input(content["type"], "type")
                        if input_status != "ok":
                            return input_status
                        input_status = validate_input(
                            content["length"], "length")
                        if input_status != "ok":
                            return input_status

                        boat.update({"name": content["name"], "type": content["type"],
                                     "length": content["length"]})
                        client.put(boat)
                        boat["id"] = boat.key.id
                        boat["self"] = (
                            f"{request.url}")
                    else:
                        return (jsonify(Error="That name is currently in use, please provide a different name"), 403)
                    if 'application/json' in request.accept_mimetypes or '*/*' in request.accept_mimetypes:
                        res = make_response()
                        res.headers.set('Location', f'{boat["self"]}')
                        res.status_code = 303
                        return res
                    else:
                        return (jsonify(Error="Response not acceptable"), 406)
                except:
                    return (jsonify(Error="The request object is missing at least one of the required attributes"), 400)
        else:
            return (jsonify(Error="Bad request, data must be in JSON format"), 415)
    elif request.method == 'PATCH':
        if request.content_type == 'application/json':
            content = request.get_json()
            boat_key = client.key(constants.boats, int(id))
            boat = client.get(key=boat_key)
            if boat is None:
                return (jsonify(Error="No boat with this boat_id exists"), 404)
            else:
                if "name" in content or "type" in content or "length" in content:
                    if "name" in content:
                        name_check = unique_check(content["name"])
                        if name_check == "unique":
                            input_status = validate_input(
                                content["name"], "name")
                            if input_status != "ok":
                                return input_status
                            boat.update({"name": content["name"]})
                        else:
                            return (jsonify(Error="That name is currently in use, please provide a different name"), 403)
                    if "type" in content:
                        input_status = validate_input(content["type"], "type")
                        if input_status != "ok":
                            return input_status
                        boat.update({"type": content["type"]})
                    if "length" in content:
                        input_status = validate_input(
                            content["length"], "length")
                        if input_status != "ok":
                            return input_status
                        boat.update({"length": content["length"]})

                    client.put(boat)

                    boat["id"] = boat.key.id
                    boat["self"] = (
                        f"{request.url}")
                else:
                    return (jsonify(Error="The request object is missing at least one of the required attributes"), 400)

                if 'application/json' in request.accept_mimetypes or '*/*' in request.accept_mimetypes:
                    return (json.dumps(boat), 200)
                else:
                    return (jsonify(Error="Response not acceptable"), 406)
        else:
            return (jsonify(Error="Bad request, data must be in JSON format"), 415)
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
        return (jsonify(Error="Method not allowed"), 405)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
