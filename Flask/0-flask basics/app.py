from flask import Flask

app = Flask(__name__)

# @app.route('/')
# def index():
#     return "<h1>Hello, World!</h1>"

@app.route('/')
def index():
    return "<h3>Hello Today we will learn about Routes and URLs</h3>"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555, debug=True)
