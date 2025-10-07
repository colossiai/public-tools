# Powershell script to download audio

param(
    [Parameter(Position=0)]
    [string]$Url
)


if ([string]::IsNullOrEmpty($Url)) {
    $Url = Read-Host "Enter YouTube URL"
}

Write-Host "Downloading: $Url" -ForegroundColor Green
.\yt-dlp.exe --no-playlist -f "bestaudio[ext=m4a]" --embed-thumbnail --embed-metadata "$Url"

# example
# .\get_m4a.ps1 "https://www.youtube.com/watch?v=LnCRFNbhJkw&list=RDLnCRFNbhJkw&start_radio=1"