import pandas as pd
import numpy as np
import streamlit as st
# import matplotlib.pylot as plt
from datetime import datetime, timedelta
from streamlit.components.v1 import html
import folium
url = "https://drive.google.com/file/d/184Yl7DjboqfU7Qkep36hrslaVwQ3hMCA/view?usp=sharing"
url='https://drive.google.com/uc?id=' + url.split('/')[-2]
df = pd.read_csv(url)

df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
# Remove seconds from the timestamp
df['timestamp'] = df['timestamp'].dt.floor('T')  # This rounds down to the nearest minute
#create new var box count which is sum of variables from col 4 to end
df.info()
print(df.head())
df['box_count'] = df.iloc[:, 6:].sum(axis=1)
print(df.head())
# Function to determine the color based on box_count
def get_color(box_count, min_count, max_count):
    if max_count - min_count == 0:
        return "#00ff00"  # Return green if all values are the same
    else:
        # Calculate the gradient by interpolating between green and red
        norm = (box_count - min_count) / (max_count - min_count)
        red = int(norm * 255)
        green = int((1 - norm) * 255)
        return f"#{red:02x}{green:02x}00"

st.sidebar.header("Filters")
if not df.empty:
    min_date = df['timestamp'].min().date()
    max_date = df['timestamp'].max().date()
    selected_date = st.sidebar.date_input("Select Date", min_value=min_date, max_value=max_date, value=min_date)

    filtered_df = df[df['timestamp'].dt.date == selected_date]
    
    if not filtered_df.empty:
        # Generating time options
        start_time = datetime.combine(datetime.min.date(), filtered_df['timestamp'].dt.time.min())
        end_time = datetime.combine(datetime.min.date(), filtered_df['timestamp'].dt.time.max())
        time_options = [start_time + timedelta(minutes=4*i) for i in range(((end_time - start_time).seconds // 240) + 1)]
        time_options = [t.time() for t in time_options]  # converting datetime objects back to time

        if 'time_index' not in st.session_state:
            st.session_state.time_index = 0

        current_time = time_options[st.session_state.time_index]
        if st.sidebar.button('Next Time Interval'):
            if st.session_state.time_index < len(time_options) - 1:
                st.session_state.time_index += 1
            else:
                st.session_state.time_index = 0  # Loop back to start
        
        # Display current time interval
        st.sidebar.text(f"Current Time: {current_time.strftime('%H:%M')}")

        # Filter data based on selected time, ignoring seconds
        filtered_df = filtered_df[filtered_df['timestamp'].dt.time == current_time]

        if not filtered_df.empty:
            # Determine the range of box_count for color scaling
            min_count, max_count = filtered_df['box_count'].min(), filtered_df['box_count'].max()

            # Create a map
            m = folium.Map(location=[filtered_df.iloc[0]['latitude'], filtered_df.iloc[0]['longitude']], zoom_start=12)
            
            # Add markers with gradient colors
            for _, row in filtered_df.iterrows():
                folium.CircleMarker(
                    location=[row['latitude'], row['longitude']],
                    radius=row['box_count'],
                    color=get_color(row['box_count'], min_count, max_count),
                    fill=True,
                    fill_color=get_color(row['box_count'], min_count, max_count)
                ).add_to(m)

            # Render the map
            st.header("Interactive Map Visualization")
            st.markdown(f"Date: {selected_date} | Time: {current_time.strftime('%H:%M')}")
            st.markdown("Bubbles represent the box count with a gradient color based on the box count.")
            
            m = m._repr_html_()  # Convert the map to an HTML representation
            html(m, width=700, height=500)
        else:
            st.error("No data available for the selected time.")
    else:
        st.error("No data available for the selected date.")
else:
    st.error("No data available.")



