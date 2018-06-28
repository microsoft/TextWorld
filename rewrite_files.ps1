Write-Host "Rewriting files for policy check"

$new_items = [System.Collections.ArrayList]@()

Get-ChildItem "*.py" -Recurse | ForEach-Object {
    $new_name = $_.Name -Replace ".py", ".txt"
    $dir_name = $_.DirectoryName
    $new_name = "${dir_name}\${new_name}"
    $new_items.Add($new_name)
    Copy-Item $_ $new_name 
}

Get-ChildItem "*.twf" -Recurse | ForEach-Object {
$new_name = $_.Name -Replace ".twf", ".txt"
    $dir_name = $_.DirectoryName
    $new_name = "${dir_name}\${new_name}"
    $new_items.Add($new_name)
    Copy-Item $_ $new_name 
    
}

$ofs = "`n"  # sets separator
"$new_items" | Out-File "files.txt"