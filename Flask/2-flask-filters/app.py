from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__, template_folder = 'templates')

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/other')
def other():
  sample = "Hello World"
  return render_template('other.html', sample = sample)

@app.template_filter('reverse')
def reverse_filter(s):
  return s[::-1]

@app.route('/redirect')
def redirect_route():
  return redirect(url_for('other'))

if __name__ == '__main__':
  app.run(debug=True)