import json
from datetime import timedelta as td
from django.utils.timezone import now

from hc.api.models import Check
from hc.test import BaseTestCase
from hc.settings import PING_ENDPOINT, SITE_ROOT


class ListChecksTestCase(BaseTestCase):

    def setUp(self):
        super(ListChecksTestCase, self).setUp()

        self.now = now().replace(microsecond=0)

        self.a1 = Check(user=self.alice, name="Alice 1")
        self.a1.timeout = td(seconds=3600)
        self.a1.grace = td(seconds=900)
        self.a1.last_ping = self.now
        self.a1.n_pings = 1
        self.a1.status = "new"
        self.a1.save()

        self.a2 = Check(user=self.alice, name="Alice 2")
        self.a2.timeout = td(seconds=86400)
        self.a2.grace = td(seconds=3600)
        self.a2.last_ping = self.now
        self.a2.status = "up"
        self.a2.save()

    def get(self):
        return self.client.get("/api/v1/checks/", HTTP_X_API_KEY="abc")

    def test_it_works(self):
        r = self.get()
        ### Assert the response status code
        assert r.status_code == 200

        doc = r.json()
        self.assertTrue("checks" in doc)

        checks = {check["name"]: check for check in doc["checks"]}
        ### Assert the expected length of checks
        assert len(checks) == 2

        ### Assert the checks Alice 1 and Alice 2's timeout, grace, ping_url, status,
        ### last_ping, n_pings and pause_url
        # Timeout
        response_a1 = checks['Alice 1']
        response_a2 = checks['Alice 2']
        a1 = {
            'name': self.a1.name,
            'timeout': int(self.a1.timeout.total_seconds()),
            'grace': int(self.a1.grace.total_seconds()),
            'ping_url': self.a1.url(),
            'status': self.a1.status,
            'last_ping': self.now.isoformat(),
            'n_pings': self.a1.n_pings,
            'pause_url': SITE_ROOT + '/api/v1/checks/' + str(self.a1.code) + '/pause'
        }

        a2 = {
            'name': self.a2.name,
            'timeout': int(self.a2.timeout.total_seconds()),
            'grace': int(self.a2.grace.total_seconds()),
            'ping_url': self.a2.url(),
            'status': self.a2.status,
            'last_ping': self.now.isoformat(),
            'n_pings': self.a2.n_pings,
            'pause_url': SITE_ROOT + '/api/v1/checks/' + str(self.a2.code) + '/pause'
        }

        self.assertDictContainsSubset(a1, response_a1)
        self.assertDictContainsSubset(a2, response_a2)

    def test_it_shows_only_users_checks(self):
        bobs_check = Check(user=self.bob, name="Bob 1")
        bobs_check.save()

        r = self.get()
        data = r.json()
        self.assertEqual(len(data["checks"]), 2)
        for check in data["checks"]:
            self.assertNotEqual(check["name"], "Bob 1")

    ### Test that it accepts an api_key in the request
    def test_it_accepts_api_key_in_request(self):
        payload = {"api_key": "abc"}
        r = self.client.post("/api/v1/checks/", json.dumps(payload), \
                             content_type="application/json")
        assert r.status_code == 201
