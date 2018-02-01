import requests
from bs4 import BeautifulSoup


class ShibbolethClient(object):

    PARSER = 'lxml'
    SHIBBOLETH_AUTH_DOMAIN = 'auth.cis.kit.ac.jp'
    SHIBBOLETH_USERNAME_KEY = 'j_username'
    SHIBBOLETH_PASSWORD_KEY = 'j_password'
    SHIBBOLETH_OPTION_DATA = {
        "_eventId_proceed": ""
    }

    def __init__(self, username, password):
        self.session = requests.session()
        self.username = username
        self.password = password

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def __parse_saml_data(self, html):
        soup = BeautifulSoup(html, self.PARSER)
        form = soup.find('form')
        action = form.get('action') 
        input_form = form.div.find_all('input')
        saml_data = {
            'RelayState': input_form[0].get('value'),
            'SAMLResponse': input_form[1].get('value')
        }
        return {'action': action, 'saml_data': saml_data}

    def get(self, url, *args, **kwards):
        # redirect to authentication page
        login_page = self.session.get(url, *args, **kwards)

        if self.SHIBBOLETH_AUTH_DOMAIN not in login_page.url:
            return login_page

        # post data
        auth_data = {
            self.SHIBBOLETH_USERNAME_KEY: self.username,
            self.SHIBBOLETH_PASSWORD_KEY: self.password,
            **self.SHIBBOLETH_OPTION_DATA
        }
        auth_res = self.session.post(login_page.url, data=auth_data)

        # parse response
        res = self.__parse_saml_data(auth_res.text)

        # Request Assertion Consumer Service
        # Redirect to target resource, and respond with target resource.
        return self.session.post(res['action'], res['saml_data'])
