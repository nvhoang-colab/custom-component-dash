from typing import Optional, Union, List
import uuid
from typing_extensions import Self

from dataclasses import dataclass, field
from dash import Dash, html
import dash_bootstrap_components as dbc
from dash.development.base_component import Component
from abc import ABC, abstractproperty, abstractmethod
from .component_register import COMPONENT_CLASS, component_register

@dataclass
class MetaComponent(ABC):
    name: str
    _index: str
    children: Optional[Union[Self, List[Self]]]
    layout: Component
    
    @property
    def index(self):
        pass
    
    @abstractmethod
    def make_layout():
        pass
    
@dataclass
class BaseComponent(MetaComponent):
    name: str = ''
    _index: str = ''
    children: Optional[Union[Self, List[Self]]] = None
    layout: Component = field(init=False)
    
    def __post_init__(self):
        self.layout = self.make_layout()
    
    @property
    def index(self):
        return self._index
    
    @index.setter
    def index(self, _value):
        self._index = _value
    
    def make_layout(self) -> Component:
        return html.Div(f"Component {self.__class__.__name__}:\nname = {self.name}, index = {self.index}", id=self.index)
    
    @classmethod
    def from_config(cls, config):
        cls_type = config.pop("type", None)
        if cls_type is not None:
            cls = COMPONENT_CLASS.get(cls_type, BaseComponent)
        children_config = config.pop("children", "")
        if isinstance(children_config, str):
            children = BaseComponent('', str(uuid.uuid4()))
        elif isinstance(children_config, List):
            children = []
            for child_config in children_config:
                child_type = child_config.pop("type")
                child_cls = COMPONENT_CLASS.get(child_type, BaseComponent)
                child_config["_index"] = f'{config["_index"]}-{child_config["_index"]}'
                children.append(child_cls.from_config(child_config))
        else:
            children_type = children_config.pop("type")
            children_cls = COMPONENT_CLASS.get(children_type, BaseComponent)
            children = children_cls.from_config(children_config)
        return cls(children=children, **config)

    def register_callback(self, dash_app: Dash):
        if self.children is None or isinstance(self.children, str):
            return
        elif isinstance(self.children, List):
            for child in self.children:
                child.register_callback(dash_app)
        else:
            self.children.register_callback(dash_app)
            

@dataclass
class Route(BaseComponent):
    href: str = ''

@dataclass
class CollapsibleComponent(BaseComponent):
    collapse_id: str = ''
    
    @property
    def index(self):
        return self._index
    
    @index.setter
    def index(self, _value):
        self.collapse_id = f"{_value}-collapse"
        self._index = _value
    
    def collapse_content(self, is_open: bool = False):
        return dbc.Collapse(self.layout, id=self.collapse_id, is_open=is_open)
    
@dataclass
@component_register
class FullyStructuredComponent(BaseComponent):
    header_id: str = ''
    nav_id: str = ''
    body_id: str = ''
    footer_id: str = ''
    
    def __post_init__(self):
        self.index = self._index
        self.layout = self.make_layout()
    
    @property
    def index(self):
        return self._index
    
    @index.setter
    def index(self, _value):
        self.header_id = f"{_value}-header"
        self.nav_id = f"{_value}-nav"
        self.body_id = f"{_value}-body"
        self.footer_id = f"{_value}-footer"
        self._index = _value

    @property
    def header(self):
        return html.Div(f"This is header of {self.name} {self.__class__.__name__}", id=self.header_id)

    @property
    def nav(self):
        return html.Div(f"This is nav of {self.name} {self.__class__.__name__}", id=self.nav_id)
    
    @property
    def body(self):
        return html.Div(f"This is body of {self.name} {self.__class__.__name__}", id=self.body_id)
    
    @property
    def footer(self):
        return html.Div(f"This is footer of {self.name} {self.__class__.__name__}", id=self.footer_id)

    def make_layout(self):
        return html.Div([
            self.header,
            self.nav,
            self.body,
            self.footer,
        ])
    