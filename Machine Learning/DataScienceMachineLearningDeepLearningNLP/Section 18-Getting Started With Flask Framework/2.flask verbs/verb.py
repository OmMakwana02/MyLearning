from flask import Flask,render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

    # Note: If we dont write anything, by default it is going to be GET request. But if we want to specify, we can do that as well.
    # Get is the default method, if we search google.com on our browser, when we hit this perticular URL, it is going to get mapped with the web server and the server is going to interact with the google web application and the default content is displayed on the browser. This is actually a GET request.


@app.route("/contact", methods=["GET","POST"])
def contact():
    if request.method ==  "POST":
        name = request.form['name']
        return f"Hello {name}!!!"
    return render_template("contact.html")
    
    # And now if we search anything on the browser, for eg. "python", it means we are giving some query, and based on that query im getting some resposne. This is actually a POST request. Here some input is going to the web server and based on that it will go ahead and interact with the web application, which in turn will communicate with the database and get the information back to the user. 

if __name__ == "__main__":
    app.run(debug=True)