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
    
    # --- HEADER MAPPING LOGIC ---
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

    valid_finger_ids = sorted([fid for fid in x_cols if fid in y_cols])
    
    if not valid_finger_ids:
        st.error("No matching header pairs like 'x0'/'y0' or 'X1'/'Y1' found in this file!")
        st.stop()
        
    tracked_columns = [x_cols[fid] for fid in valid_finger_ids] + [y_cols[fid] for fid in valid_finger_ids]

    # --- ROW-SKIPPING LOGIC ---
    valid_rows_mask = df[tracked_columns].fillna(0).abs().sum(axis=1) > 0
    filtered_df = df[valid_rows_mask].reset_index(drop=True)
    
    if filtered_df.empty:
        st.warning("All rows in this file contain only 0s or empty coordinates!")
        st.stop()

    # --- INITIALIZE SESSION STATES ---
    if "playing" not in st.session_state:
        st.session_state.playing = False
    if "current_frame" not in st.session_state:
        st.session_state.current_frame = 0

    st.subheader(f"Detected {len(valid_finger_ids)} Tracked Fingers")
    
    max_frames = len(filtered_df) - 1

    # --- CONTROL BUTTON ---
    # Removed st.rerun() from the click handler to stop full-page resets
    button_label = "⏸ Pause" if st.session_state.playing else "▶ Play"
    if st.button(button_label):
        st.session_state.playing = not st.session_state.playing

    # --- LIVE RENDER CONTAINERS ---
    slider_placeholder = st.empty()
    time_placeholder = st.empty()
    chart_placeholder = st.empty()

    # --- GLOBAL BOUNDS ---
    max_x = filtered_df[[x_cols[fid] for fid in valid_finger_ids]].max().max() * 1.1
    max_y = filtered_df[[y_cols[fid] for fid in valid_finger_ids]].max().max() * 1.1
    time_col = df.columns[0]

    # --- FIXED ANIMATION LOOP ENGINE ---
    # Keeps the loop rolling inside the same screen render cycle to eliminate scrolling jumps
    while st.session_state.playing and st.session_state.current_frame <= max_frames:
        f = st.session_state.current_frame
        
        # 1. Update Slider Element 
        slider_placeholder.slider("Timeline Frame Index", 0, max_frames, f, key=f"play_slider_{f}")
        
        # 2. Update Timestamp Text
        current_row = filtered_df.iloc[f]
        time_placeholder.write(f"**Current Frame Timestamp:** `{current_row[time_col]}`")
        
        # 3. Extract Plotting DataFrame
        plot_data = []
        for fid in valid_finger_ids:
            x_val = current_row[x_cols[fid]]
            y_val = current_row[y_cols[fid]]
            if pd.notna(x_val) and pd.notna(y_val) and (x_val != 0 or y_val != 0):
                plot_data.append({"Finger": f"Finger {fid}", "X": float(x_val), "Y": float(y_val)})
        
        frame_plot_df = pd.DataFrame(plot_data)
        
        # 4. Stream Live Plot Data
        if not frame_plot_df.empty:
            fig = px.scatter(
                frame_plot_df, x="X", y="Y", color="Finger",
                range_x=[0, max_x], range_y=[max_y, 0],
                title=f"Live Coordinates - Frame {f}"
            )
            chart_placeholder.plotly_chart(fig, use_container_width=True, key=f"live_chart_{f}")
        else:
            chart_placeholder.info("No active coordinate data points to draw for this specific frame.")
            
        time.sleep(0.05)
        
        # Advance the counter frame seamlessly
        st.session_state.current_frame += 1
        
        # Handle wrap-around loops if timeline hits the final index row
        if st.session_state.current_frame > max_frames:
            st.session_state.playing = False
            st.session_state.current_frame = 0

    # --- STATIC SELECTION FALLBACK (When Paused) ---
    if not st.session_state.playing:
        manual_frame = slider_placeholder.slider("Timeline Frame Index", 0, max_frames, st.session_state.current_frame)
        st.session_state.current_frame = manual_frame
        
        current_row = filtered_df.iloc[manual_frame]
        time_placeholder.write(f"**Current Frame Timestamp:** `{current_row[time_col]}`")
        
        plot_data = []
        for fid in valid_finger_ids:
            x_val = current_row[x_cols[fid]]
            y_val = current_row[y_cols[fid]]
            if pd.notna(x_val) and pd.notna(y_val) and (x_val != 0 or y_val != 0):
                plot_data.append({"Finger": f"Finger {fid}", "X": float(x_val), "Y": float(y_val)})
        
        frame_plot_df = pd.DataFrame(plot_data)
        
        if not frame_plot_df.empty:
            fig = px.scatter(
                frame_plot_df, x="X", y="Y", color="Finger",
                range_x=[0, max_x], range_y=[max_y, 0],
                title=f"Live Coordinates - Frame {manual_frame}"
            )
            chart_placeholder.plotly_chart(fig, use_container_width=True, key=f"static_chart_{manual_frame}")
        else:
            chart_placeholder.info("No active coordinate data points to draw for this specific frame.")
