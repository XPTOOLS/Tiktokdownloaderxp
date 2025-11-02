let visitsChart;

// Check authentication on page load
document.addEventListener('DOMContentLoaded', function() {
    checkAuthentication();
});

async function checkAuthentication() {
    const token = localStorage.getItem('admin_token');
    
    if (!token) {
        window.location.href = '/login';
        return;
    }

    try {
        const response = await fetch('/api/admin/verify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ token: token })
        });

        if (!response.ok) {
            throw new Error('Invalid token');
        }

        // User is authenticated, load admin panel
        initializeAdminPanel();
    } catch (error) {
        console.error('Authentication failed:', error);
        localStorage.removeItem('admin_token');
        window.location.href = '/login';
    }
}

function initializeAdminPanel() {
    // Add logout event listener
    document.getElementById('logoutBtn').addEventListener('click', logout);
    
    loadStats();
    loadRecentActivity();
    setupCharts();
    
    // Refresh data every 30 seconds
    setInterval(loadStats, 30000);
    setInterval(loadRecentActivity, 30000);
}

function logout() {
    localStorage.removeItem('admin_token');
    window.location.href = '/login';
}

async function loadStats() {
    try {
        const response = await fetch('/api/admin/stats');
        const stats = await response.json();
        
        document.getElementById('totalVisits').textContent = stats.totalVisits.toLocaleString();
        document.getElementById('totalDownloads').textContent = stats.totalDownloads.toLocaleString();
        document.getElementById('todayVisits').textContent = stats.todayVisits.toLocaleString();
        document.getElementById('successfulDownloads').textContent = stats.successfulDownloads.toLocaleString();
        
        updateChart(stats.visitsData);
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadRecentActivity() {
    try {
        const response = await fetch('/api/admin/activity');
        const activity = await response.json();
        
        const activityList = document.getElementById('activityList');
        
        if (activity.length === 0) {
            activityList.innerHTML = '<div class="empty-state">No recent activity found</div>';
            return;
        }
        
        activityList.innerHTML = '';
        
        activity.forEach(item => {
            const activityItem = document.createElement('div');
            activityItem.className = 'activity-item';
            activityItem.innerHTML = `
                <div class="activity-content">
                    <div class="activity-action">${item.action}</div>
                    <div class="activity-details">${item.details || 'No additional details'}</div>
                </div>
                <div class="activity-time">${new Date(item.timestamp).toLocaleString()}</div>
            `;
            activityList.appendChild(activityItem);
        });
    } catch (error) {
        console.error('Error loading activity:', error);
        const activityList = document.getElementById('activityList');
        activityList.innerHTML = '<div class="empty-state">Error loading activities</div>';
    }
}

function setupCharts() {
    const ctx = document.getElementById('visitsChart').getContext('2d');
    visitsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Website Visits',
                data: [],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: false
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                }
            }
        }
    });
}

function updateChart(visitsData) {
    if (visitsData && visitsChart) {
        visitsChart.data.labels = visitsData.labels || [];
        visitsChart.data.datasets[0].data = visitsData.data || [];
        visitsChart.update();
    }
}

async function sendNotification() {
    const message = document.getElementById('notificationMessage').value.trim();
    const actionText = document.getElementById('actionText').value.trim();
    const actionUrl = document.getElementById('actionUrl').value.trim();

    if (!message) {
        alert('Please enter a notification message');
        return;
    }

    try {
        const response = await fetch('/api/admin/notification', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message,
                actionText: actionText || null,
                actionUrl: actionUrl || null,
                timestamp: new Date().toISOString()
            })
        });

        if (response.ok) {
            alert('Notification sent successfully!');
            clearForm();
            
            // Track this activity
            await fetch('/api/admin/track-activity', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: 'Notification Sent',
                    details: `Message: ${message.substring(0, 50)}...`,
                    timestamp: new Date().toISOString()
                })
            });
            
            // Reload activities to show the new one
            loadRecentActivity();
            
        } else {
            throw new Error('Failed to send notification');
        }
    } catch (error) {
        console.error('Error sending notification:', error);
        alert('Error sending notification. Please try again.');
    }
}

function clearForm() {
    document.getElementById('notificationMessage').value = '';
    document.getElementById('actionText').value = '';
    document.getElementById('actionUrl').value = '';
}