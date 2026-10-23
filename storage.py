import io
import json
import re
import uuid
from datetime import date

import pandas as pd
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

COLUMNS = [
    "id", "jenis", "nama_task", "pic", "prioritas", "tgl_mulai", "deadline",
    "status", "progress", "catatan", "link_bukti", "tgl_selesai", "tindak_lanjut"
]
SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]


def is_admin_password_valid(candidate, configured):
    return bool(configured) and candidate == configured


def task_is_late(deadline, status, today=None):
    if not deadline or status == "Selesai":
        return False
    return str(deadline)[:10] < str(today or date.today().isoformat())


def _secrets():
    try:
        return st.secrets
    except Exception:
        return {}


def google_credentials():
    secrets = _secrets()
    config = secrets.get("gcp_service_account")
    if config:
        if hasattr(config, "to_dict"):
            config = config.to_dict()
        else:
            config = dict(config)
        return service_account.Credentials.from_service_account_info(config, scopes=SCOPES)
    key_path = secrets.get("GOOGLE_SERVICE_ACCOUNT_FILE")
    if key_path:
        return service_account.Credentials.from_service_account_file(str(key_path), scopes=SCOPES)
    raise RuntimeError("Kredensial Google belum dikonfigurasi di Streamlit Secrets.")


def drive_service():
    return build("drive", "v3", credentials=google_credentials(), cache_discovery=False)


def sheets_service():
    return build("sheets", "v4", credentials=google_credentials(), cache_discovery=False)


def _sheet_ids():
    secrets = _secrets()
    spreadsheet_id = secrets.get("TASK_SPREADSHEET_ID", "")
    if not spreadsheet_id:
        raise RuntimeError("TASK_SPREADSHEET_ID belum diset di Streamlit Secrets.")
    return str(spreadsheet_id)


def load_data():
    sid = _sheet_ids()
    result = sheets_service().spreadsheets().values().get(spreadsheetId=sid, range="Tasks!A1:M").execute()
    values = result.get("values", [])
    if not values:
        return pd.DataFrame(columns=COLUMNS)
    headers = values[0]
    rows = values[1:]
    df = pd.DataFrame(rows, columns=headers)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[COLUMNS]
    for col in ["progress"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df.fillna("")


def save_data(df):
    sid = _sheet_ids()
    values = [COLUMNS] + df[COLUMNS].fillna("").astype(str).values.tolist()
    sheets_service().spreadsheets().values().clear(spreadsheetId=sid, range="Tasks!A:M").execute()
    sheets_service().spreadsheets().values().update(
        spreadsheetId=sid, range="Tasks!A1", valueInputOption="RAW", body={"values": values}
    ).execute()


def load_members():
    sid = _sheet_ids()
    result = sheets_service().spreadsheets().values().get(spreadsheetId=sid, range="Members!A1:A").execute()
    names = [row[0].strip() for row in result.get("values", [])[1:] if row and row[0].strip()]
    return names or ["Lando", "Rahma", "Anggota 3", "Anggota 4"]


def save_members(members):
    sid = _sheet_ids()
    values = [["Anggota"]] + [[name] for name in members]
    sheets_service().spreadsheets().values().clear(spreadsheetId=sid, range="Members!A:A").execute()
    sheets_service().spreadsheets().values().update(
        spreadsheetId=sid, range="Members!A1", valueInputOption="RAW", body={"values": values}
    ).execute()


def upload_evidence(uploaded_file, task_name):
    folder_id = str(_secrets().get("DRIVE_FOLDER_ID", ""))
    if not folder_id:
        raise RuntimeError("DRIVE_FOLDER_ID belum dikonfigurasi di Streamlit Secrets.")
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", task_name).strip("_")[:70] or "task"
    filename = f"{date.today().isoformat()}_{safe_name}_{uuid.uuid4().hex[:8]}_{uploaded_file.name}"
    service = drive_service()
    media = MediaIoBaseUpload(io.BytesIO(uploaded_file.getvalue()), mimetype=uploaded_file.type or "application/octet-stream", resumable=True)
    uploaded = service.files().create(
        body={"name": filename, "parents": [folder_id]}, media_body=media,
        fields="id,name,webViewLink"
    ).execute()
    # View permission only; only the admin can upload through the app.
    service.permissions().create(
        fileId=uploaded["id"], body={"type": "anyone", "role": "reader"}, fields="id"
    ).execute()
    return uploaded.get("webViewLink", f"https://drive.google.com/file/d/{uploaded['id']}/view")


def bootstrap_spreadsheet():
    """Create required worksheet tabs/header rows. Returns spreadsheet ID and URL."""
    credentials = google_credentials()
    service = build("sheets", "v4", credentials=credentials, cache_discovery=False)
    spreadsheet = service.spreadsheets().create(body={
        "properties": {"title": "Monitoring Task Tim"},
        "sheets": [{"properties": {"title": "Tasks"}}, {"properties": {"title": "Members"}}]
    }, fields="spreadsheetId,spreadsheetUrl").execute()
    sid = spreadsheet["spreadsheetId"]
    service.spreadsheets().values().update(spreadsheetId=sid, range="Tasks!A1", valueInputOption="RAW", body={"values": [COLUMNS]}).execute()
    service.spreadsheets().values().update(spreadsheetId=sid, range="Members!A1", valueInputOption="RAW", body={"values": [["Anggota"], ["Lando"], ["Rahma"], ["Anggota 3"], ["Anggota 4"]]}).execute()
    return sid, spreadsheet["spreadsheetUrl"]
