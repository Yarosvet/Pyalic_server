from dotenv import load_dotenv
from os import path, environ

LOG_FILE = "lic_server.log"
if path.exists(path.join(path.dirname(__file__), '../.env')):
    load_dotenv(path.join(path.dirname(__file__), '../.env'))
DB_HOST = environ.get('DB_HOST')
DB_USER = environ.get('DB_USER')
DB_PASSWORD = environ.get('DB_PASSWORD')
DB_NAME = environ.get('DB_NAME')
ACCESS_TOKEN = environ.get('ACCESS_TOKEN')

REDIS_HOST = environ.get('REDIS_HOST')
REDIS_PORT = int(environ.get('REDIS_PORT'))
REDIS_PASSWORD = environ.get('REDIS_PASSWORD')
REDIS_DB = environ.get('REDIS_DB')

SESSION_ALIVE_PERIOD = int(environ.get('SESSION_ALIVE_PERIOD', default=4))
