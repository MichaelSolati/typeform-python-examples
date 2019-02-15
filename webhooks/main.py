import json
import requests
import flask
import hashlib
from time import time

# Variables, feel free to change them
formURL = 'https://michaelsolati.typeform.com/to/iCF1M5'
firebaseConfig = {
  'apiKey': 'AIzaSyAvMX9BeSWuTbhBjw5-pNL0QPx-nPlATts',
  'authDomain': 'typeform-python-examples.firebaseapp.com',
  'databaseURL': 'https://typeform-python-examples.firebaseio.com',
  'projectId': 'typeform-python-examples',
  'storageBucket': 'typeform-python-examples.appspot.com',
  'messagingSenderId': '844498531404'
}

# Message Board Handler
def webhooksMessageBoard(request: flask.Request):
  # We only accept POST and GET requests for our demo
  if request.method == 'POST':
    return post(request)
  elif request.method == 'GET':
    return get()
  else:
    flask.abort(405)

# Handle a POST request for our webhook demo
# Handles the webhook
def post(request: flask.Request):
  data = request.get_json()
  payload = {
    'timestamp': {'.sv': 'timestamp'} # Firebase's internal timestamp, don't worry about it too much
  }

  # And let's ensure we actually have answers in our response
  if data is None or 'form_response' not in data.keys() or 'answers' not in data['form_response'].keys():
    flask.abort(400)

  # Simplify the data structure just a little bit
  formResponse = data['form_response']
  
  # Access by the field type
  # Works if there's only one question by field type
  for answer in formResponse['answers']:
    if answer['type'] == 'email':
      payload['email'] = answer['email'].lower()
    if answer['type'] == 'choice':
      payload['type'] = answer['choice']['label']
    if answer['type'] == 'text':
      payload['content'] = answer['text']
  
  # # Access by the array
  # payload['email'] = formResponse['answers'][0]['email'].lower()
  # payload['type'] = formResponse['answers'][1]['choice']['label']
  # payload['content'] = formResponse['answers'][2]['text']

  # # Access by the ref
  # references = {
  #   '987c7c4d-2995-4044-9bc1-0c53a20a307e': 'email',
  #   '189ee103-d2c4-409f-be00-22e64cb54f09': 'type',
  #   '97268ad3-f0e7-4fa6-9fe5-7f5125ce1aa7': 'content'
  # }
  # for answer in formResponse['answers']:
  #   ref = answer['field']['ref']
  #   if ref in references:
  #     if references[ref] == 'email':
  #       payload['email'] = answer['email'].lower()
  #     if references[ref] == 'type':
  #       payload['type'] = answer['choice']['label']
  #     if references[ref] == 'content':
  #       payload['content'] = answer['text']


  # Get name and picture from Gravatar
  gravatar = requests.request('GET', 'https://www.gravatar.com/%s.json' % hashlib.md5(payload['email'].encode('utf-8')).hexdigest())
  if gravatar.status_code != 404:
    gravatarData = json.loads(gravatar.text)['entry'][0]
    payload['displayName'] = gravatarData['displayName']
    payload['thumbnailUrl'] = gravatarData['thumbnailUrl']
  else:
    payload['displayName'] = payload['email']
    payload['thumbnailUrl'] = 'https://api.adorable.io/avatars/285/%s.png' % payload['email']
  
  # Stringify our payload
  payload = json.dumps(payload)

  # We'll now send our request to Firebase
  response = requests.request('POST', 'https://%s.firebaseio.com/webhooks/message-board.json' % firebaseConfig['projectId'], data=payload)

  return response.text

# Handle a GET request for our webhook demo
# Serves an HTML page to view the demo
def get():
  return flask.render_template('index.html', formURL=formURL, firebaseConfig=firebaseConfig)