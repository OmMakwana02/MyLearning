import streamlit as st
import pandas as pd
import numpy as np

# Title
st.title('My First Streamlit App')

# Dispaly a simple text
st.write("Here is a simple text.")

# Creating the dataframe
df = pd.DataFrame({
    'first column': [1, 2, 3, 4],
    'second column': [10, 20, 30, 40]
})

# Displaying the datframe
st.write("Here is the DataFrame:")
st.write(df)

# Displaying a line chart

chart_data = pd.DataFrame(
    np.random.randn(20, 3),
    columns=['a', 'b', 'c']
)
st.line_chart(chart_data)
