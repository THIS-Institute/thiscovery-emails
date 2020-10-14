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
from http import HTTPStatus
from pprint import pprint

import tests.testing_utilities as test_utils
from local.dev_config import UNIT_TEST_NAMESPACE
from src.common.interviews_api_utilities import InterviewsApiClient


class TestInterviewUtilities(test_utils.BaseTestCase):
    test_data = {
        'appointment_id': '399682887',
        'interview_url': 'https://meet.myinterview.com/1b879c51-2e29-46ae-bd36-3199860e65f2',
        'event_type': 'booking',
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.interviews_client = InterviewsApiClient(
            env_override=UNIT_TEST_NAMESPACE[1:-1],
        )

    def test_01_set_interview_url_ok(self):
        result = self.interviews_client.set_interview_url(
            appointment_id=self.test_data['appointment_id'],
            interview_url=self.test_data['interview_url'],
            event_type=self.test_data['event_type'],
        )
        self.assertEqual(HTTPStatus.OK, result['statusCode'])
