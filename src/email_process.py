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
import re
import thiscovery_lib.utilities as utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from thiscovery_lib.dynamodb_utilities import Dynamodb
from thiscovery_lib.interviews_api_utilities import InterviewsApiClient
from thiscovery_lib.s3_utilities import S3Client
from thiscovery_lib.ses_utilities import SesClient


STACK_NAME = 'thiscovery-emails'


def get_forward_to_address(received_for, correlation_id=None):
    """
    Args:
        received_for:
        correlation_id:

    Returns:

    Notes:
        This function can probably be optimised by making a call to the scan method of ddb_client and then parsing the results, rather than making
        up to three separate calls to get_item

    """
    ddb_client = Dynamodb(stack_name=STACK_NAME)

    # try matching full received_for email address
    ddb_item = ddb_client.get_item(table_name='ForwardingMap', key=received_for, correlation_id=correlation_id)
    if ddb_item is not None:
        return ddb_item['forward-to']

    # try matching subdomain
    subdomain = received_for.split('@')[1]
    ddb_item = ddb_client.get_item(table_name='ForwardingMap', key=subdomain, correlation_id=correlation_id)
    if ddb_item is not None:
        return ddb_item['forward-to']

    # go for the domain catch-all rule
    ddb_item = ddb_client.get_item(table_name='ForwardingMap', key="thiscovery.org", correlation_id=correlation_id)
    if ddb_item is not None:
        return ddb_item['forward-to']


def extract_received_for(mail_object, correlation_id=None):
    received_for_pattern = re.compile(r'for (.+@.*thiscovery\.org)')
    received_value = mail_object.get('Received')
    return received_for_pattern.search(received_value).group(1)


def create_message(message_content, message_obj_http_path, correlation_id=None):
    separator = ";"
    mail_object = email.message_from_string(message_content.decode('utf-8'), policy=email.policy.default)  # https://stackoverflow.com/a/55210089
    received_for = extract_received_for(mail_object)
    recipient_list = get_forward_to_address(received_for, correlation_id=correlation_id)

    # Create a new subject line.
    subject_original = mail_object['Subject']
    subject = f"[{received_for}] " + subject_original

    # The body text of the email.
    body_text = f"The attached message was received from {separator.join(mail_object.get_all('From')).strip()}. " \
                f"It is archived at {message_obj_http_path}"

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
    msg['From'] = 'no-reply@thiscovery.org'
    msg['To'] = ", ".join(recipient_list)

    # Create a new MIME object.
    att = MIMEApplication(message_content, filename)
    att.add_header("Content-Disposition", 'attachment', filename=filename)

    # Attach the file object to the message.
    msg.attach(att)

    return recipient_list, msg.as_string()


class StoredEmail:

    def __init__(self, message_id, correlation_id=None):
        self.message_id = message_id
        self.correlation_id = correlation_id
        self.s3_client = S3Client()
        self.bucket = utils.get_secret("incoming-email-bucket")['name']
        self.message = None
        self.message_obj_http_path = None
        self.logger = utils.get_logger()

    def get_message(self, region=None):
        if region is None:
            region = utils.DEFAULT_AWS_REGION
        self.message_obj_http_path = f"http://s3.console.aws.amazon.com/s3/object/{self.bucket}/{self.message_id}?region={region}"
        message_obj = self.s3_client.get_object(bucket=self.bucket, key=self.message_id)
        self.message = message_obj['Body'].read()
        return self.message, self.message_obj_http_path

    def forward(self):
        if self.message is None:
            self.get_message()
        recipient_list, output_message = create_message(self.message, self.message_obj_http_path, self.correlation_id)
        ses_client = SesClient()
        return ses_client.send_raw_email(
            Source='no-reply@thiscovery.org',
            Destinations=recipient_list,
            RawMessage={'Data': output_message}
        )

    @staticmethod
    def get_body(mail_object):
        """
        Adapted from: https://stackoverflow.com/a/32840516
        """
        body = ""
        if mail_object.is_multipart():
            for part in mail_object.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get('Content-Disposition'))

                # skip any text/plain (txt) attachments
                if ctype == 'text/plain' and 'attachment' not in cdispo:
                    body = part.get_payload(decode=True)  # decode
                    break
        # not multipart - i.e. plain text, no attachments, keeping fingers crossed
        else:
            body = mail_object.get_payload(decode=True)
        return body

    def process_appointment_info(self):
        action_to_event_type = {
            'scheduled': 'booking',
            'rescheduled': 'rescheduling',
        }

        if self.message is None:
            self.get_message()
        mail_object = email.message_from_string(self.message.decode('utf-8'), policy=email.policy.default)
        subject = mail_object['Subject']

        # extract appointment id and action from subject line
        p = re.compile(r"Appointment (\d{5,}) ([a-z]+)")
        m = p.search(subject)
        try:
            appointment_id = m.group(1)
        except AttributeError:
            raise utils.DetailedValueError(f'Could not extract appointment id from subject line', details={
                'subject': subject,
                'correlation_id': self.correlation_id,
            })
        try:
            action = m.group(2)
        except AttributeError:
            raise utils.DetailedValueError(f'Could not extract event type from subject line', details={
                'subject': subject,
                'correlation_id': self.correlation_id,
            })

        body = self.get_body(mail_object=mail_object)

        # extract url from body
        p = re.compile(r"https?://[^\s]+")
        try:
            m = p.search(body)
        except TypeError:
            probable_encoding = chardet.detect(body)['encoding']
            body = body.decode(probable_encoding)
            m = p.search(body)
        try:
            appointment_url = m.group()
        except AttributeError:
            raise utils.DetailedValueError(f'Could not find a url in the email body', details={
                'subject': subject,
                'body': body,
                'correlation_id': self.correlation_id,
            })

        # extract env from body
        body = body.replace("\r\n", "\n")  # convert Windows newlines to UNIX format
        p = re.compile(r"^env=([a-z\-0-9]+)$", re.MULTILINE)
        m = p.search(body)
        target_env = None
        try:
            target_env = m.group(1)
        except AttributeError:
            self.logger.debug(f'Could not find env definition in email body', extra={
                'body': body,
                'correlation_id': self.correlation_id
            })

        interviews_client = InterviewsApiClient(
            env_override=target_env,
            correlation_id=self.correlation_id
        )
        return interviews_client.set_interview_url(
            appointment_id=appointment_id,
            interview_url=appointment_url,
            event_type=action_to_event_type[action]
        )


@utils.lambda_wrapper
def forward_email_handler(event, context):
    logger = event['logger']
    logger.debug('Logging event', extra={'event': event})
    message_id = event['Records'][0]['ses']['mail']['messageId']
    logger.info("Processing message object", extra={'message_id': message_id})
    s3_email = StoredEmail(
        message_id=message_id,
        correlation_id=event['correlation_id']
    )
    return s3_email.forward()


@utils.lambda_wrapper
def process_appointment(event, context):
    logger = event['logger']
    logger.debug('Logging event', extra={'event': event})
    message_id = event['Records'][0]['ses']['mail']['messageId']
    logger.info("Processing message object", extra={'message_id': message_id})
    s3_email = StoredEmail(
        message_id=message_id,
        correlation_id=event['correlation_id']
    )
    return s3_email.process_appointment_info()


def send_email(to_address, subject, message_text, message_html, source="no-reply@thiscovery.org", correlation_id=None):
    ses_client = SesClient()
    return ses_client.send_simple_email(
        source=source,
        to_=to_address,
        subject=subject,
        body_text=message_text,
        body_html=message_html,
    )


@utils.lambda_wrapper
@utils.api_error_handler
def send_email_api(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']
    logger.debug('Logging event', extra={'event': event})
    email_dict = json.loads(event['body'])
    logger.info('API call', extra={'email_dict': email_dict, 'correlation_id': correlation_id})
    alarm_test = email_dict.get('brew_coffee')
    if alarm_test:
        raise utils.DeliberateError('Coffee is not available', details={})
    status_code = send_email(
        to_address=email_dict['to'],
        subject=email_dict['subject'],
        message_text=email_dict['body_text'],
        message_html=email_dict['body_html'],
        source=email_dict.get('source', "no-reply@thiscovery.org"),
        correlation_id=correlation_id
    )
    return {"statusCode": status_code}
