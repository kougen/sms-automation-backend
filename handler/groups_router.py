
from fastapi import APIRouter
from psycopg.errors import InvalidTextRepresentation
from lib import append_cancel_message, CancelRequest
from dblib import get_db_cursor_and_connection, get_group_by_id, get_recipients_by_group_id, Logger

groupsrouter = APIRouter()

cursor, connection = get_db_cursor_and_connection()

logger = Logger("HANDLER", cursor, "GROUPS_ROUTER")

@groupsrouter.get("/", tags=["groups"])
async def get_groups():
    cursor.execute('SELECT * FROM "Group"')
    result = cursor.fetchall()
    return { "groups": result}


@groupsrouter.get("/{id}", tags=["groups"])
async def get_group_details(id: int):
    try:
        group = get_group_by_id(cursor, id)
        if not group:
            return {"message": "Invalid ID"}
        trailed_message = append_cancel_message(group.message, group.lang_codes)
        recipients = get_recipients_by_group_id(cursor, id)
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


@groupsrouter.post("/cancel", tags=["groups"])
def delete_recipient_from_group(request: CancelRequest):
    keys = request.dict().keys()
    if not request or not 'phone_number' in keys or not 'message' in keys:
        return {"message": "ERROR", "success": False}

    phone = request.phone_number
    message = request.message

    if not phone or not message:
        return {"message": "ERROR", "success": False}


    if not ("STOP" in message.upper() or "Stap" in message.upper() or "Stopp" in message.upper()):
        print(f"Received: {phone}, but no STOP message (or similar) found: {message}")
        logger.info(f"Received: {phone}, but no STOP message (or similar) found: {message}")
        return { "message": "NO_ACTION_REQUIRED", "success": True}

    try:
        existing_recipient = cursor.execute('SELECT * FROM "Recipient" WHERE "phone" = (%s)', (phone,))
        if not existing_recipient:
            logger.info(f"Recipient with phone number {phone} not found")
            return {"message": "NO_ACTION_REQUIRED", "success": True}
        else:
            cursor.execute('DELETE FROM "Recipient" WHERE "phone" = (%s)', (phone,))
            connection.commit()
            logger.info(f"Recipient with phone number {phone} deleted")
            return {"message": "OK", "success": True}
    except InvalidTextRepresentation as e:
        print(e)
        logger.error(f"Invalid phone number: {phone}")
        return {"message": "ERROR", "success": False}
    except Exception as e:
        print(e)
        logger.error(f"Error deleting recipient: {phone}")
        return {"message": "Error Occurred: " + str(e), "success": False}
