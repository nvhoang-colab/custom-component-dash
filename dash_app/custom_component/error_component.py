

from dataclasses import dataclass
from dash import html
import dash_bootstrap_components as dbc

@dataclass
class ErrorComponent:
    error_header: str = "Sorry..."
    error_type: str = ""
    error_tip: str = ""
    error_mess: str = ""
    
    @property
    def layout(self):
        return dbc.Container(
                        [
                            html.H1(self.error_header, className="text-info"),
                            html.Br(),
                            html.H2(self.error_type, className="text-danger"),
                            html.H3(self.error_tip, className="text-warning"),
                            html.Hr(),
                            html.P(self.error_mess),
                        ],
                        fluid=True,
                        className="py-3",
                    )

@dataclass
class PageNotFoundError(ErrorComponent):
    path_name: str = ""
    
    def __post_init__(self):
        self.error_type = "404: Page Not Found."
        self.error_tip = "Please check the url and try again."
        self.error_mess = f"The page /{self.path_name} you are looking for may have been moved, deleted, or possibly nerver existed."