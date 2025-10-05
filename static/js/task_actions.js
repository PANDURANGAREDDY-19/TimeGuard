// Task Actions JavaScript

// Global stopwatch state
let stopwatches = {};

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
            const timerElement = document.getElementById(`timer-${taskId}`);
            if (timerElement) {
                timerElement.textContent = formatTime(elapsed);
                // Update browser tab title
                document.title = `⏳ ${formatTime(elapsed)} | TimeGuard`;
            }
        }, 1000);
        
        // Update UI
        document.getElementById(`start-btn-${taskId}`).style.display = 'none';
        document.getElementById(`stop-btn-${taskId}`).style.display = '';
        document.getElementById(`timer-${taskId}`).classList.add('active');
        document.getElementById(`timer-${taskId}`).classList.remove('paused');
    }
}

function stopStopwatch(taskId) {
    const sw = stopwatches[taskId];
    if (sw && sw.start) {
        sw.elapsed += Date.now() - sw.start;
        clearInterval(sw.interval);
        sw.start = null;
        
        // Update UI
        const timerElement = document.getElementById(`timer-${taskId}`);
        if (timerElement) {
            timerElement.textContent = formatTime(sw.elapsed);
            timerElement.classList.remove('active');
            timerElement.classList.add('paused');
        }
        document.getElementById(`start-btn-${taskId}`).style.display = '';
        document.getElementById(`stop-btn-${taskId}`).style.display = 'none';
        
        // Reset browser tab title
        document.title = 'TimeGuard';

        // Ask to complete task
        if (confirm('Save this time as actual time for the task?')) {
            completeTask(taskId, sw.elapsed);
        }
    }
}

function deleteTask(taskId) {
    if (confirm('Are you sure you want to delete this task?')) {
        fetch(`/api/tasks/${taskId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                // Remove task element from DOM
                const taskElement = document.getElementById(`task-${taskId}`);
                if (taskElement) {
                    taskElement.remove();
                }
                // Show success message
                showNotification('Task deleted successfully', 'success');
            } else {
                showNotification('Error deleting task', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error deleting task', 'error');
        });
    }
}

function completeTask(taskId, elapsed) {
    const hours = (elapsed / 3600000).toFixed(2); // Convert ms to hours
    fetch(`/api/tasks/${taskId}/complete`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ actual_time: parseFloat(hours) })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            showNotification('Task completed successfully', 'success');
            // Reload page to update task list
            location.reload();
        } else {
            showNotification('Error completing task', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error completing task', 'error');
    });
}

function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.body.appendChild(alertDiv);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}