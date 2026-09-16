let activeStudentsData = [];
let notAttendedData = [];
let topPerformersChartInstance = null;

async function fetchDashboardData() {
    try {
        const response = await fetch('/api/stats');
        if (!response.ok) throw new Error('Failed to fetch data');
        
        const data = await response.json();

        // 1. Render KPIs
        document.getElementById('total-students').innerText = data.summary.total_students;
        document.getElementById('active-students').innerText = data.summary.active_students;
        document.getElementById('not-attended-count').innerText = data.summary.not_attended_count;

        // 2. Render Top 10 Chart
        renderTopPerformersChart(data.top_10);

        activeStudentsData = data.active_students_list || [];
        notAttendedData = data.not_attended_list || [];

        renderTable('activeTableBody', activeStudentsData, true);
        renderTable('notAttendedTableBody', notAttendedData, false);

    } catch (error) {
        console.error('Error loading dashboard:', error);
        document.getElementById('activeTableBody').innerHTML = `<tr><td colspan="8" class="no-data error-text">Error loading data.</td></tr>`;
    }
}

function renderTopPerformersChart(top10) {
    const ctx = document.getElementById('topPerformersChart').getContext('2d');
    if (topPerformersChartInstance) topPerformersChartInstance.destroy();

    topPerformersChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: top10.map(s => s.NAME),
            datasets: [
                { label: 'Easy', data: top10.map(s => s.Easy), backgroundColor: '#00b8a3' },
                { label: 'Medium', data: top10.map(s => s['Med.']), backgroundColor: '#ffc01e' },
                { label: 'Hard', data: top10.map(s => s.Hard), backgroundColor: '#ff375f' }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { stacked: true, ticks: { color: '#94a3b8' }, grid: { display: false } },
                y: { stacked: true, ticks: { color: '#94a3b8' }, grid: { color: '#334155' } }
            },
            plugins: {
                legend: { position: 'bottom', labels: { color: '#f8fafc' } }
            }
        }
    });
}

function getRankBadge(rank) {
    if (rank === 1) return '🥇 1';
    if (rank === 2) return '🥈 2';
    if (rank === 3) return '🥉 3';
    return `${rank}`;
}

function getRankIndicator(change) {
    if (change > 0) {
        // Rank improved (Green arrow UP)
        return `<span style="color: #4ade80; font-weight: bold; margin-left: 6px;" title="Climbed up ${change} places">▲ ${change}</span>`;
    } else if (change < 0) {
        // Rank dropped (Red arrow DOWN)
        return `<span style="color: #f87171; font-weight: bold; margin-left: 6px;" title="Dropped ${Math.abs(change)} places">▼ ${Math.abs(change)}</span>`;
    } else {
        // Unchanged (White dash)
        return `<span style="color: #94a3b8; margin-left: 6px;">-</span>`;
    }
}

function renderTable(elementId, students, isRanked) {
    const tbody = document.getElementById(elementId);
    tbody.innerHTML = '';

    if (!students || students.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="no-data">No records found</td></tr>`;
        return;
    }

    students.forEach((s, index) => {
        const profileLink = (s['Leetcode Link'] && s['Leetcode Link'] !== '#') 
            ? `<a href="${s['Leetcode Link']}" target="_blank" rel="noopener noreferrer" class="profile-link">View Profile ↗</a>` 
            : '-';

        let rankDisplay = '';
        if (isRanked) {
            const badge = getRankBadge(s.rank);
            const indicator = getRankIndicator(s.rank_change || 0);
            rankDisplay = `${badge} ${indicator}`;
        } else {
            rankDisplay = index + 1; // Simple S.No for Not Attended list
        }

        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="rank-cell">${rankDisplay}</td>
            <td>${s['REGISTER NUMBER']}</td>
            <td><strong>${s['NAME']}</strong></td>
            <td class="easy">${s['Easy']}</td>
            <td class="med">${s['Med.']}</td>
            <td class="hard">${s['Hard']}</td>
            <td><strong>${s['Total Completed']}</strong></td>
            <td>${profileLink}</td>
        `;
        tbody.appendChild(row);
    });
}

function filterTables() {
    const activeQuery = document.getElementById('searchInput').value.toLowerCase().trim();
    const notAttendedQuery = document.getElementById('searchNotAttendedInput').value.toLowerCase().trim();
    
    const filteredActive = activeStudentsData.filter(s => 
        s['NAME'].toLowerCase().includes(activeQuery) || 
        String(s['REGISTER NUMBER']).includes(activeQuery)
    );
    
    const filteredNotAttended = notAttendedData.filter(s => 
        s['NAME'].toLowerCase().includes(notAttendedQuery) || 
        String(s['REGISTER NUMBER']).includes(notAttendedQuery)
    );

    renderTable('activeTableBody', filteredActive, true);
    renderTable('notAttendedTableBody', filteredNotAttended, false);
}

function openModal() {
    document.getElementById('profileModal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('profileModal').style.display = 'none';
    document.getElementById('modalStatus').innerText = '';
}

async function handleProfileSubmit(event) {
    event.preventDefault();
    const submitBtn = document.getElementById('submitBtn');
    const statusMsg = document.getElementById('modalStatus');
    
    const reg_number = document.getElementById('regNumber').value.trim();
    const profile_url = document.getElementById('profileUrl').value.trim();

    submitBtn.disabled = true;
    statusMsg.innerText = 'Updating profile...';
    statusMsg.style.color = '#38bdf8';

    try {
        const response = await fetch('/api/update-profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reg_number, profile_url })
        });

        const result = await response.json();
        if (response.ok && result.success) {
            statusMsg.style.color = '#4ade80';
            statusMsg.innerText = result.message;
            setTimeout(() => {
                closeModal();
                fetchDashboardData();
            }, 1500);
        } else {
            statusMsg.style.color = '#f87171';
            statusMsg.innerText = result.message || 'Update failed.';
        }
    } catch (err) {
        statusMsg.style.color = '#f87171';
        statusMsg.innerText = 'Failed to update. Try again.';
    } finally {
        submitBtn.disabled = false;
    }
}

document.addEventListener('DOMContentLoaded', fetchDashboardData);