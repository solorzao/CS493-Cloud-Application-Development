from flask import Flask, render_template, jsonify, redirect, request, url_for, session
import constants
import requests
import random
import json

app = Flask(__name__)
app.secret_key = constants.app_secret_key

CLIENT_ID = constants.client_id
CLIENT_SECRET = constants.client_secret
SCOPE = constants.scope
REDIRECT_URI = constants.redirect_uri


@app.route('/')
def index():
    return render_template('index.html')


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
        headers = {'Authorization': 'Bearer {}'.format(
            credentials['access_token'])}
        req_uri = 'https://people.googleapis.com/v1/people/me?personFields=names'
        res = requests.get(req_uri, headers=headers)
        user_info = json.loads(res.text)
        user_info = user_info['names']
        user_last_name = user_info[0]['familyName']
        user_first_name = user_info[0]['givenName']
        return render_template('userinfo.html', last_name=user_last_name, first_name=user_first_name, state_variable=session['state'])
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
        headers = {'Authorization': 'Bearer {}'.format(
            credentials['access_token'])}
        req_uri = 'https://people.googleapis.com/v1/people/me?personFields=names'
        res = requests.get(req_uri, headers=headers)
        user_info = json.loads(res.text)
        user_info = user_info['names']
        user_last_name = user_info[0]['familyName']
        user_first_name = user_info[0]['givenName']
        return render_template('userinfo.html', last_name=user_last_name, first_name=user_first_name, state_variable=session['state'])
    else:
        return (jsonify(Error="Session states did not match"), 400)


@ app.route('/about')
def about():
    return render_template('about.html')


@ app.route('/logout')
def logout():
    session.clear()
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
