from psycopg import Cursor
from pydantic import BaseModel
import json
import datetime
import os
from pathlib import Path
import sys
from uuid import uuid4
import random
from dotenv import load_dotenv

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT")
if ENVIRONMENT == "development":   
    path_root = Path(__file__).parents[1]
    script_path = os.path.join(path_root)
    sys.path.append(script_path)

from dblib import PgRecipient, insert_log


msgs = {
    'en': os.getenv('EN_MSG'),
    'hu': os.getenv('HU_MSG'),
    'rs': os.getenv('RS_MSG')
}

BASE_PATH = os.getenv('BASE_PATH') or ''

def update_message(cursor: Cursor, id: int, status: str):
    try:
        connection = cursor.connection
        if status not in ["pending", "sent", "failed", "sending", "fetched"]:
            return {"message": "Invalid Status", "success": False}

        try:
            cursor.execute('UPDATE "PendingMessages" SET "status" = (%s) WHERE "id" = (%s)', (status, id))
            connection.commit()
            return {"message": "Status Updated", "success": True}
        except Exception as e:
            print(e)
            connection.rollback()
            return {"message": "Error Occurred: " + str(e), "success": False}
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e), "success": False}


def send_message(cursor: Cursor, group_id: int, access_url: str, status: str):
    try:
        connection = cursor.connection
        try:
            cursor.execute('INSERT INTO "PendingMessages" ("groupId", "status", "accessUrl") VALUES (%s, %s, %s) RETURNING "id"', (group_id, status, access_url))
            result = cursor.fetchone()
            connection.commit()
            if not result:
                return {"message": "Row was not inserted", "success": False}
            id = result[0]
            return {"message": f"Message added to {status} queue", "success": True, "group_id": group_id, "message_id": id}
        except Exception as e:
            print(e)
            insert_log(cursor, "ERROR", f"Uknown error wihile sending message. Error: {e}", "HANDLER")
            connection.rollback()
            return {"message": "Error Occurred: " + str(e), "success": False}
    except Exception as e:
        print(e)
        insert_log(cursor, "ERROR", f"Error while sending message. Error: {e}", "HANDLER")
        return {"message": "Error Occurred: " + str(e), "success": False}


def append_cancel_message(message: str, lang_codes: list[str] = ['en', 'hu', 'rs']):
    for lang_code in lang_codes:
        message += f' {msgs[lang_code]}'
    return message

class IdRequest(BaseModel):
    id: int


class CancelRequest(BaseModel):
    phone_number: str
    message: str

class LogRequest(BaseModel):
    level: str
    message: str
    tool: str
    comment: str = ""
    timezone: str = "UTC"
    logged_at: datetime.datetime = datetime.datetime.now()

class TestGroup:
    id: int
    name: str
    message: str
    enabled: bool = True
    lang_codes: list[str] = []
    recipients: list[PgRecipient] = []

    def get_json_string(self):
        return {
            "id": self.id,
            "name": self.name,
            "message": self.message,
            "trailed_message": append_cancel_message(self.message, self.lang_codes),
            "enabled": self.enabled,
            "lang_codes": self.lang_codes,
            "recipients": [recepient for recepient in self.recipients]
        
        }


class LogsRequest(BaseModel):
    logs: list[LogRequest]


class UpdateMessageRequest(BaseModel):
    id: int
    status: str


class MessageRequest(BaseModel):
    group_id: int
    access_url: str
    status: str = "pending"


def validate_json(json_str):
    try:
        json.loads(json_str)
    except ValueError as e:
        print(e)
        return False
    return True

def get_json_from_recipients(cursor, recipients: list[PgRecipient], message: str, lang_codes: list[str]):
    packet = {
            "id": str(uuid4()),
            "recipients": [recepient.phone_number for recepient in recipients],
            "message": append_cancel_message(message, lang_codes)
        }
    data = json.dumps(packet).encode('utf-8')
    if not validate_json(data):
        insert_log(cursor, "ERROR", f"Invalid JSON: {data}", "HANDLER")
        return None
    return data
    


def perform_test_message(cursor: Cursor, group_id: int, access_url: str):
    try:
        return send_message(cursor, group_id, access_url, "pending")
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e)}


def create_test_groups(recepient_count: int, groups_id: int, phone_numbers: list[str] = []) -> TestGroup:
    print(f"Creating test groups with {recepient_count} recipients")
    group = TestGroup()
    group.id = groups_id
    group.name = f"Test Group {groups_id}"
    group.message = "Test message from API"
    group.enabled = True
    group.lang_codes = ["hu", "rs"]
    # Randomly put the phone numbers into the groups with the recepient count amount, as these are real numbers
    recipients = []
    if len(phone_numbers) <= 0:
        recipients = [PgRecipient(f"Test Joe {i}", f"+test_num_{i}", f"email{i}.test.com", groups_id) for i in range(recepient_count)]
    else:
        for i in range(recepient_count):
            random_phone = random.choice(phone_numbers)
            recipients.append(PgRecipient(f"Test Joe {i}", random_phone, f"email{i}.test.com", groups_id))
    group.recipients = recipients
    return group
