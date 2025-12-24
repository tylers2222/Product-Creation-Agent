# 🔥 Hot Reload Guide

## What is Hot Reload?

Hot reload automatically restarts your GUI application when you save changes to `main.py`, so you don't have to manually close and reopen it every time you make changes.

## Installation

First, install the required package:

```bash
pip3 install watchdog
```

## Usage

### Option 1: Using the Shell Script (Recommended)

```bash
cd gui
./run_hot.sh
```

### Option 2: Direct Python Command

```bash
cd gui
python3 main.py --hot-reload
```

### Option 3: Normal Mode (No Hot Reload)

```bash
cd gui
python3 main.py
```

## How It Works

1. **Start the app** with `--hot-reload` flag
2. **Make changes** to `main.py`
3. **Save the file** (Cmd+S / Ctrl+S)
4. **Watch it reload** automatically! 🎉

## Tips

- 🔄 The app will restart when ANY `.py` file in the `gui` folder is modified
- 🛑 Press `Ctrl+C` in the terminal to stop hot reload
- 📝 Make sure to save your file after making changes
- ⚡ Changes appear in ~1 second after saving

## Troubleshooting

**App doesn't reload after saving?**
- Check the terminal for error messages
- Make sure you saved the file
- Try closing other instances of the app

**Import errors?**
- Make sure `watchdog` is installed: `pip3 install watchdog`

**Multiple windows opening?**
- This is normal - old window closes, new window opens
- If stuck, press `Ctrl+C` and restart

## Example Workflow

```bash
# Terminal 1: Start hot reload
cd gui
./run_hot.sh

# Terminal 2 or Editor: Make changes
# Edit main.py → Save → See changes instantly!
```

Happy coding! 🚀

