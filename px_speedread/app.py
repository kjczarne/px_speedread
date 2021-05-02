import dash
import dash_core_components as dcc
import dash_html_components as html
from dash_html_components.Button import Button
from dash_html_components.Label import Label
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
from px_speedread.crypto import decrypt_password, KEY
from px_speedread.utils import (words_per_line, lines_per_page, 
                                avg_words_per_page, words_per_minute, 
                                time_per_line)


# DATABASE =====================================================================

root = Path(os.path.dirname(__file__))
db_file_path = root / 'app.db'


@dataclass
class Tables:
    main: ClassVar[str] = "main"
    auth: ClassVar[str] = "auth"


# open DB connection
db_connection = sqlite3.connect(db_file_path)


# run schema if the tables don't exist already:
with open(Path(os.path.dirname(__file__)) / "schema.sql", 'r') as f:
    schema_string = f.read()

db_connection.execute(schema_string)


# load tables
read_table = lambda table: pd.read_sql_query(
    f"SELECT * FROM {table}", 
    db_connection
)

df_main = read_table(Tables.main)

# ==============================================================================


# BOILERPLATE ==================================================================

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.config.suppress_callback_exceptions = True


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
    html.H1(
        id='main-title', 
        children="px_speedread",
        style=Defaults.heading_style
    ),
    # --- Baseline ---
    html.H2(
        id="baseline-title",
        children="Step 1: Baseline",
        style=Defaults.heading_style
    ),
    daq.BooleanSwitch(id='show-baseline', on=Defaults.bool_switch),
    html.Div(id='baseline-container'),
    # --- Practice ---
    html.H2(
        id="practice-title",
        children="Step 2: Practice",
        style=Defaults.heading_style
    ),
    daq.BooleanSwitch(id='show-practice', on=Defaults.bool_switch),
    html.Div(id='practice-container'),
    # --- Performance ---
    html.H2(
        id="performance-title",
        children="Step 3: Track Performance",
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
    Output('baseline-container', 'children'),
    Input('show-baseline', 'on')
)
def on_show_baseline(is_on):

    cv = html.Div(children=[
        html.Ol(
            children=[
                html.Li(
                    children="Take a book which you will use for testing " + \
                        "(at best a book with little to no pictures)."
                ),
                html.Li(
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
                html.Li(
                    id='num-words-li',
                    children=[
                        dcc.Input(
                            id='num-words-per-line-input'
                        )
                    ]
                ),
                html.Li(
                    id='num-lines-li',
                    children=[
                        dcc.Input(
                            id='num-lines-per-page-input'
                        )
                    ]
                ),
            ]
        ),
        html.P(children=[
            "Your words-per-page count is:",
            html.Label(
                id='wpm-label',
                children=[]
            )
        ])
    ], style=Defaults.center_div_style)
    return on_show(is_on, cv)


@app.callback(
    Output('num-words-li', 'children'),
    Input('num-lines-thresh-input', 'value')
)
def on_thresh_specified_words(thresh):
    return [
        f"Calculate the number of words in {thresh} lines:",
        html.Br(),
        dcc.Input(id='num-words-per-line-input')
    ]


@app.callback(
    Output('num-lines-li', 'children'),
    Input('num-pages-thresh-input', 'value')
)
def on_thresh_specified_lines(thresh):
    return [
        f"Calculate the number of lines in {thresh} pages:",
        html.Br(),
        dcc.Input(id='num-lines-per-page-input')
    ]


@app.callback(
    Output('wpm-label', 'children'),
    Input('num-pages-thresh-input', 'value'),
    Input('num-lines-thresh-input', 'value'),
    Input('num-lines-per-page-input', 'value'),
    Input('num-words-per-line-input', 'value')
)
def calculate_wpm(thresh_pages, thresh_lines, num_lines_per_page, num_words_per_line):
    return html.B(avg_words_per_page(
        int(num_words_per_line) if num_words_per_line else 0,
        int(num_lines_per_page) if num_lines_per_page else 0,
        int(thresh_lines),
        int(thresh_pages)
    ), style=Defaults.heading_style)


@app.callback(
    Output('practice-container', 'children'),
    Input('show-practice', 'on')
)
def on_show_practice(is_on):
    cv = html.Div(children=[
        dcc.Markdown("**Example Markdown Text**")
    ])
    return on_show(is_on, cv)


@app.callback(
    Output('performance-container', 'children'),
    Input('show-performance', 'on')
)
def on_show_performance(is_on):
    cv = html.Div(children=[
        dcc.Markdown("**Example Markdown Text**")
    ])
    return on_show(is_on, cv)


server = app.server

if __name__ == '__main__':
    app.run_server(debug=True)
