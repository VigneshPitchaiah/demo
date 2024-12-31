from flask import Flask, render_template, request, redirect, url_for, jsonify
from supabase import create_client, Client

app = Flask(__name__)

# Supabase Connection
url = "https://fcxdbxvuxvuoownippzm.supabase.co"  # Replace with your Supabase URL
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZjeGRieHZ1eHZ1b293bmlwcHptIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTAxMTQzNSwiZXhwIjoyMDUwNTg3NDM1fQ.HH3H1ZrB8tnyDSwsCO3Yj-YChJ9nYRKvnLxQ-Iw_xTA"
supabase: Client = create_client(url, key)

def get_all_attendance():
    # Fetch all attendance records from the database
    attendance_data = supabase.table("attendance").select("id,	student_name,	networker_name,status").execute().data
    return attendance_data

@app.route('/attendance')
def view_attendance():
    # Fetch all attendance records to display
    attendance_data = supabase.table('attendance').select('id,	student_name,	networker_name, status, comment').execute().data
    return render_template('attendance.html', attendances=attendance_data)


@app.route('/')
def index():
    # Fetch unique networks
    response = supabase.table('attendance').select('networker_name').execute()
    networks = sorted(set(row['networker_name'] for row in response.data))
    return render_template('index.html', networks=networks)


@app.route('/students/<network>')
def get_students(network):
    # Fetch students by network
    response = supabase.table('attendance').select('*').eq('networker_name', network).execute()
    students = [{'id': row['id'], 'name': row['student_name']} for row in response.data]
    return jsonify(students)

@app.route('/submit', methods=['POST'])
def submit_attendance():
    data = request.form
    for key, value in data.items():
        if key.startswith('status_'):
            student_id = key.split('_')[1]
            status = value  # The selected status: 'Present', 'Absent', or 'Late'

            # Get the associated comment (if any)
            comment_key = f"comment_{student_id}"
            comment = data.get(comment_key, "")  # Default to empty if no comment is provided

            print(f"Updating student_id={student_id} with status={status} and comment={comment}")
            
            # Update the database with both status and comment
            response = supabase.table('attendance').update({'status': status, 'comment': comment}).eq('id', student_id).execute()

            # Log the response for debugging
            print(f"Supabase Response: {response}")

            # Check if the response contains data
            if not response.data:  # If `data` is empty, assume an error occurred
                print(f"Error updating student {student_id}: {response}")
                return f"Error updating database for student {student_id}.", 500

    return redirect(url_for('index'))



if __name__ == '__main__':
    app.run(debug=True)
