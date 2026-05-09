# Student Steps

## Steps (recommended)
1. Open this folder (`streamlit-app-template`) in VS Code.
2. In Terminal, move into the project directory:
- `cd streamlit-app-template`
3. Run one command:
- macOS/Linux: `python3 setup_starter.py`
- Windows: `python setup_starter.py`
4. Keep that terminal open while the app runs.
5. Close VS Code and start it again and open the project folder.
7. Try the next step
- `Cmd/Ctrl + Shift + P` -> `Python: Select Interpreter`
- choose `.venv/bin/python` (macOS/Linux) or `.venv\Scripts\python.exe` (Windows)

## If you notice an issue or get an error, sometimes it is just the issue with the terminal. close the terminal and open a new terminal and run the steps 


## What the script does
- creates/reuses `.venv`
- installs dependencies (`requirements.txt` if present, otherwise built-in defaults)
- sets VS Code to this folder's interpreter
- runs `streamlit run app.py`

## If you want separate setup/run
1. In Terminal, move into the project directory:
- `cd streamlit-app-template`
2. Setup only:
- macOS/Linux: `python3 setup_script.py`
- Windows: `python setup_script.py`
3. Run app:
- macOS/Linux: `./.venv/bin/streamlit run app.py`
- Windows: `.\.venv\Scripts\streamlit.exe run app.py`

## Common Fixes
1. `import streamlit` is underlined in VS Code:
- `Cmd/Ctrl + Shift + P` -> `Python: Select Interpreter`
- choose `.venv/bin/python` (macOS/Linux) or `.venv\Scripts\python.exe` (Windows)

2. `python` not found:
- macOS/Linux: use `python3 ...`
- Windows: use `python ...`

3. `file does not exist` / `No such file or directory`:
- you are likely in the wrong folder
- run `cd ..` once, then `cd streamlit-app-template`
- rerun: `python3 setup_starter.py` (or `python setup_starter.py` on Windows)

4. Wrong environment picked:
- close VS Code
- reopen only this project folder (not its parent folder)
- run `python3 setup_script.py` (or `python` on Windows) again

5. You pressed `Ctrl+C` during setup and `.venv` is broken:
- rerun `python3 setup_script.py` (or `python setup_script.py` on Windows)
- the script now auto-rebuilds incomplete `.venv` folders
