import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import time
import io
import imageio.v2 as imageio
import numpy as np

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
        
        fig, ax = plt.subplots(figsize=(6, 5), dpi=300)
        
        cmap = plt.cm.viridis
        colors = [cmap(i) for i in np.linspace(0, 0.8, len(valid_finger_ids))]
        
        for idx, fid in enumerate(valid_finger_ids):
            x_data = filtered_df[x_cols[fid]].values
            y_data = filtered_df[y_cols[fid]].values
            
            valid_pts = (x_data != 0) & (y_data != 0) & (pd.notna(x_data)) & (pd.notna(y_data))
            
            if np.any(valid_pts):
                ax.plot(x_data[valid_pts], y_data[valid_pts], label=f"Finger {fid}", 
                        color=colors[idx], linewidth=1.5, alpha=0.8)
                ax.scatter(x_data[valid_pts][-1], y_data[valid_pts][-1], 
                           color=colors[idx], s=30, edgecolors='black', zorder=5)
        
        ax.set_xlim(0, max_x_all)
        ax.set_ylim(max_y_all, 0)
        ax.set_xlabel("X Coordinate (px)", fontsize=10, fontweight='bold')
        ax.set_ylabel("Y Coordinate (px)", fontsize=10, fontweight='bold')
        ax.set_title("Finger Movement Trajectory Map", fontsize=11, fontweight='bold', pad=10)
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend(frameon=True, facecolor='white', edgecolor='none', fontsize=8)
        plt.tight_layout()
        
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png', dpi=300)
        img_buf.seek(0)
        plt.close(fig)
        
        st.download_button(
            label="📥 Download Journal Figure (High-Res .png)",
            data=img_buf,
            file_name="trajectory_map_figure.png",
            mime="image/png"
        )

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
