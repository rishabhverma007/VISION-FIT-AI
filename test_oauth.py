import os
# Use a public unknown code and let's see Google's error
os.environ['GOOGLE_CLIENT_ID'] = 'dummy.apps.googleusercontent.com'
os.environ['GOOGLE_CLIENT_SECRET'] = 'dummy'
import requests
from google_fit_service import GoogleFitService

s = GoogleFitService()

try:
    s.get_credentials_from_code('http://localhost:5000/oauth2callback?state=4FBOu7UU1Z5Tj7Lxp93Y4Na8XQ3qsY&code=some_random_bad_code', state='4FBOu7UU1Z5Tj7Lxp93Y4Na8XQ3qsY', code_verifier='myverifier')
except Exception as e:
    print('Error with our code:', e)

