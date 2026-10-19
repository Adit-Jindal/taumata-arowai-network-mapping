import os
import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from shapely.geometry import Point
from pyproj import Transformer

st.set_page_config(page_title="Water Zone Lookup", page_icon="📍", layout="wide")
st.title("Water Zone Lookup")
st.write("Select a point on the map or enter projected coordinates to find its matching zone.")

GDB_PATH = os.getenv("GDB_PATH", "path/to/your_data.gdb")
LAYER_NAME = os.getenv("ZONE_LAYER", "your_zone_layer")

@st.cache_data(show_spinner="Loading zone polygons…")
def load_zones(gdb_path: str, layer_name: str):
    if not os.path.exists(gdb_path):
        raise FileNotFoundError(
            f"Geodatabase not found: {gdb_path}. Set GDB_PATH to your .gdb folder."
        )
    data = gpd.read_file(gdb_path, layer=layer_name)
    if data.empty:
        raise ValueError("The selected layer contains no features.")
    if data.crs is None:
        raise ValueError("The zone layer has no CRS defined.")
    if "zone" not in data.columns:
        raise ValueError("This app expects a 'zone' field. Update it to match your layer.")
    return data

def find_matches(zones, lon, lat):
    # Map clicks arrive as WGS84 longitude/latitude; transform into the layer CRS.
    transformer = Transformer.from_crs("EPSG:4326", zones.crs, always_xy=True)
    x, y = transformer.transform(float(lon), float(lat))
    point = Point(x, y)
    valid = zones.geometry.notna() & ~zones.geometry.is_empty
    matches = zones.loc[valid & zones.geometry.covers(point)]
    return x, y, matches

def show_matches(matches):
    if matches.empty:
        st.warning("No zone polygon covers this point. Check that the point is within the mapped area.")
        return
    st.success(f"Found {len(matches)} matching feature(s).")
    cols = [
        c for c in [
            "OBJECTID", "zone", "pop_regist", "pop_low_de",
            "pop_mod_de", "pop_high_d", "pop_maori"
        ] if c in matches.columns
    ]
    st.subheader("Matching zone details")
    st.dataframe(matches[cols].reset_index(drop=True), use_container_width=True, hide_index=True)
    if len(matches) > 1:
        st.warning("Multiple polygons cover this point. It may be on a shared boundary or polygons may overlap; review the matches.")

try:
    zones = load_zones(GDB_PATH, LAYER_NAME)
except Exception as exc:
    st.error(f"Could not load the zone layer: {exc}")
    st.info("Set GDB_PATH to your .gdb folder and ZONE_LAYER to the exact layer name inside it.")
    st.stop()

tab_map, tab_coords = st.tabs(["🗺️ Click on map", "⌨️ Enter coordinates"])

with tab_map:
    st.caption("Click the map to select a location. The coordinates and matching zone will appear below.")
    # Derive a sensible map centre and extent from the actual dataset, not a hard-coded location.
    try:
        bounds = gpd.GeoSeries(zones.geometry, crs=zones.crs).to_crs("EPSG:4326").total_bounds
        minx, miny, maxx, maxy = bounds
        center = [(miny + maxy) / 2, (minx + maxx) / 2]
        map_obj = folium.Map(location=center, zoom_start=8, tiles="OpenStreetMap", control_scale=True)
        map_obj.fit_bounds([[miny, minx], [maxy, maxx]], padding=(20, 20))
    except Exception:
        center = [-41.0, 174.0]
        map_obj = folium.Map(location=center, zoom_start=5, tiles="OpenStreetMap", control_scale=True)

    # This initial milestone captures clicks. Polygon overlays can be added after confirming
    # the map provider and layer render correctly for the user's data.
    map_result = st_folium(
        map_obj,
        height=560,
        use_container_width=True,
        returned_objects=["last_clicked"],
        key="zone_click_map",
    )
    clicked = map_result.get("last_clicked") if map_result else None
    if clicked:
        lat = clicked.get("lat")
        lon = clicked.get("lng")
        st.subheader("Selected location")
        c1, c2 = st.columns(2)
        c1.metric("Latitude (EPSG:4326)", f"{lat:.6f}")
        c2.metric("Longitude (EPSG:4326)", f"{lon:.6f}")
        try:
            x, y, matches = find_matches(zones, lon, lat)
            st.caption(f"Converted to layer coordinates ({zones.crs}): X = {x:.2f}, Y = {y:.2f}")
            show_matches(matches)
        except Exception as exc:
            st.error(f"Zone lookup failed: {exc}")
    else:
        st.info("Click a point on the map to begin the lookup.")

with tab_coords:
    st.caption("Enter X and Y in EPSG:3857, as in the original app.")
    with st.form("coordinate_lookup"):
        x_in = st.number_input("X coordinate (metres)", value=19449209.0, format="%.2f")
        y_in = st.number_input("Y coordinate (metres)", value=-4405278.0, format="%.2f")
        submitted = st.form_submit_button("Find zone", type="primary")
    if submitted:
        try:
            point_gdf = gpd.GeoDataFrame(
                {"geometry": [Point(float(x_in), float(y_in))]}, crs="EPSG:3857"
            ).to_crs(zones.crs)
            point = point_gdf.geometry.iloc[0]
            valid = zones.geometry.notna() & ~zones.geometry.is_empty
            matches = zones.loc[valid & zones.geometry.covers(point)]
            show_matches(matches)
        except Exception as exc:
            st.error(f"Lookup failed: {exc}")

with st.expander("Setup instructions"):
    st.markdown("""
    1. Keep the `.gdb` folder on the computer or server running this app.
    2. Install dependencies with `pip install -r requirements.txt`.
    3. Set `GDB_PATH` to the `.gdb` folder and `ZONE_LAYER` to the exact layer name.
    4. Run `streamlit run app.py`.

    This first map version uses OpenStreetMap tiles for a simple prototype. Before production,
    choose and configure an approved basemap provider (for example, LINZ Basemaps) and include
    the provider's required attribution and API configuration.
    """)
