import json

from hc.api.models import Channel, Check
from hc.test import BaseTestCase


class CreateCheckTestCase(BaseTestCase):
    URL = "/api/v1/checks/"

    def setUp(self):
        super(CreateCheckTestCase, self).setUp()

    def post(self, data, expected_error=None):
        r = self.client.post(self.URL, json.dumps(data),
                             content_type="application/json")

        if expected_error:
            self.assertEqual(r.status_code, 400)
            ### self.assertEqual(that the expected error is the response error
            r = r.json()
            self.assertEqual(r["error"], expected_error)
        return r

    def test_it_works(self):
        r = self.post({
            "api_key": "abc",
            "name": "Foo",
            "tags": "bar,baz",
            "timeout": 3600,
            "grace": 60
        })

        self.assertEqual(r.status_code, 201)

        doc = r.json()
        self.assertIn("ping_url", doc)
        self.assertEqual(doc["name"], "Foo")
        self.assertEqual(doc["tags"], "bar,baz")

        ### assert that the expected last_ping and n_pings values
        check = Check()
        self.assertFalse(check.last_ping)
        self.assertEqual(check.n_pings, 0)

        self.assertEqual(Check.objects.count(), 1)
        check = Check.objects.get()
        self.assertEqual(check.name, "Foo")
        self.assertEqual(check.tags, "bar,baz")
        self.assertEqual(check.timeout.total_seconds(), 3600)
        self.assertEqual(check.grace.total_seconds(), 60)

    def test_it_accepts_api_key_in_header(self):
        payload = {
            "api_key": "abc",
            "name": "Fooo"
        }

        ### Make the post request and get the response
        r = self.post(payload)

        self.assertEqual(r.status_code, 201)

    def test_it_handles_missing_request_body(self):
        ### Make the post request with a missing body and get the response
        r = self.post({})

        self.assertEqual(r.status_code, 400)

    def test_it_handles_invalid_json(self):
        ### Make the post request with invalid json data type

        r = self.client.post(self.URL, {"invalid json"}, \
                content_type="application/json", HTTP_X_API_KEY="abc")

        self.assertEqual(r.json()["error"], "could not parse request body")

    def test_it_rejects_wrong_api_key(self):
        self.post({"api_key": "wrong"},
                  expected_error="wrong api_key")

    def test_it_rejects_non_number_timeout(self):
        self.post({"api_key": "abc", "timeout": "oops"},
                  expected_error="timeout is not a number")

    def test_it_rejects_non_string_name(self):
        self.post({"api_key": "abc", "name": False},
                  expected_error="name is not a string")

    ### Test for the assignment of channels
    def test_assignment_of_channels(self):
        check = Check()
        check.status = "up"
        check.user = self.alice
        check.save()

        channel = Channel(user=self.alice)
        channel.kind = "slack"
        channel.value = 'http://example.com'
        channel.email_verified = True
        channel.save()
        channel.checks.add(check)

        self.assertNotEqual(channel.checks, None)
        self.assertEqual(channel.user, self.alice)


    ### Test for the 'timeout is too small' and 'timeout is too large' errors
    def test_timeout_too_small(self):
        self.post({
            "api_key": "abc",
            "timeout": 1,
            "expected_error": "timeout_too_small"
        })

    def test_timeout_too_large(self):
        self.post({
            "api_key": "abc",
            "timeout": 90000000,
            "expected_error": "timeout_too_large"
        })
