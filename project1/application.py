import os
import requests

from flask import Flask, redirect, render_template ,request, session
from flask import jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# config DATABASE_URL to be URI from heroku
# app.config["DATABASE_URL"] = "postgres://hyruvumxngtjhb:913698cb5bfd82a618b954a3f1384da3d896a81fbd02fb529fe7c3a6421a807b@ec2-54-235-193-0.compute-1.amazonaws.com:5432/daj54d9872japr"

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=["GET", "POST"])
def index():
    """"search page"""
    # if not login then go to login page
    if session.get("userid") is None:
        return redirect("/login")
    
    if request.method == "POST":
        isbn = request.form.get("isbn")
        title = request.form.get("title")
        author = request.form.get("author")
        year = request.form.get("year")

        # search in database, ILIKE for insensitive case LIKE
        search = db.execute("SELECT * FROM books WHERE isbn ILIKE :isbn AND title ILIKE :title AND author ILIKE :author AND year LIKE :year",
                            {"isbn": isbn + "%", "title": title + "%", "author": author + "%", "year": year + "%"}).fetchall()

        return render_template("result.html", search = search)
    else:
        return render_template("index.html")

@app.route("/registration", methods=["GET", "POST"])
def registration():
    """user registration"""
    if request.method == "POST":
        # form validation
        print("validation is begin....")
        if not request.form.get("username") or not request.form.get("password") or not request.form.get("confirmation"):
            return render_template("info.html", content="all field must be filled")
        if request.form.get("password") != request.form.get("confirmation"):
            return render_template("info.html", content="your password doesn't match")
        # check username avaibility
        if db.execute("SELECT * FROM users WHERE username = :username", {"username":request.form.get("username")}).rowcount != 0:
            return render_template("info.html", content="username is not available")
        db.execute("INSERT INTO users(username, password) VALUES(:username, :password)",{
            "username":request.form.get("username"),
            "password":generate_password_hash(request.form.get("password"))
        })
        db.commit()
        return render_template("info.html", content=request.form.get("username")+" registered!")
    else:
        return render_template("registration.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """login with username and password"""

    # forget any userid
    session.clear()

    if request.method == "POST":
        # check username
        username =  db.execute("SELECT * FROM users WHERE username = :username",{
            "username":request.form.get("username")}).fetchone()
    
        # check password
        if username is None or not check_password_hash(username["password"], request.form.get("password")):
            return render_template("info.html", content="invalid username/password")
        # save userid and username
        session["userid"] = username["id"]
        session["username"] = username["username"]
        # return render_template("info.html", content="welcome " + session["username"])
        return redirect("/")
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """logout of website"""
    session.clear()
    return render_template("info.html", content="logged out! see you")


@app.route("/book/<int:id>", methods=["GET", "POST"])
def book_page(id):
    """book page, detail book"""
    # if not login, then login
    if session.get("userid") is None:
        return redirect("/login")
    if request.method == "POST":
        if request.form.get("rating") == "":
            return "give your rating first!"
        
        # user is not allowed to submit multiple review
        multiple = db.execute("SELECT * FROM book_reviews WHERE id_user = :user", {"user":session['userid']}).fetchone()
        if not multiple is None:
            return render_template("info.html", content="you are not allowed to submit multiple reviews")

        # save review
        db.execute("INSERT INTO book_reviews (id_user, id_book, rating, review) VALUES (:user, :book, :rating, :review)",
                    {"user": int(session['userid']), "book": id, 
                        "rating": int(request.form.get("rating")), "review": request.form.get('review') })
        db.commit()
        return redirect("/book/"+ str(id))
    else:
        # show book detail
        book = db.execute("SELECT * FROM books WHERE id = :id", {"id": id}).fetchone()
        reviews = db.execute("SELECT book_reviews.*, username FROM book_reviews LEFT JOIN users ON users.id = book_reviews.id_user WHERE id_book = :id_book", {"id_book": id}).fetchall()
        myreview = db.execute("SELECT * FROM book_reviews WHERE id_user = :user", {"user": session["userid"]}).fetchone()
        rating = db.execute("SELECT AVG(rating) as avg_rating FROM book_reviews WHERE id_book = :book", {"book": id}).fetchone()
        
        if rating == (None,):
            avg_rating = 0
        else:
            avg_rating = "{0:.2f}".format(rating['avg_rating'])
        
        # get JSON from Goodread
        res = requests.get("https://www.goodreads.com/book/review_counts.json", 
                            params={"key": "ruQ33OuhQYdRuYBOjLx84A", "isbns": book['isbn']})
        goodread = res.json()['books'][0]
        goodread['work_ratings_count'] = "{0:,d}".format(goodread['work_ratings_count'])

        return render_template("detail.html", book=book, reviews=reviews, myreview=myreview, rating=avg_rating, goodread=goodread)

@app.route("/api/<isbn>")
def api(isbn):
    """provide data of book in json format"""
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    # If the requested ISBN number isn’t in your database, your website should return a 404 error.
    if book is None:
        return render_template("info.html", content="Eror 404, ISBN is not found")
    rev_count = db.execute("SELECT COUNT(rating) as rev_counting, AVG(rating) as rev_avg FROM book_reviews WHERE id_book = :book", {"book": book['id']}).fetchone()
    data = {
        "title": book['title'],
        "author": book['author'],
        "year": int(book['year']),
        "isbn": book['isbn'],
        "review_count": rev_count['rev_counting'],
        "average_score": float(rev_count['rev_avg'])
    }
    return jsonify(data)

# Import: Provided for you in this project is a file called books.csv, which is a spreadsheet in CSV format of 5000 different books. Each one has an ISBN nubmer, a title, an author, and a publication year. In a Python file called import.py separate from your web application, write a program that will take the books and import them into your PostgreSQL database. You will first need to decide what table(s) to create, what columns those tables should have, and how they should relate to one another. Run this program by running python3 import.py to import the books into your database, and submit this program with the rest of your project code.
# Search: Once a user has logged in, they should be taken to a page where they can search for a book. Users should be able to type in the ISBN number of a book, the title of a book, or the author of a book. After performing the search, your website should display a list of possible matching results, or some sort of message if there were no matches. If the user typed in only part of a title, ISBN, or author name, your search page should find matches for those as well!
# Book Page: When users click on a book from the results of the search page, they should be taken to a book page, with details about the book: its title, author, publication year, ISBN number, and any reviews that users have left for the book on your website.
# Review Submission: On the book page, users should be able to submit a review: consisting of a rating on a scale of 1 to 5, as well as a text component to the review where the user can write their opinion about a book. Users should not be able to submit multiple reviews for the same book.
# Goodreads Review Data: On your book page, you should also display (if available) the average rating and number of ratings the work has received from Goodreads.
# API Access: 
