
document.addEventListener('DOMContentLoaded', function () {
    if (typeof supervisorChartsData !== 'undefined') {
        initCharts(supervisorChartsData);
    }
});

function initCharts(data) {
    // 1. Activity Chart (Bar - GitHub style analogy)
    const timelineCtx = document.getElementById('timelineChart');
    if (timelineCtx) {
        new Chart(timelineCtx, {
            type: 'bar',
            data: {
                labels: data.timeline.map(d => d.date),
                datasets: [{
                    label: 'Actividades Completadas',
                    data: data.timeline.map(d => d.count),
                    backgroundColor: '#c5a47e',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true, ticks: { stepSize: 1 } },
                    x: { grid: { display: false } }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    // 2. Course Progress (Bar)
    const courseCtx = document.getElementById('courseChart');
    if (courseCtx) {
        new Chart(courseCtx, {
            type: 'bar',
            data: {
                labels: data.course_progress.map(d => d.course__name),
                datasets: [{
                    label: 'Progreso Promedio (%)',
                    data: data.course_progress.map(d => d.avg_progress),
                    backgroundColor: '#3b82f6'
                }]
            },
            options: {
                indexAxis: 'y',
                scales: {
                    x: { max: 100 }
                }
            }
        });
    }

    // 3. Student Progress (Bar)
    const studentCtx = document.getElementById('studentChart');
    if (studentCtx) {
        new Chart(studentCtx, {
            type: 'bar',
            data: {
                labels: data.student_progress.slice(0, 10).map(d => d.app_user__username),
                datasets: [{
                    label: 'Progreso Promedio (%)',
                    data: data.student_progress.slice(0, 10).map(d => d.avg_progress),
                    backgroundColor: '#10b981'
                }]
            },
            options: {
                scales: {
                    y: { max: 100 }
                }
            }
        });
    }
}

function openManageModal(userId, userName) {
    document.getElementById('manageModal').style.display = 'flex'
    document.getElementById('manageModalTitle').innerText = 'Gestionar a ' + userName
    document.getElementById('enrollCourseUserId').value = userId
    document.getElementById('enrollPathUserId').value = userId

    // Populate current enrollments
    var content = document.getElementById('data-user-' + userId).innerHTML
    document.getElementById('currentEnrollmentsContainer').innerHTML = content

    showCourseForm() // Default view
}

function closeManageModal() {
    document.getElementById('manageModal').style.display = 'none'
}

function showCourseForm() {
    document.getElementById('enrollCourseForm').style.display = 'block'
    document.getElementById('enrollPathForm').style.display = 'none'
}

function showPathForm() {
    document.getElementById('enrollCourseForm').style.display = 'none'
    document.getElementById('enrollPathForm').style.display = 'block'
}

// Close modal if clicked outside
window.onclick = function (event) {
    var modal = document.getElementById('manageModal')
    if (event.target == modal) {
        modal.style.display = 'none'
    }
}
