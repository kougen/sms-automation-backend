from fastapi import APIRouter
from dblib import get_db_cursor_and_connection, insert_log, insert_logs, PgLog, get_db_cursor_and_connection
from lib import LogRequest, LogsRequest
import threading

log_router = APIRouter()
cursor, connection = get_db_cursor_and_connection()

@log_router.post("/log", tags=["logs"])
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
    return PgLog(request.level, request.message, request.tool, request.timezone, request.logged_at, request.comment)

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

@log_router.post("/", tags=["logs"])
async def log_multiple_messages(request: LogsRequest):
    logs = request.logs
    print(f"Received {len(logs)} logs")  
    pgLogs = [convertRequestToLog(log) for log in logs]
    threading.Thread(target=insert_logs_thread, args=(pgLogs,)).start()
    return {"message": "Thanks for the logs", "success": True}

@log_router.delete("/", tags=["logs"])
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


@log_router.get("/", tags=["logs"])
async def get_logs():
    try:
        cursor.execute('SELECT * FROM "Log"')
        result = cursor.fetchall()
        return { "logs": result}
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e), "success": False}


@log_router.get("/{level}", tags=["logs"])
async def get_logs_by_level(level: str):
    try:
        cursor.execute('SELECT * FROM "Log" WHERE "level" = (%s)', (level,))
        result = cursor.fetchall()
        return { "logs": result}
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e), "success": False}


@log_router.get("/{level}/{tool}", tags=["logs"])
async def get_logs_by_level_and_tool(level: str, tool: str):
    try:
        cursor.execute('SELECT * FROM "Log" WHERE "level" = (%s) AND "tool" = (%s)', (level, tool))
        result = cursor.fetchall()
        return { "logs": result}
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e), "success": False}
