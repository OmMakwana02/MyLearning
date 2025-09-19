from flask import Flask, request, render_template

app = Flask(__name__, template_folder = "templates")

@app.route("/")
def index():
  value = "Popat"
  value1 = "Lal"
  mylist = [1,2,3,4,5,6,7,8,9,10]
  return render_template("index.html", list = mylist, val = value, val1 = value1)

@app.route("/home")
def home():
  return "<p>Welcome to Home Page.</p>"

@app.route("/inherit")
def inherit():
  return render_template("inherit.html")



if __name__ == "__main__": 
  app.run(debug=True)