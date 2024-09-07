# app.py
from flask import Flask, render_template
import os
from dotenv import load_dotenv
from src.controllers.clientes_controller import client_blueprint

load_dotenv()

app = Flask(__name__, template_folder=os.path.join('src', 'templates'))

app.register_blueprint(client_blueprint)


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
