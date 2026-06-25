import streamlit as st
import pandas as pd
import plotly.express as px
import time

st.title("Tablet Tracking System (Robust Header Processing)")

# 1. File Uploader
uploaded_file = st.file_uploader("Upload Raw Tracking Data (.csv)", type=["csv"])

if uploaded_file is not None:
    # Read the full dataset
    df = pd.read_csv(uploaded_file)
    
    # --- NEW HEADER MAPPING LOGIC ---
    # Find all columns that match the 'x' and 'y' followed by a number rule
    x_cols = {}
    y_cols = {}
    
    for col in df.columns:
        col_clean = str(col).strip().lower()
        if col_clean.startswith('x') and col_clean[1:].isdigit():
            finger_id = int(col_clean[1:])
            x_cols[finger_id] = col
        elif col_clean.startswith('y') and col_clean[1:].isdigit():
            finger_id = int(col_clean[1:])
            y_cols[finger_id] = col

    # Only keep finger IDs that have BOTH an X and a Y column mapped
    valid_finger_ids = sorted([fid for fid in x_cols if fid in y_cols])
    
    if not valid_finger_ids:
        st.error("No matching header pairs like 'x0'/'y0' or 'X1'/'Y1' found in this file!")
        st.stop()
        
    # Gather all target coordinate column names to filter data safely
    tracked_columns = [x_cols[fid] for fid in valid_finger_ids] + [y_cols[fid] for fid in valid_finger_ids]

    # --- NEW ROW-SKIPPING LOGIC ---
    # Find rows where all coordinate columns are either 0, NaN, or empty strings
    # We check if the absolute sum of coordinates across our tracked columns is greater than 0
    valid_rows_mask = df[tracked_columns].fillna(0).abs().sum(axis=1) > 0
    filtered_df = df[valid_rows_mask].reset_index(drop=True)
    
    if filtered_df.empty:
        st.warning("All rows in this file contain only 0s or empty coordinates!")
        st.stop()

    # --- ANIMATION & LAYOUT CONTROLS ---
    st.subheader(f"Detected {len(valid_finger_ids)} Tracked Fingers")
    
    # Timeline slider based on the rows that actually contain data
    max_frames = len(filtered_df) - 1
    
    col1, col2 = st.columns([4, 1])
    with col1:
        frame_idx = st.slider("Timeline Frame Index", min_value=0, max_value=max_frames, value=0)
    with col2:
        # Simple Session State toggle to handle basic web play/pause states
        if "playing" not in st.session_state:
            st.session_state.playing = False
            
        if st.button("▶ Play / ⏸ Pause"):
            st.session_state.playing = not st.session_state.playing

    # Loop execution if play state is toggled on
    if st.session_state.playing and frame_idx < max_frames:
        for f in range(frame_idx, max_frames + 1):
            if not st.session_state.playing:
                break
            frame_idx = f
            time.sleep(0.05)
            st.rerun()

    # --- DATA EXTRACTION FOR PRESENTATION ---
    current_row = filtered_df.iloc[frame_idx]
    
    # Try to grab the time index column safely (assumes column 0 if not explicitly named)
    time_col = df.columns[0]
    current_time = current_row[time_col]
    st.write(f"**Current Frame Timestamp:** `{current_time}`")

    # Build a clean dataframe just for this frame to feed into Plotly
    plot_data = []
    for fid in valid_finger_ids:
        x_val = current_row[x_cols[fid]]
        y_val = current_row[y_cols[fid]]
        
        # Don't plot individual missing points if they drop out mid-frame
        if pd.notna(x_val) and pd.notna(y_val) and (x_val != 0 or y_val != 0):
            plot_data.append({
                "Finger": f"Finger {fid}",
                "X": float(x_val),
                "Y": float(y_val)
            })
            
    frame_plot_df = pd.DataFrame(plot_data)

    # --- PLOTLY RENDERING ---
    # Dynamically find the layout bounds based on the max values found in the data
    max_x = filtered_df[[x_cols[fid] for fid in valid_finger_ids]].max().max() * 1.1
    max_y = filtered_df[[y_cols[fid] for fid in valid_finger_ids]].max().max() * 1.1

    if not frame_plot_df.empty:
        fig = px.scatter(
            frame_plot_df, 
            x="X", 
            y="Y", 
            color="Finger",
            range_x=[0, max_x], 
            range_y=[0, max_y],
            title=f"Live Coordinates - Frame {frame_idx}"
        )
        # Flip the Y-axis to match how touch screen coordinate grids work
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No active coordinate data points to draw for this specific frame.")
