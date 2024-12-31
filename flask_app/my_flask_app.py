from flask import Flask, request, render_template, redirect, url_for, jsonify
import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)

# Load environment variables (ensure you have a .env file with the required keys)
load_dotenv()

# Supabase Connection
url = os.getenv("SUPABASE_URL")  # Supabase URL
key = os.getenv("SUPABASE_KEY")  # Supabase API Key
supabase: Client = create_client(url, key)

# Google Sheets Authentication
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# Helper function to fix Base64 padding
def fix_base64_padding(key):
    key = key.strip()  # Remove any leading or trailing whitespace
    padding_needed = len(key) % 4
    if padding_needed:
        key += '=' * (4 - padding_needed)
    return key

# Parse the JSON string from the GOOGLE_SERVICE_ACCOUNT environment variable
try:
    service_account_info = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT"))
    if 'private_key' in service_account_info:
        private_key = service_account_info['private_key']
        private_key = private_key.replace("\\n", "\n").strip()
        private_key = fix_base64_padding(private_key)
        service_account_info['private_key'] = private_key
        print("Private key loaded and fixed successfully")
    else:
        raise KeyError("Private key not found in service account info.")
except (json.JSONDecodeError, KeyError) as e:
    raise ValueError(f"Error parsing GOOGLE_SERVICE_ACCOUNT: {e}")

# Authenticate with Google Sheets
try:
    credentials = Credentials.from_service_account_info(
        service_account_info,
        scopes=SCOPES
    )
    service = build('sheets', 'v4', credentials=credentials)
    print("Google Sheets client authorized successfully")
except Exception as e:
    raise ValueError(f"Error authorizing Google Sheets client: {e}")

# Open the Google Sheet using its ID (set in environment variables)
SHEET_ID = os.getenv("GS_SHEET_ID")
sheet = service.spreadsheets()

@app.route('/attendance')
def view_attendance():
    attendance_data = supabase.table('attendance').select('id, student_name, networker_name, status, comment, timestamp').execute().data
    return render_template('attendance.html', attendances=attendance_data)

@app.route('/')
def index():
    response = supabase.table('attendance').select('networker_name').execute()
    networks = sorted(set(row['networker_name'] for row in response.data))
    return render_template('index.html', networks=networks)

@app.route('/students/<network>')
def get_students(network):
    response = supabase.table('attendance').select('*').eq('networker_name', network).execute()
    students = [{'id': row['id'], 'name': row['student_name']} for row in response.data]
    return jsonify(students)

@app.route('/submit', methods=['POST'])
def submit_attendance():
    data = request.form
    try:
        # Open the "results" worksheet or create it if not exists
        try:
            worksheet = sheet.values().get(spreadsheetId=SHEET_ID, range="results!A1").execute()
        except Exception:
            request_body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': 'results',
                            'gridProperties': {
                                'rowCount': 100,
                                'columnCount': 6
                            }
                        }
                    }
                }]
            }
            sheet.batchUpdate(spreadsheetId=SHEET_ID, body=request_body).execute()

        # Clear existing data from rows (if any)
        all_rows = sheet.values().get(spreadsheetId=SHEET_ID, range="results").execute()
        if 'values' in all_rows and len(all_rows['values']) > 1:
            range_to_clear = f"results!A2:Z{len(all_rows['values'])}"
            sheet.values().clear(spreadsheetId=SHEET_ID, range=range_to_clear).execute()

        # Fetch columns and map them to custom headers
        columns_response = supabase.table('attendance').select('*').limit(1).execute().data
        if not columns_response:
            raise Exception("Failed to fetch columns")

        custom_headers = {
            'id': 'Roll Number',
            'student_name': 'Student Name',
            'networker_name': 'Networker',
            'status': 'Status',
            'comment': 'Comment',
        }

        columns = list(columns_response[0].keys())
        columns = [column for column in columns if column != 'timestamp']
        custom_columns = [custom_headers.get(col, col) for col in columns]

        # Update headers in the "results" sheet
        sheet.values().update(
            spreadsheetId=SHEET_ID,
            range="results!A1",
            valueInputOption="RAW",
            body={"values": [custom_columns]}
        ).execute()

        # Update Supabase and fetch data for writing into the sheet
        for key, value in data.items():
            if key.startswith('status_'):
                student_id = key.split('_')[1]
                status = value
                comment_key = f"comment_{student_id}"
                comment = data.get(comment_key, "")
                supabase.table('attendance').update({
                    'status': status,
                    'comment': comment
                }).eq('id', student_id).execute()

        fetch_response = supabase.table('attendance').select('id, student_name, networker_name, status, comment').execute()
        if not fetch_response.data:
            return "No data found", 500

        all_rows = [
            [row[column] if column != 'timestamp' else row[column].split('T')[0] for column in columns]
            for row in fetch_response.data
        ]

        if all_rows:
            sheet.values().append(
                spreadsheetId=SHEET_ID,
                range="results!A2",
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body={"values": all_rows}
            ).execute()

        return redirect(url_for('index'))

    except Exception as e:
        return f"An error occurred: {e}", 500

if __name__ == '__main__':
    app.run(debug=True)
