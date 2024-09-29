from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import math
from typing import List
from .base_component import *
from .component_register import component_register
import dash_mantine_components as dmc

import pandas as pd
import dash_bootstrap_components as dbc
from dash import Dash, html, Input, Output, State, dcc, ctx
from plotly import graph_objects as go
import psutil


def get_color(percent):
    if percent > 90:
        return 'red'
    elif percent > 70:
        return 'orange'
    elif percent > 50:
        return 'yellow'
    else:
        return 'green'

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
    def current_text(self):
        return f"{self._index}-txt"
    
    @property
    def header(self):
        return html.H1(self.name)
    
    @property
    def nav(self):
        return html.Div([
            html.H4("Current Usage:"),
            html.Div(id=self.current_text)
        ])
    
    @property
    def body(self):
        return html.Div([
            dcc.Graph(id=self.fig_index),
            dcc.Interval(
                id=self.interval_index,
                interval=self.interval,
                n_intervals=0,
                disabled=True
            )
    ])
        
    @property
    def start_btn(self):
        return f"{self._index}-start-btn"
    
    @property
    def stop_btn(self):
        return f"{self._index}-stop-btn"
    
    @property
    def footer(self):
        return html.Div([
            dbc.Button("Start", id=self.start_btn, color="primary", className="me-1", disabled=False),
            dbc.Button("Stop", id=self.stop_btn, color="danger", className="me-1"),
        ])
        
    def update_figure(self):
        def func(n):
            data = self.get_current_data(n)
            cur_time, cur_ram, cur_cpu = data.iloc[-1]
            cur_text = [
                html.Span(f'Current Time: {cur_time}', style=dict(padding='20px', fontSize='24px')),
                html.Span(f'Current Usage Memory: {cur_ram:.2f}%', style=dict(padding='20px', fontSize='24px', color=get_color(cur_ram))),
                html.Span(f'Current Usage CPU: {cur_cpu:.2f}%', style=dict(padding='20px', fontSize='24px', color=get_color(cur_cpu))),
            ]
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
            return fig, cur_text
        return func
    
    def monitor_control(self):
        def func(n_start, n_stop):
            triggered_id = ctx.triggered_id
            if triggered_id == self.start_btn:
                return False, True
            elif triggered_id == self.stop_btn:
                self.data = [None for _ in range(self.max_data_range)]
                return True, False
            return False, True
        return func
        
    def register_callback(self, dash_app: Dash):
        super().register_callback(dash_app)
        dash_app.callback(
            Output(self.fig_index, "figure"),
            Output(self.current_text, "children"),
            Input(self.interval_index, "n_intervals"),
        )(self.update_figure())
        dash_app.callback(
            Output(self.interval_index, "disabled"),
            Output(self.start_btn, "disabled"),
            Input(self.start_btn, "n_clicks"),
            Input(self.stop_btn, "n_clicks"),
            prevent_initial_call=True,
        )(self.monitor_control())