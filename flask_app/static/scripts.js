document.addEventListener("DOMContentLoaded", function () {
    fetchLessons();
    fetchNetworkers();
    fetchAttendanceSummary();
    fetchNetworkAttendanceSummary();
    fetchAttendanceReport();


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
                        <select data-student-id="${student.id}" class="status-select">
                            <option value="" selected disabled>Select Status</option>
                            <option value="present">Present</option>
                            <option value="Absent/Not Interested">Absent/Not Interested</option>
                            <option value="Will take Recording">Will take Recording</option>
                        </select>
                    </td>
                    <td>
                        <textarea data-student-id="${student.id}" placeholder="Enter comment"></textarea> <!-- Comment box -->
                    </td>
                `;
                tableBody.appendChild(row);
            });

            // Add event listeners to allow corrections
            const selectElements = tableBody.querySelectorAll('.status-select');
            selectElements.forEach(select => {
                select.addEventListener('change', function () {
                    // Allow the user to change the selection
                    console.log(`Student ID: ${this.dataset.studentId}, New Value: ${this.value}`);
                });

                select.addEventListener('mousedown', function (event) {
                    if (this.value) {
                        // Reset value on click for easier corrections
                        event.preventDefault(); // Prevent dropdown from opening immediately
                        this.value = ''; // Reset selection
                    }
                });
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
    let isAtLeastOneStatusSelected = false; // Flag to check if any status is selected

    const rows = document.querySelectorAll('#attendance-table tbody tr');
    rows.forEach((row, index) => {
        const select = row.querySelector('select');
        const textarea = row.querySelector('textarea');

        if (select && textarea) {
            const status = select.value;

            if (status) {
                isAtLeastOneStatusSelected = true; // Set the flag to true if a status is selected
            }

            attendanceData.push({
                student_id: select.dataset.studentId,
                lesson_id: lessonId,
                status: status,
                comment: textarea.value || '',
            });
        } else {
            console.error(`Row ${index} is missing select or textarea elements.`);
        }
    });

    if (!isAtLeastOneStatusSelected) {
        alert('Please select a status for at least one student.');
        return;
    }

    fetch('/api/attendance', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(attendanceData),
    })
        .then(response => response.json())
        .then(response => {
            if (response.error) {
                alert(`Error: ${response.error}`);
            } else {
                alert('Attendance marked successfully!');
                window.location.reload();  // Refresh the page after submission
            }
        })
        .catch(err => console.error('Error submitting attendance:', err));
}


// Function to fetch and display attendance summary for a specific lesson
function fetchAttendanceSummary(lessonId) {
    fetch(`/api/attendance_summary_report?lesson_id=${lessonId}`)
        .then(response => response.json())
        .then(data => {
            const lessonTableBody = document.getElementById('lesson-attendance-summary').querySelector('tbody');
            lessonTableBody.innerHTML = '';  // Clear any previous data

            if (data && Array.isArray(data) && data.length > 0) {
                // Loop through the data and add rows to the table
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
                // If no data, display a message in the table
                const row = document.createElement('tr');
                row.innerHTML = `<td colspan="4">No data available</td>`;
                lessonTableBody.appendChild(row);
            }
        })
        .catch(err => console.error('Error fetching attendance summary:', err));
}


// Function to fetch and display networker attendance summary for a specific networker
function fetchNetworkAttendanceSummary(networker) {
    fetch(`/api/network_attendance?networker=${networker}`)
        .then(response => response.json())
        .then(data => {
            const networkTableBody = document.getElementById('network-attendance-summary').querySelector('tbody');
            networkTableBody.innerHTML = '';  // Clear any previous data

            if (data && Array.isArray(data) && data.length > 0) {
                // Loop through the data and add rows to the table
                data.forEach(item => {
                    const row = document.createElement('tr');

                    row.innerHTML = `
                        <td>${item.networker}</td>
                        <td>${item.present_percent.toFixed(2)}%</td>
                        <td>${item.absent_percent.toFixed(2)}%</td>
                        <td>${item.late_percent.toFixed(2)}%</td>
                        <td>${item.unknown_percent.toFixed(2)}%</td>
                    `;
                    networkTableBody.appendChild(row);
                });
            } else {
                // If no data, display a message in the table
                const row = document.createElement('tr');
                row.innerHTML = `<td colspan="5">No data available</td>`;
                networkTableBody.appendChild(row);
            }
        })
        .catch(err => console.error('Error fetching network attendance summary:', err));
}
