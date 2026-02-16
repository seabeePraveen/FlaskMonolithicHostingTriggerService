const cloneBtn = document.getElementById('clone-btn');
const repoUrlInput = document.getElementById('repo-url');
const entryPointInput = document.getElementById('entry-point');
const envVarsInput = document.getElementById('env-vars');
const requirementsInput = document.getElementById('requirements');
const statusMsg = document.getElementById('status-msg');
const loader = document.getElementById('loader');
const btnText = document.getElementById('btn-text');
const cancelEditBtn = document.getElementById('cancel-edit-btn');
const formTitle = document.getElementById('form-title');
const formSubtitle = document.getElementById('form-subtitle');

let isEditing = false;
let editingProjectName = '';

cloneBtn.addEventListener('click', async () => {
    const repoUrl = repoUrlInput.value.trim();
    const entryPoint = entryPointInput.value.trim() || 'app.py';
    const envVars = envVarsInput.value.trim();
    const requirements = requirementsInput.value.trim();

    if (!repoUrl && !isEditing) return;

    cloneBtn.disabled = true;
    loader.style.display = 'block';
    btnText.innerText = isEditing ? 'Updating...' : 'Cloning & Setting up...';
    statusMsg.style.display = 'none';

    try {
        const endpoint = isEditing ? '/update-project' : '/clone-project';
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                project_name: editingProjectName,
                repo_url: repoUrl,
                entry_point: entryPoint,
                env_vars: envVars,
                requirements: requirements
            })
        });

        const data = await response.json();

        if (response.ok) {
            statusMsg.innerText = `✅ ${data.message}`;
            statusMsg.className = 'status-success';
            statusMsg.style.display = 'block';
            setTimeout(() => location.reload(), 1500);
        } else {
            statusMsg.innerText = `❌ ${data.error || 'Failed'}`;
            statusMsg.className = 'status-error';
            statusMsg.style.display = 'block';
        }
    } catch (err) {
        statusMsg.innerText = '❌ Network error';
        statusMsg.className = 'status-error';
        statusMsg.style.display = 'block';
    } finally {
        cloneBtn.disabled = false;
        loader.style.display = 'none';
        btnText.innerText = isEditing ? 'Save Changes' : 'Clone Project';
    }
});

async function startEdit(event, projectName) {
    event.preventDefault();
    event.stopPropagation();

    isEditing = true;
    editingProjectName = projectName;
    formTitle.innerText = `Edit: ${projectName}`;
    formSubtitle.innerText = "Fetch current config and update as needed.";
    btnText.innerText = "Save Changes";
    cancelEditBtn.style.display = "block";
    repoUrlInput.disabled = true;

    window.scrollTo({ top: 0, behavior: 'smooth' });

    try {
        const response = await fetch(`/get-project/${projectName}`);
        const data = await response.json();
        if (response.ok) {
            repoUrlInput.value = data.repo_url;
            entryPointInput.value = data.entry_point || 'app.py';
            envVarsInput.value = data.env_vars || '';
            requirementsInput.value = data.requirements || '';
        }
    } catch (err) {
        alert("Failed to collect project data");
    }
}

cancelEditBtn.addEventListener('click', () => {
    isEditing = false;
    editingProjectName = '';
    formTitle.innerText = "Clone New Project";
    formSubtitle.innerText = "Enter a GitHub repository URL to host it locally.";
    btnText.innerText = "Clone Project";
    cancelEditBtn.style.display = "none";
    repoUrlInput.disabled = false;
    repoUrlInput.value = '';
    entryPointInput.value = 'app.py';
    envVarsInput.value = '';
    requirementsInput.value = '';
});

async function confirmDelete(event, projectName) {
    event.preventDefault();
    event.stopPropagation();
    if (!confirm(`Delete "${projectName}"?`)) return;
    try {
        const response = await fetch(`/delete-project/${projectName}`, { method: 'DELETE' });
        if (response.ok) location.reload();
    } catch (err) {
        alert('Delete failed');
    }
}

repoUrlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') cloneBtn.click();
});
