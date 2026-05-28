# deploy.ps1 - Deploy to Railway from Windows

Write-Host "🚀 Deploying DPDP Compliance Audit Toolchain to Railway..." -ForegroundColor Cyan

# Check if Railway CLI is installed
$railwayInstalled = Get-Command railway -ErrorAction SilentlyContinue
if (-not $railwayInstalled) {
    Write-Host "📦 Installing Railway CLI..." -ForegroundColor Yellow
    npm install -g @railway/cli
}

# Login to Railway
Write-Host "🔐 Logging into Railway..." -ForegroundColor Yellow
railway login

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Creating from template..." -ForegroundColor Yellow
    @"
GROQ_API_KEY=your_groq_api_key_here
API_PORT=8000
API_HOST=0.0.0.0
LOG_LEVEL=INFO
"@ | Out-File -FilePath ".env" -Encoding utf8
    Write-Host "📝 Please edit .env file and add your GROQ_API_KEY" -ForegroundColor Yellow
    Read-Host "Press Enter after you've added your API key"
}

# Set environment variables on Railway
Write-Host "🔧 Setting environment variables on Railway..." -ForegroundColor Yellow
$envContent = Get-Content ".env"
foreach ($line in $envContent) {
    if ($line -and $line -notmatch "^#") {
        $parts = $line -split "=", 2
        if ($parts.Count -eq 2) {
        railway variables set $parts[0]=$parts[1]
        }
    }
}

# Deploy
Write-Host "📤 Deploying to Railway..." -ForegroundColor Yellow
railway up

Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "🌐 Getting deployment URL..." -ForegroundColor Green
railway domain

Write-Host ""
Write-Host "🎉 Your DPDP Compliance Audit Toolchain is live!" -ForegroundColor Green
Write-Host "📋 API endpoints available at /, /health, /vpc/report" -ForegroundColor Cyan