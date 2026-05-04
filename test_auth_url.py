import os
os.environ['GOOGLE_CLIENT_ID'] = 'fake'
os.environ['GOOGLE_CLIENT_SECRET'] = 'fake'
from google_fit_service import GoogleFitService

s = GoogleFitService()
url, state, verifier = s.get_auth_url()
print('URL:', url)
print('VERIFIER:', verifier)
