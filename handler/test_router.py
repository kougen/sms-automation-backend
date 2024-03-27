import random
from typing import Annotated
from fastapi import Query
from lib import create_test_groups, PgRecipient, perform_test_message, test_broadcast_bulk_send, send_bulk_data
from dblib import is_server_up, get_db_cursor_and_connection
from store import test_groups, SRV_ADDR


from fastapi import APIRouter

testrouter = APIRouter()

cursor, connection = get_db_cursor_and_connection()


@testrouter.get("/sendto/{phone_numbers}", tags=["test"])
async def send_test_message_to_numbers(phone_numbers: str, at_the_same_time: bool = False):
    phone_list = phone_numbers.split(",")
    recepients: list[PgRecipient] = [PgRecipient(f"Test Joe {i}", phone_list[i], f"{i}_joe@test.com", i) for i in range(len(phone_list))]
    return perform_test_message(cursor, SRV_ADDR, recepients, "Test message from API", at_the_same_time)


@testrouter.get("/send/{msg_count}", tags=["test"])
async def send_test_message_count(msg_count: int):
    return test_broadcast_bulk_send(cursor, SRV_ADDR, msg_count)


@testrouter.get("/send", tags=["test"])
async def send_test_message_count_on_given_numbers(phone_numbers: Annotated[list[str], Query()] = [], msg_count: int = 0):
    rand_id = random.randint(0, 1000)
    group = create_test_groups(msg_count, rand_id, phone_numbers)
    test_groups[rand_id] = group

    return group.get_json_string()


@testrouter.post("/send", tags=["test"])
def execute_message_send_on_give_group(group_id: int):
    if group_id not in test_groups.keys():
        return {"message": "Invalid ID", "groups": test_groups}

    if not is_server_up(SRV_ADDR):
        return {"message": "SMS Server is down"}

    data = {
        "url": f"/test/realgroup?id={group_id}",
    }

    return send_bulk_data(cursor, SRV_ADDR, data)


@testrouter.get("/groups/{recipient_count}", tags=["test"])
async def send_test_message_to_group(recipient_count: int):
    print(f"Sending test message to group with {recipient_count} recipients")
    rand_id = random.randint(0, 1000)
    trailed_message = testrouterend_cancel_message("Test message from API", ["hu", "rs"])
    group = {
        "id": rand_id,
        "name": "Test Group",
        "message": "Test message from API",
        "trailed_message": trailed_message,
        "enabled": True,
        "lang_codes": ["hu", "rs"]
    }
    recepients: list[PgRecipient] = [PgRecipient(f"Test Joe {i}", f"+test_num_{i}", f"email{i}.test.com", rand_id) for i in range(recipient_count)]
    group["recipients"] = recepients
    return group


@testrouter.get("/realgroup", tags=["test"])
async def send_test_message_to_group_real(id: int):
    if id not in test_groups.keys():
        return {"message": "Invalid ID", "groups": test_groups}
    copied_group = test_groups[id]
    test_groups.pop(id)
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

