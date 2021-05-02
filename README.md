# px_speedread

`px_speedread` is a simple Python application designed around [Tim Ferriss' PX Project](https://tim.blog/2009/07/30/speed-reading-and-accelerated-learning/) for speed-reading.

## Setup

There are two quick ways to deploy this app:

1. Use Heroku CLI (with Heroku you can even deploy it to a website really fast). `heroku local` will start a local server if you just want to play around on your own computer.
2. Clone it with `git clone`, run `pip install -e .` at the root of the repository and run the `app.py` script.

## How it works

This app comes with a self-contained SQLite database that will be automatically created for you the first time you run the app. The database will then contain the history of your performance and can be found at `px_speedread/app.db` if you wish to access values directly.

When deployed with Heroku or just when running Python, pay attention to the URL the app is served at and go to that URL to use the web application.

The front-end consists of the following sections:

* **Add Books** - here you can add the books you'll be testing yourself with to the database.
* **Record** - here you will track your each training session.
* **Practice** - here you will find a simple calculator that will tell you how much time you're allowed to spend on one line when reading.
* **Track Performance** - here you can view charts and tables of your performance history for each of the books recorded in the database.
