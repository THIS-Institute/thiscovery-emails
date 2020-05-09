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
import email
import unittest

import src.common.utilities as utils
import src.email_process as ep
import tests.testing_utilities as test_utils


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

    def test_get_forward_to_address_ok(self):
        for k, v in TEST_FORWARDING_MAP.items():
            self.assertEqual(v, ep.get_forward_to_address(k))

    def test_create_message(self):
        with open("test_message.mime") as f:
            message_content = f.read()
            # todo: finish writing this test

