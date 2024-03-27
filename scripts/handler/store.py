import os
from dotenv import load_dotenv
from lib import TestGroup

load_dotenv()

HANDLER_VERSION = os.getenv("HANDLER_VERSION")
CHECKER_VERSION = os.getenv("CHECKER_VERSION")
WEBSITE_VERSION = os.getenv("WEBSITE_VERSION")
RECIEVER_VERSION = os.getenv("RECIEVER_VERSION")
SELF_URL = os.getenv("SELF_URL")

PHONE_SERVER_IP = os.getenv("PHONE_SERVER_IP")
PHONE_SERVER_PORT = os.getenv("PHONE_SERVER_PORT")
if not PHONE_SERVER_IP:
    PHONE_SERVER_IP = "localhost"

if not PHONE_SERVER_PORT:
    PHONE_SERVER_PORT = 12345

SRV_ADDR = (PHONE_SERVER_IP, int(PHONE_SERVER_PORT))
test_groups = {}  #type: dict[int, TestGroup]
