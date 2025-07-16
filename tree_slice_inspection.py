import streamlit as st
from PIL import Image, ExifTags
import pandas as pd
import math
import imagehash
import random  # For simulating diameter detection

st.set_page_config(page_title="Smart Tree Inspection", layout="centered")
st.title("🌲 Smart Tree Slice Inspection for ROW Vendors")

# Session data store
if "data" not in st.session_state:
    st.session_state.data = []

# Extract EXIF
def get_exif_data(image):
    try:
        exif = image._getexif()
        if not exif:
            return {}
        return {ExifTags.TAGS.get(tag, tag): value for tag, value in exif.items()}
    except Exception as e:
        st.error(f"Error extracting EXIF data: {e}")
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
    except Exception as e:
        st.error(f"Error extracting GPS data: {e}")
        return None

def compute_hash(image):
    return str(imagehash.phash(image))

def categorize_diameter(d):
    if d >= 40:
        return "A"
    elif d >= 30:
        return "B"
    return "C"

# Upload section
uploaded_files = st.file_uploader("📸 Upload Tree Slice Photos", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
if uploaded_files:
    for uploaded_file in uploaded_files:
        image = Image.open(uploaded_file)
        st.image(image, caption=f"Uploaded Photo: {uploaded_file.name}", use_column_width=True)

        exif_data = get_exif_data(image)
        timestamp = get_timestamp(exif_data)
        gps = get_gps(exif_data)

        if timestamp:
            st.success(f"📅 Timestamp from EXIF: {timestamp}")
        else:
            timestamp = st.text_input("Enter timestamp manually (YYYY-MM-DD HH:MM:SS)")

        tree_id = st.text_input("🌳 Tree ID or Vendor Reference")
        location = st.text_input("📍 Location or ROW")

        # Automatically simulate diameter detection
        diameter_cm = random.uniform(5.0, 50.0)  # Simulate a diameter between 5 and 50 cm
        st.success(f"📏 Automatically Detected Diameter: {diameter_cm:.2f} cm")

        # Calculate area based on the detected diameter
        area = round(math.pi * (diameter_cm / 2) ** 2, 2)
        category = categorize_diameter(diameter_cm)

        if st.button("Analyze & Save"):
            result = {
                "Tree ID": tree_id or "Unknown",
                "Timestamp": timestamp,
                "Location": location,
                "GPS": gps,
                "Diameter (cm)": diameter_cm,
                "Area (cm²)": area,
                "Category": category,
                "Image Hash": compute_hash(image)
            }
            st.session_state.data.append(result)
            st.success("✅ Analysis Saved!")

# Display result table
if st.session_state.data:
    df = pd.DataFrame(st.session_state.data)
    st.subheader("📋 Inspection Results")
    st.dataframe(df)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download CSV", csv, "tree_data.csv", "text/csv")
