from psycopg.errors import InvalidTextRepresentation
from lib import IdRequest, broadcast_bulk_send, send_message
from dblib import get_group_by_id, get_recipients_by_group_id, is_server_up, get_db_cursor_and_connection
from store import SRV_ADDR
from fastapi import APIRouter

sendrouter = APIRouter()

cursor, connection = get_db_cursor_and_connection()


@sendrouter.post("/", tags=["send"])
async def send_msg_to_recipients(request: IdRequest):
    try:
        group = get_group_by_id(cursor, request.id)
        if not group:
            return {"message": "Invalid ID, group not found"}
        if not group.enabled:
            return {"message": "Group is not enabled"}
        if not is_server_up(SRV_ADDR):
            return {"message": "SMS Server is down"}
        else:
            recepients = get_recipients_by_group_id(cursor, request.id)
            print(group.lang_codes)
            result = send_message(cursor, SRV_ADDR, recepients, group.message, group.lang_codes)
            resolution = { "isSent": ""}
            if result is None:
                resolution["isSent"] = "Partially Sent"
            elif result:
                resolution["isSent"] = "Sent"
            else:
                resolution["isSent"] = "Failed"
        return {"message": "Message Sent", "name": group.name, "resolution": resolution}
    except InvalidTextRepresentation as e:
        print(e)
        return {"message": "Invalid ID"}
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e)}


@sendrouter.post("/bulk", tags=["send"])
async def send_msg_to_recipients_bulk(request: IdRequest):
    print("Sending bulk message")
    try:
        return broadcast_bulk_send(cursor, SRV_ADDR, request.id)
    except InvalidTextRepresentation as e:
        print(e)
        return {"message": "Invalid ID"}
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e)}
