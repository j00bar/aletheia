import datetime
import logging
import pickle
import os
import shutil
import tempfile

from apiclient import errors
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dateutil import parser
import yaml

from ..exceptions import ConfigError, AletheiaException
from ..utils import devel_dir

MIME_TYPES = dict(
    epub='application/epub+zip',
    docx='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    rtf='application/rtf',
    html='text/html'
)
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
logger = logging.getLogger(__name__)


class Source:
    def __init__(self, folder_id, format='docx', title=None, credentials='credentials.json', token='token.pickle', 
                 devel=False, config_dir='.'):
        self.folder_id = folder_id
        self.format = format
        self.title = title
        self.credentials = os.path.join('/tmp', credentials)
        self.token = os.path.join(config_dir, token)
        self._tempdir = None
        self.devel = devel

    @property
    def working_dir(self):
        if not self._tempdir:
            if self.devel:
                self._tempdir = devel_dir(f'googledrive--{self.folder_id}--{self.format}')
            else:
                self._tempdir = tempfile.mkdtemp()
        return self._tempdir

    def cleanup(self):
        try:
            if self._tempdir:
                shutil.rmtree(self._tempdir)
        except:  # noqa: E722
            logger.warning(f'Cleanup failed removing Google tempdir {self._tempdir}')

    def get_google_creds(self, interactive=False):
        if os.path.exists(self.token):
            with open(self.token, 'rb') as token:
                creds = pickle.load(token)
        else:
            creds = None
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            elif interactive:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials, SCOPES)
                creds = flow.run_local_server(port=8888)
            else:
                raise ConfigError('No Google Drive credentials found. Run an interactive flow to generate them.')
            try:
                # Save the credentials for the next run
                with open(self.token, 'wb') as token:
                    pickle.dump(creds, token)
            except (PermissionError, OSError):
                logger.warning('Could not save updated token.')
        return creds
    
    def run(self):
        creds = self.get_google_creds()
        service = build('drive', 'v3', credentials=creds)

        if not self.title:
            response = service.files().get(fileId=self.folder_id).execute()
            self.title = response['name']

        page_token = None
        index_timestamp = 0.0
        while 1:
            try:
                param = {}
                if page_token:
                    logger.info('Getting next page of results.')
                    param['pageToken'] = page_token
                else:
                    logger.info('Getting first page of results from Google Drive folder listing.')
                response = service.files().list(
                    q=f"'{self.folder_id}' in parents and mimeType = 'application/vnd.google-apps.document'",
                    fields='files(id, name, modifiedTime)', **param
                ).execute()
                for file_ in response.get('files', []):
                    try:
                        logger.info(f'Found file {file_["name"]}.')
                        # get the file and save to disk
                        export = service.files().export_media(
                            fileId=file_['id'], mimeType=MIME_TYPES[self.format]
                        )
                        filename = f'{file_["name"]}.{self.format}'.replace('/', '-')
                        with open(os.path.join(self.working_dir, filename), 'wb') as ofs:
                            downloader = MediaIoBaseDownload(ofs, export, chunksize=1024*1024)
                            done = False
                            while not done:
                                status, done = downloader.next_chunk()
                        # Set proper file timestamps
                        mtime = parser.parse(file_['modifiedTime']).timestamp()
                        index_timestamp = max(index_timestamp, mtime)
                        os.utime(os.path.join(self.working_dir, filename),
                                 (mtime, mtime))
                    except errors.HttpError as e:
                        logger.warning(f'Error downloading file from Google "{file_["name"]}" - {file_["id"]} - {e}')
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
            except errors.HttpError as e:
                raise AletheiaException(f'Error retrieving from Google: {e}')
        logger.info('All files retrieved.')
        with open(os.path.join(self.working_dir, '_index.md'), 'w') as ofs:
            ofs.write(f'# {self.title}\n')
        os.utime(os.path.join(self.working_dir, '_index.md'), (index_timestamp, index_timestamp))
        return self.working_dir

