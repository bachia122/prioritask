import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required
# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use Postgres database
db = SQL("postgres://oxcnnvjmwcczza:be72202b1de9728488ebeb9b44c7ba539f43364d0ab0df9a591d74a86c40eb27@ec2-174-129-255-57.compute-1.amazonaws.com:5432/d2en2bca1t0jnh")


@app.route("/")
@login_required
def index():
    """Show task lists"""
    tasks1 = db.execute("SELECT * FROM tasks WHERE id = :id AND level=:level", id=session['user_id'], level=1)
    tasks2 = db.execute("SELECT * FROM tasks WHERE id = :id AND level=:level", id=session['user_id'], level=2)
    tasks3 = db.execute("SELECT * FROM tasks WHERE id = :id AND level=:level", id=session['user_id'], level=3)
    tasks4 = db.execute("SELECT * FROM tasks WHERE id = :id AND level=:level", id=session['user_id'], level=4)
    return render_template("tasks.html", tasks1 = tasks1, tasks2 = tasks2, tasks3 = tasks3, tasks4 = tasks4)


@app.route("/append1", methods=["GET", "POST"])
@login_required
def append():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        if not request.form.get("task"):
            return apology("you failed to input a task")
        else:
            db.execute("INSERT INTO tasks(id, level, task) VALUES(:id, :level, :task)", id=session['user_id'], level=1, task=request.form.get("task"))
            return redirect("/")
        # Redirect user to home page
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("add.html")

@app.route("/append2", methods=["GET", "POST"])
@login_required
def append2():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        if not request.form.get("task"):
            return apology("you failed to input a task")
        else:
            if not request.form.get("date"):
                db.execute("INSERT INTO tasks(id, level, task) VALUES(:id, :level, :task)", id=session['user_id'], level=2, task=request.form.get("task"))
            else:
                db.execute("INSERT INTO tasks(id, level, task) VALUES(:id, :level, :task)", id=session['user_id'], level=2, task=request.form.get("task")+", due "+request.form.get("date"))
            return redirect("/")
        # Redirect user to home page
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("add2.html")

@app.route("/append3", methods=["GET", "POST"])
@login_required
def append3():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        if not request.form.get("task"):
            return apology("you failed to input a task")
        else:
            if not request.form.get("person"):
                db.execute("INSERT INTO tasks(id, level, task) VALUES(:id, :level, :task)", id=session['user_id'], level=3, task=request.form.get("task"))
            else:
                db.execute("INSERT INTO tasks(id, level, task) VALUES(:id, :level, :task)", id=session['user_id'], level=3, task=request.form.get("task")+" c/o "+request.form.get("person"))
            return redirect("/")
        # Redirect user to home page
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("add3.html")

@app.route("/append4", methods=["GET", "POST"])
@login_required
def append4():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        if not request.form.get("task"):
            return apology("you failed to input a task")
        else:
            db.execute("INSERT INTO tasks(id, level, task) VALUES(:id, :level, :task)", id=session['user_id'], level=4, task=request.form.get("task"))
        return redirect("/")
        # Redirect user to home page
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("add4.html")


@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    if request.method == "POST":
        if not request.form.get("level"):
            return apology("you don't have any tasks to delete")
        else:
            db.execute("DELETE FROM tasks WHERE id = :id AND task=:task", id=session['user_id'], task=request.form.get("level"))
            return redirect("/")
    else:
        tasks1 = db.execute("SELECT * FROM tasks WHERE id = :id AND level=:level", id=session['user_id'], level=1)
        tasks2 = db.execute("SELECT * FROM tasks WHERE id = :id AND level=:level", id=session['user_id'], level=2)
        tasks3 = db.execute("SELECT * FROM tasks WHERE id = :id AND level=:level", id=session['user_id'], level=3)
        tasks4 = db.execute("SELECT * FROM tasks WHERE id = :id AND level=:level", id=session['user_id'], level=4)
        return render_template("delete.html", tasks1 = tasks1, tasks2 = tasks2, tasks3 = tasks3, tasks4 = tasks4)




@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""
    return jsonify(True)


@app.route("/info")
def info():
    """Explain how to use the matrix"""
    return render_template("info.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("you must provide your username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("you must provide your password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("your username or password is invalid", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")




@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        if not request.form.get("username"):
            return apology("you must provide a username", 400)
        """Check if username already exists"""
        result = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        if len(result) == 1:
            return apology("that username is already taken", 400)

        if not request.form.get("password"):
            return apology("you must provide your password", 400)
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("the passwords do not match", 400)

        """Add registered user to db"""
        session["user_id"] = db.execute("INSERT INTO users(username,hash) VALUES(:username, :hash)", username=request.form.get(
            "username"), hash=generate_password_hash(request.form.get("password")))

        return redirect("/")

        # Redirect user to home page
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")




def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
