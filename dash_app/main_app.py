import json
import os

from dataclasses import dataclass, field
from typing import List
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from .custom_component import PageNotFoundError, Route

from .style import *
from flask import Flask

PATH = os.getcwd() + r'/dash_app'
TITLE = 'SuperVRP Dashboard'
APP_NAME = 'SuperVRP Dashboard'
APP_SHORTNAME = 'SuperVRP'
stylesheets=[dbc.themes.CYBORG]

BASE_URL = "/"

@dataclass
class MainApp:
    routes: List[Route]
    flask_app: Flask = True
    name: str = APP_NAME
    short_name: str = APP_SHORTNAME
    title: str = TITLE
    app_path: str = PATH
    app_url: str = BASE_URL
    external_stylesheets: List = field(default_factory=list)
    dash_app: Dash = field(init=False)
    
    def __post_init__(self):
        self.external_stylesheets = stylesheets
        self.dash_app = Dash(
            server=self.flask_app,
            name=self.name,
            url_base_pathname=self.app_url,
            assets_folder=self.assets_path,
            external_stylesheets=self.external_stylesheets,
            title=self.title,
        )
        self.dash_app.layout = dmc.MantineProvider(children=self.layout, theme={"colorScheme": "dark"})
        
    @property
    def assets_path(self):
        return fr"{self.app_path}/assets"
    
    @property
    def content(self):
        return html.Div(id="page-content", style=PAGE_CONTENT_STYLE)
    
    @property
    def nav(self):
        nav_links = []
        for route in self.routes:
            nav_links.append(
                dbc.NavLink(
                    route.name,
                    active="exact",
                    href=f"{self.app_url}{route.href}"
                )
            )
        return dbc.Nav(
                    nav_links,
                    vertical=True,
                    pills=True,
                )
    
    @property
    def sidebar(self):
        return html.Div(
                [
                    html.H2(self.short_name, className="display-5"),
                    html.Hr(),
                    self.nav,
                ],
                style=SIDEBAR_STYLE,
            )

    @property
    def layout(self):
        return html.Div([
                    # dcc.Store(id='session', storage_type='session'),
                    dcc.Location(id="url"),
                    self.sidebar,
                    self.content,
                ])
    
    def render_page_content(self):
        def func(pathname: str):
            if pathname == self.app_url or self.app_url not in pathname:
                return
            pathname = pathname.removeprefix(self.app_url)
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
    component = dmc.MantineProvider(forceColorScheme="dark")
    with open(f'{PATH}/app_schema.json') as f:
        app_schema = json.load(f)
    routes = []
    for route in app_schema["routes"]:
        routes.append(Route.from_config(route))
    main_app = MainApp(flask_app=flask_app, routes=routes)
    main_app.register_callback()
    return main_app.dash_app