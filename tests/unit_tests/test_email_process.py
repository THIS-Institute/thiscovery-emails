#
#   Thiscovery API - THIS Institute’s citizen science platform
#   Copyright (C) 2019 THIS Institute
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   A copy of the GNU Affero General Public License is available in the
#   docs folder of this project.  It is also available www.gnu.org/licenses/
#
import local.dev_config  # sets env variables TEST_ON_AWS and AWS_TEST_API
import local.secrets  # sets env variables THISCOVERY_AFS25_PROFILE and THISCOVERY_AMP205_PROFILE
import email
import json
import unittest

from http import HTTPStatus

import src.email_process as ep
import thiscovery_dev_tools.testing_tools as test_utils


TEST_FORWARDING_MAP = {
    "unit-tests@thiscovery.org": [
        "unit-tests@cam.ac.uk",
        "developer@thisinstitute.cam.ac.uk",
    ],
}


class TestEmailProcessLocal(unittest.TestCase):
    """
    Use this class for tests that do not rely on any AWS resource
    """
    def test_extract_received_for(self):
        with open("test_message.mime") as f:
            mail_object = email.message_from_string(f.read())
            self.assertEqual("test@thiscovery.org", ep.extract_received_for(mail_object))


class TestEmailProcess(test_utils.BaseTestCase):
    send_email_api_endpoint = "v1/send"

    def test_get_forward_to_address_ok(self):
        for k, v in TEST_FORWARDING_MAP.items():
            self.assertEqual(v, ep.get_forward_to_address(k))

    def test_create_message(self):
        with open("test_message.mime") as f:
            message_content = f.read()
            # todo: finish writing this test

    def test_send_email_api(self):
        expected_status = HTTPStatus.OK
        email_dict = {
            "to": "test@thiscovery.org",
            "subject": "Test send email api",
            "body_text": "Lorem ipsum dolor sit amet, mea at voluptua delectus mediocritatem. "
                         "Duis sententiae duo cu, solum atqui volumus no vel, nam tation alienum at. "
                         "Soluta debitis ea mel. Sea laboramus intellegat accommodare te, vix ne etiam maiestatis. "
                         "Dico mazim quidam nam at, eu eos maiorum inimicus gloriatur. "
                         "Vim at lorem moderatius, decore iisque scribentur mel ne, eros signiferumque ei vel.",
            "body_html": "<h3>Lorem ipsum dolor sit amet, mea at voluptua delectus mediocritatem.</h3> "
                         '<p style="text-align: center;">Duis sententiae duo cu, solum atqui volumus no vel, nam tation alienum at.</p>  '
                         '<p><a href="https://www.thiscovery.org/" target="_blank">Soluta debitis ea mel. '
                         'Sea laboramus intellegat accommodare te, vix ne etiam maiestatis.</a> '
                         "Dico mazim quidam nam at, eu eos maiorum inimicus gloriatur. "
                         "Vim at lorem moderatius, decore iisque scribentur mel ne, eros signiferumque ei vel.</p>",
        }
        body_json = json.dumps(email_dict)
        result = test_utils.test_post(ep.send_email_api, self.send_email_api_endpoint, request_body=body_json)
        self.assertEqual(expected_status, result['statusCode'])
