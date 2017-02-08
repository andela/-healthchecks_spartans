from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from hc.api.models import Check


class LoginTestCase(TestCase):

    def test_it_sends_link(self):
        check = Check()
        check.save()

        session = self.client.session
        session["welcome_code"] = str(check.code)
        session.save()

        form = {"email": "alice@example.org"}

        r = self.client.post("/accounts/login/", form)
        assert r.status_code == 302

        ### Assert that a user was created
        self.assertEqual(User.objects.count(), 1)

        # And email sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Log in to healthchecks.io')

        ### Assert contents of the email body
        self.assertIn('To log into healthchecks.io', mail.outbox[0].body)

        ### Assert that check is associated with the new user
        # TODO query the new user and verify
        verify = Check.objects.get(code=check.code)
        assert verify.user

    def test_it_pops_bad_link_from_session(self):
        self.client.session["bad_link"] = True
        self.client.get("/accounts/login/")
        assert "bad_link" not in self.client.session

        ### Any other tests?
    # TODO test login with fake credentials non existent user
    # TODO non existent profile
    #  TODO WRONG EMAIL LOGIN
    def test_login_link_sent(self):
        url = '/accounts/login_link_sent/'
        r = self.client.get(url)
        self.assertTemplateUsed(r, 'accounts/login_link_sent.html')








