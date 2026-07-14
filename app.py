import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import matplotlib
import io
import numpy as np
from PIL import Image

st.title("Touchscreen Tracking")

uploaded_file = st.file_uploader("Upload Data (.csv)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    time_col = df.columns[0]
    
    analysis_type = st.selectbox(
        "Select Graph Type",
        options=["Scatterplot", "Line Graph", "Finger Active Time Breakdown"]
    )
    
    x_cols = {}
    y_cols = {}
    for col in df.columns:
        col_clean = str(col).strip().lower()
        if col_clean.startswith('x') and col_clean[1:].isdigit():
            x_cols[int(col_clean[1:])] = col
        elif col_clean.startswith('y') and col_clean[1:].isdigit():
            y_cols[int(col_clean[1:])] = col
            
    valid_finger_ids = sorted([fid for fid in x_cols if fid in y_cols])
    
    if not valid_finger_ids:
        st.error("No matching header pairs like 'x0'/'y0' found!")
        st.stop()
        
    tracked_columns = [x_cols[fid] for fid in valid_finger_ids] + [y_cols[fid] for fid in valid_finger_ids]
    valid_rows_mask = df[tracked_columns].fillna(0).abs().sum(axis=1) > 0
    filtered_df = df[valid_rows_mask].reset_index(drop=True)
    
    if filtered_df.empty:
        st.warning("No active coordinate data points found!")
        st.stop()

    max_frames = len(filtered_df) - 1
    max_x_all = filtered_df[[x_cols[fid] for fid in valid_finger_ids]].max().max() * 1.1
    max_y_all = filtered_df[[y_cols[fid] for fid in valid_finger_ids]].max().max() * 1.1
    skip_factor = 10 

    if analysis_type == "Scatterplot":
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            if "playing" not in st.session_state:
                st.session_state.playing = False
            button_label = "Pause" if st.session_state.playing else "Play"
            if st.button(button_label, key="play_coord"):
                st.session_state.playing = not st.session_state.playing
                st.rerun()
                
        with col_btn2:
            if st.button("Export as Animated GIF", key="gif_coord"):
                with st.spinner("Loading..."):
                    gif_images = []
                    fig, ax = plt.subplots(figsize=(5, 4), dpi=80)
                    cmap = matplotlib.colormaps['Set1'].resampled(len(valid_finger_ids))
                    
                    for f_idx in range(0, len(filtered_df), skip_factor):
                        current_row = filtered_df.iloc[f_idx]
                        current_ts = current_row[time_col]
                        
                        ax.clear()
                        ax.set_facecolor('#f8f9fa')
                        fig.patch.set_facecolor('#ffffff')
                        ax.set_xlim(0, max_x_all)
                        ax.set_ylim(max_y_all, 0)
                        ax.set_xlabel("X (px)")
                        ax.set_ylabel("Y (px)")
                        ax.set_title(f"Time: {current_ts}")
                        ax.grid(True, linestyle='--', color='#cccccc', alpha=0.7)
                        
                        for idx, fid in enumerate(valid_finger_ids):
                            x_v = current_row[x_cols[fid]]
                            y_v = current_row[y_cols[fid]]
                            if pd.notna(x_v) and pd.notna(y_v) and (x_v != 0 or y_v != 0):
                                ax.scatter(float(x_v), float(y_v), label=f"Finger {fid}", color=cmap(idx), s=60, edgecolors='black')
                        
                        handles, labels = ax.get_legend_handles_labels()
                        by_label = dict(zip(labels, handles))
                        ax.legend(by_label.values(), by_label.keys(), loc="upper right")
                        
                        frame_buf = io.BytesIO()
                        plt.savefig(frame_buf, format='png', bbox_inches='tight')
                        frame_buf.seek(0)
                        gif_images.append(Image.open(frame_buf))
                    
                    plt.close(fig)
                    if gif_images:
                        gif_buf = io.BytesIO()
                        gif_images[0].save(gif_buf, format='GIF', save_all=True, append_images=gif_images[1:], duration=100, loop=0)
                        st.download_button(label="Download tracking_trajectory.gif", data=gif_buf.getvalue(), file_name="tracking_trajectory.gif", mime="image/gif")

        slider_placeholder = st.empty()
        time_placeholder = st.empty()
        chart_placeholder = st.empty()

        if "current_frame" not in st.session_state:
            st.session_state.current_frame = 0

        if st.session_state.playing:
            import time as tm
            for f in range(st.session_state.current_frame, max_frames + 1):
                if not st.session_state.playing:
                    break
                st.session_state.current_frame = f
                slider_placeholder.slider("Timeline", 0, max_frames, f, key=f"play_sl_{f}")
                current_row = filtered_df.iloc[f]
                time_placeholder.write(f"**Current Time:** `{current_row[time_col]}`")
                
                plot_data = []
                for fid in valid_finger_ids:
                    x_val = current_row[x_cols[fid]]
                    y_val = current_row[y_cols[fid]]
                    if pd.notna(x_val) and pd.notna(y_val) and (x_val != 0 or y_val != 0):
                        plot_data.append({"Finger": f"Finger {fid}", "X": float(x_val), "Y": float(y_val)})
                
                frame_plot_df = pd.DataFrame(plot_data)
                if not frame_plot_df.empty:
                    fig = px.scatter(
                        frame_plot_df, 
                        x="X", 
                        y="Y", 
                        color="Finger", 
                        range_x=
