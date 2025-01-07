import pandas as pd
import folium
from streamlit_folium import st_folium
import streamlit as st

# Load your dataset
url = "https://drive.google.com/uc?id=184Yl7DjboqfU7Qkep36hrslaVwQ3hMCA"
df = pd.read_csv(url)

# Convert 'timestamp' to datetime and floor to nearest minute
df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce').dt.floor('T')

# Add a new column 'box_count' by summing specific columns (e.g., vehicle counts)
df['box_count'] = df.iloc[:, 4:].sum(axis=1)

# Streamlit Sidebar Filters
st.sidebar.header("Filters")
if not df.empty:
    # Date filter
    selected_date = st.sidebar.date_input(
        "Select Date",
        min_value=df['timestamp'].min().date(),
        max_value=df['timestamp'].max().date(),
        value=df['timestamp'].min().date()
    )

    # Filter data by date
    filtered_df = df[df['timestamp'].dt.date == selected_date]

    if not filtered_df.empty:
        # Map Center
        center_lat, center_lon = (
            filtered_df['latitude'].mean(),
            filtered_df['longitude'].mean(),
        )

        # Create the map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

        # Get min and max box_count for color scaling
        min_count, max_count = filtered_df['box_count'].min(), filtered_df['box_count'].max()

        # Function to calculate marker color (gradient from green to red)
        def get_color(box_count):
            norm = (box_count - min_count) / (max_count - min_count + 1e-5)  # Avoid division by zero
            red = int(norm * 255)
            green = int((1 - norm) * 255)
            return f"#{red:02x}{green:02x}00"

        # Add circle markers
        for _, row in filtered_df.iterrows():
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=row['box_count'] * 2 / max_count,  # Scale marker size
                color=get_color(row['box_count']),
                fill=True,
                fill_color=get_color(row['box_count']),
                fill_opacity=0.6,
            ).add_to(m)

        # Render the map
        st.title("Traffic Density Map")
        st.markdown(
            f"### Date: {selected_date}\nBubble size represents traffic density (e.g., `box_count`), with colors ranging from **green** (low density) to **red** (high density)."
        )
        st_folium(m, width=700, height=500)
    else:
        st.error("No data available for the selected date.")
else:
    st.error("No data available.")
