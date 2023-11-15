from dataclasses import dataclass
from typing import List
from .base_component import BaseComponent
from .component_register import component_register
from .components import *
import dash_mantine_components as dmc

import dash_bootstrap_components as dbc
from dash import Dash, html, Input, Output, State

@dataclass
class Route(BaseComponent):
    href: str = ''

STEP_LABEL = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth"]

@dataclass
@component_register
class StepperNavigationRoute(Route):
    children: List[FullyStructuredComponent] = None
    min_step: int = field(init=False, default=0)
    max_step: int = field(init=False)
    active: int = field(init=False, default=0)
    
    def __post_init__(self):
        super().__post_init__()
        self.max_step = len(self.children)
    
    @property
    def index(self):
        return f"stepper-{self._index}"
    
    def stepper_step(self):
        stepper_step = []
        for i, child in enumerate(self.children):
            stepper_step.append(
                    dmc.StepperStep(
                        id = child.nav_id,
                        label=f'{STEP_LABEL[i]} Step',
                        description=child.name,
                        children=child.layout
                    ),
                )
        return stepper_step
    
    def make_layout(self):
        return html.Div(dmc.Stepper(
                    id=self.index,
                    active=self.active,
                    breakpoint="sm",
                    children=self.stepper_step())
                )
    
    def register_callback(self, dash_app: Dash):
        super().register_callback(dash_app)