
import base64
from dataclasses import dataclass, field
import io
import json
from numbers import Number
import os
from typing import List

from ..style import *
from .base_component import BaseComponent, CollapsibleComponent, FullyStructuredComponent
from .component_register import component_register
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
from dash import Dash, html, Input, Output, State, dcc, no_update, ctx
import pandas as pd

DATA_PATH = os.getcwd() +'/dash_app/master_data/'

@dataclass
@component_register
class GridCRUD(CollapsibleComponent):
    grid_define_source: str = ''
    data_source: str = ''
    
    @property
    def index(self):
        return f"{self._index}-grid"
    
    @staticmethod
    def extract_col_def(raw_def):
        col_def = {}
        header = raw_def['headerName']
        if raw_def['unit']:
            header = f'{header} ({raw_def["unit"]})'
        col_def["headerName"] = header
        col_def["field"] = raw_def['field']
        col_def["editable"] = True
        if raw_def['data_type'] == "number":
            col_def["valueFormatter"] = {"function": "d3.format(',')(params.value)"}
        return col_def
    
    def get_grid_define(self):
        with open(f'{DATA_PATH}{self.grid_define_source}') as f:
            col_defs = json.load(f)
        columnDefs = []
        for col in col_defs['columnDefines']:
            children = col.get('children', None)
            if children is not None:
                children_def = []
                for child in children:
                    children_def.append(self.extract_col_def(child))
                parent_def = {}
                parent_def['headerName'] = col['headerName']
                parent_def['headerClass'] = 'center-aligned-group-header'
                parent_def['marryChildren'] = True
                parent_def['children'] = children_def
                columnDefs.append(parent_def)
            else:
                no_child_def = self.extract_col_def(col)
                no_child_def['spanHeaderHeight'] = True
                columnDefs.append(no_child_def)
        index_def = {"field": "index", "spanHeaderHeight": True, "checkboxSelection": True}
        columnDefs.insert(0, index_def)
        return columnDefs
    
    def get_data(self):
        row_data = pd.read_csv(f'{DATA_PATH}{self.data_source}')
        row_data['index'] = row_data.index
        return row_data.to_dict("records")
        
    def build_grid(self):
        grid = dag.AgGrid(
            id=self.index,
            rowData=self.get_data(),
            columnDefs=self.get_grid_define(),
            columnSize="autoSize",
            columnSizeOptions={"skipHeader": False},
            dashGridOptions={"rowSelection": "multiple"},
            defaultColDef = {
                "filter": True,
                "resizable": True,
                "sortable": True,
            },
            getRowId="params.data.index",
        )
        return grid
    
    @property
    def add_btn_id(self):
        return f"add-{self._index}"
    
    def add_btn(self):
        return dbc.Button(f"Add {self.name}", id=self.add_btn_id, color="success", className="me-1")
    
    @property
    def delete_btn_id(self):
        return f"delete-{self._index}"
    
    def delete_btn(self):
        return dbc.Button(f"Delete {self.name}", id=self.delete_btn_id, color="danger", className="me-1")
    
    @property
    def import_btn_id(self):
        return f"import-{self._index}"
    
    def import_btn(self):
        return dbc.Button(f"import {self.name}", id=self.import_btn_id, color="warning", className="me-1")
    
    @property
    def grid_output_id(self):
        return f"{self._index}-grid-output"
    
    @property
    def upload_modal_id(self):
        return f"upload-modal-{self._index}"
    
    @property
    def upload_csv_id(self):
        return f"upload-csv-{self._index}"
    
    @property
    def upload_output_id(self):
        return f"upload-output-{self._index}"
    
    def upload_modal(self):
        return dbc.Modal(id=self.upload_modal_id,
                        children=[
                            dcc.Upload(
                                id=self.upload_csv_id,
                                children=html.Div([
                                    'Drag and Drop or ',
                                    html.A('Select a .csv File')
                                ]),
                                style=UPLOAD_STYPE,
                                multiple=False
                            ),
                            html.Div(id=self.upload_output_id),
                        ]
                    )
    
    def make_layout(self):
        return html.Div(
                children=[
                    self.add_btn(),
                    self.delete_btn(),
                    self.import_btn(),
                    self.build_grid(),
                    self.upload_modal(),
                    html.Div(id=self.grid_output_id),
                ]
            )
    
    @property
    def save_btn_id(self):
        return f"save-{self._index}"
    
    def save_btn(self):
        return dbc.Button("Save", id=self.save_btn_id, class_name="mr-auto")
    
    def update_grid(self):
        def func(n_add, n_del, data):
            if ctx.triggered_id == self.add_btn_id:
                new_row = {}
                for key, value in data[0].items():
                    if key == "index":
                        new_row[key] = len(data)
                    elif isinstance(value, Number):
                        new_row[key] = 0
                    elif isinstance(value, str):
                        new_row[key] = ""
                    else:
                        new_row[key] = None
                data.insert(0, new_row)
                return False, data, self.save_btn()
            if ctx.triggered_id == self.delete_btn_id:
                return True, no_update, self.save_btn()
            return no_update, no_update, no_update
        return func
    
    def save_data(self):
        def func(n, row_data):
            if n:
                df = pd.DataFrame.from_dict(row_data)
                df.to_csv(f'{DATA_PATH}{self.data_source}', encoding='utf-8')
                return
            return no_update
        return func
    
    def import_data(self):
        def func(n, content, fn):
            if ctx.triggered_id == self.import_btn_id:
                return True, no_update, no_update
            if content:
                ext = fn.split('.')[-1]
                if ext != 'csv':
                    return True, no_update, "Chi nhan file .csv"
                else:
                    _, content_string = content.split(',')

                    decoded = base64.b64decode(content_string)
                    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
                    rowData=df.to_dict("records")
                    return False, rowData, no_update
            return no_update, no_update, no_update
        return func
    
    def register_callback(self, dash_app: Dash):
        super().register_callback(dash_app)
        
        dash_app.callback(
            Output(self.index, "deleteSelectedRows"),
            Output(self.index, "rowData"),
            Output(self.grid_output_id, "children"),
            Input(self.add_btn_id, "n_clicks"),
            Input(self.delete_btn_id, "n_clicks"),
            State(self.index, "rowData"),
            prevent_initial_call=True,
        )(self.update_grid())
        
        dash_app.callback(
            Output(self.grid_output_id, "children", allow_duplicate=True),
            Input(self.save_btn_id, "n_clicks"),
            State(self.index, "rowData"),
            prevent_initial_call=True,
        )(self.save_data())
        
        dash_app.callback(
            Output(self.upload_modal_id, "is_open", allow_duplicate=True),
            Output(self.index, "rowData", allow_duplicate=True),
            Output(self.upload_output_id, 'children', allow_duplicate=True),
            Input(self.import_btn_id, "n_clicks"),
            Input(self.upload_csv_id, "contents"),
            State(self.upload_csv_id, "filename"),
        prevent_initial_call=True,
        )(self.import_data())
        
    
@dataclass
@component_register
class TabsCollapse(FullyStructuredComponent):
    children: List[CollapsibleComponent] = field(default_factory=list)
    
    @property
    def index(self):
        return f"{self._index}-tabs-collapse"

    @property
    def header(self):
        tabs = []
        for child in self.children:
            child.tab_id = f"{child._index}-tab"
            tabs.append(dbc.Tab(label=child.name.upper(), tab_id=child.tab_id))
        dbc_tabs = dbc.Tabs(tabs, 
                 id=self.index,
                 active_tab=self.children[0].tab_id
            )
        return dbc_tabs

    @property
    def body(self):
        is_open = True
        collapse_content = []
        for child in self.children:
            collapse_content.append(child.collapse_content(is_open))
            is_open = False
        return html.Div(collapse_content)
    
    @property
    def footer(self):
        return 

    def sync_open_tab_collapse(self, child: CollapsibleComponent):
        def func(active_tab):
            return child.tab_id == active_tab
        return func
    
    def register_callback(self, dash_app: Dash):
        super().register_callback(dash_app)
        
        for child in self.children:
            dash_app.callback(
                    Output(child.collapse_id, "is_open"),
                    Input(self.index, "active_tab")
                )(self.sync_open_tab_collapse(child))

@dataclass
@component_register
class FullyStructuredCard(FullyStructuredComponent):
    children: FullyStructuredComponent = None

    @property
    def index(self):
        return f"{self._index}-card"
    
    @property
    def header(self):
        return html.H1(self.name, className="pg-h1")
    
    @property
    def body(self):
        return dbc.Card(
                    [
                        dbc.CardHeader(self.children.header),
                        dbc.CardBody(self.children.body),
                        dbc.CardFooter(self.children.footer)
                    ],
                    id=self.index)