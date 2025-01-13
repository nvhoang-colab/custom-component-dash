from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import gzip
import json
import math
from typing import List

import numpy as np
from .base_component import *
from .component_register import component_register
import dash_mantine_components as dmc

import requests

import pandas as pd
import dash_bootstrap_components as dbc
from dash import Dash, html, Input, Output, State, dcc, ctx
from plotly import graph_objects as go


VALIDATE_SERVER = "http://127.0.0.1:5000"
DATA_SOURCE_SERVER = "http://171.244.37.73:7000"

@dataclass
@component_register
class DistanceMatrixError(FullyStructuredComponent):
    current_id: str = field(init=False, default="")
    error_data: pd.DataFrame = field(init=False, default=None)
    locations: pd.DataFrame = field(init=False, default=None)
    line_fig: go.Figure = field(init=False, default=None)
    map_fig: go.Figure = field(init=False, default=None)
    
    def __post_init__(self):
        super().__post_init__()
    
    def get_data_by_id(self, id):
        res_data = requests.get(fr"{DATA_SOURCE_SERVER}/data/input/{id}")
        if res_data.status_code != 200:
            self.error_data = None
            return
        raw_data = res_data.content
        input_json = json.loads(raw_data.decode('utf-8-sig'))
        validate_api = fr"{VALIDATE_SERVER}/vrp/validate"
        response = requests.post(validate_api, json=input_json)
        if response.status_code != 400:
            self.error_data = None
            return
        content = json.loads(response.content)
        errors = content["distanceErrors"]
        locations = input_json["locations"]
        for loc in locations:
            loc["lTypes"] = loc["lTypes"][-1]
        error_df = pd.DataFrame.from_records(errors)
        self.error_data = error_df.sort_values(by=["minDistance"])
        self.locations = pd.DataFrame.from_records(locations).set_index('locationCode')
    
    @property
    def id_input(self):
        return f"{self._index}-id-input"
    
    @property
    def src_loc_input(self):
        return f"{self._index}-src-input"
    
    @property
    def dest_loc_input(self):
        return f"{self._index}-dest-input"
    
    @property
    def btn_submit_id(self):
        return f"{self._index}-btn-id"
    
    @property
    def btn_submit_loc(self):
        return f"{self._index}-btn-loc"
    
    @property
    def nav(self):
        return html.Div(
            children=[
                dbc.Label("ID:"),
                dbc.Input(id=self.id_input, placeholder="Input Id...", type="text", style={"width":"200px", "margin-bottom":"8px"}),
                dbc.Button(
                    "Submit",
                    id=self.btn_submit_id,
                    type="submit"
                ),
            ],
    )

    @property
    def line_fig_index(self):
        return f"{self._index}-lfig"
    
    @property
    def map_fig_index(self):
        return f"{self._index}-mfig"
    
    @property
    def header(self):
        return html.H1(self.name)
    
    @property
    def footer(self):
        return
    
    @property
    def collapse_id(self):
        return f"{self._index}-collapse"
    
    @property
    def collapse_content(self):
        return dbc.Card(
            [dbc.Form(
                dbc.Row(
                    [
                        dbc.Label("srcCode: ", width="auto"),
                        dbc.Col(
                            dbc.Input(id=self.src_loc_input, type="text", placeholder="Enter Location Code"),
                            className="col-auto me-3",
                        ),
                        dbc.Label("destCode: ", width="auto"),
                        dbc.Col(
                            dbc.Input(id=self.dest_loc_input, type="text", placeholder="Enter Location Code"),
                            className="col-auto me-3",
                        ),
                        dbc.Col(dbc.Button("Get Location Info", id=self.btn_submit_loc, color="primary"), width="auto"),
                    ],
                    className="g-2",
                    )
                ),
            html.Div([
                dbc.Row(
                    [
                        dbc.Col("src lat:"),
                        dbc.Col("dest lat:"),
                    ]),
                dbc.Row(
                    [
                        dbc.Col("src lon:"),
                        dbc.Col("dest lon:"),
                    ]),
                dbc.Row(
                    [
                        dbc.Col("src google maps:"),
                        dbc.Col("dest google maps:"),
                    ]),
                dbc.Row(
                    [
                        dbc.Col("direction:")
                    ])
            ]
            )
        ])
    
    @property
    def body(self):
        return dbc.Card([
            dbc.Collapse(self.collapse_content, id=self.collapse_id, is_open=False, style=dict(margin="8px")),
            dcc.Graph(id=self.line_fig_index, style=dict(margin="8px")),
            dcc.Graph(id=self.map_fig_index, style=dict(margin="8px")),
    ])
    
    def draw_line_chart(self):
        num_error = self.error_data.shape[0]
        fig = go.Figure()
        fig.add_trace(go.Scatter(
                x = list(range(num_error)),
                y = self.error_data["actuallyDisance"],
                mode='lines+markers',
                name='actuallyDisance',
                )
            )
        fig.add_trace(go.Scatter(
                x = list(range(num_error)),
                y = self.error_data["minDistance"],
                mode='lines',
                name='minDistance',
                )
            )
        fig.add_trace(go.Scatter(
                x = list(range(num_error)),
                y = 2*self.error_data["minDistance"],
                mode='lines',
                name='2 x minDistance',
                )
            )
        fig.add_trace(go.Scatter(
                x = list(range(num_error)),
                y = 3*self.error_data["minDistance"],
                mode='lines',
                name='3 x minDistance',
                )
            )
        tick_step = math.ceil(num_error/10)
        tick_vals = list(range(0, num_error, tick_step))
        fig.update_layout(
            title="Error Overview",
            xaxis = dict(
                title_text= 'Location',
                tickmode = 'array',
                tickvals = tick_vals,
                ticktext = tick_vals
            ),
            yaxis = dict(
                title_text='Distance (km)',
                tickmode = 'array',
            ),
        )
        self.line_fig = fig
    
    def draw_map_chart(self):
        fig = go.Figure()
        src_count = self.error_data.srcCode.value_counts()
        dest_count = self.error_data.destCode.value_counts()
        total_error = src_count + dest_count
        self.locations["errorCount"] = total_error
        self.locations["errorCount"] = self.locations.errorCount.fillna(0)
        
        fig.add_trace(go.Scattermapbox(
            lon=self.locations['lng'],
            lat=self.locations['lat'],
            hovertext=self.locations.index,
            hoverinfo='text',
            mode='markers',
            marker=dict(
                size=self.locations["errorCount"],
                sizemin=0.1,
            )
        ))
        fig.update_layout(
            title="Error Map Density",
            paper_bgcolor="LightSteelBlue",
            autosize=False,
            height=900,
            width=900,
            margin=dict(l=20, r=20, t=50, b=50),
            mapbox = {
                'center': {'lon': self.locations.iloc[0].lng, 'lat': self.locations.iloc[0].lat},
                'style': "open-street-map",
                'zoom': 5}
        )
        self.map_fig = fig
     
    def update_figure(self):
        def func(n, id):
            if n and self.current_id != id:
                self.get_data_by_id(id)
                if self.error_data is None:
                    return None, None, False
                self.current_id = id
                self.draw_line_chart()
                self.draw_map_chart()
            return self.line_fig, self.map_fig, True
        return func
    
    def register_callback(self, dash_app: Dash):
        super().register_callback(dash_app)
        dash_app.callback(
            Output(self.line_fig_index, "figure"),
            Output(self.map_fig_index, "figure"),
            Output(self.collapse_id, "is_open"),
            Input(self.btn_submit_id, "n_clicks"),
            State(self.id_input, "value"),
            prevent_initial_call=True,
        )(self.update_figure())