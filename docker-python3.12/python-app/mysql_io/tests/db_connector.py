
import os
import mysql.connector
from mysql.connector.abstracts import MySQLConnectionAbstract
from dotenv import load_dotenv

# --- Database Connection Setup ---

# This script is in /mysql, so we go up one level to /python-app, then to /responce
ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "responce", ".env")
load_dotenv(ENV_PATH)

# Path to SSL certificates, relative to this script's location
MYSQL_DIR = os.path.join(os.path.dirname(__file__), "..", "responce", ".mysql-out")

# Centralized database configuration
db_config = {
    "host": os.environ.get("DOMAIN","uroktime.store"),
    "port": os.environ.get("MYSQL_EXTERNAL_PORT",45321),
    "user": os.environ.get("MYSQL_USER", "appuser"),
    "password": os.environ.get("MYSQL_PASSWORD"),
    "database": os.environ.get("MYSQL_DATABASE", "school_sheduller"),
    "ssl_ca":   os.path.join(MYSQL_DIR, "ca.pem"),
    "ssl_cert": os.path.join(MYSQL_DIR, "client-cert.pem"),
    "ssl_key":  os.path.join(MYSQL_DIR, "client-key.pem"),
    "ssl_verify_cert": True,
    "connection_timeout": 10,
}

def get_db_connection() -> MySQLConnectionAbstract:
    """
    Establishes and returns a new MySQL database connection using the centralized configuration.
    
    Raises:
        ValueError: If the database password is not set in the .env file.
        mysql.connector.Error: For other connection errors.
        
    Returns:
        A MySQLConnectionAbstract object.
    """
    if not db_config["password"]:
        raise ValueError("Database password (MYSQL_PASSWORD) not found in .env file.")
    
    return mysql.connector.connect(**db_config)
