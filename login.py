import requests
from bs4 import BeautifulSoup


class ShibbolethAuthError(Exception):
    pass


class SAMLResponseParseError(Exception):
    pass


class ShibbolethClient(object):
    """
    A wrapper for requests in order to through Shibboleth Authentication
    """

    PARSER = 'lxml'  # type: str
    SHIBBOLETH_AUTH_DOMAIN = 'auth.cis.kit.ac.jp'  # type: str
    SHIBBOLETH_USERNAME_KEY = 'j_username'  # type: str
    SHIBBOLETH_PASSWORD_KEY = 'j_password'  # type: str
    SHIBBOLETH_OPTION_DATA = {"_eventId_proceed": ""}  # type: dict
    SHIBBOLETH_PASS_WEBSTORAGE_CONF_PARAMS = {
        "shib_idp_ls_exception.shib_idp_session_ss": "",
        "shib_idp_ls_success.shib_idp_session_ss": True,
        "_eventId_proceed": ""
    }  # type: dict

    def __init__(self, username: str, password: str):
        """
        Setting up instance
        :param username:student id. for example 'b0000000'
        :param password:password for above user
        """
        self.session = requests.session()
        self.username = username
        self.password = password

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def _parse_saml_data(self, html):
        soup = BeautifulSoup(html, self.PARSER)
        form_error = soup.select('p.form-error')
        if len(form_error) != 0:
            raise ShibbolethAuthError(form_error[0].get_text())
        try:
            form = soup.find('form')
            action = form.get('action')
            saml_data = {
                'RelayState': form.select('input[name="RelayState"]')[0].get('value'),
                'SAMLResponse': form.select('input[name="SAMLResponse"]')[0].get('value')
            }
        except Exception:
            raise SAMLResponseParseError('Could not parse response.')
        return action, saml_data

    def _is_continue_required(self, html):
        soup = BeautifulSoup(html, self.PARSER)
        form = soup.find('form')
        username = form.select('input[id="username"]')
        password = form.select('input[id="password"]')
        if len(username) == 0 and len(password) == 0:
            return True
        return False

    def get(self, url: str, **kwards) -> requests.models.Response:
        """
        Get page from specified url through Shibboleth authentication.
        :param url:get url
        :param kwards:option args for `requests.get()`
        """
        # redirect to authentication page
        login_page = self.session.get(url, **kwards)

        if self.SHIBBOLETH_AUTH_DOMAIN not in login_page.url:
            return login_page

        # skip webstorage confirmation
        if self._is_continue_required(login_page.text):
            # TODO: パラメータ決め打ちなのでどうにかしたい
            login_page = self.session.post(login_page.url, data=self.SHIBBOLETH_PASS_WEBSTORAGE_CONF_PARAMS)

        # post data
        auth_data = {
            self.SHIBBOLETH_USERNAME_KEY: self.username,
            self.SHIBBOLETH_PASSWORD_KEY: self.password,
            **self.SHIBBOLETH_OPTION_DATA
        }
        auth_res = self.session.post(login_page.url, data=auth_data)

        # parse response
        action_url, saml_data = self._parse_saml_data(auth_res.text)

        # Request Assertion Consumer Service
        # Redirect to target resource, and respond with target resource.
        return self.session.post(action_url, data=saml_data)

    def close(self) -> None:
        """
        Close requests.session
        """
        self.session.close()
