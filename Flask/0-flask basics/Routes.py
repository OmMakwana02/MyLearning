from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def index():
    return "<h1>Hello people</h1>"

@app.route('/about')
def about():
    return "<h1>Tell something about yourself.</h1>"

@app.route('/greet/<name>') # Here name is a dynamic Variable.
def greet(name):
    return f"Hello {name}"

@app.route('/add/<num1>/<num2>/<int:num3>/<int:num4>')
# ''' Here if we write: @app.route('/add/<num1>/<num2>'), it takes the input value as string.
#  therefore, we specify the datatype of the input.
#  The correct code wil be: @app.route('/add/<int:num1>/<int:num2>')'''
def add(num1, num2, num3, num4):
    return f"The Addition is {num1} + {num2} = {num1+num2} \n The actual Addition is {num3} + {num4} = {num3+num4}"

# Handling URLs
@app.route('/handle_url_parameters')
def handle_url_parameters():
    if 'greeting' in request.args.keys() and 'name' in request.args.keys():
        greeting = request.args['greeting']
        name = request.args.get('name')
        return f"{name} greets you {greeting}"
    else:
        return "A parameter is missing."


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5556,  debug = True)
