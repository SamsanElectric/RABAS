
import streamlit as st
from PIL import Image, ExifTags
import math
import pandas as pd
import datetime
import imagehash
import io

st.set_page_config(page_title="Smart Tree Slice Inspection", layout="centered")
st.title("🌲 Smart Tree Slice Inspection App (for ROW Vendors)")
st.write("Upload tree slice photos with ruler, and this tool will auto-classify and track them.")

if "data" not in st.session_state:
    st.session_state.data = []

def get_exif_data(image):
    try:
        exif = image._getexif()
        if not exif:
            return {}
        return {
            ExifTags.TAGS.get(tag, tag): value
            for tag, value in exif.items()
            if tag in ExifTags.TAGS
        }
    except:
        return {}

def get_timestamp(exif_data):
    if 'DateTimeOriginal' in exif_data:
        return exif_data['DateTimeOriginal']
    elif 'DateTime' in exif_data:
        return exif_data['DateTime']
    return None

def get_gps(exif_data):
    gps = exif_data.get('GPSInfo')
    if not gps:
        return None
    try:
        def convert(coord):
            d, m, s = coord
            return d[0]/d[1] + (m[0]/m[1])/60 + (s[0]/s[1])/3600
        lat = convert(gps[2])
        if gps[1] == 'S': lat = -lat
        lon = convert(gps[4])
        if gps[3] == 'W': lon = -lon
        return (lat, lon)
    except:
        return None

def compute_hash(image):
    return str(imagehash.phash(image))

def categorize_diameter(d):
    if d >= 40:
        return "A"
    elif d >= 30:
        return "B"
    return "C"

uploaded_file = st.file_uploader("📸 Upload Tree Slice Photo", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Photo", use_column_width=True)

    exif_data = get_exif_data(image)
    timestamp = get_timestamp(exif_data)
    gps = get_gps(exif_data)

    if timestamp:
        st.success(f"📅 Timestamp from EXIF: {timestamp}")
    else:
        timestamp = st.text_input("Enter photo time manually (YYYY-MM-DD HH:MM:SS)")

    location = st.text_input("📍 Location or ROW Name", "")
    tree_id = st.text_input("🌳 Tree ID or Vendor Reference", "")
    diameter_cm = st.number_input("📏 Measured Diameter from Photo (cm)", min_value=0.0, step=0.1)
    if st.button("Analyze & Save"):
        if diameter_cm > 0:
            area = round(math.pi * (diameter_cm / 2) ** 2, 2)
            category = categorize_diameter(diameter_cm)
            result = {
                "Tree ID": tree_id or "Unknown",
                "Timestamp": timestamp,
                "Location": location,
                "GPS": gps,
                "Diameter (cm)": diameter_cm,
                "Area (cm²)": area,
                "Category": category,
                "Hash": compute_hash(image)
            }
            st.session_state.data.append(result)
            st.success("✅ Analysis Saved!")

if st.session_state.data:
    df = pd.DataFrame(st.session_state.data)
    st.subheader("📋 Inspection Results")
    st.dataframe(df)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download CSV", csv, "tree_data.csv", "text/csv")
