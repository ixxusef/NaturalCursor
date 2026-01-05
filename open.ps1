$chromePath = "$env:ProgramFiles\Google\Chrome\Application\chrome.exe"
$userDataDir = "$env:LOCALAPPDATA\Google\Chrome\User Data"

Start-Process $chromePath -ArgumentList @(
    "--remote-debugging-port=9222"
    "--user-data-dir=$userDataDir"
    "--profile-directory=Default"
)
#RUN:
#.\open.ps1
#In this directory.