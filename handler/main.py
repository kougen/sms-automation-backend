from fastapi import  FastAPI
from .test_router import testrouter
from .send_router import sendrouter
from .groups_router import groupsrouter
from .health_router import health_router
from .log_router import log_router
from .messages_router import messagesrouter

from lib import msgs
from dblib import get_db_cursor_and_connection
from store import SELF_URL, BASE_PATH

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
app.include_router(health_router, prefix="/health")
app.include_router(log_router)
app.include_router(messagesrouter, prefix="/messages")

@app.get("/", tags=["health"])
async def home_api():
    return {"message": "Hello World"}


@app.get("/trail-messages")
async def get_stopwords():
    return msgs

