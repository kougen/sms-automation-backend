from fastapi.responses import JSONResponse
from psycopg.errors import InvalidTextRepresentation
import datetime
from fastapi import FastAPI
import threading
from lib import msgs, LogRequest, LogsRequest, PhoneRequest, PutPendingMessageRequest, BASE_PATH
from dblib import get_group_by_id, is_server_up, get_db_cursor_and_connection, insert_log, insert_logs, PgLog
from store import SRV_ADDR, HANDLER_VERSION, CHECKER_VERSION, WEBSITE_VERSION, RECIEVER_VERSION, SELF_URL
from test_router import testrouter
from send_router import sendrouter
from groups_router import groupsrouter

result = get_db_cursor_and_connection()

if not result:
    raise Exception("Could not connect to database")

cursor, connection = result

tags_metadata = [
    {
        "name": "groups",
        "description": "Operations with groups.",
    },
    {
        "name": "send",
        "description": "Operations with sending messages.",
    },
    {
        "name": "logs",
        "description": "Operations with logs.",
    },
    {
        "name": "health",
        "description": "Operations with health checks.",
    },
    {
        "name": "messages",
        "description": "Operations with the pending messages.",
    },
    {
        "name": "test",
        "description": "Test operations for development, no real harm can be done.",
    }
]

description = """
SMS Automation API Helps you manage your tools. 🚀

## Groups

You can **read groups** and **send messages** to them.

## Send

You will be able to:

* **Create users** (_not implemented_).
* **Read users** (_not implemented_).
"""
print(f"Starting FastAPI on port 8000 ({SELF_URL}), with base path: {BASE_PATH}")
app = FastAPI(
    title="SMS Automation API",
    description=description,
    summary="Sms Automation API",
    version="0.0.1",
    terms_of_service=f"{SELF_URL}/terms/",
    contact={
        "name": "Joshua Hegedus",
        "url": "https://kou-gen.net/support",
        "email": "josh.hegedus@outlook.com",
    },
    # Closed source license
    license_info={
        "name": "Proprietary",
        "url": "https://en.wikipedia.org/wiki/Proprietary_software",
    },
    openapi_tags=tags_metadata,
    root_path=BASE_PATH
)

app.include_router(testrouter, prefix="/test")
app.include_router(sendrouter, prefix="/send")
app.include_router(groupsrouter, prefix="/groups")

@app.get("/", tags=["health"])
async def home_api():
    return {"message": "Hello World"}


@app.get("/ping", tags=["health"])
async def ping():
    data = {
            "time": datetime.datetime.now().isoformat(),
            "timezone": "UTC",
            "status": "up"
        }
    return JSONResponse(content=data)


@app.get("/ping/{host}", tags=["health"])
async def ping_db(host: str):
    if host == "phone":
        result = is_server_up(SRV_ADDR)
        return { "host": SRV_ADDR, "status": "up" if result else "down"}


@app.get("/version", tags=["health"])
async def get_version():
    return {
        "handler": HANDLER_VERSION,
        "checker": CHECKER_VERSION,
        "website": WEBSITE_VERSION,
        "reciever": RECIEVER_VERSION
    }

@app.delete('/purge/db', tags=["health"])
async def purge_database():
    try:
        cursor.execute('DELETE FROM "Log"')
        cursor.execute('DELETE FROM "Recipient"')
        cursor.execute('DELETE FROM "Group"')
        cursor.execute('DELETE FROM "RunningJobs"')
        connection.commit()
        return {"message": "Database Purged", "success": True}
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e), "success": False}

@app.delete('/purge/{table}', tags=["health"])
async def purge_table(table: str):
    try:
        cursor.execute(f'DELETE FROM %s', (table,))
        connection.commit()
        return {"message": f"{table} Purged", "success": True}
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e), "success": False}


@app.get("/trail-messages")
async def get_stopwords():
    return msgs


@app.delete("/cancel", tags=["groups"])
def delete_recipient_from_group(phone: PhoneRequest, id: int = -1):
    query = ""
    data = tuple()
    if id == -1:
        query = 'DELETE FROM "Recipient" WHERE "phone" = (%s)'
        data = (phone.phone_number,)
        group = get_group_by_id(cursor, id)
        if not group:
            return {"message": "Invalid ID", "success": False}
    else:
        query = 'DELETE FROM "Recipient" WHERE "groupId" = (%s) AND "phone" = (%s)'
        data = (id, phone.phone_number)
    try:
        cursor.execute(query, data)
        connection.commit()
        if id == -1:
            return {"message": "Recipient Deleted", "success": True}
        else:
            return {"message": f"Recipient Deleted from group: {id}",  "success": True}
    except InvalidTextRepresentation as e:
        print(e)
        return {"message": "Invalid ID", "success": False}
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e), "success": False}


@app.post("/log", tags=["logs"])
def log_message(request: LogRequest):
    level = request.level
    message = request.message
    tool = request.tool
    comment = request.comment
    logged_at = request.logged_at
    if not level or not message or not tool:
        return {"message": "Invalid Request", "success": False}
    try:
        insert_log(cursor, level, message, tool, comment, logged_at=logged_at)
        return {"message": "Log Inserted", "success": True}
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e), "success": False}

def convertRequestToLog(request: LogRequest):
    return PgLog(request.level, request.message, request.tool, request.comment, request.timezone, request.logged_at)

def runAsyncLogInsert(c, logs):
    print(f"Inserting {len(logs)} logs")
    try:
        insert_logs(c, logs)
        print(f"Inserted {len(logs)} logs")
    except Exception as e:
        print(e)

def insert_logs_thread(logs: list[PgLog]):
    split_logs = [logs[i:i + 50] for i in range(0, len(logs), 50)]
    print(f"Split into {len(split_logs)} batches")
    cursors = [get_db_cursor_and_connection()[0] for i in range(len(split_logs))]
    print(f"Got {len(cursors)} cursors")
    try:
        for log_batch in split_logs:
            threading.Thread(target=runAsyncLogInsert, args=(cursors.pop(), log_batch)).start()
        print(f"Started {len(split_logs)} threads")
    except Exception as e:
        print(e)
        print(f"Error inserting logs: {e}")

@app.post("/logs", tags=["logs"])
async def log_multiple_messages(request: LogsRequest):
    logs = request.logs
    print(f"Received {len(logs)} logs")  
    pgLogs = [convertRequestToLog(log) for log in logs]
    threading.Thread(target=insert_logs_thread, args=(pgLogs,)).start()
    return {"message": "Thanks for the logs", "success": True}

@app.delete("/logs", tags=["logs"])
async def delete_logs(mode: str):
    try:
        if mode == "all":
            cursor.execute('DELETE FROM "Log"')
            connection.commit()
            return {"message": "All Logs Deleted", "success": True}
        elif mode == "old":
            cursor.execute('DELETE FROM "Log" WHERE "timestamp" < now() - interval \'30 days\'')
            connection.commit()
            return {"message": "Old Logs Deleted", "success": True}
        else:
            return {"message": "Invalid Mode", "success": False}
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e), "success": False}


@app.get("/logs", tags=["logs"])
async def get_logs():
    try:
        cursor.execute('SELECT * FROM "Log"')
        result = cursor.fetchall()
        return { "logs": result}
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e), "success": False}


@app.get("/logs/{level}", tags=["logs"])
async def get_logs_by_level(level: str):
    try:
        cursor.execute('SELECT * FROM "Log" WHERE "level" = (%s)', (level,))
        result = cursor.fetchall()
        return { "logs": result}
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e), "success": False}


@app.get("/logs/{level}/{tool}", tags=["logs"])
async def get_logs_by_level_and_tool(level: str, tool: str):
    try:
        cursor.execute('SELECT * FROM "Log" WHERE "level" = (%s) AND "tool" = (%s)', (level, tool))
        result = cursor.fetchall()
        return { "logs": result}
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e), "success": False}


@app.get("/messages", tags=["messages"])
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


@app.get("/messages/{id}", tags=["messages"])
async def get_pending_messages_by_group_id(id: int):
    try:
        cursor.execute('SELECT * FROM "PendingMessage" WHERE "groupId" = (%s)', (id,))
        result = cursor.fetchall()
        return { "messages": result}
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e), "success": False}


@app.get("/messages/{id}/recipients", tags=["messages"])
async def get_pending_messages_recipients(id: int):
    try:
        cursor.execute('SELECT * FROM "PendingMessage" WHERE "groupId" = (%s)', (id,))
        result = cursor.fetchall()
        return { "messages": result}
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e), "success": False}


@app.put("/messages/{id}", tags=["messages"])
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
