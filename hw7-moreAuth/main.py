from flask import Flask, render_template, jsonify, redirect, request, url_for, session, make_response, abort
from google.cloud import datastore
from google.oauth2 import id_token
from google.auth import crypt
from google.auth import jwt
from google.auth.transport import requests as id_requests
import requests
import constants
import random
import json

app = Flask(__name__)
client = datastore.Client()
app.secret_key = constants.app_secret_key

CLIENT_ID = constants.client_id
CLIENT_SECRET = constants.client_secret
SCOPE = constants.scope
REDIRECT_URI = constants.redirect_uri


def get_sub_info():
    if 'Authorization' in request.headers:
        user_jwt = request.headers['Authorization']
        user_jwt = user_jwt.replace('Bearer ', '')
        req = id_requests.Request()    
        
        try:
            id_info = id_token.verify_oauth2_token(
                user_jwt, req, CLIENT_ID)
            sub_info = id_info['sub']
            return sub_info
        except:
            return "Error"
    else:
        return "Error"

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/boats', methods=['POST', 'GET'])
def boats_get_post():
    if request.method == 'POST':
        try:
            content = request.get_json()
            new_boat = datastore.entity.Entity(key=client.key(constants.boats))
            new_boat.update({"name": content["name"], "type": content["type"],
                             "length": content["length"], "public": content["public"]})
            owner = get_sub_info()

            if owner != "Error":
                new_boat.update({"owner": owner})
                client.put(new_boat)

                new_boat["id"] = new_boat.key.id
                new_boat["self"] = (
                    f"{request.url}/" + str(new_boat["id"]))
                return (json.dumps(new_boat), 201)
            else:
                return (jsonify(Error="Missing or invalid JWT"), 401)
        except:
            return (jsonify(Error="The request object is missing at least one of the required attributes"), 400)
    elif request.method == 'GET':
        query = client.query(kind=constants.boats)
        results = list(query.fetch())
        for e in results:
            e["id"] = e.key.id
            e["self"] = (
                f"{request.url}/" + str(e["id"]))
        boat_list = []
        owner = get_sub_info()

        if owner != "Error":
            for e in results:
                if e["owner"] == owner:
                    boat_list.append(e)
        else:
            for e in results:
                if e["public"] == True:
                    boat_list.append(e)

        return (json.dumps(boat_list), 200)
    else:
        return 'Method not recognized'


@app.route('/boats/<id>', methods=['DELETE'])
def boat_delete(id):
    if request.method == 'DELETE':
        owner = get_sub_info()

        if owner != "Error":
            boat_key = client.key(constants.boats, int(id))
            boat = client.get(key=boat_key)
            if boat is not None:
                if boat["owner"] == owner:
                    client.delete(boat_key)
                    return ('', 204)
                else:
                    return (jsonify(Error="The boat associated with this ID is owned by someone else, it can only be deleted by the owner."), 403)
            else:
                return (jsonify(Error="No boat with this boat_id exists"), 403)
        else:
            return (jsonify(Error="Missing or invalid JWT"), 401)
    else:
        return 'Method not recognized'


@app.route('/owners/<id>/boats', methods=['GET'])
def owner_boats_get(id):
    if request.method == 'GET':
        query = client.query(kind=constants.boats)
        results = list(query.fetch())

        boat_list = []

        for e in results:
            e["id"] = e.key.id
            e["self"] = (
                f"{request.url}/" + str(e["id"]))
            if e["public"] == True and e["owner"] == id:
                boat_list.append(e)

        return (json.dumps(boat_list), 200)
    else:
        return 'Method not recognized'


@app.route('/oauth')
def oauth():
    if 'credentials' not in session:
        session['state'] = "randomstate" + str(random.randint(1, 9999999))
        request_url = f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={SCOPE}&state={session['state']}"
        return redirect(request_url)
    credentials = json.loads(session['credentials'])
    if credentials['expires_in'] <= 0:
        session['state'] = "randomstate" + str(random.randint(1, 9999999))
        request_url = f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={SCOPE}&state={session['state']}"
        return redirect(request_url)
    else:
        return render_template('oauth.html')


@app.route('/userinfo')
def user_info():
    if 'code' not in request.args and 'credentials' not in session:
        return render_template('userinfobad.html', message="Please navigate to the OAuth tab for authorization first.")
    if 'credentials' in session:
        credentials = json.loads(session['credentials'])
        req = id_requests.Request()
        try:
            id_token.verify_oauth2_token(
                credentials['id_token'], req, CLIENT_ID)
            return render_template('userinfo.html', jwt_var=credentials['id_token'])
        except:
            return (jsonify(Error="Invalid credentials, session may have expired. Please login again."), 401)
    if request.args.get('state') == session.get('state'):
        auth_code = request.args.get('code')
        data = {'code': auth_code,
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'redirect_uri': REDIRECT_URI,
                'grant_type': 'authorization_code'}
        res = requests.post(
            'https://oauth2.googleapis.com/token', data=data)
        session['credentials'] = res.text
        credentials = json.loads(session['credentials'])
        req = id_requests.Request()
        try:
            id_token.verify_oauth2_token(
                credentials['id_token'], req, CLIENT_ID)
            return render_template('userinfo.html', jwt_var=credentials['id_token'])
        except:
            return (jsonify(Error="Missing or invalid JWT"), 401)
    else:
        return (jsonify(Error="Session states did not match"), 400)


@ app.route('/about')
def about():
    return render_template('about.html')


@ app.route('/logout')
def logout():
    session.clear()
    return render_template('logout.html')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
