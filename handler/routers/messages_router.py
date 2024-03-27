
from fastapi import APIRouter
from lib import PutPendingMessageRequest
from dblib import get_db_cursor_and_connection

messagesrouter = APIRouter()

cursor, connection = get_db_cursor_and_connection()

@messagesrouter.get("/", tags=["messages"])
async def get_pending_messages(filter: str = "pending"):
    query = ""
    if filter == "all":
        query = 'SELECT * FROM "PendingMessage"'
    elif filter == "sent":
        query = 'SELECT * FROM "PendingMessage" WHERE "status" = "sent"'
    elif filter == "failed":
        query = 'SELECT * FROM "PendingMessage" WHERE "status" = "failed"'
    elif filter == "pending":
        query = 'SELECT * FROM "PendingMessage" WHERE "status" = "pending"'
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return { "messages": result}
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e), "success": False}


@messagesrouter.get("/{id}", tags=["messages"])
async def get_pending_messages_by_group_id(id: int):
    try:
        cursor.execute('SELECT * FROM "PendingMessage" WHERE "groupId" = (%s)', (id,))
        result = cursor.fetchall()
        return { "messages": result}
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e), "success": False}


@messagesrouter.get("/{id}/recipients", tags=["messages"])
async def get_pending_messages_recipients(id: int):
    try:
        cursor.execute('SELECT * FROM "PendingMessage" WHERE "groupId" = (%s)', (id,))
        result = cursor.fetchall()
        return { "messages": result}
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e), "success": False}


@messagesrouter.put("/{id}", tags=["messages"])
async def update_pending_message_status(id: int, request: PutPendingMessageRequest):
    status = request.status

    if status not in ["pending", "sent", "failed"]:
        return {"message": "Invalid Status", "success": False}

    try:
        cursor.execute('UPDATE "PendingMessage" SET "status" = (%s) WHERE "id" = (%s)', (status, id))
        connection.commit()
        return {"message": "Status Updated", "success": True}
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e), "success": False}
