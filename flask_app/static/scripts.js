document.addEventListener("DOMContentLoaded", function () {
    fetchLessons();
    fetchNetworkers();
    fetchAttendanceSummary();
    fetchNetworkAttendanceSummary();

    // Event listener for submitting attendance
    document.getElementById('submit-button').addEventListener('click', submitAttendance);
});

function fetchLessons() {
    fetch('/api/lessons')
        .then(response => response.json())
        .then(lessons => {
            const lessonSelect = document.getElementById('lesson');
            lessons.forEach(lesson => {
                const option = document.createElement('option');
                option.value = lesson.id;
                option.textContent = lesson.title;
                lessonSelect.appendChild(option);
            });

            lessonSelect.addEventListener('change', updateStudentTable);
        })
        .catch(err => console.error('Error fetching lessons:', err));
}

function fetchNetworkers() {
    fetch('/api/networkers')
        .then(response => response.json())
        .then(networkers => {
            const networkerSelect = document.getElementById('networker');
            networkers.forEach(networker => {
                const option = document.createElement('option');
                option.value = networker;
                option.textContent = networker;
                networkerSelect.appendChild(option);
            });

            networkerSelect.addEventListener('change', updateStudentTable);
        })
        .catch(err => console.error('Error fetching networkers:', err));
}

function updateStudentTable() {
    const lessonId = document.getElementById('lesson').value;
    const networker = document.getElementById('networker').value;

    if (lessonId && networker) {
        fetchStudentsForNetworker(networker, lessonId);
    } else {
        document.getElementById('attendance-table').querySelector('tbody').innerHTML = '';
    }
}

function fetchStudentsForNetworker(networker, lessonId) {
    fetch(`/api/students?networker=${networker}&lesson_id=${lessonId}`)
        .then(response => response.json())
        .then(students => {
            const tableBody = document.getElementById('attendance-table').querySelector('tbody');
            tableBody.innerHTML = ''; // Clear existing rows

            students.forEach(student => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${student.reg_number}</td>
                    <td>${student.name}</td>
                    <td>
                        <select data-student-id="${student.id}">
                            <option value="present">Present</option>
                            <option value="absent">Absent</option>
                            <option value="late">Late</option>
                        </select>
                    </td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(err => console.error('Error fetching students:', err));
}


function submitAttendance() {
    const lessonId = document.getElementById('lesson').value;
    const networker = document.getElementById('networker').value;

    if (!lessonId || !networker) {
        alert('Please select a lesson and a networker.');
        return;
    }

    const attendanceData = [];
    const selects = document.querySelectorAll('#attendance-table select');
    selects.forEach(select => {
        const studentId = select.dataset.studentId;
        const status = select.value;
        attendanceData.push({
            student_id: studentId,
            lesson_id: lessonId,
            status: status
        });
    });

    fetch('/api/attendance', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(attendanceData)
    })
        .then(response => response.json())
        .then(() => {
            alert('Attendance marked successfully!');
        })
        .catch(err => console.error('Error submitting attendance:', err));
}

function fetchAttendanceSummary() {
    fetch('/api/attendance_summary')
        .then(response => response.json())
        .then(data => {
            const lessonTableBody = document.getElementById('lesson-attendance-summary').querySelector('tbody');
            lessonTableBody.innerHTML = '';

            if (data && Array.isArray(data) && data.length > 0) {
                data.forEach(item => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                            <td>${item.lesson_title}</td>
                            <td>${item.present_count}</td>
                            <td>${item.absent_count}</td>
                            <td>${item.late_count}</td>
                        `;
                    lessonTableBody.appendChild(row);
                });
            } else {
                const row = document.createElement('tr');
                row.innerHTML = `<td colspan="4">No data available</td>`;
                lessonTableBody.appendChild(row);
            }
        })
        .catch(err => console.error('Error fetching attendance summary:', err));
}

function fetchNetworkAttendanceSummary() {
    fetch('/api/network_attendance')
        .then(response => response.json())
        .then(data => {
            const networkTableBody = document.getElementById('network-attendance-summary').querySelector('tbody');
            networkTableBody.innerHTML = '';

            if (data && Array.isArray(data) && data.length > 0) {
                data.forEach(item => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                            <td>${item.networker}</td>
                            <td>${item.present_percent.toFixed(2)}%</td>
                            <td>${item.absent_percent.toFixed(2)}%</td>
                            <td>${item.late_percent.toFixed(2)}%</td>
                        `;
                    networkTableBody.appendChild(row);
                });
            } else {
                const row = document.createElement('tr');
                row.innerHTML = `<td colspan="4">No data available</td>`;
                networkTableBody.appendChild(row);
            }
        })
        .catch(err => console.error('Error fetching network attendance summary:', err));
}
