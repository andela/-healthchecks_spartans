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

        # assert the user doesn't exist before post operation
        self.assertEqual(len(User.objects.filter(email=form["email"])), 0)
        self.initial_user_count = User.objects.count()

        r = self.client.post("/accounts/login/", form)
        assert r.status_code == 302

        ### Assert that a user was created
        self.new_user_count = User.objects.count()
        self.assertEqual(self.new_user_count - self.initial_user_count, 1)

        # And email sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Log in to healthchecks.io')

        ### Assert contents of the email body
        self.assertIn('To log into healthchecks.io', mail.outbox[0].body)

        ### Assert that check is associated with the new user
        self.test_user_list = User.objects.filter(email=form["email"])
        self.test_check = Check.objects.get(user=self.test_user_list[0].id)
        self.assertEqual(self.test_user_list[0].id, self.test_check.user_id)

    def test_it_pops_bad_link_from_session(self):
        self.client.session["bad_link"] = True
        self.client.get("/accounts/login/")
        assert "bad_link" not in self.client.session

        ### Any other tests?
    def test_login_link_sent(self):
        url = '/accounts/login_link_sent/'
        r = self.client.get(url)
        self.assertTemplateUsed(r, 'accounts/login_link_sent.html')

    def test_set_password_link_sent(self):
        url = '/accounts/set_password_link_sent/'
        r = self.client.get(url)
        self.assertTemplateUsed(r, 'accounts/set_password_link_sent.html')

    def test_login_with_valid_credentials(self):
        form = {'username': 'alice@example.org', 'password': "password"}
        r = self.client.post("/accounts/login/", form)
        self.assertEqual(r.status_code, 200)

    def test_login_with_ivalid_credentials(self):
        form = {'username': 'alice@example.org', 'password': "password2"}
        r = self.client.post("/accounts/login/", form)
        self.assertTemplateUsed(r, 'accounts/login.html')





