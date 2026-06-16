import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time

# Set up the web page title and description
st.set_page_config(page_title="Tablet Tracking Dashboard", layout="centered")
st.title("📱 Tablet Tracking Animation Dashboard")
st.write("Upload a CSV file with your block data format (Time, all Xs, then all Ys) to automatically animate your tracking data.")

# 1. FILE UPLOADER COMPONENT
uploaded_file = st.file_uploader("Drop your tracking CSV or TXT file here", type=["csv", "txt"])

if uploaded_file is not None:
    try:
        # Load data using Pandas
        df = pd.read_csv(uploaded_file)
        
        # 2. PARSE THE BLOCK DATA FORMAT
        # Column 0 is Time. The remaining columns are divided perfectly in half.
        total_cols = len(df.columns)
        coordinate_cols = total_cols - 1
        total_fingers = int(coordinate_cols / 2)
        
        # Calculate row boundaries
        total_rows = len(df)
        
        st.success(f"Successfully loaded data! Found {total_fingers} tracking fingers across {total_rows} frames.")
        
        # --- AUTOMATIC AXIS BOUNDARY CALCULATOR ---
        # Look across columns 1 to (total_fingers) for X max, and remaining for Y max
        x_columns = df.columns[1:total_fingers + 1]
        y_columns = df.columns[total_fingers + 1:]
        
        max_val_x = float(df[x_columns].max().max())
        max_val_y = float(df[y_columns].max().max())
        
        # Add 10% safety padding so tracking dots don't clip at the edges
        max_val_x = ceiling_x = max_val_x * 1.1 if max_val_x > 0 else 100
        max_val_y = ceiling_y = max_val_y * 1.1 if max_val_y > 0 else 100
        
        # 3. TIMELINE SLIDER CONTROL
        # Creates a slider that automatically sets its range matching your file length
        frame_idx = st.slider("Timeline Frames (Scrub manually here)", min_value=0, max_value=total_rows - 1, value=0)
        
        # 4. PLAY ANIMATION CONTROL
        # If the user clicks "Play", this loop auto-increments the frames to play like a video
        play_clicked = st.button("▶ Play Animation")
        
        # A container placeholder so our plot refreshes smoothly in one spot on screen
        plot_placeholder = st.empty()
        
        # Core chart rendering function to keep code clean
        def draw_chart(current_frame):
            fig = go.Figure()
            
            # Fetch the selected row numbers
            row_data = df.iloc[current_frame]
            timestamp = row_data.iloc[0]
            
            # Loop through every finger and grab its specific coordinates
            for i in range(total_fingers):
                x_val = row_data.iloc[1 + i]
                y_val = row_data.iloc[1 + total_fingers + i]
                
                # Check for noise or 0 data to mirror your safety logic
                if x_val > 0.1 and y_val > 0.1:
                    fig.add_trace(go.Scatter(
                        x=[x_val],
                        y=[y_val],
                        mode='markers',
                        name=f'Finger {i}',
                        marker=dict(size=14, symbol='circle')
                    ))
            
            # 5. CHART AXIS AND LAYOUT CONFIGURATION
            fig.update_layout(
                xaxis=dict(range=[0.1, max_val_x], title="X Coordinate"),
                yaxis=dict(range=[max_val_y, 0.1], title="Y Coordinate"), # REVERSED Y-AXIS (Max to Min) for Tablet Grids
                height=500,
                title=f"Frame Timeline View | Time: {timestamp}s (Row {current_frame})",
                showlegend=True
            )
            return fig

        # If Play is pressed, run the animation sequence loop
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