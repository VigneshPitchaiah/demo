$(document).ready(function () {
    // Handle Network Selection (unchanged)
    $('#network').change(function () {
        const network = $(this).val();
        if (network) {
            $.get(`/students/${network}`)
                .done(function (data) {
                    let studentHTML = '<table class="table-wrapper table-responsive" id="attendance-table">';  // Ensure proper ID
                    studentHTML += '<tr><th>ID</th><th>Student</th><th>Will Join on 03</th><th>Cannot Join on 03</th><th>No Response</th><th>Comment</th></tr>';
                    data.forEach(student => {
                        studentHTML += ` 
                            <tr>
                                <td>${student.id}</td>
                                <td>${student.name}</td>
                                <td><input type="radio" name="status_${student.id}" value="Will Join on 03" aria-label="Will join on 03"></td>
                                <td><input type="radio" name="status_${student.id}" value="Cannot Join on 03" aria-label="Cannot join on 03"></td>
                                <td><input type="radio" name="status_${student.id}" value="No Response" aria-label="No response"></td>
                                <td><input type="text" name="comment_${student.id}" class="form-control" placeholder="Add a comment" aria-label="Comment for ${student.name}"></td>
                            </tr>`;
                    });
                    studentHTML += '</table>';
                    $('#student-list').html(studentHTML);

                    // Re-enable the search functionality after the data is loaded
                    enableSearch();  // Calling the search setup function
                })
                .fail(function () {
                    $('#student-list').html('<p class="text-danger">Failed to load students. Please try again later.</p>');
                });
        } else {
            $('#student-list').html('');
        }
    });

    // Function to Enable the Search on the Table
    function enableSearch() {
        let debounceTimeout;
        $('#search-bar').on('input', function () {
            clearTimeout(debounceTimeout);
            debounceTimeout = setTimeout(() => {
                const searchTerm = $(this).val().toLowerCase();
                $('#student-list table tbody tr').each(function () {  // Ensure the search is targeting the correct table
                    const studentName = $(this).find('td:nth-child(2)').text().toLowerCase();
                    const status = $(this).find('td:nth-child(3)').text().toLowerCase();
                    const comment = $(this).find('td:nth-child(4)').text().toLowerCase();
                    const id = $(this).find('td:nth-child(1)').text().toLowerCase();

                    if (studentName.includes(searchTerm) || status.includes(searchTerm) || comment.includes(searchTerm) || id.includes(searchTerm)) {
                        $(this).show();
                    } else {
                        $(this).hide();
                    }
                });
            }, 300); // Debounce timeout of 300ms
        });
    }

    // Sidebar toggle functionality
    $('#sidebar-toggle').click(function () {
        const sidebar = $('#sidebar');
        const pageContentWrapper = $('#page-content-wrapper');

        // Toggle active class for both sidebar and page content wrapper
        sidebar.toggleClass('active');
        pageContentWrapper.toggleClass('active');
    });
});
