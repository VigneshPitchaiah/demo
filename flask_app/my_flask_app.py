from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client

app = Flask(__name__)

# Supabase Configuration
SUPABASE_URL = 'https://fcxdbxvuxvuoownippzm.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZjeGRieHZ1eHZ1b293bmlwcHptIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTAxMTQzNSwiZXhwIjoyMDUwNTg3NDM1fQ.HH3H1ZrB8tnyDSwsCO3Yj-YChJ9nYRKvnLxQ-Iw_xTA'

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
@app.route('/mark_attendance')
def mark_attendance():
    return render_template('mark_attendance.html')

@app.route('/attendance_summary')
def attendance_summary_page():
    return render_template('attendance_summary.html')

# API to fetch all lessons
@app.route('/api/lessons', methods=['GET'])
def get_lessons():
    response = supabase.table('lessons').select('*').execute()
    lessons = response.data
    return jsonify(lessons)

# API to fetch all networkers
@app.route('/api/networkers', methods=['GET'])
def get_networkers():
    response = supabase.table('students').select('networker').execute()
    networkers = set([student['networker'] for student in response.data if student['networker']])
    ordered_networkers = sorted(networkers)  # Sort the network names alphabetically
    return jsonify(ordered_networkers)

# API to fetch students for a selected networker
@app.route('/api/students', methods=['GET'])
def get_students_for_networker():
    networker = request.args.get('networker')

    if not networker:
        return jsonify({"error": "networker is required"}), 400
    
    # Fetch students under the selected networker
    response = supabase.table('students').select('*').filter('networker', 'eq', networker).execute()
    return jsonify(response.data)

@app.route('/api/attendance', methods=['POST'])
def submit_attendance():
    try:
        attendance_data = request.json

        # Validate data format
        if not isinstance(attendance_data, list):
            return jsonify({'error': 'Invalid attendance data format, expected an array.'}), 400
        
        for record in attendance_data:
            student_id = record['student_id']
            lesson_id = record['lesson_id']
            status = record['status']
            comment = record.get('comment', '')

            # Check if student and lesson exist
            student_response = supabase.table('students').select('id').eq('id', student_id).execute()
            lesson_response = supabase.table('lessons').select('id').eq('id', lesson_id).execute()

            if not student_response.data:
                return jsonify({'error': f"Student with id {student_id} does not exist."}), 400
            if not lesson_response.data:
                return jsonify({'error': f"Lesson with id {lesson_id} does not exist."}), 400

            # Insert attendance
            response = supabase.table('attendance').insert({
                'student_id': student_id,
                'lesson_id': lesson_id,
                'status': status,
                'comment': comment
            }).execute()
            # Check if the insertion was successful
            if response.data:  # Check if data exists in the response
                print(f"Attendance successfully marked for student {student_id} in lesson {lesson_id}")
            elif response.error:  # Check if an error is present
                raise Exception(f"Error inserting attendance: {response.error}")
            else:
                raise Exception("Unknown error occurred while inserting attendance.")

        return jsonify({'message': 'Attendance marked successfully!'}), 200

    except Exception as e:
        # Log the error and return the error message
        print(f"Error occurred: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
# API to get attendance statistics
@app.route('/api/attendance/stats', methods=['GET'])
def get_attendance_stats():
    lesson_id = request.args.get('lesson_id')
    
    if not lesson_id:
        return jsonify({"error": "lesson_id is required"}), 400

    # Get counts of present, absent, and late students
    present_count = supabase.table('attendance').select('*').eq('lesson_id', lesson_id).eq('status', 'present').execute().count
    absent_count = supabase.table('attendance').select('*').eq('lesson_id', lesson_id).eq('status', 'absent').execute().count
    late_count = supabase.table('attendance').select('*').eq('lesson_id', lesson_id).eq('status', 'late').execute().count

    stats = {
        "present": present_count,
        "absent": absent_count,
        "late": late_count
    }

    return jsonify(stats)

# API to get attendance summary per lesson
@app.route('/api/attendance_summary_report', methods=['GET'])
def attendance_summary():
    try:
        # Fetch all attendance records
        response = supabase.table('attendance').select('lesson_id, status').execute()

        if response.data:
            # Initialize a dictionary to store aggregated data
            lesson_data = {}

            for item in response.data:
                lesson_id = item['lesson_id']
                status = item['status']

                # Initialize the lesson entry if it doesn't exist
                if lesson_id not in lesson_data:
                    lesson_data[lesson_id] = {'present': 0, 'absent': 0, 'late': 0}

                # Increment the appropriate status count
                if status == 'present':
                    lesson_data[lesson_id]['present'] += 1
                elif status == 'absent':
                    lesson_data[lesson_id]['absent'] += 1
                elif status == 'late':
                    lesson_data[lesson_id]['late'] += 1

            # Fetch lesson titles and merge with the attendance data
            lesson_summary = []
            for lesson_id, counts in lesson_data.items():
                # Get the lesson title from the 'lessons' table
                lesson_response = supabase.table('lessons').select('title').eq('id', lesson_id).execute()
                lesson_title = lesson_response.data[0]['title'] if lesson_response.data else "Unknown Lesson"
                
                lesson_summary.append({
                    'lesson_title': lesson_title,
                    'present_count': counts['present'],
                    'absent_count': counts['absent'],
                    'late_count': counts['late']
                })

            return jsonify(lesson_summary)

        else:
            return jsonify({'error': 'No data available'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# API to get network attendance summary
@app.route('/api/network_attendance', methods=['GET'])
def network_attendance():
    try:
        # Step 1: Fetch attendance data
        response = supabase.table('attendance').select('student_id, status').execute()
        print("Attendance Data:", response.data)

        if response.data:
            network_data = {}

            for item in response.data:
                student_id = item['student_id']
                status = item['status']

                # Step 2: Fetch student networker
                student_response = supabase.table('students').select('networker').eq('id', student_id).execute()
                print(f"Student ID: {student_id}, Response: {student_response.data}")

                networker = student_response.data[0]['networker'] if student_response.data else None

                if networker:
                    if networker not in network_data:
                        network_data[networker] = {'present': 0, 'absent': 0, 'late': 0, 'total': 0}

                    network_data[networker]['total'] += 1
                    network_data[networker][status] += 1

            # Step 3: Calculate percentages
            network_summary = []
            for networker, stats in network_data.items():
                present_percent = (stats['present'] / stats['total']) * 100 if stats['total'] > 0 else 0
                absent_percent = (stats['absent'] / stats['total']) * 100 if stats['total'] > 0 else 0
                late_percent = (stats['late'] / stats['total']) * 100 if stats['total'] > 0 else 0

                network_summary.append({
                    'networker': networker,
                    'present_percent': present_percent,
                    'absent_percent': absent_percent,
                    'late_percent': late_percent
                })

            print("Network Summary:", network_summary)
            return jsonify(network_summary)

        else:
            print("No attendance data available.")
            return jsonify([]), 404

    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': str(e)}), 500


# New route to display the detailed attendance records
@app.route('/attendance_details')
def attendance_details():
    try:
        # Define the SQL query for attendance summary per student and lesson
        query = """
        SELECT 
            s.networker AS networker_role,
            s.name AS student_name,
            l.title AS lesson_title,
            a.status AS attendance_status,
            CAST(COUNT(a.id) AS integer) AS count_status
        FROM 
            public.students s
        LEFT JOIN 
            public.attendance a ON s.id = a.student_id
        LEFT JOIN 
            public.lessons l ON a.lesson_id = l.id
        GROUP BY 
            s.networker, s.name, l.title, a.status
        ORDER BY 
            attendance_status;
        """
        
        # Execute the query using Supabase
        response = supabase.rpc('execute_raw_sql', {'query': query}).execute()

        if response.data:
            return render_template('attendance_details.html', records=response.data)
        else:
            return "No data found", 404

    except Exception as e:
        return f"Error: {str(e)}", 500


if __name__ == '__main__':
    app.run(debug=True)
