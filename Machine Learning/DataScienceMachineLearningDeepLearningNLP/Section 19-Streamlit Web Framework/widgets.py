import streamlit as st
import pandas as pd
import numpy as np

st.title('Streamlit Widgets')

name = st.text_input('Enter your name:')

age = st.slider('Enter your age:', 0, 100, 25)

options = ["Python", "Java", "C++", "JavaScript", "Ruby", "Rust"]
choice = st.selectbox("Choose your fav language:", options)


if name:
    st.write(f"Hello, {name}.")

st.write(f"Your age is {age}.")

st.write(f"Your fav language is {choice}.")

data = {
    'name': ['Tom', 'Nick', 'John', 'Ann'],
    'age': [20, 21, 19, 18],
    'city': ['NY', 'LA', 'SF', 'CHI']
}
df=pd.DataFrame(data)
st.write(df)
# Upload button

uploaded_file = st.file_uploader("Choose a CSV file" ,type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write(df)