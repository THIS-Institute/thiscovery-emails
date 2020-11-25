import local.dev_config  # sets env variables
import local.secrets  # sets env variables
import email
from pprint import pprint
from src.email_process import StoredEmail


def main(message_id):
    s3_email = StoredEmail(message_id=message_id)
    s3_email.get_message()
    mail_object = email.message_from_string(s3_email.message.decode('utf-8'), policy=email.policy.default)
    pprint(s3_email.get_body(mail_object))


if __name__ == '__main__':
    s3_object_id = 'p3igf50ki9h9a1e1ea3ckff6rgun80lis8pa5701'
    main(message_id=s3_object_id)
