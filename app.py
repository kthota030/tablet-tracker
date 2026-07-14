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
        options=["Scatterplot", "Line Graph"]
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
                        range_x=[0, max_x_all], 
                        range_y=[max_y_all, 0], 
                        template="plotly_white",
                        color_discrete_sequence=px.colors.qualitative.Set1
                    )
                    chart_placeholder.plotly_chart(fig, use_container_width=True, key=f"ch_l_{f}")
                tm.sleep(0.05)
            if st.session_state.current_frame >= max_frames:
                st.session_state.playing = False
                st.session_state.current_frame = 0
                st.rerun()
        else:
            m_frame = slider_placeholder.slider("Timeline", 0, max_frames, st.session_state.current_frame)
            st.session_state.current_frame = m_frame
            current_row = filtered_df.iloc[m_frame]
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
                    range_x=[0, max_x_all], 
                    range_y=[max_y_all, 0], 
                    template="plotly_white",
                    color_discrete_sequence=px.colors.qualitative.Set1
                )
                chart_placeholder.plotly_chart(fig, use_container_width=True, key=f"ch_s_{m_frame}")

    elif analysis_type == "Line Graph":
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            if "playing_line" not in st.session_state:
                st.session_state.playing_line = False
            button_label = "Pause" if st.session_state.playing_line else "Play"
            if st.button(button_label, key="play_line_btn"):
                st.session_state.playing_line = not st.session_state.playing_line
                st.rerun()
        
        with col_btn2:
            if st.button("Export as GIF", key="gif_line"):
                with st.spinner("Loading..."):
                    gif_images = []
                    fig, ax = plt.subplots(figsize=(5, 4), dpi=80)
                    cmap = matplotlib.colormaps['Set1'].resampled(len(valid_finger_ids))
                    
                    for f_idx in range(0, len(filtered_df), skip_factor):
                        ax.clear()
                        ax.set_facecolor('#f8f9fa')
                        ax.set_xlim(0, max_x_all)
                        ax.set_ylim(max_y_all, 0)
                        ax.set_xlabel("X (px)")
                        ax.set_ylabel("Y (px)")
                        current_ts = filtered_df.iloc[f_idx][time_col]
                        ax.set_title(f"Time: {current_ts}")
                        ax.grid(True, linestyle='--', color='#cccccc', alpha=0.7)
                        
                        start_window = max(0, f_idx - 25)
                        history_df = filtered_df.iloc[start_window:f_idx + 1]
                        
                        for idx, fid in enumerate(valid_finger_ids):
                            fx = history_df[x_cols[fid]].values
                            fy = history_df[y_cols[fid]].values
                            valid_mask = (pd.notna(fx)) & (pd.notna(fy)) & (fx != 0) & (fy != 0)
                            
                            if np.any(valid_mask):
                                ax.plot(fx[valid_mask], fy[valid_mask], label=f"Finger {fid}", color=cmap(idx), linewidth=2)
                        
                        handles, labels = ax.get_legend_handles_labels()
                        by_label = dict(zip(labels, handles))
                        if by_label:
                            ax.legend(by_label.values(), by_label.keys(), loc="upper right")
                            
                        frame_buf = io.BytesIO()
                        plt.savefig(frame_buf, format='png', bbox_inches='tight')
                        frame_buf.seek(0)
                        gif_images.append(Image.open(frame_buf))
                        
                    plt.close(fig)
                    if gif_images:
                        gif_buf = io.BytesIO()
                        gif_images[0].save(gif_buf, format='GIF', save_all=True, append_images=gif_images[1:], duration=100, loop=0)
                        st.download_button(label="Download line_trajectory.gif", data=gif_buf.getvalue(), file_name="line_trajectory.gif", mime="image/gif")

        slider_placeholder = st.empty()
        time_placeholder = st.empty()
        chart_placeholder = st.empty()

        if "current_line_frame" not in st.session_state:
            st.session_state.current_line_frame = 0

        if st.session_state.playing_line:
            import time as tm
            for f in range(st.session_state.current_line_frame, max_frames + 1):
                if not st.session_state.playing_line:
                    break
                st.session_state.current_line_frame = f
                slider_placeholder.slider("Timeline", 0, max_frames, f, key=f"line_sl_{f}")
                current_row = filtered_df.iloc[f]
                time_placeholder.write(f"**Current Time:** `{current_row[time_col]}`")
                
                start_frame = max(0, f - 25)
                history_df = filtered_df.iloc[start_frame:f + 1]
                
                line_data = []
                for fid in valid_finger_ids:
                    for _, row in history_df.iterrows():
                        x_val = row[x_cols[fid]]
                        y_val = row[y_cols[fid]]
                        if pd.notna(x_val) and pd.notna(y_val) and (x_val != 0 or y_val != 0):
                            line_data.append({
                                "Finger": f"Finger {fid}",
                                "X Coordinate": float(x_val),
                                "Y Coordinate": float(y_val)
                            })
                
                frame_line_df = pd.DataFrame(line_data)
                if not frame_line_df.empty:
                    fig = px.line(
                        frame_line_df, 
                        x="X Coordinate", 
                        y="Y Coordinate", 
                        color="Finger", 
                        range_x=[0, max_x_all], 
                        range_y=[max_y_all, 0], 
                        template="plotly_white",
                        color_discrete_sequence=px.colors.qualitative.Set1
                    )
                    chart_placeholder.plotly_chart(fig, use_container_width=True, key=f"line_ch_l_{f}")
                tm.sleep(0.05)
            if st.session_state.current_line_frame >= max_frames:
                st.session_state.playing_line = False
                st.session_state.current_line_frame = 0
                st.rerun()
        else:
            m_frame = slider_placeholder.slider("Timeline", 0, max_frames, st.session_state.current_line_frame)
            st.session_state.current_line_frame = m_frame
            current_row = filtered_df.iloc[m_frame]
            time_placeholder.write(f"**Current Time:** `{current_row[time_col]}`")
            
            start_frame = max(0, m_frame - 25)
            history_df = filtered_df.iloc[start_frame:m_frame + 1]
            
            line_data = []
            for fid in valid_finger_ids:
                for _, row in history_df.iterrows():
                    x_val = row[x_cols[fid]]
                    y_val = row[y_cols[fid]]
                    if pd.notna(x_val) and pd.notna(y_val) and (x_val != 0 or y_val != 0):
                        line_data.append({
                            "Finger": f"Finger {fid}",
                            "X Coordinate": float(x_val),
                            "Y Coordinate": float(y_val)
                        })
            frame_line_df = pd.DataFrame(line_data)
            if not frame_line_df.empty:
                fig = px.line(
                    frame_line_df, 
                    x="X Coordinate", 
                    y="Y Coordinate", 
                    color="Finger", 
                    range_x=[0, max_x_all], 
                    range_y=[max_y_all, 0], 
                    template="plotly_white",
                    color_discrete_sequence=px.colors.qualitative.Set1
                )
                chart_placeholder.plotly_chart(fig, use_container_width=True, key=f"line_ch_s_{m_frame}")

    st.write("---")
    st.subheader("Data Analysis Document Generation")
    if st.button("Generate Data Analysis Report"):
        st.markdown("### Documented System Analysis Metrics")
        total_recorded_intervals = len(filtered_df)
        st.write(f"Total trackable timeline entries evaluated: {total_recorded_intervals}")
        
        for fid in valid_finger_ids:
            fx = filtered_df[x_cols[fid]]
            fy = filtered_df[y_cols[fid]]
            active_mask = (pd.notna(fx)) & (pd.notna(fy)) & (fx != 0) & (fy != 0)
            active_count = active_mask.sum()
            
            st.markdown(f"#### Finger {fid} Operational Profile")
            if active_count > 0:
                act_pct = (active_count / total_recorded_intervals) * 100
                mean_x = fx[active_mask].mean()
                mean_y = fy[active_mask].mean()
                st.write(f"Active engagement threshold representation: {act_pct:.2f}% of monitored runtime duration ({active_count} explicit frames verified)")
                st.write(f"Calculated coordinate tracking balance center: X: {mean_x:.1f} px, Y: {mean_y:.1f} px")
            else:
                st.write("No positional touch coordinates captured over the runtime threshold history for this finger identity signature.")
