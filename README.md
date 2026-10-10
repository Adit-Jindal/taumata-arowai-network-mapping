# Taumata Arowai — Coordinate-to-Zone Prototype

A local Streamlit interface for testing coordinate-to-polygon lookup against a
private File Geodatabase (`.gdb`).

## Requirements

- Python 3.10+ recommended
- Your private `.gdb` folder
- The exact name of the polygon layer inside that geodatabase

## Setup

Open a terminal in this folder and install dependencies:

```bash
python -m venv .venv
```

Activate the virtual environment:

Windows:
```bash
.venv\Scripts\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

Then:

```bash
pip install -r requirements.txt
```

Set the geodatabase path and layer name before launching (use absolute paths).

Windows PowerShell:
```powershell
$env:GDB_PATH="C:\path\to\your_data.gdb"
$env:ZONE_LAYER="AklDizzy"
streamlit run app.py
```

macOS/Linux:
```bash
export GDB_PATH="/path/to/your_data.gdb"
export ZONE_LAYER="AklDizzy"
streamlit run app.py
```

## Coordinate conventions

The prototype accepts X/Y coordinates in EPSG:3857. It transforms the input
point to the layer's CRS before evaluating polygon coverage. Do not enter
longitude/latitude into these fields.

The lookup uses polygon `covers`, so points on boundaries may match multiple
features. The app displays all matches rather than silently selecting one.


## Known edge cases
- Entering coordinates out of the range of the project database shows an error message, allowing you to change the values entered.
- Entering a non-numeric input defaults to the testing example coordinates (does not throw an error).

## Privacy and deployment

The geodatabase is not bundled with this code. Keep it in an approved location
and follow your organization's data-handling requirements. For a hosted app,
the server must have authorized access to the geodatabase; do not put private
data in a public repository.
