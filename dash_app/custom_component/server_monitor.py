from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import math
from typing import List
from .base_component import *
from .component_register import component_register
import dash_mantine_components as dmc

import pandas as pd
import dash_bootstrap_components as dbc
from dash import Dash, html, Input, Output, State, dcc
from plotly import graph_objects as go
import psutil

    
@dataclass
@component_register
class LiveUpdateFigure(FullyStructuredComponent):
    window_size: int = 360
    interval: int = 10000
    max_ticks: int = 20
    max_data_range: int = field(init=False)
    data: list[dict] = field(init=False)
    
    def __post_init__(self):
        super().__post_init__()
        self.max_data_range = 2*self.window_size
        self.data = [None for _ in range(self.max_data_range)]
    
    
    def get_current_data(self, n):
        now = datetime.now(timezone.utc) + timedelta(seconds=7*3600)
        run_time = now.strftime('%H:%M')
        mem = psutil.virtual_memory()
        men_percent = 100*mem.used/mem.total
        cpu_percent = psutil.cpu_percent(interval=0.1)
        # per_cpu = psutil.cpu_percent(interval=0.1, percpu=True)
        cur_index = n%self.window_size
        self.data[cur_index] = self.data[cur_index + self.window_size ] = {
            "Time": run_time,
            "Memory Usage": men_percent,
            "CPU Usage": cpu_percent,
        }
        cur_data = self.data[cur_index + 1:cur_index + self.window_size + 1]
        df = pd.DataFrame.from_records([_d for _d in cur_data if _d is not None])
        return df

    @property
    def fig_index(self):
        return f"{self._index}-fig"
    
    @property
    def interval_index(self):
        return f"{self._index}-itv"
    
    @property
    def header(self):
        return html.H1(self.name)
    
    @property
    def body(self):
        return html.Div([
            dcc.Graph(id=self.fig_index),
            dcc.Interval(
                id=self.interval_index,
                interval=self.interval,
                n_intervals=0
            )
    ])
        
    def update_figure(self):
        def func(n):
            data = self.get_current_data(n)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                    x = list(range(self.window_size)),
                    y = data["Memory Usage"],
                    mode='lines+markers',
                    name='Memory Usage',
                    )
                )
            fig.add_trace(go.Scatter(
                    x = list(range(self.window_size)),
                    y = data["CPU Usage"],
                    mode='lines+markers',
                    name='CPU Usage')
                )
            tick_step = math.ceil(data.shape[0]/self.max_ticks)
            tick_vals = list(range(0, data.shape[0], tick_step))
            fig.update_layout(
                xaxis = dict(
                    title_text='Time',
                    tickmode = 'array',
                    tickvals = tick_vals,
                    ticktext = data["Time"][tick_vals]
                ),
                yaxis = dict(
                    range=[0, 101],
                    title_text='% Usage',
                    tickmode = 'array',
                    tickvals = list(range(0, 101, 25)),
                ),
            )
            return fig
        return func
        
    def register_callback(self, dash_app: Dash):
        super().register_callback(dash_app)
        dash_app.callback(
            Output(self.fig_index, "figure"),
            Input(self.interval_index, "n_intervals"),
        )(self.update_figure())