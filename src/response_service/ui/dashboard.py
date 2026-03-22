DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Playbook Manager - Response Service</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            background: #1a1a2e;
            color: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
        }
        header h1 {
            font-size: 1.5rem;
            font-weight: 600;
        }
        header .status {
            font-size: 0.85rem;
            opacity: 0.8;
            margin-top: 5px;
        }
        .status-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            margin-left: 10px;
        }
        .status-badge.healthy {
            background: #22c55e;
            color: white;
        }
        .status-badge.error {
            background: #ef4444;
            color: white;
        }
        .card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 20px;
            margin-bottom: 20px;
        }
        .card h2 {
            font-size: 1.1rem;
            margin-bottom: 15px;
            color: #1a1a2e;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #eee;
        }
        th {
            font-weight: 600;
            color: #666;
            font-size: 0.85rem;
            text-transform: uppercase;
        }
        tr:hover {
            background: #f9f9f9;
        }
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 500;
            transition: opacity 0.2s;
        }
        .btn:hover {
            opacity: 0.9;
        }
        .btn-primary {
            background: #3b82f6;
            color: white;
        }
        .btn-success {
            background: #22c55e;
            color: white;
        }
        .btn-danger {
            background: #ef4444;
            color: white;
        }
        .btn-secondary {
            background: #e5e7eb;
            color: #333;
            margin-right: 5px;
        }
        .btn-sm {
            padding: 4px 8px;
            font-size: 0.75rem;
            margin-right: 5px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
            font-size: 0.9rem;
        }
        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 0.95rem;
        }
        .error-msg {
            background: #fef2f2;
            border: 1px solid #fecaca;
            color: #dc2626;
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 15px;
        }
        .success-msg {
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            color: #16a34a;
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 15px;
        }
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        .modal.active {
            display: flex;
        }
        .modal-content {
            background: white;
            border-radius: 8px;
            padding: 25px;
            width: 90%;
            max-width: 500px;
            max-height: 90vh;
            overflow-y: auto;
        }
        .grid-2 {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
        }
        .stat-box {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        .stat-item {
            background: #f9f9f9;
            padding: 15px;
            border-radius: 4px;
            border-left: 4px solid #3b82f6;
        }
        .stat-item .value {
            font-size: 2rem;
            font-weight: bold;
            color: #3b82f6;
        }
        .stat-item .label {
            font-size: 0.85rem;
            color: #666;
        }
        code {
            background: #f0f0f0;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: monospace;
            font-size: 0.9em;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #999;
        }
        @media (max-width: 768px) {
            .grid-2 {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <header>
        <h1>Response Service - Playbook Manager</h1>
        <div class="status">
            <span id="status-text">Loading...</span>
            <span id="mongodb-badge" class="status-badge" style="display:none;"></span>
            <span id="redis-badge" class="status-badge" style="display:none;"></span>
        </div>
    </header>

    <div class="container">
        <div id="error-msg"></div>
        <div id="success-msg"></div>

        <div class="grid-2">
            <div>
                <div class="card">
                    <h2>Playbooks <button class="btn btn-primary" style="float:right" onclick="openCreateModal()">+ New</button></h2>
                    <div id="playbooks-table-container" class="loading">Loading playbooks...</div>
                </div>
            </div>

            <div>
                <div class="card stat-box">
                    <div class="stat-item">
                        <div class="value" id="total-playbooks">0</div>
                        <div class="label">Total Playbooks</div>
                    </div>
                    <div class="stat-item">
                        <div class="value" id="enabled-playbooks">0</div>
                        <div class="label">Enabled</div>
                    </div>
                </div>

                <div class="card">
                    <h2>Test Playbook</h2>
                    <div class="form-group">
                        <label>Signal Type</label>
                        <select id="test-signal" onchange="updateTestSignal()">
                            <option value="">Select signal...</option>
                            <option value="DB_SLOW_QUERY">DB_SLOW_QUERY</option>
                            <option value="HTTP_ERROR_SPIKE">HTTP_ERROR_SPIKE</option>
                            <option value="AUTH_FAILURE_SPIKE">AUTH_FAILURE_SPIKE</option>
                            <option value="DEPLOYMENT_FAILURE">DEPLOYMENT_FAILURE</option>
                            <option value="HIGH_LATENCY">HIGH_LATENCY</option>
                            <option value="CACHE_ERROR">CACHE_ERROR</option>
                        </select>
                    </div>
                    <button class="btn btn-primary" onclick="testPlaybook()" style="width:100%">Run Test</button>
                    <div id="test-result" style="margin-top:15px; display:none; background:#f0f0f0; padding:10px; border-radius:4px; font-family:monospace; font-size:0.85rem; max-height:200px; overflow-y:auto;"></div>
                </div>
            </div>
        </div>
    </div>

    <!-- Create/Edit Modal -->
    <div id="playbookModal" class="modal">
        <div class="modal-content">
            <h3 id="modal-title">Create Playbook</h3>
            <form id="playbookForm" onsubmit="savePlaybook(event)">
                <div class="form-group">
                    <label>Signal Type *</label>
                    <select id="signal-type" required>
                        <option value="">Select signal type...</option>
                        <option value="DB_SLOW_QUERY">DB_SLOW_QUERY</option>
                        <option value="HTTP_ERROR_SPIKE">HTTP_ERROR_SPIKE</option>
                        <option value="AUTH_FAILURE_SPIKE">AUTH_FAILURE_SPIKE</option>
                        <option value="DEPLOYMENT_FAILURE">DEPLOYMENT_FAILURE</option>
                        <option value="HIGH_LATENCY">HIGH_LATENCY</option>
                        <option value="CACHE_ERROR">CACHE_ERROR</option>
                        <option value="MEMORY_PRESSURE">MEMORY_PRESSURE</option>
                        <option value="CPU_SPIKE">CPU_SPIKE</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>Action *</label>
                    <select id="action" required>
                        <option value="">Select action...</option>
                        <option value="restart_database">restart_database</option>
                        <option value="restart_api">restart_api</option>
                        <option value="lock_accounts">lock_accounts</option>
                        <option value="rollback_deployment">rollback_deployment</option>
                        <option value="scale_service">scale_service</option>
                        <option value="restart_cache">restart_cache</option>
                        <option value="notify_oncall">notify_oncall</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>Description</label>
                    <textarea id="description" placeholder="Describe this playbook..."></textarea>
                </div>

                <div class="form-group">
                    <label>Enabled</label>
                    <select id="enabled">
                        <option value="true">Yes</option>
                        <option value="false">No</option>
                    </select>
                </div>

                <div style="margin-top:20px; display:flex; gap:10px;">
                    <button type="button" class="btn btn-secondary" onclick="closeModal()" style="flex:1;">Cancel</button>
                    <button type="submit" class="btn btn-primary" style="flex:1;">Save</button>
                </div>
            </form>
        </div>
    </div>

    <script>
        const API_URL = window.location.origin;
        let playbooks = [];
        let editingId = null;

        // Load playbooks on page load
        document.addEventListener('DOMContentLoaded', () => {
            loadPlaybooks();
            loadHealth();
            setInterval(loadPlaybooks, 10000);
            setInterval(loadHealth, 10000);
        });

        async function loadHealth() {
            try {
                const res = await fetch(`${API_URL}/health`);
                const data = await res.json();
                document.getElementById('status-text').textContent = `Status: ${data.status}`;

                const mongoBadge = document.getElementById('mongodb-badge');
                const redisBadge = document.getElementById('redis-badge');

                if (data.mongodb_connected) {
                    mongoBadge.textContent = '✓ MongoDB';
                    mongoBadge.classList.add('healthy');
                    mongoBadge.style.display = 'inline-block';
                }
                if (data.redis_enabled) {
                    redisBadge.textContent = '✓ Redis';
                    redisBadge.classList.add('healthy');
                    redisBadge.style.display = 'inline-block';
                }
            } catch (err) {
                document.getElementById('status-text').textContent = 'Status: Error';
            }
        }

        async function loadPlaybooks() {
            try {
                const res = await fetch(`${API_URL}/playbooks`);
                if (!res.ok) throw new Error('Failed to load playbooks');
                playbooks = await res.json();
                document.getElementById('total-playbooks').textContent = playbooks.length;
                document.getElementById('enabled-playbooks').textContent = playbooks.filter(p => p.enabled).length;
                renderPlaybooksTable();
            } catch (err) {
                showError(err.message);
            }
        }

        function renderPlaybooksTable() {
            const container = document.getElementById('playbooks-table-container');
            if (playbooks.length === 0) {
                container.innerHTML = '<p style="text-align:center; color:#999;">No playbooks. Create one to get started.</p>';
                return;
            }

            let html = '<table><thead><tr><th>Signal Type</th><th>Action</th><th>Status</th><th>Actions</th></tr></thead><tbody>';
            for (const pb of playbooks) {
                html += `<tr>
                    <td><strong>${pb.signal_type}</strong>${pb.description ? '<br><span style="font-size:0.85rem;color:#999;">' + pb.description + '</span>' : ''}</td>
                    <td><code>${pb.action}</code></td>
                    <td><button class="btn btn-sm ${pb.enabled ? 'btn-success' : 'btn-secondary'}" onclick="togglePlaybook('${pb.id}', ${pb.enabled})">${pb.enabled ? 'Enabled' : 'Disabled'}</button></td>
                    <td>
                        <button class="btn btn-sm btn-secondary" onclick="editPlaybook('${pb.id}')">Edit</button>
                        <button class="btn btn-sm btn-danger" onclick="deletePlaybook('${pb.id}')">Delete</button>
                    </td>
                </tr>`;
            }
            html += '</tbody></table>';
            container.innerHTML = html;
        }

        async function togglePlaybook(id, currentEnabled) {
            try {
                const res = await fetch(`${API_URL}/playbooks/${id}/toggle`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ enabled: !currentEnabled })
                });
                if (!res.ok) throw new Error('Failed to toggle');
                showSuccess(`Playbook ${!currentEnabled ? 'enabled' : 'disabled'}`);
                loadPlaybooks();
            } catch (err) {
                showError(err.message);
            }
        }

        async function deletePlaybook(id) {
            if (!confirm('Delete this playbook?')) return;
            try {
                const res = await fetch(`${API_URL}/playbooks/${id}`, { method: 'DELETE' });
                if (!res.ok) throw new Error('Failed to delete');
                showSuccess('Playbook deleted');
                loadPlaybooks();
            } catch (err) {
                showError(err.message);
            }
        }

        function openCreateModal() {
            editingId = null;
            document.getElementById('modal-title').textContent = 'Create Playbook';
            document.getElementById('signal-type').disabled = false;
            document.getElementById('playbookForm').reset();
            document.getElementById('playbookModal').classList.add('active');
        }

        function editPlaybook(id) {
            const pb = playbooks.find(p => p.id === id);
            if (!pb) return;
            editingId = id;
            document.getElementById('modal-title').textContent = 'Edit Playbook';
            document.getElementById('signal-type').value = pb.signal_type;
            document.getElementById('signal-type').disabled = true;
            document.getElementById('action').value = pb.action;
            document.getElementById('description').value = pb.description;
            document.getElementById('enabled').value = pb.enabled.toString();
            document.getElementById('playbookModal').classList.add('active');
        }

        function closeModal() {
            document.getElementById('playbookModal').classList.remove('active');
        }

        async function savePlaybook(e) {
            e.preventDefault();
            try {
                const data = {
                    signal_type: document.getElementById('signal-type').value,
                    action: document.getElementById('action').value,
                    description: document.getElementById('description').value,
                    enabled: document.getElementById('enabled').value === 'true',
                    parameters: {}
                };

                const url = editingId ? `${API_URL}/playbooks/${editingId}` : `${API_URL}/playbooks`;
                const method = editingId ? 'PUT' : 'POST';

                const res = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || 'Failed to save');
                }

                showSuccess(editingId ? 'Playbook updated' : 'Playbook created');
                closeModal();
                loadPlaybooks();
            } catch (err) {
                showError(err.message);
            }
        }

        async function testPlaybook() {
            const signal = document.getElementById('test-signal').value;
            if (!signal) {
                showError('Select a signal type to test');
                return;
            }

            try {
                const res = await fetch(`${API_URL}/simulate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ signal_type: signal })
                });
                const data = await res.json();
                const resultDiv = document.getElementById('test-result');
                resultDiv.textContent = JSON.stringify(data, null, 2);
                resultDiv.style.display = 'block';
            } catch (err) {
                showError('Test failed: ' + err.message);
            }
        }

        function updateTestSignal() {
            document.getElementById('test-result').style.display = 'none';
        }

        function showError(msg) {
            const div = document.getElementById('error-msg');
            div.className = 'error-msg';
            div.textContent = msg;
            setTimeout(() => { div.textContent = ''; }, 5000);
        }

        function showSuccess(msg) {
            const div = document.getElementById('success-msg');
            div.className = 'success-msg';
            div.textContent = msg;
            setTimeout(() => { div.textContent = ''; }, 3000);
        }
    </script>
</body>
</html>
"""
