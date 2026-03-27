function copyCode(btn) {
    const codeText = document.getElementById('command-text').innerText;
    
    navigator.clipboard.writeText(codeText).then(() => {
        // Visual feedback
        btn.classList.add('copied');
        const btnText = btn.querySelector('.btn-text');
        const originalText = btnText.innerText;
        btnText.innerText = 'Copied';
        
        // Reset after 2 seconds
        setTimeout(() => {
            btn.classList.remove('copied');
            btnText.innerText = originalText;
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
        alert('Failed to copy automatically. Please copy manually.');
    });
}

function getOS() {
    const userAgent = navigator.userAgent;
    const platform = navigator.platform;
    
    if (userAgent.indexOf("Win") !== -1 || platform.indexOf("Win") !== -1) return "Windows";
    if (userAgent.indexOf("Linux") !== -1 || platform.indexOf("Linux") !== -1) return "Linux";
    if (userAgent.indexOf("Mac") !== -1 || platform.indexOf("Mac") !== -1) return "macOS";
    if (userAgent.indexOf("X11") !== -1) return "UNIX";
    return "Unknown";
}

function updateCommand() {
    const os = getOS();
    const osInfoElement = document.getElementById('os-info');
    const commandElement = document.getElementById('command-text');
    const baseUrl = window.location.origin;
    
    // Update Status Badge
    osInfoElement.innerText = `Detected: ${os}`;
    
    // Set Command based on OS
    if (os === "Windows") {
        commandElement.innerText = `iex (New-Object Net.WebClient).DownloadString('${baseUrl}/InstallScript/install.ps1')`;
    } else if (os === "Linux" || os === "macOS" || os === "UNIX") {
        commandElement.innerText = `curl -sL ${baseUrl}/InstallScript/install.sh | bash`;
    } else {
        commandElement.innerText = '# Unsupported Operating System';
    }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', updateCommand);