import os
import google.oauth2.credentials
import google_auth_oauthlib.flow
from google.auth.transport.requests import Request
import requests
import datetime
import logging
import secrets

class GoogleFitService:
    def __init__(self):
        # Allow OAuth over HTTP for testing (remove for production)
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        
        self.client_id = os.environ.get('GOOGLE_CLIENT_ID')
        self.client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
        self.redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/oauth2callback')
        
        self.SCOPES = [
            'https://www.googleapis.com/auth/fitness.activity.read',
            'https://www.googleapis.com/auth/fitness.body.read',
            'https://www.googleapis.com/auth/fitness.heart_rate.read'
        ]

    def get_auth_url(self):
        """Generates the Google OAuth2 authorization URL."""
        if not self.client_id or not self.client_secret:
            raise ValueError("Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET env variables")

        flow = google_auth_oauthlib.flow.Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=self.SCOPES,
            autogenerate_code_verifier=False
        )
        flow.redirect_uri = self.redirect_uri
        # Do not use PKCE because it conflicts with standard Google Web App OAuth
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        return authorization_url, state, None

    def get_credentials_from_code(self, authorization_response, state=None, code_verifier=None):
        """Exchanges the authorization solution for credentials."""
        flow = google_auth_oauthlib.flow.Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=self.SCOPES,
            state=state,
            autogenerate_code_verifier=False
        )
        flow.redirect_uri = self.redirect_uri
        if code_verifier:
            flow.code_verifier = code_verifier
        # Use authorization_response to let the library parse the code from the full URL
        flow.fetch_token(
            authorization_response=authorization_response
        )
        return flow.credentials

    def credentials_to_dict(self, credentials):
        """Converts credentials to a dictionary for session storage."""
        return {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'scopes': credentials.scopes
            # client_id and client_secret are not stored to save session space
        }

    def dict_to_credentials(self, creds_dict):
        """reconstructs credentials from a dictionary."""
        # Inject the static client info back in
        if 'client_id' not in creds_dict:
            creds_dict['client_id'] = self.client_id
        if 'client_secret' not in creds_dict:
            creds_dict['client_secret'] = self.client_secret
            
        return google.oauth2.credentials.Credentials(
            **creds_dict
        )

    def get_fitness_data(self, credentials):
        """Fetches steps, calories, and heart rate for today."""
        # Check if token is expired and refresh if needed
        # Note: In a full app, auto-refresh would happen here or via the transport
        
        headers = {'Authorization': f'Bearer {credentials.token}'}
        
        # Time range: Start of today to now
        now = datetime.datetime.utcnow()
        start_of_day = datetime.datetime(now.year, now.month, now.day)
        
        # Convert to nanoseconds
        start_time_ns = int(start_of_day.timestamp() * 1e9)
        end_time_ns = int(now.timestamp() * 1e9)
        
        # Request body for aggregate data
        body = {
            "aggregateBy": [
                {"dataTypeName": "com.google.step_count.delta"},
                {"dataTypeName": "com.google.calories.expended"},
                {"dataTypeName": "com.google.heart_rate.bpm"}
            ],
            "bucketByTime": {"durationMillis": 86400000}, # 1 day bucket
            "startTimeMillis": int(start_of_day.timestamp() * 1000),
            "endTimeMillis": int(now.timestamp() * 1000)
        }
        
        try:
            response = requests.post(
                "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate",
                headers=headers,
                json=body
            )
            
            data = response.json()
            
            # Parse results
            steps = 0
            calories = 0
            heart_rate = "--"
            
            if "bucket" in data:
                for bucket in data["bucket"]:
                    for dataset in bucket["dataset"]:
                        data_type = dataset["dataSourceId"] # or point type
                        for point in dataset["point"]:
                            for value in point["value"]:
                                # Identifying the metric based on structure or order is tricky without checking dataSourceId carefully
                                # But aggregate request returns them in order requested usually, checking type is safer
                                
                                # Simplified parsing logic
                                # Steps usually intVal
                                if "step_count" in dataset.get("dataSourceId", ""):
                                    steps += value.get("intVal", 0)
                                # Calories usually fpVal
                                elif "calories" in dataset.get("dataSourceId", ""):
                                    calories += value.get("fpVal", 0)
                                # Heart rate usually fpVal
                                elif "heart_rate" in dataset.get("dataSourceId", ""):
                                    # HR might be avg, min, max if aggregated.
                                    # If not aggregated properly, might be individual points.
                                    # Since we bucketed by day, we get day stats.
                                    # Let's take the max or avg if available.
                                    heart_rate = int(value.get("fpVal", 0))

            return {
                "steps": steps,
                "calories": int(calories),
                "heart_rate": heart_rate
            }
            
        except Exception as e:
            logging.error(f"Error fetching Google Fit data: {e}")
            return None
