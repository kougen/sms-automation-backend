from dotenv import load_dotenv
import os
import sys
from pathlib import Path
import time
load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT")
if ENVIRONMENT == "development":   
    path_root = Path(__file__).parents[1]
    script_path = os.path.join(path_root)
    sys.path.append(script_path)

from dblib import wait_for_healthy_website

WEBSITE_URL = os.getenv("WEBSITE_URL")


if not WEBSITE_URL:
    WEBSITE_URL = "http://localhost:3000"

def main():
    print("Hello World")
    while True:
        wait_for_healthy_website(base_url=WEBSITE_URL)
        print("Website is healthy")
        # Wait of 20 minutes
        time.sleep(1200)


if __name__ == "__main__":
    main()
