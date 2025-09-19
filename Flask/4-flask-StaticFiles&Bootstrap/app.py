from flask import Flask, render_template, url_for, redirect, request

app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/')

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)


## For Bootstrap, you can download the zip file of Bootstrap from the official website and extract it into the static folder. 
## All the css files goes to css folder and js files goes to js folder.