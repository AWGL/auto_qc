import subprocess
from django.conf import settings


def message_slack(message):
    # build curl command and run it
    command = "curl -X POST -H 'Content-type: application/json' --data '{" + f'"text":"{message}"' + "}' " + settings.SLACK_URL
    subprocess.run(command, shell=True)
    print ('Slack message sent.')
