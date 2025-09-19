from flask import Flask

app = Flask(__name__)
'''
It creates an instance of the Flask class, which will be your WSGI (Web Server Gateway Interface) application.
'''
# Creating a basic route
@app.route("/")
def welcome():
    return "Welcome to this Flask Course. Enjoy."

# We can make as many route as possible.

@app.route("/home")
def home():
    return "This is my home page."

@app.route("/index")
def index():
    return "This is index page."

if __name__ == "__main__":
    app.run(debug=True)

'''
In this app.run() have some attributes: 
host - this is nothing but hostname, we can set it.
debug - when this is true, the changes 
'''