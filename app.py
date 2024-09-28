from flask import Flask

import os
from dash_app import create_dash_application

PATH = os.getcwd()

app = Flask(__name__)
dash_app = create_dash_application(app)


if __name__ == "__main__":
    app.run(host="0.0.0.0",port=7070,debug=False)
