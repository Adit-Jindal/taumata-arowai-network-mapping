import os
import streamlit as st
import geopandas as gpd
from shapely.geometry import Point

st.set_page_config(
    page_title="Water Zone Lookup",
    page_icon="📍",
    layout="centered",
)

st.title("Water Zone Lookup")
st.write(
    "Enter projected coordinates (X, Y) in EPSG:3857 to find "
    "the zone polygon covering that point."
)

st.info(
    "Prototype: this app expects coordinates in EPSG:3857 "
    "(WGS 84 / Pseudo-Mercator), not longitude and latitude."
)

# Configure these values using environment variables, or edit the defaults.
GDB_PATH = os.getenv("GDB_PATH", "path/to/your_data.gdb")
LAYER_NAME = os.getenv("ZONE_LAYER", "your_zone_layer")

@st.cache_data(show_spinner="Loading zone polygons…")
def load_zones(gdb_path: str, layer_name: str):
    if not os.path.exists(gdb_path):
        raise FileNotFoundError(
            f"Geodatabase not found: {gdb_path}. "
            "Set GDB_PATH to the location of your .gdb folder."
        )

    data = gpd.read_file(gdb_path, layer=layer_name)

    if data.empty:
        raise ValueError("The selected layer contains no features.")

    if data.crs is None:
        raise ValueError(
            "The zone layer has no CRS defined. Set the correct CRS "
            "in the source data before running the lookup."
        )

    if "zone" not in data.columns:
        raise ValueError(
            "This example expects a 'zone' field. "
            "Update the code to use the actual field name."
        )

    return data

with st.form("coordinate_lookup"):
    st.subheader("Enter coordinates")
    x = st.number_input(
        "X coordinate (metres)",
        value=19449209.0,
        format="%.2f",
        help="Use the X value shown by QGIS Identify Features.",
    )
    y = st.number_input(
        "Y coordinate (metres)",
        value=-4405278.0,
        format="%.2f",
        help="Use the Y value shown by QGIS Identify Features.",
    )
    submitted = st.form_submit_button("Find zone", type="primary")

if submitted:
    try:
        zones = load_zones(GDB_PATH, LAYER_NAME)

        # Input coordinates are in EPSG:3857. Transform the point
        # if the zone layer uses a different CRS.
        point_gdf = gpd.GeoDataFrame(
            {"geometry": [Point(float(x), float(y))]},
            crs="EPSG:3857",
        ).to_crs(zones.crs)
        point = point_gdf.geometry.iloc[0]

        # covers() includes points on polygon boundaries. Multiple
        # matches are reported rather than silently choosing one.
        valid_geometries = zones.geometry.notna() & ~zones.geometry.is_empty
        matches = zones.loc[
            valid_geometries & zones.geometry.covers(point)
        ]

        if matches.empty:
            st.warning(
                "No zone polygon covers this point. Check the coordinates, "
                "the CRS, and whether the point is within the mapped area."
            )
        else:
            st.success(f"Found {len(matches)} matching feature(s).")

            display_columns = [
                column for column in
                ["OBJECTID", "zone", "pop_regist", "pop_low_de",
                 "pop_mod_de", "pop_high_d", "pop_maori"]
                if column in matches.columns
            ]

            st.subheader("Matching zone details")
            st.dataframe(
                matches[display_columns].reset_index(drop=True),
                use_container_width=True,
                hide_index=True,
            )

            if len(matches) > 1:
                st.warning(
                    "More than one polygon covers this point. "
                    "It may be on a shared boundary or the polygons may "
                    "overlap. Review the matches before assigning a zone."
                )

    except Exception as exc:
        st.error(f"Lookup failed: {exc}")
        st.caption(
            "Check the geodatabase path, layer name, required fields, "
            "and Python dependencies."
        )

with st.expander("Testing example"):
    st.markdown(
        """
        Use 
        x = 19449209.0
        y = -4405278.0
        and expect the zone 'North Shore West' to be returned.
        """
    )

with st.expander("Setup instructions"):
    st.markdown(
        """
        1. Keep the `.gdb` folder on the computer or server running this app.
        2. Install dependencies with `pip install -r requirements.txt`.
        3. Set `GDB_PATH` to the `.gdb` folder and `ZONE_LAYER` to the
           exact layer name inside it.
        4. Run `streamlit run app.py`.
        """
    )
