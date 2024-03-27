from fastapi import APIRouter
from dblib import is_server_up, get_db_cursor_and_connection
from fastapi.responses import JSONResponse
import datetime
from store import SRV_ADDR, HANDLER_VERSION, CHECKER_VERSION, WEBSITE_VERSION, RECIEVER_VERSION

health_router = APIRouter()

cursor, connection = get_db_cursor_and_connection()

@health_router.get("/ping", tags=["health"])
async def ping():
    data = {
            "time": datetime.datetime.now().isoformat(),
            "timezone": "UTC",
            "status": "up"
        }
    return JSONResponse(content=data)


@health_router.get("/ping/{host}", tags=["health"])
async def ping_db(host: str):
    if host == "phone":
        result = is_server_up(SRV_ADDR)
        return { "host": SRV_ADDR, "status": "up" if result else "down"}


@health_router.get("/version", tags=["health"])
async def get_version():
    return {
        "handler": HANDLER_VERSION,
        "checker": CHECKER_VERSION,
        "website": WEBSITE_VERSION,
        "reciever": RECIEVER_VERSION
    }



@health_router.delete('/purge/db', tags=["health"])
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

@health_router.delete('/purge/{table}', tags=["health"])
async def purge_table(table: str):
    try:
        cursor.execute(f'DELETE FROM %s', (table,))
        connection.commit()
        return {"message": f"{table} Purged", "success": True}
    except Exception as e:
        print(e)
        return {"message": "Error Occurred: " + str(e), "success": False}
