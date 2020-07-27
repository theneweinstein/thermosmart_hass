from . import ThermosmartDevice
from typing import Optional, Union, Callable, Dict
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import TokenExpiredError
from requests import Response

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
        scope: Optional[str] = "ot"
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_updater = token_updater
        self.scope = scope

        extra = {"client_id": self.client_id, "client_secret": self.client_secret}

        self._oauth = OAuth2Session(
            client_id=client_id,
            token=token,
            token_updater=token_updater,
            redirect_uri=self.redirect_uri,
            scope=scope
        )

    def get_thermostat_id(self):
        return (self.get('/thermostat'))['hw']

    def refresh_tokens(self) -> Dict[str, Union[str, int]]:
        """Refresh and return new tokens."""
        token = self._oauth.refresh_token(TOKEN_URL)

        if self.token_updater is not None:
            self.token_updater(token)

        return token

    def request(self, method: str, path: str, **kwargs) -> Response:
        """Make a request.

        We don't use the built-in token refresh mechanism of OAuth2 session because
        we want to allow overriding the token refresh logic.
        """
        url = BASE_URL + path
        try:
            return getattr(self._oauth, method)(url, **kwargs)
        except TokenExpiredError:
            self._oauth.token = self.refresh_tokens()

            return getattr(self._oauth, method)(url, **kwargs)

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

    def _make_authorization_headers(self):
        auth_header = base64.b64encode((self.client_id + ':' + self.client_secret).encode('ascii'))
        return {'Authorization': 'Basic %s' % auth_header.decode('ascii')}

    def request_token(
        self, authorization_response: Optional[str] = None, code: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generic method for fetching a Thermosmart access token.
        :param authorization_response: Authorization response URL, the callback
                                       URL of the request back to you.
        :param code: Authorization code
        :return: A token dict
        """

        return self._oauth.fetch_token(
            TOKEN_URL,
            authorization_response=authorization_response,
            code=code,
            client_secret=self.client_secret,
            include_client_id=True,
            headers = self._make_authorization_headers()
        )