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
import chardet
import email
import json

import unittest

from http import HTTPStatus
from pprint import pprint

from src.common.s3_utilities import S3Client
import src.common.utilities as utils
import src.email_process as ep
import tests.testing_utilities as test_utils
from local.secrets import THISCOVERY_PROD_PROFILE


class TestStoredEmail(test_utils.BaseTestCase):
    def test_01(self):
        stored_email = ep.StoredEmail(message_id="k3vnqosoe68auc5ou6053meeaepfl73e0bl7kh01")
        # stored_email = ep.StoredEmail(message_id="5tofbsoeh8s6qfhthh5vgqapqornu04mkme0ocg1")
        stored_email.s3_client = S3Client(profile_name=THISCOVERY_PROD_PROFILE)
        stored_email.get_message()
        mail_object = email.message_from_string(stored_email.message.decode('utf-8'), policy=email.policy.default)
        body = stored_email.get_body(mail_object)
        probable_encoding = chardet.detect(body)['encoding']
        print(probable_encoding)
        body = body.decode(probable_encoding)
        pprint(body)
