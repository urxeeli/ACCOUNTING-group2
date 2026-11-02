# Accounting App

Desktop accounting app built with Python and Tkinter. It includes a journal,
ledger, worksheet, trial balance, income statement, and classified balance sheet.

## Run from source

From this folder, run:

```bat
python main.py
```

The app uses Python's standard library and does not require additional packages
to run from source.

## Build the Windows executable

Install PyInstaller if it is not already installed:

```bat
python -m pip install pyinstaller
```

Then run `build_app.bat`. The executable is created in a new versioned folder
under `dist\`; this allows rebuilding while an older app instance is still open.

Run the latest successful build with `run_app.bat`.

## Data and reports

When running from source, journal entries and custom accounts are stored in
`accounting_data.json` next to the source files. Packaged builds store data in
`%LOCALAPPDATA%\AccountingApp\accounting_data.json` so it remains writable and
persists when a new build is installed. Older data files beside earlier
executables are detected and loaded automatically. Reports can be exported as
CSV from their respective tabs.

If an existing data file is corrupt, the app asks before doing anything. If you
choose to continue with an empty ledger, it first copies the damaged file to a
timestamped `.bak` file and leaves that backup untouched.
