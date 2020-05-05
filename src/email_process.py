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
import http
import json

# import common.utilities as utils
# from common.ses_utilities import SesClient


ses_client = None


# @utils.lambda_wrapper
def forward_email_handler(event, context):
    # logger = event['logger']
    message = event['Records'][0]['ses']['mail']
    print(json.dumps(message))
    # message_id = event['Records'][0]['ses']['mail']['messageId']
    # logger.info("Processing message", extra={'message_id': message_id})


# def send_email():
#     global ses_client
#     if ses_client is None:
#         ses_client = SesClient()
#     ses_client.send_email()
#
#
# @utils.lambda_wrapper
# @utils.api_error_handler
# def send_email_api(event, context):
#     logger = event['logger']
#     correlation_id = event['correlation_id']
#     email_dict = json.loads(event['body'])
#     logger.info('API call', extra={'email_dict': email_dict, 'correlation_id': correlation_id})
#     new_user_task = create_user_task(ut_json, correlation_id)
#     return {"statusCode": http.HTTPStatus.NO_CONTENT, "body": json.dumps(new_user_task)}