import os
import sys
import unittest
import contextlib
import codecs
import urllib.parse

from unittest.mock import MagicMock, patch
from pathlib import Path
from nose.tools import eq_, ok_, raises

module_path = Path(os.path.abspath(__file__)).parents[2]
sys.path.append(module_path.as_posix())

from shibboleth_login import ShibbolethClient, SAMLResponseParseError, ShibbolethAuthError


class TestShibbolethClient(unittest.TestCase):

    responses = {}
    correct_saml_resp = {
        'RelayState': 'RelayState',
        'SAMLResponse': 'SAMLResponse'
    }

    @classmethod
    def setUpClass(cls):
        sample_list = [
            'webstorage_confirm.html',
            'auth_form.html',
            'auth_error.html',
            'auth_success.html',
            'internal_auth.html'
        ]
        sample_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'samples')
        auth_url = "https://auth.cis.kit.ac.jp/idp/profile/SAML2/Redirect/SSO;jsessionid=hoge?execution=e1s1"
        after_auth_url = 'https://portal.student.kit.ac.jp/'
        for p in [os.path.join(sample_dir_path, sample_path) for sample_path in sample_list]:
            with codecs.open(p, 'r', encoding='utf-8') as fp:
                name, _ = os.path.splitext(os.path.basename(p))
                resp = MagicMock(
                    url=auth_url if name != 'internal_auth' else after_auth_url,
                    text=fp.read()
                )
                cls.responses[name] = resp

    def setUp(self):
        self.client = ShibbolethClient('hoge', 'fuga')

    def tearDown(self):
        self.client.close()

    def test_is_continue_required(self):
        """Normal Test for `ShibbolethClient._is_continue_required`"""
        expect_true = self.client._is_continue_required(self.responses['webstorage_confirm'].text)
        ok_(expect_true)
        expect_false = self.client._is_continue_required(self.responses['auth_form'].text)
        ok_(not expect_false)

    def test_parse_saml_data(self):
        """Normal test for `ShibbolethClient._parse_saml_data`"""
        action, saml_resp = self.client._parse_saml_data(self.responses['auth_success'].text)
        parsed = urllib.parse.urlparse(action)
        eq_(parsed.scheme, 'https')
        eq_(parsed.path, '/Shibboleth.sso/SAML2/POST')
        eq_(parsed.netloc, 'portal.student.kit.ac.jp')
        eq_(parsed.query, '')
        eq_(parsed.fragment, '')
        eq_(saml_resp, self.correct_saml_resp)

    @raises(SAMLResponseParseError)
    def test_parse_saml_data_parse_error(self):
        """SAMLResponseParseError test for `ShibbolethClient._parse_saml_data`"""
        self.client._parse_saml_data(self.responses['internal_auth'].text)

    @raises(ShibbolethAuthError)
    def test_parse_saml_data_auth_error(self):
        """ShibbolethAuthError test for `ShibbolethClient._parse_saml_data`"""
        self.client._parse_saml_data(self.responses['auth_error'].text)

    def test_get_with_webstorage_confirmation(self):
        """Normal Test for `ShibbolethClient.get` with webstorage confirmation"""
        with contextlib.ExitStack() as stack:
            patched_post = stack.enter_context(
                patch('requests.Session.post', side_effect=[
                    self.responses['auth_form'], self.responses['auth_success'], self.responses['internal_auth']
                ])
            )
            patched_get = stack.enter_context(
                patch('requests.Session.get',
                      return_value=self.responses['webstorage_confirm'])
            )
            actual_resp = self.client.get(self.responses['internal_auth'].url)
            # check `requests.Session.get`
            ok_(patched_get.called)
            eq_(patched_get.call_count, 1)
            positional_args = patched_get.call_args[0]
            optional_args = patched_get.call_args[1]
            eq_(self.responses['internal_auth'].url, positional_args[0])
            eq_({}, optional_args)
            # check `requests.Session.post`
            ok_(patched_post.called)
            eq_(patched_post.call_count, 3)
            # first call
            positional_args = patched_post.call_args_list[0][0]
            optional_args = patched_post.call_args_list[0][1]
            eq_(self.responses['webstorage_confirm'].url, positional_args[0])
            eq_({
                'data': ShibbolethClient.SHIBBOLETH_PASS_WEBSTORAGE_CONF_PARAMS
            }, optional_args)
            # second call
            positional_args = patched_post.call_args_list[1][0]
            optional_args = patched_post.call_args_list[1][1]
            eq_(self.responses['auth_form'].url, positional_args[0])
            eq_({
                'data': {
                    ShibbolethClient.SHIBBOLETH_USERNAME_KEY: 'hoge',
                    ShibbolethClient.SHIBBOLETH_PASSWORD_KEY: 'fuga',
                    **ShibbolethClient.SHIBBOLETH_OPTION_DATA
                }
            }, optional_args)
            # third call
            positional_args = patched_post.call_args_list[2][0]
            optional_args = patched_post.call_args_list[2][1]
            eq_('https://portal.student.kit.ac.jp/Shibboleth.sso/SAML2/POST', positional_args[0])
            eq_({'data': self.correct_saml_resp}, optional_args)
            # check response
            eq_(self.responses['internal_auth'].text, actual_resp.text)
            eq_(self.responses['internal_auth'].url, actual_resp.url)

    def test_get_without_webstorage_confirmation(self):
        """Normal Test for `ShibbolethClient.get` without webstorage confirmation"""
        with contextlib.ExitStack() as stack:
            patched_post = stack.enter_context(
                patch('requests.Session.post', side_effect=[
                    self.responses['auth_success'], self.responses['internal_auth']
                ])
            )
            patched_get = stack.enter_context(
                patch('requests.Session.get',
                      return_value=self.responses['auth_form'])
            )
            actual_resp = self.client.get(self.responses['internal_auth'].url)
            # check `requests.Session.get`
            ok_(patched_get.called)
            eq_(patched_get.call_count, 1)
            positional_args = patched_get.call_args[0]
            optional_args = patched_get.call_args[1]
            eq_(self.responses['internal_auth'].url, positional_args[0])
            eq_({}, optional_args)
            # check `requests.Session.post`
            ok_(patched_post.called)
            eq_(patched_post.call_count, 2)
            # first call
            positional_args = patched_post.call_args_list[0][0]
            optional_args = patched_post.call_args_list[0][1]
            eq_(self.responses['auth_form'].url, positional_args[0])
            eq_({
                'data': {
                    ShibbolethClient.SHIBBOLETH_USERNAME_KEY: 'hoge',
                    ShibbolethClient.SHIBBOLETH_PASSWORD_KEY: 'fuga',
                    **ShibbolethClient.SHIBBOLETH_OPTION_DATA
                }
            }, optional_args)
            # Second call
            positional_args = patched_post.call_args_list[1][0]
            optional_args = patched_post.call_args_list[1][1]
            eq_('https://portal.student.kit.ac.jp/Shibboleth.sso/SAML2/POST', positional_args[0])
            eq_({'data': self.correct_saml_resp}, optional_args)
            # check response
            eq_(self.responses['internal_auth'].text, actual_resp.text)
            eq_(self.responses['internal_auth'].url, actual_resp.url)

    def test_get_without_auth(self):
        """Normal test for `ShibbolethClient.get` when already authenticated"""
        with contextlib.ExitStack() as stack:
            patched_post = stack.enter_context(
                patch('requests.Session.post', return_value='')
            )
            patched_get = stack.enter_context(
                patch('requests.Session.get', return_value=self.responses['internal_auth'])
            )
            actual_resp = self.client.get(self.responses['internal_auth'].url)
            # check `requests.Session.post`
            ok_(not patched_post.called)
            # check `requests.Session.get
            ok_(patched_get.called)
            eq_(patched_get.call_count, 1)
            positional_args = patched_get.call_args[0]
            optional_args = patched_get.call_args[1]
            eq_(self.responses['internal_auth'].url, positional_args[0])
            eq_({}, optional_args)
            # check response
            eq_(actual_resp.url, self.responses['internal_auth'].url)
            eq_(actual_resp.text, self.responses['internal_auth'].text)

