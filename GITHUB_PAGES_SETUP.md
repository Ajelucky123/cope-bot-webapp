# GitHub Pages Setup for Web App

## Step 1: Create a GitHub Repository

1. Go to https://github.com/new
2. Create a new repository (e.g., `cope-bot-webapp`)
3. Make it **public** (required for free GitHub Pages)
4. Don't initialize with README (we'll push our files)

## Step 2: Initialize Git and Push Files

Open terminal in your project folder and run:

```bash
cd webapp
git init
git add index.html
git commit -m "Initial commit - COPE Bot Web App"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/cope-bot-webapp.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username and `cope-bot-webapp` with your repository name.

## Step 3: Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** tab
3. Scroll down to **Pages** section (left sidebar)
4. Under **Source**, select:
   - Branch: `main`
   - Folder: `/ (root)`
5. Click **Save**

## Step 4: Get Your GitHub Pages URL

Your webapp will be available at:
```
https://YOUR_USERNAME.github.io/cope-bot-webapp/index.html
```

Replace:
- `YOUR_USERNAME` with your GitHub username
- `cope-bot-webapp` with your repository name

## Step 5: Update .env File

Add this line to your `.env` file:
```env
WEBAPP_URL=https://YOUR_USERNAME.github.io/cope-bot-webapp/index.html
```

## Step 6: Restart Your Bot

After updating `.env`, restart your bot:
```bash
python main.py
```

## Notes

- GitHub Pages may take a few minutes to deploy after pushing
- The URL is permanent (unlike ngrok which changes)
- Free GitHub Pages requires public repositories
- For private repos, you need GitHub Pro or use a different hosting

## Troubleshooting

### "404 Not Found" error
- Wait a few minutes for GitHub Pages to deploy
- Check that the branch is set to `main` in Pages settings
- Verify the file path is correct in the URL

### Changes not showing
- GitHub Pages can take 1-5 minutes to update
- Clear your browser cache
- Check the repository to ensure files were pushed

### HTTPS required
- GitHub Pages automatically provides HTTPS
- Make sure you use `https://` in your WEBAPP_URL (not `http://`)

