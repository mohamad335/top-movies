from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
from dotenv import load_dotenv
import os
load_dotenv()
movies_api_key = os.getenv("MOVIES_API_KEY")
movies_api_url =os.getenv("MOVIES_API_URL")
movies_api_details=os.getenv("MOVIES_API_DETAILS")
movies_url_image= os.getenv("MOVIES_URL_IMAGE")
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

Bootstrap5(app)

# CREATE DB
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies.db"
db = SQLAlchemy(model_class=Base)
db.init_app(app)
# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
with app.app_context():
    db.create_all()

class MoviesRate(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5", validators=[DataRequired()])
    review = StringField("Your Review",validators=[DataRequired()])
    submit = SubmitField("Done")
class AddMovie(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")
# CREATE TABLE

@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    return render_template("index.html",movies=all_movies)
@app.route("/edit", methods=["GET", "POST"])
def update_rate():
    form = MoviesRate()
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", movie=movie, form=form)
@app.route("/delete")
def delete_movie():
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))
@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = AddMovie()
    if form.validate_on_submit():
        response = requests.get(movies_api_url, params={"api_key": movies_api_key, "query": form.title.data})
        data = response.json()["results"]
        return render_template("select.html", options=data)
    return render_template("add.html", form=form)
@app.route("/find")
def find_movie():
    movie_details_url = f"{movies_api_details.replace('movie_id', request.args.get('id'))}"
    response = requests.get(movie_details_url, params={"api_key": movies_api_key})
    data = response.json()
    new_movie = Movie(
        title=data["title"],
        year=data["release_date"].split("-")[0],
        description=data["overview"],
        img_url=f"{movies_url_image}{data['poster_path']}"
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for("home"))
if __name__ == '__main__':
    app.run(debug=True)
