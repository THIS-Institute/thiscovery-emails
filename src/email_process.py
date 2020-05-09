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
# import http
# import json
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

import common.utilities as utils
from common.dynamodb_utilities import Dynamodb
from common.s3_utilities import S3Client
from common.ses_utilities import SesClient


def get_forward_to_address(received_for, correlation_id=None):
    ddb_client = Dynamodb()
    ddb_item = ddb_client.get_item(table_name='ForwardingMap', key=received_for, correlation_id=correlation_id)
    if ddb_item is not None:
        return ddb_item['forward-to']


def extract_received_for(mail_object, correlation_id=None):
    received_for_pattern = re.compile(r'for (.+@.*thiscovery\.org)')
    received_value = mail_object.get('Received')
    return received_for_pattern.search(received_value).group(1)


def create_message(message_content, message_obj_http_path, correlation_id=None):
    separator = ";"
    mail_object = email.message_from_string(message_content.decode('utf-8'))
    received_for = extract_received_for(mail_object)
    recipient_list = get_forward_to_address(received_for, correlation_id=correlation_id)

    # Create a new subject line.
    subject_original = mail_object['Subject']
    subject = f"[{received_for}] " + subject_original

    # The body text of the email.
    body_text = f"The attached message was received from {separator.join(mail_object.get_all('From'))}. " \
                f"This message is archived at {message_obj_http_path}"

    # The file name to use for the attached message. Uses regex to remove all
    # non-alphanumeric characters, and appends a file extension.
    filename = re.sub('[^0-9a-zA-Z]+', '_', subject_original) + ".eml"

    # Create a MIME container.
    msg = MIMEMultipart()
    # Create a MIME text part.
    text_part = MIMEText(body_text, _subtype="html")
    # Attach the text part to the MIME message.
    msg.attach(text_part)

    # Add subject, from and to lines.
    msg['Subject'] = subject
    msg['From'] = mail_object['From']
    msg['To'] = ", ".join(recipient_list)

    # Create a new MIME object.
    att = MIMEApplication(message_content, filename)
    att.add_header("Content-Disposition", 'attachment', filename=filename)

    # Attach the file object to the message.
    msg.attach(att)

    return recipient_list, msg.as_string()


def get_message_from_s3(s3_bucket_name, object_key, region=None, correlation_id=None):
    if region is None:
        region = utils.DEFAULT_AWS_REGION
    s3_client = S3Client()
    message_obj_http_path = f"http://s3.console.aws.amazon.com/s3/object/{s3_bucket_name}/{object_key}?region={region}"
    message_obj = s3_client.get_object(bucket=s3_bucket_name, key=object_key)
    message_content = message_obj['Body'].read()
    return message_content, message_obj_http_path


def forward_email(message_id, correlation_id=None):
    incoming_email_bucket = utils.get_secret("incoming-email-bucket")['name']
    message_content, message_obj_http_path = get_message_from_s3(incoming_email_bucket, message_id, correlation_id)
    recipient_list, output_message = create_message(message_content, message_obj_http_path, correlation_id)
    ses_client = SesClient()
    return ses_client.send_raw_email(
        Source='no-reply@thiscovery.org',
        Destinations=recipient_list,
        RawMessage={'Data': output_message}
    )


@utils.lambda_wrapper
def forward_email_handler(event, context):
    logger = event['logger']
    logger.debug('Logging event', extra={'event': event})
    message_id = event['Records'][0]['ses']['mail']['messageId']
    logger.info("Processing message object", extra={'message_id': message_id})
    return forward_email(message_id=message_id, correlation_id=event['correlation_id'])

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