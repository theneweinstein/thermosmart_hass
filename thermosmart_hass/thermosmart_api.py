from . import ThermosmartDevice
from typing import Optional, Union, Callable, Dict
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import TokenExpiredError
from requests import (
    Response,
    request as rq,
)

from typing import Any, Callable, Dict, Optional, Tuple, Union


import base64
import requests
import os
import json
import sys
from urllib.parse import urlencode

BASE_URL = 'https://api.thermosmart.com'
OAUTH_URL = 'https://api.thermosmart.com/oauth2/authorize'
TOKEN_URL = 'https://api.thermosmart.com/oauth2/token'

class ThermosmartApi:
    '''
    Implements Authorization Code Flow for Thermosmart's OAuth implementation.
    '''

    def __init__(
        self, 
        client_id: str = None,
        client_secret: str = None, 
        redirect_uri: Optional[str] = None,
        token: Optional[Dict[str, str]] = None,
        token_updater: Optional[Callable[[str], None ]] = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_updater = token_updater

        self._oauth = OAuth2Session(
            client_id=client_id,
            token=token,
            token_updater=token_updater,
            redirect_uri=self.redirect_uri,
        )

    def get_thermostat_id(self):
        return (self.get('/thermostat')).json()['hw']

    def request(self, method: str, path: str, **kwargs) -> Response:
        """Make a request.

        We don't use the built-in token refresh mechanism of OAuth2 session because
        we want to allow overriding the token refresh logic.
        """
        url = BASE_URL + path
        response = getattr(self._oauth, method)(url, **kwargs)

        if response.status_code == 204:
            raise Exception("Empty update.")
        elif response.status_code == 400:
            raise Exception("Invalid update:" + r.json()['error'])
        elif response.status_code == 403:
            raise Exception("Unauthorized access.")
        elif response.status_code == 404:
            raise Exception("Thermostat not found.")
        elif response.status_code == 500:
            raise Exception("Something went wrong with processing the request.")

        return response

    def get(self, path: str, **kwargs) -> Response:
        """Fetch data from API."""
        return self.request('get', path, **kwargs)

    def post(self, path: str, **kwargs) -> Response:
        """Fetch data from API."""
        return self.request('post', path, headers={"Content-Type": "application/json"}, **kwargs)

    def put(self, path: str, **kwargs) -> Response:
        """Fetch data from API."""
        return self.request('put', path, headers={"Content-Type": "application/json"}, **kwargs)

    def get_authorization_url(self, state: Optional[str] = None) -> Tuple[str, str]:
        return self._oauth.authorization_url(OAUTH_URL, state)

    def request_token(
        self, authorization_response: Optional[str] = None
        ) -> Dict[str, str]:
        """
        Generic method for fetching a Thermosmart access token.
        :param authorization_response: Authorization response URL, the callback
                                       URL of the request back to you.
        :return: A token dict
        """

        return self._oauth.fetch_token(
            TOKEN_URL,
            authorization_response=authorization_response,
            client_id=self.client_id,
            client_secret=self.client_secret,   
        )