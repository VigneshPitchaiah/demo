import os
import json
from flask import Flask, render_template, request, redirect, url_for, jsonify
from supabase import create_client, Client
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Load environment variables
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
google_credentials = json.loads(os.getenv("GOOGLE_SHEETS_CREDENTIALS"))
google_sheet_id = os.getenv("GOOGLE_SHEET_ID")

# Supabase Connection
supabase: Client = create_client(supabase_url, supabase_key)


print(f'*************************google_credentials***************\n {google_credentials}')
print(google_credentials["private_key"])

# Google Sheets Authentication
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = None  # Initialize creds to ensure it's in scope

try:
    creds = ServiceAccountCredentials.from_json_keyfile_dict(google_credentials, scopes=scope)
    print("Credentials loaded successfully.")
except Exception as e:
    print("Failed to load credentials:", e)

if creds:
    try:
        client = gspread.authorize(creds)
        print("Client authorized successfully.")
    except Exception as e:
        print("Failed to authorize client:", e)
else:
    print("Cannot proceed without valid credentials.")

# Open the Google Sheet using its ID (You already provided the ID)
sheet = client.open_by_key(google_sheet_id).sheet1

@app.route('/attendance')
def view_attendance():
    attendance_data = supabase.table('attendance_copy').select('id, student_name, networker_name, status, comment, timestamp').execute().data
    return render_template('attendance.html', attendances=attendance_data)


@app.route('/')
def index():
    response = supabase.table('attendance_copy').select('networker_name').execute()
    networks = sorted(set(row['networker_name'] for row in response.data))
    return render_template('index.html', networks=networks)


@app.route('/students/<network>')
def get_students(network):
    # Fetch students by network
    response = supabase.table('attendance_copy').select('*').eq('networker_name', network).execute()
    students = [{'id': row['id'], 'name': row['student_name']} for row in response.data]
    return jsonify(students)

@app.route('/submit', methods=['POST'])
def submit_attendance():
    data = request.form
    try:
        # Open or create the "results" worksheet
        try:
            worksheet = client.open_by_key('1JfH9Nft6QM56ErL42h8gJmyjEbuVgXJxTw2-4tFLJq4').worksheet("results")
            print("Worksheet 'results' found.")
        except gspread.exceptions.WorksheetNotFound:
            print("Worksheet 'results' not found. Creating a new one...")
            worksheet = client.open_by_key('1JfH9Nft6QM56ErL42h8gJmyjEbuVgXJxTw2-4tFLJq4').add_worksheet(title="results", rows=100, cols=6)

        # Get the total number of rows and clear rows below the header (row 1)
        all_rows = worksheet.get_all_values()
        if len(all_rows) > 1:  # If there are data rows below the header
            worksheet.delete_rows(2, len(all_rows))  # Deletes rows starting from row 2 onwards

        # Get all column names dynamically from the database
        columns_response = supabase.table('attendance_copy').select('*').limit(1).execute().data
        if not columns_response:
            raise Exception("Failed to fetch columns")
        custom_headers = {
            'id': 'Roll Number',
            'student_name': 'Student Name',
            'networker_name': 'Networker',
            'status': 'Status',
            'comment': 'Comment',
            # Add any other columns you have, mapping to custom names
        }

        # Extract column names from the first row
        # Exclude 'timestamp' from the columns if it's not needed
        columns = list(columns_response[0].keys())
        columns = [column for column in columns if column != 'timestamp']

        # Create custom columns based on your custom_headers mapping
        custom_columns = [custom_headers.get(col, col) for col in columns]

        # Check if the first row already contains headers
        existing_headers = worksheet.row_values(1)

        # Only append header row if it's not already present
        if not existing_headers:
            worksheet.append_row(custom_columns)  # Add header row
            print(f"Worksheet headers added.")
        else:
            print(f"Headers already exist.")

        # Process attendance submissions and update DB first
        for key, value in data.items():
            if key.startswith('status_'):
                student_id = key.split('_')[1]
                status = value  # The selected status: 'Present', 'Absent', or 'Late'

                # Get the associated comment (if any)
                comment_key = f"comment_{student_id}"
                comment = data.get(comment_key, "")  # Default to empty if no comment is provided

                # Update the database with both status and comment, exclude 'timestamp' from the update
                update_response = supabase.table('attendance_copy').update({
                    'status': status,
                    'comment': comment
                }).eq('id', student_id).execute()

                print(f"Update Response for Student {student_id}: {update_response}")

        # Fetch all rows from the database after all updates
        fetch_response = supabase.table('attendance_copy').select('id, student_name, networker_name, status, comment').execute()
        if not fetch_response.data:
            print(f"No data found in the attendance table.")
            return "No data found", 500

        # Prepare the rows for Google Sheets by extracting all column values
        all_rows = []
        for row in fetch_response.data:
            # Format the timestamp field if necessary
            formatted_row = [row[column] if column != 'timestamp' else row[column].split('T')[0] for column in columns]  # Format as 'YYYY-MM-DD'
            all_rows.append(formatted_row)

        # Write all rows to Google Sheets starting from row 2 (leaving row 1 as header)
        if all_rows:
            worksheet.append_rows(all_rows, value_input_option='RAW', insert_data_option='INSERT_ROWS')
            print(f"Written {len(all_rows)} rows to Google Sheets.")

        return redirect(url_for('index'))

    except Exception as e:
        print(f"An error occurred during submission: {e}")
        return f"An error occurred: {e}", 500


if __name__ == '__main__':
    app.run(debug=True)
