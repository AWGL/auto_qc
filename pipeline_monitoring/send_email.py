import pickle
import os.path
import base64
import urllib.error
import urllib3
import mimetypes
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def send_email_via_api(to_address, message_title, message_body, credentials_json):

	credent = authenticate(SCOPES, credentials_json)

	m = create_message(to_address, to_address, message_title, message_body)

	serv = build('gmail', 'v1', credentials=credent)

	send_message(serv , "me", m)


def authenticate(scope, credentials_json):
	creds = None
	# The file token.pickle stores the user's access and refresh tokens, and is
	# created automatically when the authorization flow completes for the first
	# time.
	if os.path.exists('token.pickle'):
		with open('token.pickle', 'rb') as token:
			creds = pickle.load(token)
	# If there are no (valid) credentials available, let the user log in.
	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			creds.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file(
				credentials_json, SCOPES)
			creds = flow.run_local_server()
		# Save the credentials for the next run
		with open('token.pickle', 'wb') as token:
			pickle.dump(creds, token)
	return(creds)


def create_message(sender, to, subject, message_text):
  """Create a message for an email.
  Args:
	sender: Email address of the sender.
	to: Email address of the receiver.
	subject: The subject of the email message.
	message_text: The text of the email message.
  Returns:
	An object containing a base64url encoded email object.
  """
  message = MIMEText(message_text)
  message['to'] = to
  message['from'] = sender
  message['subject'] = subject
  return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

def create_message_with_attachment(sender, to, subject, message_text, file):
	"""Create a message for an email.
	Args:
	sender: Email address of the sender.
	to: Email address of the receiver.
	subject: The subject of the email message.
	message_text: The text of the email message.
	file: The path to the file to be attached.
	Returns:
	An object containing a base64url encoded email object.
	"""
	message = MIMEMultipart()
	message['to'] = to
	message['from'] = sender
	message['subject'] = subject

	msg = MIMEText(message_text)
	message.attach(msg)

	content_type, encoding = mimetypes.guess_type(file)

	if content_type is None or encoding is not None:
		content_type = 'application/octet-stream'
		main_type, sub_type = content_type.split('/', 1)
	if main_type == 'text':
		fp = open(file, 'rb')
		msg = MIMEText(fp.read(), _subtype=sub_type)
		fp.close()
	elif main_type == 'image':
		fp = open(file, 'rb')
		msg = MIMEImage(fp.read(), _subtype=sub_type)
		fp.close()
	elif main_type == 'audio':
		fp = open(file, 'rb')
		msg = MIMEAudio(fp.read(), _subtype=sub_type)
		fp.close()
	else:
		fp = open(file, 'rb')
		msg = MIMEBase(main_type, sub_type)
		msg.set_payload(fp.read())
		fp.close()
	filename = os.path.basename(file)
	msg.add_header('Content-Disposition', 'attachment', filename=filename)
	message.attach(msg)

	return {'raw': base64.urlsafe_b64encode(message.as_string())}

def send_message(service, user_id, message):
	"""Send an email message.
	Args:
	service: Authorized Gmail API service instance.
	user_id: User's email address. The special value "me"
	can be used to indicate the authenticated user.
	message: Message to be sent.
	Returns:
	Sent Message.
	"""
	try:
		message = (service.users().messages().send(userId=user_id, body=message)
			   .execute())
		print('Message Id: %s' % message['id'])
		return message
	except:
		print('An error occurred: %s' % error)

if __name__ == '__main__':
	main()