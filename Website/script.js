function copyCode(btn) {
            const codeText = btn.parentElement.querySelector('.code-text').innerText;
            navigator.clipboard.writeText(codeText).then(() => {
                // 可选：点击后改变图标提示已复制
                const originalHTML = btn.innerHTML;
                btn.innerHTML = '<span style="font-size:12px; color:green;">Copied!</span>';
                setTimeout(() => {
                    btn.innerHTML = originalHTML;
                }, 2000);
            });
        }

function getOS() {
  const userAgent = navigator.userAgent;
  
  if (userAgent.indexOf("Win") !== -1) return "Windows";
  if (userAgent.indexOf("Linux") !== -1) return "Linux";
  if (userAgent.indexOf("Mac") !== -1) return "MacOS";
  if (userAgent.indexOf("X11") !== -1) return "UNIX";
  
  return "Unknown";
}

if (getOS() == "Windows") {
    document.getElementsByClassName("code-text")[0].innerText = "powershell -c iex (New-Object Net.WebClient).DownloadString('" + window.location.origin + "/InstallScript/install.ps1" + "')";
} else if (getOS() == "Linux") {
    document.getElementsByClassName("code-text")[0].innerText = "curl -sL " + window.location.origin + "/InstallScript/install.sh | bash";
}