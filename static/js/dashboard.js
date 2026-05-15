// static/js/dashboard.js

// Wait for the page to load completely
document.addEventListener('DOMContentLoaded', function() {
    
    // ============================================================
    // TAB SWITCHING FUNCTIONALITY
    // ============================================================
    
    // Get all tab buttons and tab content elements
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    // Add click event to each tab button
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            
            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked button and corresponding content
            this.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });
    
    // ============================================================
    // SEARCH/FILTER FUNCTIONALITY
    // ============================================================
    
    // Get all search input fields
    const searchInputs = document.querySelectorAll('.search-input');
    
    searchInputs.forEach(input => {
        input.addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase();
            const tableId = this.getAttribute('data-table');
            const table = document.getElementById(tableId);
            const rows = table.getElementsByTagName('tr');
            
            // Loop through all table rows (skip header row)
            for (let i = 1; i < rows.length; i++) {
                const row = rows[i];
                const text = row.textContent.toLowerCase();
                
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            }
        });
    });
    
    // ============================================================
    // AUTO-REFRESH FUNCTIONALITY
    // ============================================================
    
    let autoRefreshInterval = null;
    const refreshBtn = document.getElementById('refreshBtn');
    const autoRefreshCheckbox = document.getElementById('autoRefresh');
    const lastUpdatedSpan = document.getElementById('lastUpdated');
    
    // Function to update the last updated timestamp
    function updateTimestamp() {
        if (lastUpdatedSpan) {
            const now = new Date();
            const timeString = now.toLocaleTimeString();
            lastUpdatedSpan.textContent = `Last updated: ${timeString}`;
        }
    }
    
    // Function to refresh the page
    function refreshPage() {
        window.location.reload();
    }
    
    // Manual refresh button
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshPage);
    }
    
    // Auto-refresh checkbox
    if (autoRefreshCheckbox) {
        autoRefreshCheckbox.addEventListener('change', function() {
            if (this.checked) {
                // Refresh every 30 seconds
                autoRefreshInterval = setInterval(refreshPage, 30000);
            } else {
                if (autoRefreshInterval) {
                    clearInterval(autoRefreshInterval);
                }
            }
        });
    }
    
    // Set initial timestamp
    updateTimestamp();
    
    // ============================================================
    // STATISTICS CALCULATION
    // ============================================================
    
    function calculateStats() {
        const interfaceTables = document.querySelectorAll('.interface-table');
        
        interfaceTables.forEach(table => {
            const deviceCard = table.closest('.device-card');
            if (!deviceCard) return;
            
            const rows = table.getElementsByTagName('tr');
            let totalPorts = 0;
            let upPorts = 0;
            
            for (let i = 1; i < rows.length; i++) {
                totalPorts++;
                const statusCell = rows[i].cells[1];
                if (statusCell && statusCell.textContent.includes('connected')) {
                    upPorts++;
                }
            }
            
            // Update or create stats display
            let statsDiv = deviceCard.querySelector('.device-stats');
            if (!statsDiv) {
                statsDiv = document.createElement('div');
                statsDiv.className = 'stats';
                const deviceHeader = deviceCard.querySelector('.device-header');
                if (deviceHeader) {
                    deviceHeader.insertAdjacentElement('afterend', statsDiv);
                }
            }
            
            statsDiv.innerHTML = `
                <div class="stat-card">
                    <h4>Total Ports</h4>
                    <div class="stat-value">${totalPorts}</div>
                </div>
                <div class="stat-card">
                    <h4>Active Ports</h4>
                    <div class="stat-value">${upPorts}</div>
                </div>
                <div class="stat-card">
                    <h4>Health</h4>
                    <div class="stat-value">${totalPorts > 0 ? Math.round((upPorts / totalPorts) * 100) : 0}%</div>
                </div>
            `;
        });
    }
    
    // Calculate stats after page loads
    calculateStats();
});

// Show loading overlay on refresh
$('#refreshBtn').on('click', function() {
    $('#loadingOverlay').show();
    location.reload();
});

// Hide loading overlay when page loads
$(window).on('load', function() {
    $('#loadingOverlay').hide();
});