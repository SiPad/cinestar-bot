import requests
import urllib.request
from pyquery import PyQuery
from redmail import outlook

from settings import SMTP_USER, SMTP_PASS, RECEIVERS

# Location doesn't matter. Movies of the week are same everywhere
URL = "https://www.cinestar.de/kino-bremen-kristall-palast/film-der-woche"


class Movie:
    def __init__(self, movie_id, title, poster_url):
        self.movie_id = movie_id
        self.title = title
        self.poster_url = poster_url


def query_movie_information(movie_id):
    response = requests.get(
        f"https://www.cinestar.de/api/show/{movie_id}?appVersion=1.5.3"
    )
    json = response.json()
    title = json["title"]
    # The URL from the API contains a quite small picture
    # We want a big one
    poster_url = json["poster"].replace("/poster_tile/", "/web_l/")
    return Movie(movie_id, title, poster_url)


def get_movies_of_the_week(webpage):
    ids_text: str = webpage("[data-show-ids]")[0].attrib["data-show-ids"]
    ids = map(int, ids_text.split(","))
    movies = map(query_movie_information, ids)
    return list(movies)


def write_new_date(date):
    with open("cinestar-date", "w") as f:
        return f.write(date)


def get_last_date():
    try:
        with open("cinestar-date", "r") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def get_webpage():
    pq = PyQuery(URL)
    return pq


def get_date_text(webpage: PyQuery):
    date_text = webpage("div.subHeadline")[0].text.strip()
    return date_text


def send_mail(movie: Movie, date: str, cover_file: str):
    outlook.username = SMTP_USER
    outlook.password = SMTP_PASS

    outlook.send(
        sender=f"Cinestar Bot <{outlook.username}>",
        subject="Film der Woche",
        receivers=RECEIVERS,
        html=f"""
        <h2>{movie.title}</h2>
        <h3>{date}</h3>
        {{{{ my_image }}}}
    """,
        body_images={
            "my_image": f"{cover_file}",
        },
    )


def main():
    webpage = get_webpage()
    date = get_date_text(webpage)
    last_date = get_last_date()
    if date != last_date:
        write_new_date(date)
        movies = get_movies_of_the_week(webpage)

        for i, movie in enumerate(movies):
            cover_file = f"movie-{i}.jpg"
            urllib.request.urlretrieve(movie.poster_url, cover_file)
            send_mail(movie, date, cover_file)


if __name__ == "__main__":
    main()
