import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time

# Set up the web page title and description
st.set_page_config(page_title="Fast Tablet Tracking Dashboard", layout="centered")
st.title("⚡ High-Speed Tablet Tracking Dashboard")
st.write("Optimized for instant file loading and rapid frame updates.")

# Initialize a background "session state" memory to track animation playback status
if "playing" not in st.session_state:
    st.session_state.playing = False
if "current_frame" not in st.session_state:
    st.session_state.current_frame = 0

# 1. FILE UPLOADER COMPONENT
uploaded_file = st.file_uploader("Drop your tracking CSV or TXT file here", type=["csv", "txt"])

if uploaded_file is not None:
    try:
        # Load data instantly using Pandas and cache it
        @st.cache_data
        def load_data(file):
            return pd.read_csv(file)
            
        df = load_data(uploaded_file)
        
        # 2. PARSE THE BLOCK DATA FORMAT
        total_cols = len(df.columns)
        coordinate_cols = total_cols - 1
        total_fingers = int(coordinate_cols / 2)
        total_rows = len(df)
        
        # --- AUTOMATIC AXIS BOUNDARY CALCULATOR ---
        x_columns = df.columns[1:total_fingers + 1]
        y_columns = df.columns[total_fingers + 1:]
        
        max_val_x = float(df[x_columns].max().max())
        max_val_y = float(df[y_columns].max().max())
        
        # Add 10% safety padding
        max_val_x = max_val_x * 1.1 if max_val_x > 0 else 100
        max_val_y = max_val_y * 1.1 if max_val_y > 0 else 100
        
        # 3. INTERFACE CONTROLS
        col1, col2 = st.columns([1, 4])
        with col1:
            # Play / Pause toggle button
            if st.session_state.playing:
                if st.button("⏸ Pause"):
                    st.session_state.playing = False
                    st.rerun()
            else:
                if st.button("▶ Play Animation"):
                    st.session_state.playing = True
                    st.rerun()
                    
        with col2:
            # Manual slider that links directly to our current frame state memory
            frame_idx = st.slider(
                "Timeline Frames", 
                min_value=0, 
                max_value=total_rows - 1, 
                value=st.session_state.current_frame,
                key="slider_frame"
            )
            # Update our state memory if the user manually changes the slider
            if frame_idx != st.session_state.current_frame and not st.session_state.playing:
                st.session_state.current_frame = frame_idx

        # 4. DRAW THE CURRENT ACTIVE FRAME (Super Fast Rendering)
        row_data = df.iloc[st.session_state.current_frame]
        timestamp = row_data.iloc[0]
        
        fig = go.Figure()
        
        for i in range(total_fingers):
            x_val = row_data.iloc[1 + i]
            y_val = row_data.iloc[1 + total_fingers + i]
            
            if x_val > 0.1 and y_val > 0.1:
                fig.add_trace(go.Scatter(
                    x=[x_val],
                    y=[y_val],
                    mode='markers',
                    name=f'Finger {i}',
                    marker=dict(size=14, symbol='circle')
                ))
        
        fig.update_layout(
            xaxis=dict(range=[0.1, max_val_x], title="X Coordinate"),
            yaxis=dict(range=[max_val_y, 0.1], title="Y Coordinate"), # REVERSED Y-AXIS
            height=500,
            title=f"Timeline View | Time: {timestamp}s (Frame {st.session_state.current_frame} / {total_rows - 1})",
            showlegend=True
        )
        
        # Display the chart with a unique key per frame to maximize render efficiency
        st.plotly_chart(fig, use_container_width=True, key=f"chart_{st.session_state.current_frame}")
        
        # 5. ANIMATION LOOP ENGINE
        if st.session_state.playing:
            if st.session_state.current_frame < total_rows - 1:
                # Step forward to the next frame and instantly refresh the page
                st.session_state.current_frame += 1
                time.sleep(0.01) # Controls animation speed (0.01 = very fast)
                st.rerun()
            else:
                # Stop if we hit the end of the file
                st.session_state.playing = False
                st.session_state.current_frame = 0
                st.rerun()
                
    except Exception as e:
        st.error(f"Error parsing data layout: {e}. Ensure your columns are ordered as Time, X0, X1..., Y0, Y1...")
