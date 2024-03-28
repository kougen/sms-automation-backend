import random
from typing import Annotated
from fastapi import Query
from lib import append_cancel_message, create_test_groups, PgRecipient, perform_test_message, update_message, send_message
from dblib import get_db_cursor_and_connection
from store import test_groups, SELF_URL


from fastapi import APIRouter

testrouter = APIRouter()

cursor, connection = get_db_cursor_and_connection()


@testrouter.post("/addmessage", tags=["test"])
async def add_message_to_pending_queue():
    group_id = random.randint(0, 1000)
    access_url = f"{SELF_URL}/nonexistent/{group_id}"
    return send_message(cursor, group_id, access_url, "pending")

@testrouter.get("/send", tags=["test"])
async def send_test_message_count_on_given_numbers(phone_numbers: Annotated[list[str], Query()] = [], msg_count: int = 0):
    rand_id = random.randint(0, 1000)
    group = create_test_groups(msg_count, rand_id, phone_numbers)
    test_groups[rand_id] = group
    access_url = f"{SELF_URL}/test/realgroup"
    result = perform_test_message(cursor, rand_id, access_url)
    if result:
        print("Registered pending message")

    return group.get_json_string()

@testrouter.get("/send/{recipient_count}", tags=["test"])
async def send_test_message_to_group(recipient_count: int):
    print(f"Sending test message to group with {recipient_count} recipients")
    rand_id = random.randint(0, 1000)
    group = create_test_groups(recipient_count, rand_id)
    test_groups[rand_id] = group
    access_url = f"{SELF_URL}/test/realgroup"
    result = perform_test_message(cursor, rand_id, access_url)
    if result:
        print("Registered pending message")
    return group.get_json_string()


@testrouter.get("/realgroup", tags=["test"])
async def send_test_message_to_group_real(group_id: int, message_id: int):
    if group_id not in test_groups.keys():
        cursor.execute('DELETE FROM "PendingMessages" WHERE "groupId" = (%s)', (group_id,))
        return {"message": "Invalid ID, group not found. Deleted from pending messages."}
    copied_group = test_groups[group_id]
    test_groups.pop(group_id)
    update_message(cursor, message_id, "fetched")
    return copied_group.get_json_string()


@testrouter.get("/realgroup/all", tags=["test"])
async def send_test_message_to_group_real_all():
    return test_groups


@testrouter.delete("/realgroup", tags=["test"])
async def delete_test_group(id: int):
    if id not in test_groups:
        return {"message": "Invalid ID"}
    test_groups.pop(id)
    return {"message": "Group Deleted", "success": True}


@testrouter.delete("/realgroup/all", tags=["test"])
async def delete_all_test_groups():
    test_groups.clear()
    return {"message": "All Groups Deleted", "success": True}

