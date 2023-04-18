import base64
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os import environ
from typing import Optional
from jinja2 import Template


def lambda_handler(event: Optional[dict] = None, context=None):
    debug_sleep = environ.get("debug_sleep")
    if debug_sleep:
        print('sleeping for', debug_sleep)
        try:
            from time import sleep
            sleep(int(debug_sleep))
        except ValueError:
            ...

    if not event:
        return {
            'statusCode': 500,
            'body': 'Specify recipients in event'
        }
    host = environ.get('host')
    port = int(environ.get('port'))
    user = environ.get('user')
    passwd = environ.get('passwd')
    sender = environ.get('sender')
    template = base64.b64decode(environ.get('template', '')).decode('utf-8')
    project_id = environ.get('project_id')

    template_vars = {
        'project_id': project_id
    }
    template_vars.update(event.get('template_vars', {}))

    recipients = event.get('recipients', [])
    if not recipients:
        return {
            'statusCode': 500,
            'body': 'Specify recipients in event'
        }

    subject = event.get('subject', 'Invitation to centry project')

    try:
        with smtplib.SMTP_SSL(host=host, port=port) as client:
            client.ehlo()
            client.login(user, passwd['value'])

            for recipient in recipients:
                user_template_vars = {**template_vars, 'recipient': recipient}
                email_content = Template(template)

                msg_root = MIMEMultipart('alternative')
                msg_root['Subject'] = subject
                msg_root['From'] = sender
                msg_root['To'] = recipient['email']
                msg_root.attach(
                    MIMEText(email_content.render(user_template_vars), 'html')
                )
                client.sendmail(sender, recipient['email'], msg_root.as_string())

                print(f'Email sent to {recipient["email"]}')
    except Exception as e:
        from traceback import format_exc
        print(format_exc())
        return {
            'statusCode': 500,
            'body': json.dumps(str(e))
        }
    return {
        'statusCode': 200,
        'body': json.dumps('Email sent')
    }
