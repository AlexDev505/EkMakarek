from flask import Flask

from config import load_config
from logger import init_logger

config = load_config()
init_logger(config)
app = Flask(__name__)
