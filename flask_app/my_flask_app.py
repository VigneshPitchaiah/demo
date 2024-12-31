import os
import json
from flask import Flask, render_template, request, redirect, url_for, jsonify
from supabase import create_client, Client
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Load environment variables (ensure you have a .env file with the required keys)
from dotenv import load_dotenv
load_dotenv()

# Supabase Connection
url = os.getenv("SUPABASE_URL")  # Supabase URL
key = os.getenv("SUPABASE_KEY")  # Supabase API Key
supabase: Client = create_client(url, key)

# Google Sheets Authentication
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Parse the JSON string from the GOOGLE_SERVICE_ACCOUNT environment variable
service_account_info = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT"))

service_account_info['private_key'] = service_account_info['private_key'].replace("\\n", "\n")
print('**'*50)
print(service_account_info['private_key'])

# Use the parsed JSON dictionary for Google Sheets credentials
creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
client = gspread.authorize(creds)  # Initialize the client here

# Open the Google Sheet using its ID (set in environment variables)
sheet = client.open_by_key(os.getenv("GS_SHEET_ID")).sheet1

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
        try:
            worksheet = client.open_by_key(os.getenv("GS_SHEET_ID")).worksheet("results")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = client.open_by_key(os.getenv("GS_SHEET_ID")).add_worksheet(title="results", rows=100, cols=6)

        all_rows = worksheet.get_all_values()
        if len(all_rows) > 1:
            worksheet.delete_rows(2, len(all_rows))

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
        existing_headers = worksheet.row_values(1)

        if not existing_headers:
            worksheet.append_row(custom_columns)

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
            worksheet.append_rows(all_rows, value_input_option='RAW', insert_data_option='INSERT_ROWS')

        return redirect(url_for('index'))

    except Exception as e:
        return f"An error occurred: {e}", 500

if __name__ == '__main__':
    app.run(debug=True)
