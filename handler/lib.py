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

from dblib import PgRecipient, get_group_by_id, insert_log, get_client, is_server_up


msgs = {
    'en': os.getenv('EN_MSG'),
    'hu': os.getenv('HU_MSG'),
    'rs': os.getenv('RS_MSG')
}

BASE_PATH = os.getenv('BASE_PATH') or ''

def append_cancel_message(message: str, lang_codes: list[str] = ['en', 'hu', 'rs']):
    for lang_code in lang_codes:
        message += f' {msgs[lang_code]}'
    return message

class IdRequest(BaseModel):
    id: int


class PhoneRequest(BaseModel):
    phone_number: str

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


class PutPendingMessageRequest(BaseModel):
    status: str


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
    

def send_message(cursor, srvr_addr, recipients: list[PgRecipient], message: str, lang_codes: list[str]):
    try:
        for recepient in recipients:
            client = get_client(srvr_addr)
            print(f'\t{recepient.name} - {recepient.phone_number}')
            try:
                packet = {
                        "id": str(uuid4()),
                        "phone": recepient.phone_number,
                        "message": append_cancel_message(message, lang_codes)
                    }
                data = json.dumps(packet).encode('utf-8')
                print(f'Sending: {data}')
                client.sendall(data)
                response = client.recv(2048)
                print(f'Response: {response}')
                insert_log(cursor, "INFO", f"Messege sent to {recepient.phone_number} ({recepient.group_id}) with response: {response}", "HANDLER")
            except Exception as e:
                print(e)
                insert_log(cursor, "ERROR", f"Error sending message to {recepient.phone_number} ({recepient.group_id}). {e}", "HANDLER")
                return None
            client.close()
        return True
    except Exception as e:
        print(e)
        insert_log(cursor, "ERROR", f"Uknown error wihile sending message. Error: {e}", "HANDLER")
        return False


def perform_test_message(cursor, server, recepients: list[PgRecipient], message: str, at_the_same_time):
    print(f"Sending {len(recepients)} messages at the same time: {at_the_same_time}")
    try:
        if not is_server_up(server):
            return {"message": "SMS Server is down"}
        else:
            result = send_message(cursor, server, recepients, "Test message from API", ["hu", "rs"])
            resolution = { "isSent": ""}
            if result is None:
                resolution["isSent"] = "Partially Sent"
            elif result:
                resolution["isSent"] = "Sent"
            else:
                resolution["isSent"] = "Failed"
        return {"message": "Message Sent", "resolution": resolution}
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e)}


def send_bulk_data(cursor, server, data: dict):
    try:
        json_data = json.dumps(data).encode('utf-8')
        client = get_client(server)
        client.sendall(json_data)
        response = client.recv(2048)
        print(f'Response: {response}')
        client.close()
        return {"message": "Bulk message broadcasted", "data": data, "response": response}
    except Exception as e:
        print(e)
        insert_log(cursor, "ERROR", f"Uknown error wihile sending message. Error: {e}", "HANDLER")
        return {"message": "Error Occurred: " + str(e)}


def broadcast_bulk_send(cursor, server, group_id: int):
    group = get_group_by_id(cursor, group_id)
    if not group:
        return {"message": "Invalid ID, group not found"}
    if not group.enabled:
        return {"message": "Group is not enabled"}
    if not is_server_up(server):
        return {"message": "SMS Server is down"}
    else:
        data = {
            "url": f"/groups/{group.id}",
        }
        return send_bulk_data(cursor, server, data)

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


def test_broadcast_bulk_send(cursor, server, count: int):
    if not is_server_up(server):
        return {"message": "SMS Server is down"}
    data = {
        "url": f"/test/groups/{count}",
    }
    return send_bulk_data(cursor, server, data)
