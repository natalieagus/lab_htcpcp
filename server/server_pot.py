import sys
import os
import random

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Get the parent directory by going one level up
parent_dir = os.path.dirname(current_dir)

# Add the config directory to the system path
config_dir = os.path.join(parent_dir, "config")
sys.path.append(config_dir)

from config import (
    HOST,
    LOCALHOST,
    COFFEE_SERVER_PORT,
    ACCEPTED_COFFEE_SCHEMES,
    ACCEPTED_METHODS,
    MILKS,
    ACCEPTED_ADDITIONS,
    COFFEE_BEANS,
    TIME_STRING_FORMAT,
    COFFEE_BEANS_VARIETY,
    BREW_TIME,
)
import datetime
import logging
import socket
import json
import os

# standard constants
brewing_file = "db/currently_brewing.json"
past_coffee_file = "db/past_coffees.json"


def main(argv):
    # Set seed
    random.seed(datetime.datetime.now().timestamp())

    # setup logs
    logging.basicConfig(filename="log/coffeepot.log", level=logging.DEBUG)

    # instantiate server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Get the local machine's IP address
    host = HOST

    if len(sys.argv) > 1 and  "-local" in sys.argv:
        host = LOCALHOST

    server.bind((host, COFFEE_SERVER_PORT))

    # rewrite the currently brewing file every time the program starts up
    # a coffee pot that has been stopped in the middle of operation should not pick up where it left off (!)
    with open(brewing_file, "w+") as f:
        f.write("{}")

    if not os.path.isfile(past_coffee_file):
        with open(past_coffee_file, "w+") as f:
            f.write("")

    # start listening for connections
    CHECK_INTERVAL = 1.0
    server.settimeout(
        CHECK_INTERVAL
    )  # Check for SIGINT every `CHECK_INTERVAL` seconds
    server.listen()
    print(
        f"Listening for connections on {str(host)}:{str(COFFEE_SERVER_PORT)}"
    )
    while True:

        # Restart `accept` call every cycle, so a `SIGINT` can go through (for Windows)
        try:
            connection, address = server.accept()
        except TimeoutError:
            continue

        # set timeout so requests cannot hang
        connection.settimeout(5)

        print("\n====================\nConnected to: ", address)

        processing_request = True

        while processing_request:
            # get message
            message = connection.recv(1024)
            now = datetime.datetime.now().strftime(TIME_STRING_FORMAT)
            print(f"Message received at {now}:\n{message}")
            message = message.decode()

            last_request = message

            if len(message.strip().replace("\n", "").replace("\r", "")) == 0:
                processing_request = False

            logging.info("Received message: " + message)

            # get last coffee
            with open(brewing_file, "r") as f:
                last_coffee = json.load(f)

            method = message.split(" ")[0]
            if (
                last_coffee
                and last_coffee["brew_time_end"]
                and (method == "BREW" or method == "POST")
            ):
                # get last_coffee["brew_time_end"] as datetime object
                last_brewed = datetime.datetime.strptime(
                    last_coffee["brew_time_end"], TIME_STRING_FORMAT
                )
                if (
                    last_brewed + datetime.timedelta(seconds=BREW_TIME)
                    > datetime.datetime.now()
                ) and message.find("stop") == -1:
                    # this is when you want to brew a coffee again when the pot is still brewing something
                    response = (
                        "HTCPCP/1.1 406 Not Acceptable\r\n\r\n" + "Pot is busy"
                    )
                    connection.send(bytes(response.encode()))
                    processing_request = False
                else:
                    with open(brewing_file, "w+") as f:
                        f.write("{}")

            url = message.split(" ")[1]
            headers = message.split("\r\n")

            content_type = [
                header
                for header in headers
                if header.startswith("Content-Type")
            ]

            try:
                requested_pot = (
                    [
                        header
                        for header in headers
                        if header.startswith("Use-Pot")
                    ][0]
                    .split(":")[1]
                    .strip()
                    .split(";")
                )
                requested_pot = requested_pot[0]
            except Exception as e:
                requested_pot = ""

            processing_request = ensure_request_is_valid(
                url,
                content_type,
                method,
                connection,
                requested_pot,
                ACCEPTED_COFFEE_SCHEMES,
                ACCEPTED_METHODS,
                b"HTCPCP/1.1 404 Server Could Not be Found\r\n\r\n" 
            )

            if processing_request:

                (
                    additions,
                    processing_request,
                    pour_milk_start,
                ) = process_additions(
                    headers, processing_request, connection
                )

                if processing_request and method in ACCEPTED_METHODS:
                    current_date = datetime.datetime.now().strftime(
                        TIME_STRING_FORMAT
                    )

                    ## TODO: Create response headers 
                    headers_to_send = []

                    response = create_request_response(
                        method, message, additions, pour_milk_start
                    )

                    final_response = "".join(headers_to_send) + response

                    logging.info("Sending response: " + final_response)

                else:
                    # TODO: Handle other cases that passes ensure_request_is_valid but isn't supported
                    # if we reach here, request is valid, but the server doesn't support this feature 
                    # e.g: 406
                    final_response = ""
                    

                connection.send(bytes(final_response.encode("utf-8")))

            processing_request = False

        # close connection after request has been processed
        logging.info("Closing connection")
        connection.close()
        logging.info("Connection closed")


def send_error_message(connection, message):
    """Send an error message to the connection and return False."""
    connection.send(message)
    return False

def ensure_request_is_valid(url, content_type, method, connection, requested_pot,
                            accepted_coffee_schemes, accepted_methods, not_found_message):
    # TODO: Basic request checking 
    """
    This method checks if the URL scheme is correct. You shall: 
    
    1. Validate the scheme against accepted_coffee_schemes
    2. Check for correct URL path format
    3. Validate the HTTP method: check method against accepted_methods
    4. Check the content type format to conform to "application/coffee-pot-command"
    5. Specific check for "tea" pot request

    If all checks pass, return True, otherwise return False

    For each case 1 to 5 above, call send_error_message(error_message) with an appropriately crafted error message containing status code and reason-phrase. The arg not_found_message gives you a general idea of the format of the expected error message conforming to HTCPCP/1.0 protocol.
    """
    return True

def process_additions(headers, processing_request, connection):
    accept_additions = [
        header for header in headers if header.startswith("Accept-Additions")
    ]

    pour_milk_start = ""

    if len(accept_additions) > 0:
        additions = accept_additions[0].split(":")[1].strip().split(";")
        invalid_addition = False

        pour_milk_start = ""
        for item in additions:
            if ACCEPTED_ADDITIONS.get(item.lower().strip()) is None:
                invalid_addition = True
            elif item.lower() in MILKS and pour_milk_start == "":
                # pour milk in 10 secs, after brew
                pour_milk_start = (
                    datetime.datetime.now()
                    + datetime.timedelta(seconds=BREW_TIME)
                ).strftime(TIME_STRING_FORMAT)

        if invalid_addition:
            processing_request = False
    else:
        additions = None

    return additions, processing_request, pour_milk_start


def create_request_response(method, message, additions, pour_milk_start):
    response = ""

    if method == "GET":
        with open(brewing_file, "r") as f:
            response = json.load(f)
            response = json.dumps(response)

    if method == "PROPFIND":
        with open(brewing_file, "r") as f:
            currently_brewing = json.load(f)

        coffee_bean = currently_brewing.get("coffee_bean")
        response = json.dumps(coffee_bean)

    elif method == "BREW" or method == "POST":
        response_body = message.split("\r\n\r\n")[-1]

        if response_body == "stop":
            with open(brewing_file, "w+") as f:
                f.write("{}")
        elif response_body == "start":
            now = datetime.datetime.now().strftime(TIME_STRING_FORMAT)
            end_time = (
                datetime.datetime.now() + datetime.timedelta(seconds=BREW_TIME)
            ).strftime(TIME_STRING_FORMAT)
            coffee_bean = COFFEE_BEANS[random.randint(0, COFFEE_BEANS_VARIETY)]

            if additions == None:
                additions = []

            if pour_milk_start == None:
                milk_status = ""
            else:
                milk_status = pour_milk_start

            record_to_save = json.dumps(
                {
                    "date": now,
                    "beverage_type": "Coffee",
                    "additions": additions,
                    "brew_time_end": end_time,
                    "pour_milk_start": milk_status,
                    "coffee_bean": coffee_bean,
                    "pour_milk_stop": False
                }
            )

            with open(past_coffee_file, "a+") as coffee_records:
                coffee_records.write(record_to_save + "\n")

            with open(brewing_file, "w+") as brewing_record:
                brewing_record.write(record_to_save)
        else:
            response = "HTCPCP/1.1 400 Bad Request\r\n\r\n"

    elif method == "WHEN":
        with open(brewing_file, "r") as f:
            response = json.load(f)
        pour_milk_start = datetime.datetime.strptime(
            response.get("pour_milk_start"), TIME_STRING_FORMAT
        )
        brew_time_end_object = datetime.datetime.strptime(
            response.get("brew_time_end"), TIME_STRING_FORMAT
        )
        now = datetime.datetime.strptime(
            datetime.datetime.now().strftime(TIME_STRING_FORMAT),
            TIME_STRING_FORMAT,
        )
        if now >= brew_time_end_object and pour_milk_start != None:
            response["pour_milk_stop"] = True
        update_current_brew(response)
        # save to file 
        response = json.dumps(response)
    return response


def update_current_brew(response):
    new_record = []
    with open(brewing_file, 'r') as coffee_records:
        for line in coffee_records:
            current_coffee = json.loads(line)
            if response.get("date", False) == current_coffee.get("date", False):
                current_coffee["pour_milk_stop"] = response.get("pour_milk_stop", False)
            new_record.append(json.dumps(current_coffee))
            
    # Write the modified content back to the file or a new file.
    with open(brewing_file, 'w') as file:  # Use 'file_path' for the same file or 'new_file_path' for a new file.
        for coffee_record in new_record:
            file.write(coffee_record + '\n') 

if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        print("Exiting Ducky's Coffeepot Server, Bye!")
        exit()
