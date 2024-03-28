
from fastapi import APIRouter
from lib import UpdateMessageRequest, update_message, MessageRequest, send_message
from dblib import get_db_cursor_and_connection

messagesrouter = APIRouter()

cursor, connection = get_db_cursor_and_connection()

@messagesrouter.get("/pull", tags=["messages"])
async def get_pending_messages(filter: str = "all"):

    if filter not in ["all", "pending", "sent", "failed", "sending"]:
        return {"message": "Invalid Filter", "success": False}
    try:
        if filter == "all":
            cursor.execute('SELECT * FROM "PendingMessages"')
        else:
            cursor.execute('SELECT * FROM "PendingMessages" WHERE "status" = (%s)', (filter,))
        result = cursor.fetchall()
        messages = []

        for message in result:
            messages.append({
                "id": message[0],
                "groupId": message[1],
                "createdAt": message[2],
                "updatedAt": message[3],
                "status": message[4],
                "accessUrl": f"{message[5]}?group_id={message[1]}&message_id={message[0]}"
            })
        return { "messages": messages}
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e), "success": False}


@messagesrouter.get("/{id}", tags=["messages"])
async def get_pending_messages_by_group_id(id: int):
    try:
        cursor.execute('SELECT * FROM "PendingMessages" WHERE "id" = (%s)', (id,))
        result = cursor.fetchall()
        if not result:
            return None
        message = result[0]
        return {
            "id": message[0],
            "groupId": message[1],
            "createdAt": message[2],
            "updatedAt": message[3],
            "status": message[4],
            "accessUrl": f"{message[5]}?group_id={message[1]}&message_id={message[0]}"
        }
        
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e), "success": False}


@messagesrouter.get("/{id}/recipients", tags=["messages"])
async def get_pending_messages_recipients(id: int):
    try:
        cursor.execute('SELECT * FROM "PendingMessages" WHERE "groupId" = (%s)', (id,))
        result = cursor.fetchall()
        return { "messages": result}
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e), "success": False}


@messagesrouter.put("/{id}", tags=["messages"])
async def update_pending_message_status(request: UpdateMessageRequest):
    status = request.status
    id = request.id
    return update_message(cursor, id, status)

@messagesrouter.post("/", tags=["messages"])
async def add_message_to_pending_queue(request: MessageRequest):
    group_id = request.group_id
    access_url = request.access_url
    return send_message(cursor, group_id, access_url)

@messagesrouter.put("/set/{id}/sent", tags=["messages"])
async def set_message_sent(id: int):
    return update_message(cursor, id, "sent")

@messagesrouter.put("/set/{id}/failed", tags=["messages"])
async def set_message_failed(id: int):
    return update_message(cursor, id, "failed")

@messagesrouter.put("/set/{id}/sending", tags=["messages"])
async def set_message_sending(id: int):
    return update_message(cursor, id, "sending")

@messagesrouter.delete("/{id}", tags=["messages"])
async def delete_pending_message(id: int):
    try:
        cursor.execute('DELETE FROM "PendingMessages" WHERE "id" = (%s)', (id,))
        connection.commit()
        return {"message": "Message Deleted", "success": True}
    except Exception as e:
        print(e)
        connection.rollback()
        return {"message": "Error Occurred: " + str(e), "success": False}


@messagesrouter.delete("/", tags=["messages"])
async def delete_all_pending_messages():
    try:
        cursor.execute('DELETE FROM "PendingMessages"')
        connection.commit()
        return {"message": "All Messages Deleted", "success": True}
    except Exception as e:
        print(e)
        connection.rollback()
        return {"message": "Error Occurred: " + str(e), "success": False}
