# Quick Start Guide

## Installation (30 seconds)

### macOS/Linux
```bash
cd gui/
./install.sh
```

### Windows
```cmd
cd gui
install.bat
```

### Manual
```bash
pip install -r requirements.txt
```

## Configuration (1 minute)

**Edit `main.py`:**

1. **Line 25** - Set your API URL:
   ```python
   API_BASE_URL = "https://your-api-url.com"
   ```

2. **Line 34** (Optional) - Change password:
   ```python
   CORRECT_PASSWORD = "your-password"
   ```

## Run

```bash
python main.py
```

## First Use

1. **Login** with password (default: `999999`)
2. **Enter product details:**
   - Brand Name
   - Product Name
3. **Add options** (comma-separated):
   - Size: `50 g, 100 g, 200 g`
   - Flavor: `Chocolate, Vanilla`
4. **Click** "🔄 Generate All Variants"
5. **Fill variant details** (SKU, Barcode, Price, etc.)
6. **Click** "📤 Send Request"
7. **Wait** for success popup with Shopify link!

## Distributing to Users

### Create Standalone App

**macOS/Windows:**
```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

Executable will be in `dist/` folder.

### Share as Package

Just zip the entire `gui/` folder:
- Users run `install.sh` or `install.bat`
- They edit `main.py` for API URL
- Run `python main.py`

## Support

- **Password Issues:** Delete `login_tracking.json`
- **API Errors:** Check `API_BASE_URL` is correct
- **Missing Fields:** Expand window, fields might be cut off

---

That's it! You're ready to create Shopify products. 🚀



