import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import matplotlib
import time
import io
import numpy as np
from PIL import Image

st.title("Tablet Tracking System")

uploaded_file = st.file_uploader("Upload Raw Tracking Data (.csv)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
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

    valid_rows_mask = df[tracked_columns].fillna(0).abs().sum(axis=1) > 0
    filtered_df = df[valid_rows_mask].reset_index(drop=True)
    
    if filtered_df.empty:
        st.warning("All rows in this file contain only 0s or empty coordinates!")
        st.stop()

    if "playing" not in st.session_state:
        st.session_state.playing = False
    if "current_frame" not in st.session_state:
        st.session_state.current_frame = 0

    max_frames = len(filtered_df) - 1

    col_btn1, col_btn2 = st.columns([1, 1])
    
    with col_btn1:
        button_label = "⏸ Pause" if st.session_state.playing else "▶ Play"
        if st.button(button_label):
            st.session_state.playing = not st.session_state.playing
            st.rerun()
            
    with col_btn2:
        max_x_all = filtered_df[[x_cols[fid] for fid in valid_finger_ids]].max().max() * 1.1
        max_y_all = filtered_df[[y_cols[fid] for fid in valid_finger_ids]].max().max() * 1.1
        
        if st.button("📥 Generate and Download Animated GIF"):
            with st.spinner("Compiling animated GIF (this may take a moment)..."):
                gif_images = []
                
                # Setup hidden Matplotlib figure canvas for background rendering
                fig, ax = plt.subplots(figsize=(6, 5), dpi=100)
                cmap = matplotlib.colormaps['viridis'].resampled(len(valid_finger_ids))
                
                for f_idx in range(len(filtered_df)):
                    current_row = filtered_df.iloc[f_idx]
                    
                    # Verify if this specific frame contains any active non-zero data points
                    frame_has_valid_data = False
                    for fid in valid_finger_ids:
                        x_v = current_row[x_cols[fid]]
                        y_v = current_row[y_cols[fid]]
                        if pd.notna(x_v) and pd.notna(y_v) and (x_v != 0 or y_v != 0):
                            frame_has_valid_data = True
                            break
                    
                    # Skip frames that have no visible coordinates
                    if not frame_has_valid_data:
                        continue
                        
                    ax.clear()
                    ax.set_xlim(0, max_x_all)
                    ax.set_ylim(max_y_all, 0)
                    ax.set_xlabel("X Coordinate (px)", fontweight='bold')
                    ax.set_ylabel("Y Coordinate (px)", fontweight='bold')
                    ax.set_title(f"Trajectory Animation - Frame {f_idx}", fontweight='bold')
                    ax.grid(True, linestyle='--', alpha=0.5)
                    
                    # Plot every active finger marker concurrently for this timestamp frame
                    for idx, fid in enumerate(valid_finger_ids):
                        x_v = current_row[x_cols[fid]]
                        y_v = current_row[y_cols[fid]]
                        if pd.notna(x_v) and pd.notna(y_v) and (x_v != 0 or y_v != 0):
                            ax.scatter(float(x_v), float(y_v), label=f"Finger {fid}", color=cmap(idx), s=80, edgecolors='black', zorder=3)
                    
                    # Deduplicate legend items
                    handles, labels = ax.get_legend_handles_labels()
                    by_label = dict(zip(labels, handles))
                    ax.legend(by_label.values(), by_label.keys(), loc="upper right")
                    
                    # Save snapshot to an image frame buffer array
                    frame_buf = io.BytesIO()
                    plt.savefig(frame_buf, format='png', bbox_inches='tight')
                    frame_buf.seek(0)
                    gif_images.append(Image.open(frame_buf))
                
                plt.close(fig)
                
                if gif_images:
                    gif_buf = io.BytesIO()
                    # Compile the image array sequence into a single loopable GIF file container
                    gif_images[0].save(
                        gif_buf,
                        format='GIF',
                        save_all=True,
                        append_images=gif_images[1:],
                        duration=40,  # Speed adjustment: 40ms per frame produces a fast frame rate animation
                        loop=0
                    )
                    gif_buf.seek(0)
                    
                    st.download_button(
                        label="Click here to save tracking_trajectory.gif",
                        data=gif_buf.getvalue(),
                        file_name="tracking_trajectory.gif",
                        mime="image/gif"
                    )
                else:
                    st.error("No valid multi-finger tracking coordinate matrices detected to export.")

    slider_placeholder = st.empty()
    time_placeholder = st.empty()
    chart_placeholder = st.empty()

    max_x = filtered_df[[x_cols[fid] for fid in valid_finger_ids]].max().max() * 1.1
    max_y = filtered_df[[y_cols[fid] for fid in valid_finger_ids]].max().max() * 1.1
    
    time_col = df.columns[0]

    if st.session_state.playing:
        for f in range(st.session_state.current_frame, max_frames + 1):
            if not st.session_state.playing:
                break
            
            st.session_state.current_frame = f
            slider_placeholder.slider("Timeline Frame Index", 0, max_frames, f, key=f"play_slider_{f}")
            
            current_row = filtered_df.iloc[f]
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
                    title=f"Live Coordinates - Frame {f}"
                )
                chart_placeholder.plotly_chart(fig, use_container_width=True, key=f"live_chart_{f}")
            else:
                chart_placeholder.info("No active coordinate data points to draw for this specific frame.")
                
            time.sleep(0.05)
            
        if st.session_state.current_frame >= max_frames:
            st.session_state.playing = False
            st.session_state.current_frame = 0
            st.rerun()

    else:
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
