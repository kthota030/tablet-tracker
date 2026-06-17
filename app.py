import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Set up the web page title and description
st.set_page_config(page_title="Tablet Tracking Dashboard", layout="centered")
st.title("📱 Smooth Tablet Tracking Dashboard")
st.write("Upload a CSV file with your block data format to see a smooth, lag-free animation pipeline.")

# 1. FILE UPLOADER COMPONENT
uploaded_file = st.file_uploader("Drop your tracking CSV or TXT file here", type=["csv", "txt"])

if uploaded_file is not None:
    try:
        # Load data using Pandas
        df = pd.read_csv(uploaded_file)
        
        # 2. PARSE THE BLOCK DATA FORMAT
        total_cols = len(df.columns)
        coordinate_cols = total_cols - 1
        total_fingers = int(coordinate_cols / 2)
        total_rows = len(df)
        
        st.success(f"Successfully loaded data! Found {total_fingers} tracking fingers across {total_rows} frames.")
        
        # --- AUTOMATIC AXIS BOUNDARY CALCULATOR ---
        x_columns = df.columns[1:total_fingers + 1]
        y_columns = df.columns[total_fingers + 1:]
        
        max_val_x = float(df[x_columns].max().max())
        max_val_y = float(df[y_columns].max().max())
        
        # Add 10% safety padding
        max_val_x = max_val_x * 1.1 if max_val_x > 0 else 100
        max_val_y = max_val_y * 1.1 if max_val_y > 0 else 100
        
        # 3. PRE-BUILD THE ANIMATION FRAMES NATIVELY
        animation_frames = []
        for current_frame in range(total_rows):
            row_data = df.iloc[current_frame]
            timestamp = row_data.iloc[0]
            
            frame_traces = []
            # Gather coordinate tracking dots for this specific frame row
            for i in range(total_fingers):
                x_val = row_data.iloc[1 + i]
                y_val = row_data.iloc[1 + total_fingers + i]
                
                if x_val > 0.1 and y_val > 0.1:
                    frame_traces.append(go.Scatter(
                        x=[x_val],
                        y=[y_val],
                        mode='markers',
                        name=f'Finger {i}',
                        marker=dict(size=14, symbol='circle')
                    ))
            
            # Save this snapshot state as an official Plotly Frame configuration
            animation_frames.append(go.Frame(
                data=frame_traces,
                name=str(current_frame),
                layout=go.Layout(title_text=f"Timeline View | Time: {timestamp}s (Frame {current_frame})")
            ))
            
        # 4. INITIAL BASE DATA STATE (Frame 0)
        initial_traces = []
        first_row = df.iloc[0]
        for i in range(total_fingers):
            x_val = first_row.iloc[1 + i]
            y_val = first_row.iloc[1 + total_fingers + i]
            if x_val > 0.1 and y_val > 0.1:
                initial_traces.append(go.Scatter(
                    x=[x_val],
                    y=[y_val],
                    mode='markers',
                    name=f'Finger {i}',
                    marker=dict(size=14, symbol='circle')
                ))
                
        # 5. ASSEMBLE MASTER CHART OBJECT WITH EMBEDDED CONTROLS
        fig = go.Figure(
            data=initial_traces,
            layout=go.Layout(
                xaxis=dict(range=[0.1, max_val_x], title="X Coordinate"),
                yaxis=dict(range=[max_val_y, 0.1], title="Y Coordinate"), # REVERSED Y-AXIS
                height=550,
                title=f"Timeline View | Time: {df.iloc[0].iloc[0]}s (Frame 0)",
                showlegend=True,
                
                # Native, optimized HTML5 playback buttons directly inside the chart canvas
                updatemenus=[dict(
                    type="buttons",
                    buttons=[
                        dict(label="▶ Play",
                             method="animate",
                             args=[None, dict(frame=dict(duration=20, redraw=True), fromcurrent=True)]),
                        dict(label="⏸ Pause",
                             method="animate",
                             args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")])
                    ],
                    direction="left",
                    pad={"r": 10, "t": 10},
                    showactive=False,
                    x=0.1,
                    xanchor="right",
                    y=0,
                    yanchor="top"
                )]
            ),
            frames=animation_frames
        )
        
        # 6. INJECT NATIVE TIMELINE TRACKBAR/SLIDER
        sliders_dict = {
            "active": 0,
            "yanchor": "top",
            "xanchor": "left",
            "currentvalue": {
                "font": {"size": 14},
                "prefix": "Scrubbed Frame: ",
                "visible": True,
                "xanchor": "right"  # FIXED PROP NAME
            },
            "transition": {"duration": 0},
            "pad": {"b": 10, "t": 50},
            "len": 0.9,
            "x": 0.1,
            "y": 0,
            "steps": []
        }
        
        for current_frame in range(total_rows):
            slider_step = {
                "args": [
                    [str(current_frame)],
                    {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}
                ],
                "label": str(current_frame),
                "method": "animate"
            }
            sliders_dict["steps"].append(slider_step)
            
        fig.update_layout(sliders=[sliders_dict])
        
        # Output the master responsive figure asset to screen once
        st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error parsing data layout: {e}. Ensure your columns are ordered as Time, X0, X1..., Y0, Y1...")
