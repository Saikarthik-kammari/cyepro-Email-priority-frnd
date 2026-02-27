import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def get_unread_emails(service, max_results=10):
    try:
        results = service.users().messages().list(userId='me', q='is:unread', maxResults=max_results).execute()
        messages = results.get('messages', [])
        emails = []
        for msg in messages:
            msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            payload = msg_data['payload']
            headers = payload['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
            from_ = next((h['value'] for h in headers if h['name'] == 'From'), '(Unknown)')
            snippet = msg_data.get('snippet', '')
            emails.append({
                'id': msg['id'],
                'subject': subject,
                'from': from_,
                'snippet': snippet,
                'full_body': snippet  # for demo; can fetch more if needed
            })
        return emails
    except HttpError as error:
        print(f'An error occurred: {error}')
        return []

def add_label(service, msg_id, label_id):
    service.users().messages().modify(
        userId='me',
        id=msg_id,
        body={
            'addLabelIds': [label_id]
        }
    ).execute()

def get_label_id(service, label_name):
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    for label in labels:
        if label['name'] == label_name:
            return label['id']

    return None