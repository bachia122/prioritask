import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

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


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    cash = db.execute("SELECT cash FROM users WHERE id = :id", id=session['user_id'])
    cash = usd(float("{0:.2f}".format(cash[0]["cash"])))
    stocks = db.execute("SELECT * FROM stocks WHERE id = :id", id=session['user_id'])
    #stock.name = db.execute("SELECT name FROM stocks WHERE id = :id", id = session['user_id'])
    return render_template("portfolio.html", cash=cash, stocks=stocks)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")
    else:
        if not request.form.get("symbol"):
            return apology("missing symbol", 400)

        quote = lookup(request.form.get("symbol"))
        if quote == None:
            return apology("invalid symbol", 400)

        shares = request.form.get("shares")
        if not shares:
            return apology("missing shares", 400)
        if shares.isdigit() == False:
            return apology("invalid shares", 400)

        cost = float(int(shares) * quote['price'])
        cash = db.execute("SELECT cash FROM users WHERE id = :id", id=session['user_id'])
        balance = float(cash[0]['cash'])
        if balance < cost:
            return apology("not enough cash", 400)
        else:
            db.execute("INSERT INTO stocks(id, stock, name, shares, price, total) VALUES(:id, :stock, :name, :shares, :price, :total)",
                id= session['user_id'], stock=quote['symbol'], name=quote['name'], shares=shares, price=usd(quote['price']), total=usd(cost))
            net = float(balance) - float(cost)
        db.execute("UPDATE users SET cash = :cash WHERE id = :id", id=session['user_id'], cash=float("{0:.2f}".format(net)))
        return redirect("/")


@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""
    return jsonify(True)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Return stock quote."""
    if request.method == "GET":
        return render_template("quote.html")
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("missing symbol", 400)

        quote = lookup(request.form.get("symbol"))
        if quote == None:
            return apology("invalid symbol", 400)
        stock_name = quote.get('name')
        stock_symbol = quote.get('symbol')
        stock_price = usd(quote.get('price'))

        return render_template("quote1.html", stock_name=stock_name, stock_symbol=stock_symbol, stock_price=stock_price)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        if not request.form.get("username"):
            return apology("must provide username", 400)
        """Check if username already exists"""
        result = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        if len(result) == 1:
            return apology("username already taken", 400)

        if not request.form.get("password"):
            return apology("must provide password", 400)
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 400)

        """Add registered user to db"""
        session["user_id"] = db.execute("INSERT INTO users(username,hash) VALUES(:username, :hash)", username=request.form.get(
            "username"), hash=generate_password_hash(request.form.get("password")))

        return redirect("/")

        # Redirect user to home page
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "GET":
        stocks = db.execute("SELECT * FROM stocks WHERE id = :id", id=session['user_id'])
        return render_template("sell.html", stocks=stocks)
    else:

        if not request.form.get("symbol"):
            return apology("missing symbol", 400)

        shares = request.form.get("shares")
        if not shares:
            return apology("missing shares", 400)
        if shares.isdigit() == False:
            return apology("invalid shares", 400)
        quote = lookup(request.form.get("symbol"))
        cost = float(int(shares) * quote['price'])
        cash = db.execute("SELECT cash FROM users WHERE id = :id", id=session['user_id'])

        current_shares=db.execute("SELECT shares FROM stocks WHERE id = :id AND stock = :stock", id=session['user_id'], stock=request.form.get("symbol"))
        #check if have enough shares
        myShares = current_shares[0]["shares"]
        if int(myShares) < int(shares):
            return apology("You don't have enough shares")

        transaction_id=db.execute("SELECT * FROM stocks WHERE id = :id AND stock = :stock", id=session['user_id'], stock=request.form.get("symbol"))
        transaction_id = int(transaction_id[0]['transaction'])
        db.execute("DELETE from stocks WHERE transaction = :transaction", transaction=transaction_id)

        balance = float(cash[0]['cash'])
        net = float(balance) + float(cost)
        db.execute("UPDATE users SET cash = :cash WHERE id = :id", id=session['user_id'], cash=float("{0:.2f}".format(net)))
        return redirect("/")



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
