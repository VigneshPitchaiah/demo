$(document).ready(function () {
    // Handle Network Selection
    $('#network').change(function () {
        const network = $(this).val();
        if (network) {
            $.get(`/students/${network}`, function (data) {
                let studentHTML = '<table><tr><th>ID</th><th>Student</th><th>Will Join on 03</th><th>Cannot Join on 03</th><th>No Response</th><th>Comment</th></tr>';
                data.forEach(student => {
                    studentHTML += `
                        <tr>
                            <td>${student.id}</td> <!-- Display the ID -->
                            <td>${student.name}</td>
                            <td><input type="radio" name="status_${student.id}" value="Will Join on 03"></td>
                            <td><input type="radio" name="status_${student.id}" value="Cannot Join on 03"></td>
                            <td><input type="radio" name="status_${student.id}" value="No Response"></td>
                            <td><input type="text" name="comment_${student.id}" class="form-control" placeholder="Add a comment"></td>
                        </tr>`;
                });
                studentHTML += '</table>';
                $('#student-list').html(studentHTML);
            });
        } else {
            $('#student-list').html('');
        }
    });

    // Handle Search Bar functionality
    $('#search-bar').on('input', function () {
        var searchTerm = $(this).val().toLowerCase();
        $('#attendance-table tbody tr').each(function () {
            var studentName = $(this).find('td:nth-child(2)').text().toLowerCase();
            var status = $(this).find('td:nth-child(3)').text().toLowerCase();
            var comment = $(this).find('td:nth-child(4)').text().toLowerCase();
            var id = $(this).find('td:nth-child(1)').text().toLowerCase();
            var network = $(this).find('td:nth-child(5)').text().toLowerCase();

            if (studentName.includes(searchTerm) || status.includes(searchTerm) || comment.includes(searchTerm) || id.includes(searchTerm) || network.includes(searchTerm)) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    });
});
