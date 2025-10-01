import os, requests, datetime
from urllib.parse import quote
from typing import Optional
from fastapi import HTTPException
import msal
from backend.utils.logger import get_logger

logger = get_logger("sharepoint_service")

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SP_SITE_HOST = os.getenv("SHAREPOINT_SITE_HOST")
SP_SITE_NAME = os.getenv("SHAREPOINT_SITE_NAME")
SP_DOC_LIB  = os.getenv("SHAREPOINT_DOC_LIB", "Shared Documents")
SP_FOLDER   = os.getenv("SHAREPOINT_FOLDER_PATH", "Cross-functional/Zendesk/Bi-Weekly Reports")

def _log(msg: str):
    """Lightweight timestamped log for SharePoint ops."""
    print(f"[{datetime.datetime.now().isoformat()}] [SharePoint] {msg}")

def _enc(path: str) -> str:
    return "/".join(quote(seg, safe="") for seg in path.strip("/").split("/"))

def _token() -> str:
    authority = f"https://login.microsoftonline.com/{TENANT_ID}"
    app = msal.ConfidentialClientApplication(
        CLIENT_ID, authority=authority, client_credential=CLIENT_SECRET
    )
    res = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" not in res:
        _log(f"Auth failed: {res}")
        raise HTTPException(status_code=502, detail="Failed to authenticate with Microsoft Graph.")
    return res["access_token"]

def _hdr(tok: str) -> dict:
    return {"Authorization": f"Bearer {tok}"}

def _site_id(tok: str) -> str:
    url = f"https://graph.microsoft.com/v1.0/sites/{SP_SITE_HOST}:/sites/{SP_SITE_NAME}"
    r = requests.get(url, headers=_hdr(tok), timeout=60)
    if not r.ok:
        _log(f"Site lookup failed {r.status_code}: {r.text}")
        raise HTTPException(status_code=502, detail="SharePoint site not found.")
    return r.json()["id"]

def _drive_id(tok: str, site_id: str, drive_name: Optional[str]) -> str:
    if not drive_name:
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive"
        r = requests.get(url, headers=_hdr(tok), timeout=60)
        if not r.ok:
            _log(f"Drive lookup failed: {r.status_code} {r.text}")
            raise HTTPException(status_code=502, detail="Default drive not found.")
        return r.json()["id"]

    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
    r = requests.get(url, headers=_hdr(tok), timeout=60)
    if not r.ok:
        _log(f"Drive list failed: {r.status_code} {r.text}")
        raise HTTPException(status_code=502, detail="Drive list fetch failed.")

    for d in r.json().get("value", []):
        if (d.get("name") or "").strip().lower() == drive_name.strip().lower():
            return d["id"]

    raise HTTPException(status_code=502, detail=f"Drive '{drive_name}' not found")


def upload_bytes(filename: str, content: bytes) -> str:
    # Validate env vars
    missing = [k for k, v in [
        ("TENANT_ID", TENANT_ID), ("CLIENT_ID", CLIENT_ID), ("CLIENT_SECRET", CLIENT_SECRET),
        ("SHAREPOINT_SITE_HOST", SP_SITE_HOST), ("SHAREPOINT_SITE_NAME", SP_SITE_NAME),
        ("SHAREPOINT_DOC_LIB", SP_DOC_LIB), ("SHAREPOINT_FOLDER_PATH", SP_FOLDER)
    ] if not v]
    if missing:
        logger.error(f"Missing env vars: {missing}")
        raise HTTPException(status_code=502, detail=f"Missing env vars: {', '.join(missing)}")

    try:
        tok = _token()
        site_id = _site_id(tok)
        drive_id = _drive_id(tok, site_id, SP_DOC_LIB)
        path = _enc(f"{SP_FOLDER}/{filename}")
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{path}:/content"

        logger.info(f"Uploading {filename} to SharePoint at {SP_FOLDER}")
        r = requests.put(url, headers=_hdr(tok), data=content, timeout=300)

        if not r.ok:
            try:
                body = r.json()
            except Exception:
                body = r.text
            logger.error(f"Upload failed {r.status_code}: {body}")
            raise HTTPException(status_code=502, detail="SharePoint upload failed.")

        web_url = (r.json() or {}).get("webUrl", "")
        if not web_url:
            logger.error("Upload succeeded but no webUrl returned.")
            raise HTTPException(status_code=502, detail="Upload succeeded but no webUrl returned.")

        logger.info(f"Uploaded {filename} successfully → {web_url}")
        return web_url

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during SharePoint upload: {e}")
        raise HTTPException(status_code=502, detail=f"Unexpected SharePoint error: {e}")