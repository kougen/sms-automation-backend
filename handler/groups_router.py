
from fastapi import APIRouter
from psycopg.errors import InvalidTextRepresentation
from lib import append_cancel_message
from dblib import get_db_cursor_and_connection, get_group_by_id, get_recipients_by_group_id


groupsrouter = APIRouter()

cursor, connection = get_db_cursor_and_connection()

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
