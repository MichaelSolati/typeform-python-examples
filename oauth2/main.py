import json
import requests
import flask
from urllib.parse import urlencode
import os

# We'll fetch our environment variables here. See `.env.sample.yml` to learn how to configure this...
gcpProjectId = os.environ.get('GCPPROJECTID')
tfClient = os.environ.get('TFCLIENT')
tfSecret = os.environ.get('TFSECRET')


# OAuth 2 initializer, just generates the URL and sends a page to the user for them to authorize the application
def oauth2Request(request: flask.Request):
  # This only handles GET requests
  if request.method != 'GET':
    flask.abort(405)
  
  # Define all scopes you want access to here, all scopes available here => https://developer.typeform.com/get-started/scopes/
  scopes = ['accounts:read', 'forms:read']

  oauth2URL = 'https://api.typeform.com/oauth/authorize?client_id=%s&redirect_uri=https://us-central1-%s.cloudfunctions.net/oauth2&scope=%s' % (tfClient, gcpProjectId, '+'.join(scopes))

  return flask.render_template('request.html', oauth2URL=oauth2URL)

# Handler from OAuth scopes request
def oauth2(request: flask.Request):
  # This only handles GET requests
  if request.method != 'GET':
    flask.abort(405)

  # Get code from OAuth request, if any
  code = request.args.get('code', None)

  # Check if we have a code, if not, then our app hasn't been authorized (yet!)
  if code == None:
    return oauth2Request(request)

  # Time to get our access token so we can make requests on the users behalf
  headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'cache-control': 'no-cache'
  }

  payload = {
    'grant_type': 'authorization_code',
    'code': code,
    'client_id': tfClient,
    'client_secret': tfSecret,
    'redirect_uri': 'https://us-central1-%s.cloudfunctions.net/oauth2' % gcpProjectId
  }

  # Stringify our payload
  payload = urlencode(payload)
  
  # Now we can get our access token
  authTokenResponse = requests.request('POST', 'https://api.typeform.com/oauth/token', data=payload, headers=headers)

  accessToken = json.loads(authTokenResponse.text).pop('access_token', None)
  
  # Check if we didn't get an access token
  if accessToken == None:
    return oauth2Request(request)

  # If we did get an access token we can now request the users data
  headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': 'Bearer %s' % accessToken,
    'cache-control': 'no-cache'
  }

  userResponse = requests.request('GET', 'https://api.typeform.com/me', data='', headers=headers)

  user = json.loads(userResponse.text)

  # We can also get a list of all of their forms!
  formsResponse = requests.request('GET', 'https://api.typeform.com/forms', data='', headers=headers, params={'page': '1', 'page_size': '200' })

  forms = json.loads(formsResponse.text).get('items', [])

  return flask.render_template('display.html', user=user, forms=forms)