from flask import Flask, request, jsonify, render_template
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler 
import pickle




application = Flask(__name__)
app = application

# importing the pkl files
ridge_model = pickle.load(open('models/ridge.pkl', 'rb'))
standard_scaler = pickle.load(open('models/scaler.pkl', 'rb'))

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/predict', methods=['GET', 'POST'])
def predict():
  if request.method == "pOST":
    pass
  else:
    return render_template('predict.html')

if __name__ == "__main__":
  app.run(host="0.0.0.0")