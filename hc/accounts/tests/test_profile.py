from django.core import mail

from hc.test import BaseTestCase
from hc.accounts.models import Member
from hc.api.models import Check
from django.contrib.auth.models import User
from hc.accounts.models import Profile
from django.core.signing import Signer
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from hc.accounts.models import ACCEPT_DAILY_REPORTS, ACCEPT_WEEKLY_REPORTS, ACCEPT_MONTHLY_REPORTS, UNSUBSCRIBE_REPORTS

class ProfileTestCase(BaseTestCase):

    def test_it_sends_set_password_link(self):
        self.client.login(username="alice@example.org", password="password")

        form = {"set_password": "1"}
        r = self.client.post("/accounts/profile/", form)
        assert r.status_code == 302

        # profile.token should be set now

        self.alice.profile.refresh_from_db()
        token = self.alice.profile.token

        # Assert that the token is set
        self.assertTrue(len(token) > 10)

        #Assering that the email has been sent
        self.assertEqual(len(mail.outbox), 1)

        # Asserting the contents of the mail contents (subject and contents)
        self.assertEqual(mail.outbox[0].subject, 'Set password on healthchecks.io')
        self.assertIn("Hello,\n\nHere's a link to set a password for your account on healthchecks.io:", mail.outbox[0].body)

    def test_it_sends_daily_report(self):

        check = Check(name="Test Check", user=self.alice)
        check.save()
        self.alice.profile.reports_allowed = ACCEPT_DAILY_REPORTS

        self.alice.profile.send_report()

        #Assert that the email was sent
        self.assertEqual(len(mail.outbox), 1)

        # Checking the subject of the email that was sent

        self.assertEqual(mail.outbox[0].subject, 'Daily Report')

        # Checking the content of the email that was sent
        self.assertIn('This is a Daily report sent by healthchecks.io.', mail.outbox[0].body)

    def test_it_sends_weekly_report(self):

        check = Check(name="Test Check", user=self.alice)
        check.save()
        self.alice.profile.reports_allowed = ACCEPT_WEEKLY_REPORTS

        self.alice.profile.send_report()

        #Assert that the email was sent
        self.assertEqual(len(mail.outbox), 1)

        # Checking the subject of the email that was sent

        self.assertEqual(mail.outbox[0].subject, 'Weekly Report')

        # Checking the content of the email that was sent
        self.assertIn('This is a Weekly report sent by healthchecks.io.', mail.outbox[0].body)
    def test_it_sends_monthly_report(self):

        check = Check(name="Test Check", user=self.alice)
        check.save()
        self.alice.profile.reports_allowed = ACCEPT_MONTHLY_REPORTS

        self.alice.profile.send_report()

        #Assert that the email was sent
        self.assertEqual(len(mail.outbox), 1)

        # Checking the subject of the email that was sent

        self.assertEqual(mail.outbox[0].subject, 'Monthly Report')

        # Checking the content of the email that was sent
        self.assertIn('This is a Monthly report sent by healthchecks.io.', mail.outbox[0].body)

    def test_it_adds_team_member(self):

        self.client.login(username="alice@example.org", password="password")

        form = {"invite_team_member": "1", "email": "frank@example.org"}
        r = self.client.post("/accounts/profile/", form)
        assert r.status_code == 200

        member_emails = set()
        for member in self.alice.profile.member_set.all():
            member_emails.add(member.user.email)

        ### Assert the existence of the member emails

        self.assertTrue("frank@example.org" in member_emails)
        self.assertTrue("bob@example.org" in member_emails)
        assert len(mail.outbox) > 0

        ###Assert that the email was sent and check email content
        self.assertIn('frank@example.org',mail.outbox[0].to)
        self.assertIn("You have been invited to join alice@example.org on ", mail.outbox[0].subject)
        self.assertIn("You will be able to manage their existing monitoring checks and set up new", mail.outbox[0].body)

    def test_add_team_member_checks_team_access_allowed_flag(self):
        self.client.login(username="charlie@example.org", password="password")

        form = {"invite_team_member": "1", "email": "frank@example.org"}
        r = self.client.post("/accounts/profile/", form)
        assert r.status_code == 403

    def test_it_removes_team_member(self):
        self.client.login(username="alice@example.org", password="password")

        form = {"remove_team_member": "1", "email": "bob@example.org"}
        r = self.client.post("/accounts/profile/", form)
        assert r.status_code == 200

        self.assertEqual(Member.objects.count(), 0)

        self.bobs_profile.refresh_from_db()
        self.assertEqual(self.bobs_profile.current_team, None)

    def test_it_sets_team_name(self):
        self.client.login(username="alice@example.org", password="password")

        form = {"set_team_name": "1", "team_name": "Alpha Team"}
        r = self.client.post("/accounts/profile/", form)
        assert r.status_code == 200

        self.alice.profile.refresh_from_db()
        self.assertEqual(self.alice.profile.team_name, "Alpha Team")

    def test_set_team_name_checks_team_access_allowed_flag(self):
        self.client.login(username="charlie@example.org", password="password")

        form = {"set_team_name": "1", "team_name": "Charlies Team"}
        r = self.client.post("/accounts/profile/", form)
        assert r.status_code == 403

    def test_it_switches_to_own_team(self):
        self.client.login(username="bob@example.org", password="password")

        self.client.get("/accounts/profile/")

        # After visiting the profile page, team should be switched back
        # to user's default team.
        self.bobs_profile.refresh_from_db()
        self.assertEqual(self.bobs_profile.current_team, self.bobs_profile)

    def test_it_shows_badges(self):
        self.client.login(username="alice@example.org", password="password")
        Check.objects.create(user=self.alice, tags="foo a-B_1  baz@")
        Check.objects.create(user=self.bob, tags="bobs-tag")

        r = self.client.get("/accounts/profile/")
        self.assertContains(r, "foo.svg")
        self.assertContains(r, "a-B_1.svg")

        # Expect badge URLs only for tags that match \w+
        self.assertNotContains(r, "baz@.svg")

        # Expect only Alice's tags
        self.assertNotContains(r, "bobs-tag.svg")

    ### Test it creates and revokes API key
    def test_it_revokes_api_key(self):
        # Login
        self.client.login(username="alice@example.org", password="password")
        form ={'revoke_api_key': '1'}
        r = self.client.post("/accounts/profile/", form)
        self.assertEqual(r.status_code, 200)
        self.alice.profile.refresh_from_db()
        self.assertEqual(self.alice.profile.api_key, "")

    def test_create_api_key(self):
        self.client.login(username="alice@example.org", password="password")
        form = {'create_api_key': '1'}
        r = self.client.post("/accounts/profile/", form)
        self.assertEqual(r.status_code, 200)

        self.alice.profile.refresh_from_db()
        api_key = self.alice.profile.api_key
        self.assertTrue(len(api_key) > 10)
        self.assertIsNotNone(api_key)
        self.assertContains(r, "The API key has been created!")

    def test_show_api_key(self):
        self.client.login(username="alice@example.org", password="password")
        form = {'show_api_key': '1'}
        r = self.client.post("/accounts/profile/", form)
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'accounts/profile.html')
        self.assertEqual(r.context[-1]['show_api_key'], True)

    def test_update_reports_allowed_daily(self):
        self.client.login(username="alice@example.org", password="password")
        form = {'update_reports_allowed': '', 'reports_allowed': ACCEPT_MONTHLY_REPORTS}
        r = self.client.post("/accounts/profile/", form)
        self.assertEqual(r.status_code, 200)
        self.alice.profile.refresh_from_db()
        self.assertEqual(self.alice.profile.reports_allowed, ACCEPT_MONTHLY_REPORTS)

    def test_update_reports_allowed_weekly(self):
        self.client.login(username="alice@example.org", password="password")
        form = {'update_reports_allowed': '', 'reports_allowed': ACCEPT_WEEKLY_REPORTS}
        r = self.client.post("/accounts/profile/", form)
        self.assertEqual(r.status_code, 200)
        self.alice.profile.refresh_from_db()
        self.assertEqual(self.alice.profile.reports_allowed, ACCEPT_WEEKLY_REPORTS)

    def test_update_reports_allowed_monthly(self):
        self.client.login(username="alice@example.org", password="password")
        form = {'update_reports_allowed': '', 'reports_allowed': ACCEPT_DAILY_REPORTS}
        r = self.client.post("/accounts/profile/", form)
        self.assertEqual(r.status_code, 200)
        self.alice.profile.refresh_from_db()
        self.assertEqual(self.alice.profile.reports_allowed, ACCEPT_DAILY_REPORTS)

    def test_disable_reports(self):
        self.client.login(username="alice@example.org", password="password")
        form = {'update_reports_allowed': '', 'reports_allowed': UNSUBSCRIBE_REPORTS}
        r = self.client.post("/accounts/profile/", form)
        self.assertEqual(r.status_code, 200)
        self.alice.profile.refresh_from_db()
        self.assertEqual(self.alice.profile.reports_allowed, UNSUBSCRIBE_REPORTS)

    def test_unsubscribe_reports(self):
        self.sam = User(username="sam", email="sam@example.org")
        self.sam.set_password("password")
        self.sam.save()
        self.sam_profile = Profile(user=self.sam, api_key="abc", token='')
        signer = Signer()
        value = signer.sign('secret-token')
        self.sam_profile.token = value
        self.sam_profile.team_access_allowed = True
        self.sam_profile.save()
        self.client.login(username="sam@example.org", password="password")
        url = "/accounts/unsubscribe_reports/%s/" % self.sam.username
        self.client.get(url, {'token': value})
        self.sam_profile.refresh_from_db()
        self.assertEqual(self.sam_profile.reports_allowed, UNSUBSCRIBE_REPORTS)

    def test_unsubscribe_reports_with_invalid_token(self):
        self.sam = User(username="sam", email="sam@example.org")
        self.sam.set_password("password")
        self.sam.save()
        self.sam_profile = Profile(user=self.sam, api_key="abc", token='')
        signer = Signer()
        value = signer.sign('secret-token')
        self.sam_profile.token = value
        self.sam_profile.team_access_allowed = True
        self.sam_profile.save()
        self.client.login(username="sam@example.org", password="password")
        url = "/accounts/unsubscribe_reports/%s/" % self.sam.username
        invalid_token = signer.sign('invalid-token')
        self.client.get(url, {'token': invalid_token})
        self.assertEqual(self.sam_profile.reports_allowed, UNSUBSCRIBE_REPORTS)

    def test_unsubscribe_reports_with_bad_signature(self):
        self.sam = User(username="sam", email="sam@example.org")
        self.sam.set_password("password")
        self.sam.save()
        self.sam_profile = Profile(user=self.sam, api_key="abc", token='')
        signer = Signer()
        value = signer.sign('secret-token')
        self.sam_profile.token = value
        self.sam_profile.team_access_allowed = True
        self.sam_profile.save()
        self.client.login(username="sam@example.org", password="password")
        url = "/accounts/unsubscribe_reports/%s/" % self.sam.username
        r = self.client.get(url, {'token': 'secret-token'})
        self.assertEqual(r.status_code, 400)

    def test_it_set_password(self):
        self.profile.token = make_password("secret-token")
        self.profile.save()
        self.client.login(username="alice@example.org", password="password")
        url = "/accounts/set_password/secret-token/"
        r = self.client.post(url)
        self.assertContains(r, "Set a Password")
        self.assertTemplateUsed(r, "accounts/set_password.html")

    def test_set_password_with_invalid_token(self):
        self.profile.token = make_password("secret-token")
        self.profile.save()
        self.client.login(username="alice@example.org", password="password")
        url = "/accounts/set_password/invalid/"
        r = self.client.post(url)
        self.assertEqual(r.status_code, 400)

    def test_set_password_redirects(self):
        self.profile.token = make_password("secret-token")
        self.profile.save()
        self.client.login(username="alice@example.org", password="password")
        form = {"password": "password2"}
        url = "/accounts/set_password/secret-token/"
        r = self.client.post(url, form)
        self.assertRedirects(r, "/accounts/profile/")









