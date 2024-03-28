from psycopg.errors import InvalidTextRepresentation
from lib import IdRequest, send_message, append_cancel_message, update_message
from dblib import get_group_by_id, get_recipients_by_group_id, get_db_cursor_and_connection, Logger
from store import SELF_URL
from fastapi import APIRouter

sendrouter = APIRouter()

cursor, connection = get_db_cursor_and_connection()

logger = Logger("HANDLER:SEND", cursor)

@sendrouter.post("/", tags=["send"])
async def send_msg_to_recipients(request: IdRequest):
    try:
        group = get_group_by_id(cursor, request.id)
        if not group:
            return {"message": "Invalid ID, group not found"}
        if not group.enabled:
            return {"message": "Group is not enabled"}
        else:
            access_url = f"{SELF_URL}/send/group"
            result = send_message(cursor, group.id, access_url, "pending")
            if result:
                return {"message": "Registered pending message"}
            else:
                return {"message": "Error Occurred"}
    except InvalidTextRepresentation as e:
        print(e)
        return {"message": "Invalid ID"}
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e)}



@sendrouter.get("/group", tags=["groups"])
async def get_group_details(group_id: int, message_id: int):
    try:
        group = get_group_by_id(cursor, group_id)
        if not group:
            cursor.execute('DELETE FROM "PendingMessages" WHERE "groupId" = (%s)', (group_id,))
            return {"message": "Invalid ID, group not found. Deleted from pending messages."}
        trailed_message = append_cancel_message(group.message, group.lang_codes)
        recipients = get_recipients_by_group_id(cursor, group_id)
        update_message(cursor, message_id, "fetched")
        return {
            "id": group.id,
            "name": group.name,
            "message": group.message,
            "enabled": group.enabled,
            "lang_codes": group.lang_codes,
            "recipients": recipients,
            "trailed_message": trailed_message
        }
    except InvalidTextRepresentation as e:
        print(e)
        return {"message": "Invalid ID"}
    except Exception as e:
        print(f"Error in get_group_details: {e}")
        return {"message": "Error Occurred: " + str(e), "path": "get_group_details"}
