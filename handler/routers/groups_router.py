
from fastapi import APIRouter
from psycopg.errors import InvalidTextRepresentation
from lib import append_cancel_message, PhoneRequest
from dblib import get_db_cursor_and_connection, get_group_by_id, get_recipients_by_group_id, Logger

groupsrouter = APIRouter()

cursor, connection = get_db_cursor_and_connection()

logger = Logger("HANDLER:GROUPS", cursor)

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
        recipients = get_recipients_by_group_id(cursor, id)
        trailed_message = append_cancel_message(group.message, group.lang_codes)
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
        print(e)
        return {"message": "Error Occurred: " + str(e)}


@groupsrouter.delete("/cancel", tags=["groups"])
def delete_recipient_from_group(phone: str):
    if not phone:
        return {"message": "Invalid Phone Number", "success": False}

    try:
        existing_recipient = cursor.execute('SELECT * FROM "Recipient" WHERE "phone" = (%s)', (phone,))
        if not existing_recipient:
            logger.info(f"Recipient with phone number {phone} not found")
            return {"message": "Recipient not found", "success": False}
        else:
            cursor.execute('DELETE FROM "Recipient" WHERE "phone" = (%s)', (phone,))
            connection.commit()
            logger.info(f"Recipient with phone number {phone} deleted")
            return {"message": "Recipient Deleted", "success": True}
    except InvalidTextRepresentation as e:
        print(e)
        logger.error(f"Invalid phone number: {phone}")
        return {"message": "Invalid ID", "success": False}
    except Exception as e:
        print(e)
        logger.error(f"Error deleting recipient: {phone}")
        return {"message": "Error Occurred: " + str(e), "success": False}
