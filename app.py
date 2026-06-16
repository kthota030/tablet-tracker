import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time


st.set_page_config(page_title="Tablet Tracking Dashboard", layout="centered")
st.title(" Tablet Tracking Animation Dashboard")
st.write("Upload a CSV file with your block data format (Time, all Xs, then all Ys) to automatically animate your tracking data.")


uploaded_file = st.file_uploader("Drop your tracking CSV or TXT file here", type=["csv", "txt"])

if uploaded_file is not None:
    try:
       
        df = pd.read_csv(uploaded_file)
        
       
        total_cols = len(df.columns)
        coordinate_cols = total_cols - 1
        total_fingers = int(coordinate_cols / 2)
        
       
        total_rows = len(df)
        
        st.success(f"Successfully loaded data! Found {total_fingers} tracking fingers across {total_rows} frames.")
        
      
        x_columns = df.columns[1:total_fingers + 1]
        y_columns = df.columns[total_fingers + 1:]
        
        max_val_x = float(df[x_columns].max().max())
        max_val_y = float(df[y_columns].max().max())
        
      
        max_val_x = ceiling_x = max_val_x * 1.1 if max_val_x > 0 else 100
        max_val_y = ceiling_y = max_val_y * 1.1 if max_val_y > 0 else 100
        
       
        frame_idx = st.slider("Timeline Frames (Scrub manually here)", min_value=0, max_value=total_rows - 1, value=0)
        
        
        play_clicked = st.button("▶ Play Animation")
        
        
        plot_placeholder = st.empty()
        
       
        def draw_chart(current_frame):
            fig = go.Figure()
            
        
            row_data = df.iloc[current_frame]
            timestamp = row_data.iloc[0]
            
           
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
                yaxis=dict(range=[max_val_y, 0.1], title="Y Coordinate"), # REVERSED Y-AXIS (Max to Min) for Tablet Grids
                height=500,
                title=f"Frame Timeline View | Time: {timestamp}s (Row {current_frame})",
                showlegend=True
            )
            return fig

      
        if play_clicked:
            for current_frame in range(0, total_rows):
                fig = draw_chart(current_frame)
                plot_placeholder.plotly_chart(fig, use_container_width=True)
                time.sleep(0.02) # Control playback frame rate speed
            st.info("Animation sequence complete.")
        else:
            # Otherwise, just render whatever frame the manual slider is set to
            fig = draw_chart(frame_idx)
            plot_placeholder.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error parsing data layout: {e}. Ensure your columns are ordered as Time, X0, X1..., Y0, Y1...")
