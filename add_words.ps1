$files = @(git diff --name-only main)

if ($files.Count -eq 1 -and $files -eq 'data.json') {
    git add data.json 
    git commit -m "feat(data): more words"
    Write-Host "Only data.json was changed, commited to git"
} else {
    Write-Host "Error: Other files were modified or no files were changed."
    # Put your fallback commands here
}