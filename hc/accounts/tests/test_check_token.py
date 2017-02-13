from django.contrib.auth.hashers import make_password
from hc.test import BaseTestCase


class CheckTokenTestCase(BaseTestCase):

    def setUp(self):
        super(CheckTokenTestCase, self).setUp()
        self.profile.token = make_password("secret-token")
        self.profile.save()

    def test_it_shows_form(self):
        r = self.client.get("/accounts/check_token/alice/secret-token/")
        self.assertContains(r, "You are about to log in")

    def test_it_redirects(self):
        r = self.client.post("/accounts/check_token/alice/secret-token/")
        self.assertRedirects(r, "/checks/")

        # After login, token should be blank
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.token, "")

    ### Login and test it redirects already logged in
    def test_redirects_when_logged_in(self):
        self.client.login(username=self.alice.email, password="password")
        url = "/accounts/check_token/alice/secret-token/"
        r = self.client.post(url)
        self.assertRedirects(r, "/checks/", 302)

    ### Login with a bad token and check that it redirects
    def test_redirect_with_bad_token(self):
        url = "/accounts/check_token/alice/invalid-token/"
        r = self.client.post(url)
        self.assertRedirects(r, '/accounts/login/', 302)

    ### Any other tests?
    def test_logout_redirects(self):
        url = '/accounts/logout/'
        r = self.client.get(url)
        self.assertRedirects(r, '/', 302)




