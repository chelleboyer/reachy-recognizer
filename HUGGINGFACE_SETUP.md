# Setting Up Your Hugging Face Space

## Files Created

Your Hugging Face Space now includes:

- `app.py` - Main Gradio application
- `requirements.txt` - Python dependencies
- `README.md` - Space description with metadata
- `.gitignore` - Files to exclude from git
- `docs/index.html` - Static installation page (optional)

## Steps to Create the Space on Hugging Face

### 1. Create a New Space

1. Go to [Hugging Face](https://huggingface.co/)
2. Click on your profile → **New Space**
3. Fill in the details:
   - **Space name**: `reachy_mini_app_example` (or your preferred name)
   - **License**: MIT
   - **SDK**: Gradio
   - **Space hardware**: CPU basic (free tier)
   - **Visibility**: Public

### 2. Push Your Code

Option A: **Using Git**

```bash
# Navigate to the app directory
cd c:\code\reachy-mini-dev\reachy_mini_app_example

# Initialize git if not already done
git init

# Add the Hugging Face remote (replace YOUR_USERNAME)
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/reachy_mini_app_example

# Add and commit files
git add app.py requirements.txt README.md .gitignore
git commit -m "Initial commit: Reachy Recognizer Space"

# Push to Hugging Face
git push hf main
```

Option B: **Using Hugging Face Web Interface**

1. After creating the Space, click **Files** → **Add file**
2. Upload each file:
   - `app.py`
   - `requirements.txt`
   - `README.md`
3. Commit the changes

### 3. Enable Static Site (for index.html)

If you want to use the static `index.html` for one-click installation:

1. In your Space settings, enable **Static Site**
2. Upload `docs/index.html` to the root of your Space
3. The static page will be available at `https://YOUR_USERNAME.github.io/reachy_mini_app_example/`

### 4. Test Your Space

1. Wait for the Space to build (usually 1-2 minutes)
2. Access it at: `https://huggingface.co/spaces/YOUR_USERNAME/reachy_mini_app_example`
3. Test the installation button with your Reachy dashboard URL

## Updating the index.html

Your `docs/index.html` is already configured to point to:
- Repository: `https://github.com/chelleboyer/reachy-recognizer`
- App name: `reachy_recognizer`

This should work correctly for installation to Reachy robots.

## Space URL

Once created, your Space will be available at:
- **Gradio App**: `https://huggingface.co/spaces/YOUR_USERNAME/reachy_mini_app_example`
- **Static Page**: `https://YOUR_USERNAME.github.io/reachy_mini_app_example/` (if using GitHub Pages)

## Troubleshooting

### Space Build Fails
- Check the **Logs** tab in your Space
- Verify `requirements.txt` dependencies
- Ensure Python version compatibility (3.8+)

### Installation Button Doesn't Work
- Verify your Reachy dashboard is running
- Check the dashboard URL is correct
- Ensure CORS is enabled on your Reachy dashboard

### Space Not Loading
- Clear browser cache
- Check Space status in Hugging Face
- Restart the Space from the Settings tab

## Next Steps

1. Create the Space on Hugging Face
2. Push your code
3. Test the installation flow
4. Update your main repository README with the Space link
5. Share the Space URL with others!

## Support

For issues with:
- **The Space**: Check Hugging Face documentation
- **Reachy Installation**: Refer to Reachy Mini documentation
- **The App**: Create an issue on [GitHub](https://github.com/chelleboyer/reachy-recognizer)
