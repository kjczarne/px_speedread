from datetime import datetime
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash_html_components.Button import Button
from dash_html_components.Label import Label
from pandas.io.formats import style
import plotly.express as px
import pandas as pd
import numpy as np
from dash.dependencies import Input, Output, State
import dash_table as dtb
import dash_daq as daq
import sqlite3
import os
from pathlib import Path
from dataclasses import dataclass
from typing import ClassVar
import dash_auth
from dash.exceptions import PreventUpdate
from px_speedread.crypto import decrypt_password, KEY
from px_speedread.utils import (f_words_per_line, f_lines_per_page, 
                                avg_words_per_page, words_per_minute, 
                                time_per_line)


# DATABASE =====================================================================

root = Path(os.path.dirname(__file__))
db_file_path = root / 'app.db'


@dataclass
class Tables:
    main: ClassVar[str] = "main"
    auth: ClassVar[str] = "auth"
    books: ClassVar[str] = "books"


# open DB connection
db_connection = sqlite3.connect(db_file_path)


# run schema if the tables don't exist already:
with open(Path(os.path.dirname(__file__)) / "schema.sql", 'r') as f:
    schema_string = f.read()

db_connection.executescript(schema_string)


# load tables
read_table = lambda table, db_connection: pd.read_sql_query(
    f"SELECT * FROM {table}", 
    db_connection
)

df_main = read_table(Tables.main, db_connection)
df_books = read_table(Tables.books, db_connection)


# with sqlite you must pay attention to not modify the db
# in multiple threads at once:
db_connection.close()

# ==============================================================================


# BOILERPLATE ==================================================================

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.config.suppress_callback_exceptions = True


NCLICKS_BOOK_SUBMIT = 0
NCLICKS_EVENT_SUBMIT = 0


@dataclass
class Defaults:
    bool_switch: ClassVar[bool] = False
    heading_style: ClassVar[dict] = {"text-align": "center"}
    link_style: ClassVar[dict] = {"text-align": "center", "font-size": "25px"}
    paragraph_style: ClassVar[dict] = {"text-align": "justify"}
    center_div_style: ClassVar[dict] = {"text-align": "center"}
    centered_notice: ClassVar[dict] = {
        "text-align": "center",
        "font-weight": "bold"
    }


data_table = lambda component_id, df: dtb.DataTable(
    id=component_id,
    columns=[{"name": i, "id": i} for i in df.columns],
    data=df.to_dict('records')
)

# ==============================================================================


# APP ==========================================================================
app.layout = html.Div(children=[
    dcc.Store(id='memory'),
    html.H1(
        id='main-title', 
        children="px_speedread",
        style=Defaults.heading_style
    ),
    # --- Book Add ---
    html.H2(
        id="add-book-title",
        children="Add Books",
        style=Defaults.heading_style
    ),
    daq.BooleanSwitch(id='show-add-books', on=Defaults.bool_switch),
    html.Div(id='add-books-container'),
    # --- Baseline ---
    html.H2(
        id="event-form-title",
        children="Record",
        style=Defaults.heading_style
    ),
    daq.BooleanSwitch(id='show-event-form', on=Defaults.bool_switch),
    html.Div(id='event-form-container'),
    # --- Practice ---
    html.H2(
        id="practice-title",
        children="Practice",
        style=Defaults.heading_style
    ),
    daq.BooleanSwitch(id='show-practice', on=Defaults.bool_switch),
    html.Div(id='practice-container'),
    # --- Performance ---
    html.H2(
        id="performance-title",
        children="Track Performance",
        style=Defaults.heading_style
    ),
    daq.BooleanSwitch(id='show-performance', on=Defaults.bool_switch),
    html.Div(id='performance-container')
], style={"padding": "30px 60px 30px 60px"})


def on_show(is_on: bool, component):
    if is_on:
        return component
    else:
        return []


@app.callback(
    Output('num-words-p', 'children'),
    Input('num-lines-thresh-input', 'value')
)
def on_thresh_specified_words(thresh):
    return [
        f"Calculate the number of words in {thresh} lines:",
        html.Br(),
        dcc.Input(id='num-words-per-line-input')
    ]


@app.callback(
    Output('num-lines-p', 'children'),
    Input('num-pages-thresh-input', 'value')
)
def on_thresh_specified_lines(thresh):
    return [
        f"Calculate the number of lines in {thresh} pages:",
        html.Br(),
        dcc.Input(id='num-lines-per-page-input')
    ]


@app.callback(
    Output('add-books-container', 'children'),
    Input('show-add-books', 'on')
)
def on_show_add_books(is_on):
    cv = html.Div(
        children=[
            html.Label("Book name:"),
            dcc.Input(id='add-book-name'),
            html.Br(),
            html.Label("Book author:"),
            dcc.Input(id='add-book-author'),
            html.Br(),
            html.P(
                children=[
                    "Determine how many lines and pages you want to " + \
                        "use to calculate the average",
                    html.Br(),
                    "Number of lines",
                    html.Br(),
                    dcc.Input(
                        id='num-lines-thresh-input',
                        value=5
                    ),
                    html.Br(),
                    "Number of pages",
                    html.Br(),
                    dcc.Input(
                        id='num-pages-thresh-input',
                        value=5
                    ),
                    html.Br()
                ]
            ),
            html.P(
                id='num-words-p',
                children=[
                    dcc.Input(
                        id='num-words-per-line-input'
                    )
                ]
            ),
            html.P(
                id='num-lines-p',
                children=[
                    dcc.Input(
                        id='num-lines-per-page-input'
                    )
                ]
            ),
            html.Button(id='submit-book', children="Submit"),
            html.Br(),
            html.P(id='book-added')
        ], style=Defaults.center_div_style
    )
    return on_show(is_on, cv)


@app.callback(
    Output('book-added', 'children'),
    Input('submit-book', 'n_clicks'),
    State('add-book-name', 'value'),
    State('add-book-author', 'value'),
    State('num-lines-thresh-input', 'value'),
    State('num-pages-thresh-input', 'value'),
    State('num-lines-per-page-input', 'value'),
    State('num-words-per-line-input', 'value')
)
def on_book_submit(
    nclicks,
    name,
    author,
    thresh_lines,
    thresh_pages,
    lines_in_pages,
    words_in_lines
):
    if nclicks:
        if nclicks > 0:
            wpp = avg_words_per_page(
                int(words_in_lines) if words_in_lines else 0,
                int(lines_in_pages) if lines_in_pages else 0,
                int(thresh_lines) if thresh_lines else 1,
                int(thresh_pages) if thresh_pages else 1
            )
            
            wpl = f_words_per_line(
                int(words_in_lines) if words_in_lines else 0,
                int(thresh_lines) if thresh_lines else 1
            )

            db_connection = sqlite3.connect(db_file_path)
            df_books = read_table(Tables.books, db_connection)

            last_id = df_books['id'].max() if len(df_books['id']) > 0 else -1

            db_connection.executescript(
                f"INSERT INTO {Tables.books} VALUES(" + \
                    f"{last_id + 1}, '{name}', '{author}', " + \
                    f"{thresh_lines}, {thresh_pages}, {wpp}, {wpl});")

            return "Book submitted!"
    return ""


@app.callback(
    Output('wpp-label', 'children'),
    Input('book-select-dropdown', 'value')
)
def get_wpp(existing_book_id):
    db_connection = sqlite3.connect(db_file_path)
    df_books = read_table(Tables.books, db_connection)
    if not existing_book_id is None:
        return html.B(
            df_books['wpp'].loc[existing_book_id] if not df_books['wpp'].empty else 0,
            style=Defaults.heading_style
        )
    else:
        return html.B("")


@app.callback(
    Output('event-form-container', 'children'),
    Input('show-event-form', 'on')
)
def on_show_event_form(is_on):
    db_connection = sqlite3.connect(db_file_path)
    df_books = read_table(Tables.books, db_connection)
    cv = html.Div(children=[
        html.Ol(
            children=[
                html.Li(
                    children=[
                        "Select a book: ",
                        dcc.Dropdown(
                            id='book-select-dropdown',
                            options=[
                                {
                                    'label': name + " by " + author,
                                    'value': _id
                                } for name, author, _id in zip(
                                    df_books['name'], df_books['author'], df_books['id']
                                )
                            ]
                        )
                    ]
                ),
                html.P(children=[
                    "Your words-per-page count is:",
                    html.Label(
                        id='wpp-label',
                        children=[]
                    )
                ]),
                html.Li(
                    id='event-form-test-tresh-li',
                    children=[
                        "Determine how long you want to test yourself " + \
                            "for your reading speed (minutes)",
                        html.Br(),
                        dcc.Input(
                            id='num-minutes-test-thresh-input',
                            value=3
                        ),
                    ]
                ),
                html.Li(
                    id='event-form-test-li',
                    children=[
                        "How many lines did you manage to read?",
                        html.Br(),
                        dcc.Input(
                            id='num-lines-test-input',
                            value=0
                        ),
                    ]
                ),
                html.Button(
                    id='record-submit',
                    children="Submit"
                ),
                html.Div(
                    id='wpm-div',
                    children=[]
                ),
                html.P(id='record-submitted')
            ]
        ),
        
    ], style=Defaults.center_div_style)
    return on_show(is_on, cv)


@app.callback(
    Output('wpm-div', 'children'),
    Input('record-submit', 'n_clicks'),
    State('num-minutes-test-thresh-input', 'value'),
    State('num-lines-test-input', 'value'),
    State('book-select-dropdown', 'value')
)
def calculate_wpm(nclicks, minutes_spent, lines_read, existing_book_id):
    db_connection = sqlite3.connect(db_file_path)
    df_books = read_table(Tables.books, db_connection)
    if not existing_book_id is None:
        wpl = df_books['wpl'].loc[existing_book_id] if not df_books['wpl'].empty else 1
    else:
        wpl = 0
    
    wpm = words_per_minute(
        int(lines_read) if lines_read else 0,
        int(wpl) if wpl else 0,
        int(minutes_spent) if minutes_spent else 0
    )

    if nclicks:
        if nclicks > 0:
            db_connection = sqlite3.connect(db_file_path)
            df_main = read_table(Tables.main, db_connection)

            last_id = df_main['id'].max() if len(df_main['id']) > 0 else -1

            db_connection.executescript(
                f"INSERT INTO {Tables.main} VALUES(" + \
                    f"{last_id + 1}, '{datetime.now()}', {wpm}, " + \
                    f"{existing_book_id});")
            
            return html.B(
                children=[
                    "Your words-per-minute score is:",
                    html.Label(
                        id='wpm-label',
                        children=[wpm]
                    )
                ]
            )
    
    return html.B(
        children=[
            "Your words-per-minute score is..."
        ]
    )
    

@app.callback(
    Output('practice-container', 'children'),
    Input('show-practice', 'on')
)
def on_show_practice(is_on):
    db_connection = sqlite3.connect(db_file_path)
    df_books = read_table(Tables.books, db_connection)
    cv = html.Div(children=[
        html.P("Select a book: "),
        dcc.Dropdown(
            id='select-book-practice',
            options=[
                {
                    'label': name + " by " + author,
                    'value': _id
                } for name, author, _id in zip(
                    df_books['name'], df_books['author'], df_books['id']
                )
            ]
        ),
        html.P(children=[
            "What is your desired words-per-minute target?"
        ]),
        dcc.Input(id='target-wpm-input'),
        html.Div(id='target-wpm-div')
    ], style=Defaults.center_div_style)
    return on_show(is_on, cv)


@app.callback(
    Output('target-wpm-div', 'children'),
    Input('target-wpm-input', 'value'),
    Input('select-book-practice', 'value')
)
def on_target_wpm(target_wpm, existing_book_id):
    db_connection = sqlite3.connect(db_file_path)
    df_books = read_table(Tables.books, db_connection)
    if not existing_book_id is None:
        wpl = df_books['wpl'].loc[existing_book_id] if not df_books['wpl'].empty else 1
    else:
        wpl = 0
    tpl = time_per_line(int(target_wpm), int(wpl)) if target_wpm else 0
    return [
        html.P("You should read one line per: "),
        html.B(f"{tpl} seconds"),
        html.Br(),
        html.B("Rememeber to use a tracker and not read for comprehension.")
    ]


@app.callback(
    Output('performance-container', 'children'),
    Input('show-performance', 'on')
)
def on_show_performance(is_on):
    db_connection = sqlite3.connect(db_file_path)
    df_main = read_table(Tables.main, db_connection)
    df_main['book_id'] = df_main['book_id'].astype(int)
    df_book = read_table(Tables.books, db_connection)
    df_book['id'] = df_book['id'].astype(int)
    df_main = pd.merge(
        df_main,
        df_book,
        left_on="book_id",
        right_on="id"
    )
    
    ids = set(df_main['book_id'])
    sub_dfs = [df_main[df_main['book_id'] == _id] for _id in ids]

    cv = html.Div(children=[
        html.Div(id=f'results-book-{df["book_id"]}', children=[
            html.H3(df["name"].iloc[0] + " by " + df["author"].iloc[0]),
            dcc.Graph(figure=px.line(df, x='date', y='wpm')),
            data_table('history-table', df)
        ], style=Defaults.center_div_style) for df in sub_dfs
    ])
    return on_show(is_on, cv)


server = app.server

if __name__ == '__main__':
    app.run_server(debug=True)
