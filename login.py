import requests
from bs4 import BeautifulSoup


class ShibbolethClient(object):

    session = requests.session()

    def __init__(self, username, password, login_url=None, *args, **kwards):
        self.username = username
        self.password = password
        self.url = login_url if login_url else 'https://portal.student.kit.ac.jp/'

    def __enter__(self):
        self.get()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    @staticmethod
    def parse_saml_data(html):
        soup = BeautifulSoup(html, "lxml")
        form = soup.find('form')
        action = form.get('action')
        input_form = form.div.find_all('input')
        relay_state = input_form[0].get('value')
        saml_response = input_form[1].get('value')
        saml_data = {
            'RelayState': relay_state,
            'SAMLResponse': saml_response
        }
        return {'action': action, 'saml_data': saml_data}

    def get(self, url=None):
        # redirect to authentication page
        if url:
            login_page = self.session.get(url, timeout=20)
        else:
            login_page = self.session.get(self.url, timeout=20)

        if 'auth.cis.kit.ac.jp' not in login_page.url:
            return login_page

        # post data
        auth_data = {
            "j_username": self.username,
            "j_password": self.password,
            "_eventId_proceed": ""
        }
        auth_res = self.session.post(login_page.url, data=auth_data)

        # parse response
        res = self.parse_saml_data(auth_res.text)

        # Request Assertion Consumer Service
        # Redirect to target resource, and respond with target resource.
        return self.session.post(res['action'], res['saml_data'])
