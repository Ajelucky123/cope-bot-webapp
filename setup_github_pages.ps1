# GitHub Pages Setup Helper Script
Write-Host "=== COPE Bot Web App - GitHub Pages Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check if git is installed
try {
    $gitVersion = git --version
    Write-Host "✅ Git is installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Git is not installed. Please install Git first:" -ForegroundColor Red
    Write-Host "   https://git-scm.com/download/win" -ForegroundColor Yellow
    exit
}

Write-Host ""
Write-Host "Follow these steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Create a new repository on GitHub:" -ForegroundColor White
Write-Host "   https://github.com/new" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Make it PUBLIC (required for free GitHub Pages)" -ForegroundColor White
Write-Host ""
Write-Host "3. Copy your repository URL (e.g., https://github.com/username/repo.git)" -ForegroundColor White
Write-Host ""
$repoUrl = Read-Host "Enter your GitHub repository URL"

if ($repoUrl) {
    Write-Host ""
    Write-Host "Setting up git repository..." -ForegroundColor Cyan
    
    # Navigate to webapp directory
    if (Test-Path "webapp") {
        Set-Location webapp
        
        # Initialize git if not already
        if (-not (Test-Path ".git")) {
            git init
            Write-Host "✅ Git repository initialized" -ForegroundColor Green
        }
        
        # Add files
        git add index.html
        git add README.md
        
        # Check if there are changes
        $status = git status --porcelain
        if ($status) {
            git commit -m "Initial commit - COPE Bot Web App"
            Write-Host "✅ Files committed" -ForegroundColor Green
        } else {
            Write-Host "ℹ️  No changes to commit" -ForegroundColor Yellow
        }
        
        # Set branch to main
        git branch -M main
        
        # Add remote
        git remote remove origin 2>$null
        git remote add origin $repoUrl
        Write-Host "✅ Remote added" -ForegroundColor Green
        
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Cyan
        Write-Host "1. Push to GitHub:" -ForegroundColor White
        Write-Host "   git push -u origin main" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "2. Enable GitHub Pages:" -ForegroundColor White
        Write-Host "   - Go to repository Settings > Pages" -ForegroundColor Yellow
        Write-Host "   - Source: Branch 'main', Folder '/ (root)'" -ForegroundColor Yellow
        Write-Host "   - Click Save" -ForegroundColor Yellow
        Write-Host ""
        
        # Extract username and repo name from URL
        if ($repoUrl -match "github\.com/([^/]+)/([^/]+)") {
            $username = $matches[1]
            $repoName = $matches[2] -replace '\.git$', ''
            $pagesUrl = "https://$username.github.io/$repoName/index.html"
            
            Write-Host "3. Your GitHub Pages URL will be:" -ForegroundColor White
            Write-Host "   $pagesUrl" -ForegroundColor Green
            Write-Host ""
            Write-Host "4. Add this to your .env file:" -ForegroundColor White
            Write-Host "   WEBAPP_URL=$pagesUrl" -ForegroundColor Yellow
        }
        
        Set-Location ..
    } else {
        Write-Host "❌ webapp directory not found" -ForegroundColor Red
    }
} else {
    Write-Host "❌ No repository URL provided" -ForegroundColor Red
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

