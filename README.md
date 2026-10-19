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

## Incorporating map 
```Python
from pyproj import Transformer

# Transformer from WGS84 (lat/lon) to EPSG:3857 (X/Y meters)
transformer = Transformer.from_crtm(4326, 3857, always_xy=True)


def latlon_to_epsg3857(lat, lon):
    x, y = transformer.transform(lon, lat)
    return x, y
```

```Python
import folium
import streamlit as st
from streamlit_folium import st_folium

st.title("Auckland Zone Lookup")

# Default view centered over Auckland (Latitude, Longitude)
AUCKLAND_CENTER = [-36.8485, 174.7633]
DEFAULT_ZOOM = 11

st.subheader("Select Location")
st.caption("Click anywhere on the Auckland map to automatically pick coordinates.")

# 1. Initialize Map
m = folium.Map(location=AUCKLAND_CENTER, zoom_start=DEFAULT_ZOOM)

# 2. Render Map and capture user clicks
map_data = st_folium(m, width=700, height=500, key="auckland_map")

# 3. Handle Click Event
selected_lat, selected_lon = None, None

if map_data and map_data.get("last_clicked"):
    selected_lat = map_data["last_clicked"]["lat"]
    selected_lon = map_data["last_clicked"]["lng"]

    st.success(f"Selected Point: Lat {selected_lat:.5f}, Lon {selected_lon:.5f}")

    # Convert lat/lon to EPSG:3857 X/Y coordinates as expected by the prototype
    x_3857, y_3857 = latlon_to_epsg3857(selected_lat, selected_lon)

    st.write(f"**Transformed EPSG:3857 Coordinates:** X = `{x_3857:.2f}`, Y = `{y_3857:.2f}`")

    # Pass x_3857 and y_3857 directly to your polygon covers lookup logic
    # e.g., results = perform_zone_lookup(x_3857, y_3857)
else:
    st.info("Click a point on the map to query the geodatabase zone.")
```

## Known edge cases
- Entering coordinates out of the range of the project database shows an error message, allowing you to change the values entered.
- Entering a non-numeric input defaults to the testing example coordinates (does not throw an error).

## Privacy and deployment

The geodatabase is not bundled with this code. Keep it in an approved location
and follow your organization's data-handling requirements. For a hosted app,
the server must have authorized access to the geodatabase; do not put private
data in a public repository.
