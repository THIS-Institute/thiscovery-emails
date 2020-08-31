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
import thiscovery_lib.utilities as utils
from botocore.exceptions import ClientError


class SesClient(utils.BaseClient):
    CHARSET = "UTF-8"

    def __init__(self, profile_name=None):
        super().__init__('ses', profile_name=profile_name)

    def send_simple_email(self, source, to_, subject, body_text, body_html, **kwargs):
        """
        Sends an email to a single recipient

        Args:
            source (str): The email address that is sending the email
            to_ (str): The email address that is receiving the email
            subject (str): The subject line
            body_text (str): Body of the email in plain text format
            body_html (str): Body of the email in html
            **kwargs: Optional parameters (see documentation)

        Returns:
            None
        """
        return self.send_email(source=source, destination={'ToAddresses': [to_]},
                               message={
                                   'Subject': {
                                       'Charset': self.CHARSET,
                                       'Data': subject,
                                   },
                                   'Body': {
                                       'Html': {
                                           'Charset': self.CHARSET,
                                           'Data': body_html,
                                       },
                                       'Text': {
                                           'Charset': self.CHARSET,
                                           'Data': body_text,
                                       },
                                   },
                               },
                               **kwargs
                               )

    def send_email(self, source, destination, message, **kwargs):
        """
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ses.html#SES.Client.send_email

        Args:
            source (str): The email address that is sending the email
            destination (dict): The destination for this email, composed of To:, CC:, and BCC: fields.
            message (dict): The message to be sent.
            **kwargs: Optional parameters (see documentation)

        Returns:
            None
        """
        try:
            response = self.client.send_email(Destination=destination, Message=message, Source=source)
            status_code = response['ResponseMetadata']['HTTPStatusCode']
            return status_code
        except ClientError as e:
            self.logger.error(e)

    def send_raw_email(self, **kwargs):
        """
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ses.html#SES.Client.send_raw_email
        """
        try:
            response = self.client.send_raw_email(**kwargs)
            status_code = response['ResponseMetadata']['HTTPStatusCode']
            return status_code
        except ClientError as e:
            self.logger.error(e)
