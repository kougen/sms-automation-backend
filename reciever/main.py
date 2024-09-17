import socket
import os
import sys
from pathlib import Path
import threading
from dotenv import load_dotenv
import json
from psycopg.connection import Connection

from psycopg.cursor import Cursor

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT")
if ENVIRONMENT == "development":   
    path_root = Path(__file__).parents[1]
    script_path = os.path.join(path_root)
    sys.path.append(script_path)

from dblib import has_subscription, get_db_cursor_and_connection, insert_log

RECEIVER_IP = '0.0.0.0'
RECEIVER_PORT = 5002
RECEIVER_ADDR = (RECEIVER_IP, RECEIVER_PORT)

def handler_data(data, conn: socket.socket, cursor: Cursor, connection: Connection):
    json_data = json.loads(data)
    phone = json_data['sender']
    message = json_data['message']  # type: str
    if not ("STOP" in message.upper() or "Stap" in message.upper() or "Stopp" in message.upper()):
        print(f"Received: {phone}, but no STOP message (or similar) found: {message}")
        insert_log(cursor, "INFO", f"Received: {phone}, but no STOP message (or similar) found: {message}", "RECEIVER")
        conn.sendall(b"NO_ACTION_REQUIRED")
        conn.close()
        return
    print(f"Received: {phone}")
    if not has_subscription(cursor, phone):
        print(f"Phone {phone} does not have a subscription")
        insert_log(cursor, "INFO", f"Phone {phone} does not have a subscription", "RECEIVER")
        conn.sendall(b"NO_ACTION_REQUIRED")
        conn.close()
        return
    try:
        # Count the records with the given phone number
        cursor.execute('SELECT COUNT(*) FROM "Recipient" WHERE "phone" = (%s)', (phone,))
        count = cursor.fetchone()
        if count is not None:
            count = count[0]
        print(f"Unsubscribing {count} records with phone {phone}")
        # Setting the 'isSubscribed' to False for all records with the given phone number
        cursor.execute('UPDATE "Recipient" SET "isSubscribed" = FALSE WHERE "phone" = (%s)', (phone,))
        connection.commit()
        insert_log(cursor, "INFO", f"Deleted {count} records with phone {phone}", "RECEIVER")
        conn.sendall(b"OK")
        print(f"Deleted {count} records with phone {phone}")
    except Exception as e:
        print(e)
        conn.sendall(b"ERROR")
        print(f"Error deleting records with phone {phone}, {e}")
        insert_log(cursor, "ERROR", f"Error deleting records with phone {phone}, {e}", "RECEIVER")
    conn.close()


def main():

    result = get_db_cursor_and_connection()

    if not result:
        raise Exception("Could not connect to database")

    cursor, connection = result
    receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    receiver.bind(RECEIVER_ADDR)
    receiver.listen()
    print(f"Listening on {RECEIVER_ADDR}")
    try:
        while True:
            conn, addr = receiver.accept()
            print(f"Connected to {addr}")
            data = conn.recv(2048)
            if b'PING' in data:
                print("Received PING")
                conn.sendall(b'PONG')
                conn.close()
                continue
            handler_data(data, conn, cursor, connection)
    except KeyboardInterrupt:
        print("Closing server")
        receiver.close()
        cursor.close()
        connection.close()
        exit(0)


if __name__ == "__main__":
    main()

