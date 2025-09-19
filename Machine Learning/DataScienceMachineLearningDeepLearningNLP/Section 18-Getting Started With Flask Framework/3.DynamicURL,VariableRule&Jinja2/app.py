from flask import Flask, render_template, request, redirect,url_for

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# @app.route("/submt", methods=["GET", "POST"])
# def submt():
#     if request.method == "POST":
#         name = request.form['name']
#         return f"Hello {name}!!!"
#     return render_template("form.html")

# Variable Rule
@app.route("/win/<int:score>")
def win(score):
    return f"Your score is {score}"

@app.route("/result/<int:res>")
def result(res):
    result = "Pass" if res >= 50 else "Fail"
    return render_template("result.html", results=res) 


@app.route("/success/<int:score>")
def success(score):
    res=""
    if score >= 50:
        res = "PASSED"
    else:
        res = "FAILED"

    exp = {'score':score, 'res':res}

    return render_template("pricee.html", results = exp)

@app.route("/successif/<int:score>")
def successif(score):
    return render_template("result.html", results = score)

@app.route("/fail/<int:score>")
def fail(score):
    return render_template("result.html", results = score)

@app.route("/pce", methods=["POST","GET"])
def pce():
    if request.method == "POST":
        try:
            physics = float(request.form.get('physics', 0))
            chemistry = float(request.form.get('chemistry', 0))
            maths = float(request.form.get('maths', 0))
            biology = float(request.form.get('biology', 0))

            total = (physics + chemistry + maths + biology) / 4
            return redirect(url_for("result", res=int(total)))

        except ValueError:
            return "Invalid input! Please enter valid numbers."

    return render_template("getresult.html")


if __name__ == "__main__":
    app.run(debug=True)