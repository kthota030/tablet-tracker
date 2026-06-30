import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Tablet Tracking System (Prototype)")

uploaded_file = st.file_uploader("Upload Data (.csv)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    

    st.dataframe(df.head())
    
    st.write("### Plot Settings")
    x_axis = st.selectbox("Select X Column", options=df.columns)
    y_axis = st.selectbox("Select Y Column", options=df.columns)
    
    if x_axis and y_axis:
        fig = px.scatter(
            df, 
            x=x_axis, 
            y=y_axis, 
            title="Static Coordinate Plot"
        )
        
        fig.update_yaxes(autorange="reversed")
        
        st.plotly_chart(fig, use_container_width=True)
