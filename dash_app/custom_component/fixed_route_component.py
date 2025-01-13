import base64
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import gzip
import io
import json
import math
import time
from typing import List

import numpy as np
from .base_component import *
from .routes import SharedDataStep
from .component_register import component_register
import dash_mantine_components as dmc

import requests

import pandas as pd
import dash_bootstrap_components as dbc
from dash import Dash, html, Input, Output, State, dcc, ctx, no_update
from plotly import graph_objects as go

VENDOR_CONVERT = {
    "NL": "nhat long",
    "TC": "thanh cong",
    "HV": "heo vang",
    "THL": "thai ha",
    "COL": "columbus"
}

CAPACITY_CONVERT = {
    "VC": "2.0",
    "VA": "1.25",
    "VD": "3.5",
    "VE": "5.0",
    "VG": "7.0",
    "VQ": "9.0",
    "VI": "11.0",
    "VK": "15.0",
    "VU": "2.0",
    "VV": "3.5",
    "VN": "Cont",
    "VR": "VAN",
}

@dataclass
@component_register
class JsonUploader(SharedDataStep):
    
    def __post_init__(self):
        super().__post_init__()
    
    @property
    def upload_id(self):
        return f'uploader-{self.index}'
    
    @property
    def upload_output(self):
        return f'output-{self.index}'
    
    def make_layout(self):
        return html.Div([
            dcc.Upload(
                id=self.upload_id,
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select JSON Input')
                ]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px'
                },
                multiple=False,
            ),
            html.Div(id=self.upload_output),
        ])
    
    @staticmethod
    def extract_item(item: dict):
        piece_weight = item["weight"]/item["quantity"]
        piece_cbm = item["cbm"]/item["quantity"]
        piece_cost = item["itemCost"]/item["quantity"]
        return dict(
            quantityPerBox=item["quantityPerBox"],
            weight=piece_weight,
            cbm=piece_cbm,
            cost=piece_cost,
            size=item["size"],
            iType=item["iType"],
            quantityPerPallet=item["quantityPerPallet"],
        )
    
    def parse_contents(self, contents, filename):
        content_type, content_string = contents.split(',')

        decoded = base64.b64decode(content_string)
        try:
            if 'json' in content_type:
                data = json.loads(decoded.decode('utf-8-sig'))
                requests = data.get("requests", [])
                master_requests = {}
                master_items = {}
                for req in requests:
                    req["itemGroupList"] = []
                    req["orderCode"] = req["orderCode"].split("_")[0]
                    items = req.pop("items")
                    new_items = {}
                    for it in items:
                        sku = it["iType"]["typeOfItemByStackRule"]
                        if sku not in master_items:
                            master_items[sku] = self.extract_item(it)
                        new_items[sku] = (it["itemCode"], it["quantity"])
                    req["items"] = new_items
                    if req["orderCode"] in master_requests:
                        return no_update, html.Div("Need depot info")
                    master_requests[req["orderCode"]] = req
                vehicles = data.get("vehicles")
                master_vehicles = defaultdict(dict)
                for veh in vehicles:
                    # if veh["quantity"] == 0:
                    #     continue
                    vendor = veh['vType']['typeOfVehicleByVendor']
                    v, c = vendor.split('-')
                    try:
                        trans = VENDOR_CONVERT[v]
                    except KeyError:
                        trans = v.lower()
                    try:
                        truck = CAPACITY_CONVERT[c]
                    except KeyError:
                        return no_update, html.Div("Need more vehicle info")
                    try:
                        master_vehicles[trans][truck].append(veh)
                    except KeyError:
                        master_vehicles[trans][truck] = [veh]
                data["requests"] = master_requests
                data["vehicles"] = master_vehicles
                data["items"] = master_items
        except Exception as e:
            return no_update, html.Div([
                'There was an error processing this file.',
                f'{type(e)}: {e.args}'
            ])

        return data, html.Div([
                html.H5([
                    html.Span(f"{filename}"),
                    html.Span(" upload sucessfully!", style=dict(color="green"))
                    ]),
                # html.H6(datetime.fromtimestamp(date)),
            ])
        
    def uploader(self):
        def update_output(content, name):
            if content is not None:
                children = self.parse_contents(content, name)
                return children
        return update_output
    
    def register_callback(self, dash_app: Dash):
        super().register_callback(dash_app)
        dash_app.callback(
            Output('session-storage', 'data', allow_duplicate=True),
            Output(self.upload_output, 'children'),
            Input(self.upload_id, 'contents'),
            State(self.upload_id, 'filename'),
            prevent_initial_call=True,
            allow_duplicate=True,
        )(self.uploader())
        
@dataclass
@component_register
class XlsxUploader(SharedDataStep):
    
    def __post_init__(self):
        super().__post_init__()
    
    @property
    def upload_id(self):
        return f'uploader-{self.index}'
    
    @property
    def upload_output(self):
        return f'output-{self.index}'
    
    def make_layout(self):
        return html.Div([
            dcc.Upload(
                id=self.upload_id,
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Excel Manual')
                ]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px'
                },
                multiple=False,
            ),
            html.Div(id=self.upload_output),
        ])
    
    @staticmethod
    def get_item(item: dict, code: str, quantity: int, leftover_quantity: int):
        true_qtt = min(leftover_quantity, quantity*item["quantityPerBox"])
        return dict(
            itemCode = code,
            quantity = true_qtt,
            weight = true_qtt*item["weight"],
            cbm = true_qtt*item["cbm"],
            quantityPerBox = item["quantityPerBox"],
            size = item["size"],
            iType = item["iType"],
            itemCost = true_qtt*item["cost"],
        ), leftover_quantity - true_qtt
    
    def parse_contents(self, contents, filename, cur_data):
        content_type, content_string = contents.split(',')

        decoded = base64.b64decode(content_string)
        try:
            if 'csv' in content_type:
                df = pd.read_csv(
                    io.StringIO(decoded.decode('utf-8')))
                tripNo = -1
                tripRequest = {}
                tripVehicle = {}
                alert = []
                for i, row in df.iterrows():
                    if pd.notna(row.truckType):
                        tripNo += 1
                        try:
                            tripVehicle[str(tripNo)] = cur_data["vehicles"][row.vendor.lower()][str(row.truckType)]
                        except KeyError:
                            tripVehicle[str(tripNo)] = []
                        if len(tripVehicle[str(tripNo)]) == 0:
                            alert.append(html.Div(f"Nha thau [{row.vendor}] khong co loai xe truckType={row.truckType}"))
                        tripRequest[str(tripNo)] = {}
                    orderCode = str(row.orderCode)
                    try:
                        req = tripRequest[str(tripNo)].get(orderCode, cur_data["requests"][orderCode].copy())
                        items_in_req = cur_data["requests"][orderCode]["items"]
                    except KeyError:
                        alert.append(html.Div(f"Khong tim thay orderCode [{orderCode}] trong input."))
                        continue
                    try:
                        code, qtt = items_in_req.pop(row.sku)
                        md_item = cur_data["items"][row.sku]
                        code = f'{code}-{str(tripNo)}-{i}'
                        new_it, qtt = self.get_item(md_item, code, row.quantity, qtt)
                    except KeyError:
                        alert.append(html.Div(f"Khong tim thay item [{row.sku} ({code})] trong input hoac so luong khong du."))
                        continue
                    if qtt > 0:
                        items_in_req[row.sku] = (code, qtt)
                    try:
                        req["items"].append(new_it)
                    except:
                        req["items"] = [new_it]
                    tripRequest[str(tripNo)][orderCode] = req
                for req in cur_data["requests"].values():
                    item_in_req = req["items"]
                    new_items = []
                    for sku, value in item_in_req.items():
                        code, qtt = value
                        if qtt <= 0:
                            continue
                        code = f"UN{code}"
                        md_item = cur_data["items"][sku]
                        new_it, _ = self.get_item(md_item, code, qtt, qtt)
                        new_items.append(new_it)
                    req["items"] = new_items
                cur_data["tripRequest"] = tripRequest
                cur_data["tripVehicle"] = tripVehicle
        except Exception as e:
            return no_update, html.Div([
                'There was an error processing this file.',
                f'{type(e)}: {e.args}'
            ] + alert)

        return cur_data, html.Div([
                html.H5([
                    html.Span(f"{filename}"),
                    html.Span(" upload sucessfully!", style=dict(color="green"))
                    ]),
                # html.H6(datetime.fromtimestamp(date)),
            ] + alert)
        
    def uploader(self):
        def update_output(content, name, cur_data):
            if content is not None:
                children = self.parse_contents(content, name, cur_data)
                return children
        return update_output
    
    def register_callback(self, dash_app: Dash):
        super().register_callback(dash_app)
        dash_app.callback(
            Output('session-storage', 'data', allow_duplicate=True),
            Output(self.upload_output, 'children'),
            Input(self.upload_id, 'contents'),
            State(self.upload_id, 'filename'),
            State('session-storage', 'data'),
            prevent_initial_call=True,
        )(self.uploader())


@dataclass
@component_register
class Downloader(SharedDataStep):
    
    def __post_init__(self):
        super().__post_init__()
    
    @property
    def select_id(self):
        return f'select-{self.index}'
    
    @property
    def download_id(self):
        return f'download-{self.index}'
    
    @property
    def run_id(self):
        return f'run-{self.index}'
    
    @property
    def refresh_id(self):
        return f'refresh-{self.index}'
    
    def make_layout(self):
        return html.Div([
            dmc.Button("Refresh", id=self.refresh_id),
            dmc.Select(
                id=self.select_id,
                data=[],
                placeholder="Select one route to download",
                label="Select route",
                w=200,
                mb=10,
            ),
            dmc.Button("Download", id=self.download_id),
            dcc.Download(id="download-text"),
            dmc.Button("Run", id=self.run_id),
            html.Div(id="output-text")
        ])
    
    def selecter(self):
        def update_output(n, cur_data):
            if n and cur_data:
                data = [dict(value="all", label="All Routes")]
                for key in cur_data["tripRequest"].keys():
                    data.append(dict(value=key, label=f"Route {key}"))
                return data
            return no_update
        return update_output
    
    @staticmethod
    def get_json(value, cur_data):
        if value != "all":
            requests = list(cur_data["tripRequest"].get(value, {}).values())
            vehicles = cur_data["tripVehicle"].get(value, [])
            for req in requests:
                req["assignedVehicle"] = None
                req["tripNo"] = value
        else:
            requests = []
            vehicles = []
            for vendor in cur_data["vehicles"].values():
                for veh in vendor.values():
                    vehicles += veh
            for key in cur_data["tripRequest"].keys():
                _reqs = list(cur_data["tripRequest"][key].values())
                _vehs = cur_data["tripVehicle"][key]
                for req in _reqs:
                    req["orderCode"] = req["orderCode"] + key
                    req["assignedVehicle"] = _vehs[0]["vehicleCode"]
                    req["tripNo"] = key
                requests += _reqs
            requests += list(req for req in cur_data["requests"].values() if len(req["items"]))
            
        algoParams = cur_data["algoParams"]
        name = f"M{int(time.time())}"
        algoParams["trackingId"] += f"_{name}_{value}"
        data = dict(
            customers=cur_data["customers"],
            depots=cur_data["depots"],  
            distances=cur_data["distances"],  
            locations=cur_data["locations"],  
            matrixConfig=cur_data["matrixConfig"],  
            algoParams=algoParams,  
            routingFee=cur_data["routingFee"],  
            requests=requests,
            vehicles=vehicles,
        )
        return data, name
        
    def downloader(self):
        def update_output(n, value, cur_data):
            if ctx.triggered_id == self.download_id:
                data, name = self.get_json(value, cur_data)
                json_data = json.dumps(data)
                return dict(content=json_data, filename=f'{name}.json')
            return no_update
        return update_output
    
    def runner(self):
        def update_output(n, value, cur_data):
            import requests
            if ctx.triggered_id == self.run_id:
                data, name = self.get_json(value, cur_data)
                requests.post("http://171.244.37.73:7000/vrp/fixed_route_internal", json=data, headers={"Content-Type":"application/json"})
                return name
            return ""
        return update_output
    
    def register_callback(self, dash_app: Dash):
        super().register_callback(dash_app)
        dash_app.callback(
            Output(self.select_id, 'data'),
            Input(self.refresh_id, 'n_clicks'),
            Input('session-storage', 'data'),
        )(self.selecter())
        dash_app.callback(
            Output("download-text", "data"),
            Input(self.download_id, 'n_clicks'),
            Input(self.select_id, 'value'),
            Input('session-storage', 'data'),
        )(self.downloader())
        dash_app.callback(
            Output("output-text", "children"),
            Input(self.run_id, 'n_clicks'),
            Input(self.select_id, 'value'),
            Input('session-storage', 'data'),
        )(self.runner())