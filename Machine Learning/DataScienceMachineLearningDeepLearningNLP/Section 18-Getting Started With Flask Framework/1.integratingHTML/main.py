from flask import Flask,render_template
'''
render_template will be responsible for in redirecting a perticular HTML page.
'''

app = Flask(__name__)

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/about")
def about():
    return render_template('about.html')



if __name__ == "__main__":
    app.run(debug=True)