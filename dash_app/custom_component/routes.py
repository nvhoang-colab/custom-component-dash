from dataclasses import dataclass, field
from typing import List, Dict
from .base_component import *
from .component_register import component_register
import dash_mantine_components as dmc

import dash_bootstrap_components as dbc
from dash import Dash, html, Input, Output, State, ctx, dcc

@dataclass
@component_register
class NavigationRoute(Route):
    children: FullyStructuredComponent = None

    def __post_init__(self):
        super().__post_init__()

    @property
    def index(self):
        return f"route-{self._index}"

    
    def make_layout(self):
        return html.Div(
                    id=self.index,
                    children=self.children.layout
                )

    def register_callback(self, dash_app: Dash):
        super().register_callback(dash_app)
    
STEP_LABEL = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth"]

@dataclass
@component_register
class SharedDataStep(FullyStructuredComponent):
    data: Dict = field(init=False)
    
    def __post_init__(self):
        super().__post_init__()
    
    def make_layout(self):
        return html.Div(
                    id=self.index,
                    children=self.children.layout
                )
        
    def register_callback(self, dash_app: Dash):
        super().register_callback(dash_app)

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
    
    @property
    def next_id(self):
        return f"next-{self.index}"
    
    @property
    def next_btn(self):
        return dmc.Button("Next", id=self.next_id, disabled=False)
    
    @property
    def back_id(self):
        return f"back-{self.index}"
    
    @property
    def back_btn(self):
        return dmc.Button("Back", id=self.back_id, variant="default", disabled=True)
    
    def stepper_step(self):
        stepper_step = []
        for i, child in enumerate(self.children):
            stepper_step.append(
                    dmc.StepperStep(
                        id = child.nav_id,
                        label=f'{STEP_LABEL[i]}',
                        description=child.name,
                        children=child.layout,
                        allowStepSelect=False,
                    ),
                )
        return stepper_step
    
    def make_layout(self):
        return html.Div([
            dcc.Store(id='session-storage', storage_type='session'),
            dmc.Container(
                [
                    dmc.Stepper(
                        id=self.index,
                        active=self.active,
                        size="sm",
                        children=self.stepper_step()
                    ),
                    dmc.Group(
                        justify="center",
                        mt="xl",
                        children=[
                            self.back_btn,
                            self.next_btn
                        ],
                    ),
                ]
            )
        ])
    
    def update_step(self):
        def update(b, n, cur):
            button_id = ctx.triggered_id
            step = self.active
            if button_id == self.back_id:
                step = step - 1
            if button_id == self.next_id:
                step = step + 1
            self.active = step
            if step == 0:
                return step, True, False
            elif step < self.max_step:
                return step, False, False
            else:
                return step, False, True
        return update
    
    def register_callback(self, dash_app: Dash):
        super().register_callback(dash_app)
        dash_app.callback(
            Output(self.index, "active"),
            Output(self.back_btn, "disabled"),
            Output(self.next_btn, "disabled"),
            Input(self.back_id, "n_clicks"),
            Input(self.next_id, "n_clicks"),
            State(self.index, "active"),
            prevent_initial_call=True,
        )(self.update_step())