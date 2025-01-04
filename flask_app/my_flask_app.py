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


@app.route('/api/network_attendance', methods=['GET'])
def network_attendance():
    try:
        # SQL query to pass to the stored procedure
        sql_query = """
        WITH AttendanceWithNetworker AS (
            SELECT
                a.networker,
                b.status,
                CASE 
                    WHEN b.status = '' OR b.status IS NULL THEN 'Unknown'
                    ELSE b.status
                END AS valid_status
            FROM
                students a
            LEFT JOIN
                attendance b
            ON
                a.id = b.student_id
        ),
        AggregatedAttendance AS (
            SELECT
                networker,
                valid_status AS status,
                COUNT(*) AS status_count,
                SUM(COUNT(*)) OVER (PARTITION BY networker) AS total
            FROM
                AttendanceWithNetworker
            GROUP BY
                networker, valid_status
        ),
        AttendancePercentages AS (
            SELECT
                networker,
                MAX(CASE WHEN status = 'present' THEN (status_count * 100.0 / total)::double precision ELSE 0::double precision END) AS present_percent,
                MAX(CASE WHEN status = 'Absent/Not Interested' THEN (status_count * 100.0 / total)::double precision ELSE 0::double precision END) AS absent_percent,
                MAX(CASE WHEN status = 'Will take Recording' THEN (status_count * 100.0 / total)::double precision ELSE 0::double precision END) AS late_percent,
                MAX(CASE WHEN status = 'Unknown' THEN (status_count * 100.0 / total)::double precision ELSE 0::double precision END) AS unknown_percent
            FROM
                AggregatedAttendance
            GROUP BY
                networker
        )
        
        SELECT
            networker,
            present_percent,
            absent_percent,
            late_percent,
            unknown_percent
        FROM
            AttendancePercentages;
        """

        # Call the stored procedure using Supabase RPC
        response = supabase.rpc('new_execute_sql', {'query': sql_query}).execute()

        if response.data:
            # Process and return the response
            network_summary = [
                {
                    'networker': row['networker'],
                    'present_percent': row['present_percent'],
                    'absent_percent': row['absent_percent'],
                    'late_percent': row['late_percent'],
                    'unknown_percent': row['unknown_percent']
                }
                for row in response.data
            ]
            return jsonify(network_summary)
        else:
            return jsonify([]), 404

    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/attendance_details')
def attendance_details():
    try:
        # Define the SQL query for attendance summary per student and lesson
        query = """
        SELECT 
            s.networker AS networker_name,
            s.reg_number AS reg_number, 
            s.name AS student_name,
            MAX(CASE WHEN a.lesson_id = '2fa47ba0-74a3-4308-8b13-c5c5dd6e6e72' THEN a.status END) AS "BB1",
            MAX(CASE WHEN a.lesson_id = 'e765cfae-0c2b-4619-8a0d-0e81e034afdd' THEN a.status END) AS "Review 1",
            MAX(CASE WHEN a.lesson_id = '5c41211b-dbdd-428b-97f6-3fb08a914e5e' THEN a.status END) AS "BB2",
            MAX(CASE WHEN a.lesson_id = '8c97ccf2-8625-4a13-9292-0ca42dab7d51' THEN a.status END) AS "BB3",
            MAX(CASE WHEN a.lesson_id = '2cb665fd-05e6-4e37-9a94-93b51c21aa52' THEN a.status END) AS "Review 2-3",
            MAX(CASE WHEN a.lesson_id = '3a9305d6-aa60-4a6e-b774-672792c62967' THEN a.status END) AS "BB4",
            MAX(CASE WHEN a.lesson_id = '45801f05-fd36-432e-bdb0-0373147b5e76' THEN a.status END) AS "BB5",
            MAX(CASE WHEN a.lesson_id = 'cc606305-0767-4efe-b1bc-02beee4666ee' THEN a.status END) AS "Review 4-5",
            MAX(CASE WHEN a.lesson_id = '2cae1fcf-107b-4ed9-90bd-76e5f73cf875' THEN a.status END) AS "BB6"
        FROM 
            public.students s
        LEFT JOIN 
            public.attendance a ON s.id = a.student_id
        LEFT JOIN 
            public.lessons l ON a.lesson_id = l.id
        GROUP BY 
            s.name, s.networker, s.reg_number
        ORDER BY 
            s.name;
        """
        
        # Execute the query using the corrected stored procedure
        response = supabase.rpc('execute_raw_sql', {'query': query}).execute()
        
        if response.data:
            return render_template('attendance_details.html', records=response.data)
        else:
            return "No data found", 404

    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
