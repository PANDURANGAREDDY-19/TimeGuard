// Stopwatch logic per task
const stopwatches = {};

function formatTime(ms) {
    const totalSeconds = Math.floor(ms / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

function startStopwatch(taskId) {
    if (!stopwatches[taskId]) {
        stopwatches[taskId] = { start: null, elapsed: 0, interval: null };
    }
    const sw = stopwatches[taskId];
    if (!sw.start) {
        sw.start = Date.now();
        sw.interval = setInterval(() => {
            const elapsed = sw.elapsed + (Date.now() - sw.start);
            document.getElementById(`timer-${taskId}`).textContent = formatTime(elapsed);
        }, 1000);
        document.getElementById(`start-btn-${taskId}`).style.display = 'none';
        document.getElementById(`stop-btn-${taskId}`).style.display = '';
    }
}

function stopStopwatch(taskId) {
    const sw = stopwatches[taskId];
    if (sw && sw.start) {
        sw.elapsed += Date.now() - sw.start;
        clearInterval(sw.interval);
        sw.start = null;
        document.getElementById(`timer-${taskId}`).textContent = formatTime(sw.elapsed);
        document.getElementById(`start-btn-${taskId}`).style.display = '';
        document.getElementById(`stop-btn-${taskId}`).style.display = 'none';
        // Prompt to save as actual_time
        if (confirm('Save this time as actual time for the task?')) {
            const hours = (sw.elapsed / 3600000).toFixed(2);
            fetch(`/api/tasks/${taskId}/complete`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ actual_time: parseFloat(hours) })
            })
            .then(response => response.json())
            .then(data => {
                if (data.message) {
                    alert('Task completed and time saved!');
                    location.reload();
                } else {
                    alert('Error completing task');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error completing task');
            });
        }
    }
}
// Task Management Functions
function createTask() {
    const form = document.getElementById('taskForm');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    
    fetch('/api/tasks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            location.reload();
        } else {
            let errorMsg = 'Error creating task';
            if (data.error) {
                errorMsg += ': ' + data.error;
                if (data.details) {
                    errorMsg += ' (' + data.details + ')';
                }
            }
            alert(errorMsg);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error creating task: ' + error);
    });
}

function deleteTask(taskId) {
    if (confirm('Are you sure you want to delete this task?')) {
        fetch(`/api/tasks/${taskId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                document.querySelector(`tr[data-task-id="${taskId}"]`).remove();
            } else {
                alert('Error deleting task');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error deleting task');
        });
    }
}

function completeTask(taskId) {
    const actualTime = prompt('Enter actual time spent (in hours):');
    if (actualTime && !isNaN(actualTime)) {
        fetch(`/api/tasks/${taskId}/complete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ actual_time: parseFloat(actualTime) })
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                if (data.deviation_detected) {
                    const deviationType = data.deviation_percent > 0 ? 'longer' : 'shorter';
                    const percentage = Math.abs(data.deviation_percent * 100).toFixed(1);
                    alert(`Task completed! Note: This task took ${percentage}% ${deviationType} than estimated.`);
                } else {
                    alert('Task completed successfully!');
                }
                location.reload();
            } else {
                alert('Error completing task');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error completing task');
        });
    }
}

// Theme Management
function toggleTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
}

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
    }
});

// Auto-refresh for real-time updates
setInterval(function() {
    if (window.location.pathname.includes('/dashboard/')) {
        // Refresh page data every 30 seconds
        const currentPath = window.location.pathname;
        if (currentPath.includes('/admin') || currentPath.includes('/user')) {
            // Could implement AJAX refresh here for better UX
        }
    }
}, 30000);