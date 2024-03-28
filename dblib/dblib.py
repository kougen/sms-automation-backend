from datetime import datetime
from typing import Union
from psycopg.connection import Connection
from psycopg.cursor import Cursor
from psycopg.errors import InvalidTextRepresentation
import time
import requests
import socket
import os
import psycopg

class PgRecipient:
    def __init__(self, name, phone_number, email, group_id):
        self.group_id = group_id
        self.name = name
        self.phone_number = phone_number
        self.email = email


class PgGroup:
    def __init__(self, id, name, interval, created_at, updated_at, enabled, message, lang_codes):
        self.id = id
        self.name = name
        self.enabled = enabled
        self.updated_at = updated_at
        self.created_at = created_at
        self.message = message
        self.interval = interval
        self.lang_codes = lang_codes


class PgLog:
    def __init__(self, level, message, tool, timezone="UTC", logged_at=None, comment=""):
        self.level = level
        self.message = message
        self.tool = tool
        self.timezone = timezone
        self.logged_at = logged_at
        self.comment = comment

        self.id: str
        self.created_at: datetime


class Logger:
    def __init__(self, tool: str, cursor: Cursor, comment: str = ""):
        self.tool = tool
        self.cursor = cursor
        self.comment = comment

    def info(self, message: str, comment: str = ""):
        comment = comment or self.comment
        insert_log(self.cursor, "INFO", message, self.tool, comment)
    
    def error(self, message: str, comment: str = ""):
        comment = comment or self.comment
        insert_log(self.cursor, "ERROR", message, self.tool, comment)

    def warning(self, message: str, comment: str = ""):
        comment = comment or self.comment
        insert_log(self.cursor, "WARNING", message, self.tool, comment)


def get_group_by_id(cursor, id: int) -> Union[PgGroup, None]:
    try:
        cursor.execute('SELECT * FROM "Group" WHERE id = (%s)', (id,))
        result = cursor.fetchall() or []
        if len(result) == 0:
            return None
        group = PgGroup(result[0][0], result[0][1], result[0][2], result[0][3], result[0][4], result[0][5], result[0][6], result[0][7] or [])
        return group
    except InvalidTextRepresentation as e:
        print(e)
        return None
    except Exception as e:
        print(e)
        return None

def insert_log(cursor: Cursor, level: str, message: str, tool: str, comment: str = "", timezone: str = "UTC", logged_at = datetime.now()):
    try:
        connection = cursor.connection
        try:
            cursor.execute('INSERT INTO "Log" ("level", "message", "tool", "comment", "timezone", "loggedAt") VALUES (%s, %s, %s, %s, %s, %s)', (level, message, tool, comment, timezone, logged_at))
            connection.commit()
            return True
        except Exception as e:
            print(e)
            connection.rollback()
    except Exception as e:
        print(e)

    return False


def insert_logs(cursor: Cursor, logs: list[PgLog]):
    try:
        connection = cursor.connection
        try:
            for log in logs:
                cursor.execute('INSERT INTO "Log" ("level", "message", "tool", "comment", "timezone", "loggedAt") VALUES (%s, %s, %s, %s, %s, %s)', (log.level, log.message, log.tool, log.comment, log.timezone, log.logged_at))
            connection.commit()
            return True
        except Exception as e:
            print(e)
            connection.rollback()
    except Exception as e:
        print(e)

    return False


def is_subscribed(cursor, group_id, phone):
    try:
        cursor.execute('SELECT * FROM "Recipient" WHERE "phone" = (%s)', (group_id, phone))
        result = cursor.fetchall()
        return len(result) > 0
    except Exception as e:
        print(e)
        return False


def has_subscription(cursor: Cursor, phone):
    try:
        cursor.execute('SELECT * FROM "Recipient" WHERE "phone" = (%s)', (phone,))
        result = cursor.fetchall()
        return len(result) > 0
    except Exception as e:
        print(e)
        return False


def get_recipients_by_group_id(cursor, group_id) -> list[PgRecipient]:
    recepients = []
    try:
        cursor.execute('select * from "Recipient" r where r."groupId" = (%s)', (group_id,))
        result = cursor.fetchall() or []
        for row in result:
            recepient = PgRecipient(row[0], row[2], row[1], group_id)
            recepients.append(recepient)
        return recepients
    except InvalidTextRepresentation as e:
        print(e)
        return []
    except Exception as e:
        print(e)
        return []


def wait_for_healthy_website(base_url: str, test_path: str = '/api/health', startup_path: str = '/api/startup'):
    while True:
        try:
            print(f"Checking website health for: {base_url}{test_path}")
            response = requests.get(f"{base_url}{test_path}")
            if response.status_code == 200 and response.json()['status'] == 'healthy':
                result = requests.get(f"{base_url}{startup_path}")
                print(f"Startup response: {result.status_code}")
                break
            else:
                print("Not healthy! Waiting for website to start!")
                time.sleep(5)
        except Exception as e:
            print(e)
            print("Waiting for server to start!")
            time.sleep(5)

def get_db_cursor_and_connection() -> tuple[Cursor, Connection]:
    HOST = os.getenv("DB_HOST")
    USER = os.getenv("DB_USER")
    PASSWORD = os.getenv("DB_PASSWORD")
    DATABASE = os.getenv("DB_NAME")
    PORT = os.getenv("DB_PORT")

    if not HOST or not USER or not PASSWORD or not DATABASE or not PORT:
        raise ValueError("One or more environment variables are missing")

    try:
        connection = psycopg.connect(
            host=HOST,
            user=USER,
            password=PASSWORD,
            dbname=DATABASE,
            port=PORT
        )
        return connection.cursor(), connection
    except psycopg.OperationalError as e:
        print(e)
        print("Connection failed")
        print("Values: ", HOST, USER, PASSWORD, DATABASE, PORT)
        print("Please check the environment variables")
        exit(1)
