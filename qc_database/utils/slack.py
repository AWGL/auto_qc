import subprocess

def message_slack(message):
    # url saved in file so it isn't posted on github
    with open('slack_url.txt') as f:
        slack_url = f.read()
    
    # build curl command and run it
    command = "curl -X POST -H 'Content-type: application/json' --data '{" + f'"text":"{message}"' + "}' " + slack_url
    subprocess.run(command, shell=True)
