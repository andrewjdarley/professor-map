const activateBtn = document.getElementById('activateBtn');
const settingsBtn = document.getElementById('settingsBtn');
const statusIndicator = document.getElementById('statusIndicator');
const statusMessage = document.getElementById('statusMessage');
const statusText = document.getElementById('statusText');

activateBtn.addEventListener('click', async () => {
    activateBtn.disabled = true;
    showStatus('Activating...', 'loading');

    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        chrome.tabs.sendMessage(tabs[0].id, { action: 'activate' }, (response) => {
            if (response && response.success) {
                updateStatusUI(true);
                showStatus('✓ Extension activated!', 'success');
            } else {
                showStatus('✗ Could not activate on this page.', 'error');
            }
            activateBtn.disabled = false;
        });
    });
});

settingsBtn.addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
});

function updateStatusUI(isActive) {
    if (isActive) {
        statusIndicator.classList.remove('inactive');
        activateBtn.textContent = 'Active';
        activateBtn.style.opacity = '0.5';
        statusText.textContent = '✓ Extension is running.';
    } else {
        statusIndicator.classList.add('inactive');
        activateBtn.textContent = 'Activate';
        activateBtn.style.opacity = '1';
        statusText.textContent = 'Waiting for activation...';
    }
}

function showStatus(message, type) {
    statusMessage.textContent = message;
    statusMessage.className = `status-message ${type}`;
    statusMessage.classList.remove('hidden');

    if (type === 'success') {
        setTimeout(() => {
            statusMessage.classList.add('hidden');
        }, 3000);
    }
}

updateStatusUI(false);