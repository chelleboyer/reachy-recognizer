# 🚀 Reachy Mini App Example - Quick Reference

## What This Is

A Hugging Face Space that provides:
1. Information about the Reachy Recognizer project
2. One-click installation to Reachy Mini robots
3. Installation status and feedback

## Files Overview

```
reachy_mini_app_example/
├── app.py                    # Main Gradio application
├── requirements.txt          # Python dependencies (gradio, requests)
├── README.md                 # Space description with HF metadata
├── .gitignore               # Git ignore rules
├── test_app.py              # Local testing script
├── HUGGINGFACE_SETUP.md     # Detailed setup instructions
├── docs/
│   └── index.html           # Static installation page (alternative UI)
└── .github/
    └── workflows/
        └── sync-to-hf.yml   # Auto-sync to HF (optional)
```

## Quick Start

### 1. Test Locally

```bash
cd reachy_mini_app_example
pip install gradio requests
python test_app.py
```

Visit `http://localhost:7860` to see your app.

### 2. Create Hugging Face Space

1. Go to https://huggingface.co/new-space
2. Name: `reachy_mini_app_example`
3. SDK: Gradio
4. Visibility: Public

### 3. Push to Hugging Face

```bash
# Add Hugging Face remote (replace YOUR_USERNAME)
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/reachy_mini_app_example

# Push files
git add app.py requirements.txt README.md .gitignore
git commit -m "Initial Space setup"
git push hf main
```

### 4. Access Your Space

- **Gradio App**: `https://huggingface.co/spaces/YOUR_USERNAME/reachy_mini_app_example`
- **Static Page**: Use GitHub Pages for `docs/index.html`

## Installation Flow

1. User visits your Space
2. Enters their Reachy dashboard URL (e.g., `http://localhost:8000`)
3. Clicks "Install to Reachy"
4. App sends POST request to `{dashboard_url}/api/install` with:
   ```json
   {
     "url": "https://github.com/chelleboyer/reachy-recognizer",
     "name": "reachy_recognizer"
   }
   ```
5. Reachy dashboard installs the app

## Customization

### Change Repository URL

Edit these locations in the files:
- `app.py`: Line ~78 (install_to_reachy function)
- `docs/index.html`: Lines 141, 200, 239
- `README.md`: Installation examples

### Change App Name

Update in same locations as above, replacing `reachy_recognizer` with your app name.

### Styling

Modify the Gradio theme in `app.py`:
```python
with gr.Blocks(theme=gr.themes.Soft()) as demo:
```

Options: `Soft()`, `Base()`, `Glass()`, `Monochrome()`

## Troubleshooting

### "Module not found: gradio"
```bash
pip install gradio requests
```

### Space won't build on HF
- Check the Logs tab in your Space
- Verify `requirements.txt` syntax
- Ensure Python 3.8+ compatibility

### Installation button fails
- Verify Reachy dashboard is running
- Check dashboard URL format
- Test with curl command first

## Support

- **App Issues**: https://github.com/chelleboyer/reachy-recognizer/issues
- **HF Space Help**: https://huggingface.co/docs/hub/spaces
- **Gradio Docs**: https://gradio.app/docs
