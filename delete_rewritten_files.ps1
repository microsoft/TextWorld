Write-Host "Deleting rewritten files for policy check"

Get-Content "files.txt" | ForEach-Object {
    Remove-Item -Path $_
}
Remove-Item -Path "files.txt"