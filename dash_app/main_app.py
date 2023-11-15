import json
import os

from dataclasses import dataclass, field
from typing import List
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from .custom_component.error_component import PageNotFoundError

from .style import *
from flask import Flask
from .custom_component import Route

assets_path = os.getcwd() +'/dash_app/assets'

stylesheets=[dbc.themes.CYBORG]

base_url = "/dash/"

@dataclass
class MainApp:
    routes: List[Route]
    flask_app: Flask = True
    name: str = 'SuperVRP Dashboard'
    short_name: str = 'SuperVRP'
    url_base_pathname: str = base_url
    assets_folder: str = assets_path
    external_stylesheets: List = field(default_factory=list)
    dash_app: Dash = field(init=False)
    
    def __post_init__(self):
        self.external_stylesheets = stylesheets
        self.dash_app = Dash(
            server=self.flask_app,
            name=self.name,
            url_base_pathname=self.url_base_pathname,
            assets_folder=self.assets_folder,
            external_stylesheets=self.external_stylesheets,
        )
        self.dash_app.layout = dmc.MantineProvider(children=self.layout(), theme={"colorScheme": "dark"})
        
    def content(self):
        return html.Div(id="page-content", style=PAGE_CONTENT_STYLE)
    
    def nav(self):
        nav_links = []
        for route in self.routes:
            nav_links.append(
                dbc.NavLink(
                    route.name,
                    active="exact",
                    href=f"{self.url_base_pathname}{route.href}"
                )
            )
        return dbc.Nav(
                    nav_links,
                    vertical=True,
                    pills=True,
                )
    
    def sidebar(self):
        return html.Div(
                [
                    html.H2(self.short_name, className="display-5"),
                    html.Hr(),
                    self.nav(),
                ],
                style=SIDEBAR_STYLE,
            )

    def layout(self):
        return html.Div([dcc.Store(id='session', storage_type='session'), dcc.Location(id="url"), self.sidebar(), self.content()])
    
    def render_page_content(self):
        def func(pathname: str):
            if pathname == self.url_base_pathname or self.url_base_pathname not in pathname:
                return
            pathname = pathname.removeprefix(self.url_base_pathname)
            for route in self.routes:
                if route.href == pathname:
                    return route.layout
            else:
                return PageNotFoundError(path_name=pathname).layout
        return func
    
    def register_callback(self):
        for route in self.routes:
            route.register_callback(self.dash_app)
        self.dash_app.callback(
            Output("page-content", "children"),
            Input("url", "pathname")
        )(self.render_page_content())
        
def create_dash_application(flask_app):
    component = dmc.MantineProvider(withGlobalStyles=True, theme={"colorScheme": "dark"})
    with open(f'dash_app/app_schema.json') as f:
        app_schema = json.load(f)
    routes = []
    for route in app_schema["routes"]:
        routes.append(Route.from_config(route))
    main_app = MainApp(flask_app=flask_app, routes=routes)
    main_app.register_callback()
    return main_app.dash_app