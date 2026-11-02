import os

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
GOOGLE_DOC = "application/vnd.google-apps.document"
TEXT_FILE = "text/plain"


def _service():
    creds = service_account.Credentials.from_service_account_file(
        os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"], scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def list_documents(folder_id: str) -> list[dict]:
    """Return id, title, url and modified time for each Google Doc or .txt file in the folder."""
    service = _service()
    query = (
        f"'{folder_id}' in parents and trashed = false "
        f"and (mimeType = '{GOOGLE_DOC}' or mimeType = '{TEXT_FILE}')"
    )
    docs, page_token = [], None
    while True:
        resp = (
            service.files()
            .list(
                q=query,
                fields="nextPageToken, files(id, name, mimeType, webViewLink, modifiedTime)",
                pageSize=100,
                pageToken=page_token,
            )
            .execute()
        )
        for f in resp.get("files", []):
            docs.append(
                {
                    "id": f["id"],
                    "title": f["name"],
                    "mime_type": f["mimeType"],
                    "url": f["webViewLink"],
                    "modified_time": f["modifiedTime"],
                }
            )
        page_token = resp.get("nextPageToken")
        if not page_token:
            return docs


def fetch_document(doc_id: str, mime_type: str | None = None) -> str:
    """Return the plain text of one Google Doc or uploaded .txt file."""
    files = _service().files()
    if mime_type is None:
        mime_type = files.get(fileId=doc_id, fields="mimeType").execute()["mimeType"]
    if mime_type == GOOGLE_DOC:
        data = files.export(fileId=doc_id, mimeType="text/plain").execute()
    else:
        data = files.get_media(fileId=doc_id).execute()
    return data.decode("utf-8")
