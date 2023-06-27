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
not_found_message = b"HTCPCP/1.1 404 Not Found\r\n\r\n"

# states
pouring_milk = None
last_request = None


def main(argv):
    global pouring_milk
    global last_request
    # Set seed
    random.seed(datetime.datetime.now().timestamp())

    # setup logs
    logging.basicConfig(filename="log/coffeepot.log", level=logging.DEBUG)

    # instantiate server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Get the local machine's IP address
    host = HOST

    if len(sys.argv) > 1 and sys.argv[1] == "-local":
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
                ):
                    response = (
                        "HTCPCP/1.1 406 Not Acceptable\r\n\r\n"
                        + ", ".join(list(ACCEPTED_ADDITIONS.keys())).strip(
                            ", "
                        )
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

            safe = [header for header in headers if header.startswith("Safe:")]

            if safe and safe[0] == "Yes":
                message = last_request
                method = message.split(" ")[0]
                url = message.split(" ")[1]
                headers = message.split("\r\n")

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
            )

            if processing_request:

                (
                    additions,
                    processing_request,
                    pouring_milk,
                ) = process_additions(
                    headers, processing_request, pouring_milk, connection
                )

                if processing_request and method in ACCEPTED_METHODS:
                    current_date = datetime.datetime.now().strftime(
                        TIME_STRING_FORMAT
                    )

                    # response body
                    headers_to_send = [
                        "HTCPCP/1.1 200 OK\r\n",
                        "Server: CoffeePot\r\n",
                        "Content-Type: message/coffeepot\r\n",
                        "Date: " + current_date + "\r\n\r\n",
                    ]

                    response = create_request_response(
                        method, message, additions, pouring_milk
                    )

                    final_response = "".join(headers_to_send) + response

                    logging.info("Sending response: " + final_response)

                elif not processing_request:
                    final_response = (
                        "HTCPCP/1.1 406 Not Acceptable\r\n\r\n"
                        + ", ".join(list(ACCEPTED_ADDITIONS.keys())).strip(
                            ", "
                        )
                    )

                connection.send(bytes(final_response.encode("utf-8")))

            processing_request = False

        # close connection after request has been processed
        logging.info("Closing connection")
        connection.close()
        logging.info("Connection closed")


def ensure_request_is_valid(
    url, content_type, method, connection, requested_pot
):
    processing_request = True
    if "coffee://" not in url:
        connection.send(b"HTCPCP/1.1 400 Bad Request\n\n")
        processing_request = False

    if (
        url.split("://")[0].encode().decode("ascii")
        not in ACCEPTED_COFFEE_SCHEMES
    ):
        connection.send(not_found_message)
        processing_request = False
    try:
        if url.split("://")[1] != "ducky":
            connection.send(not_found_message)
            processing_request = False
    except Exception as _:
        connection.send(not_found_message)
        processing_request = False

    if method not in ACCEPTED_METHODS:
        connection.send(b"HTCPCP/1.1 501 Not Implemented\r\n\r\n")
        processing_request = False

    if (
        content_type
        and content_type[0] != "Content-Type: application/coffee-pot-command"
    ):
        connection.send(b"HTCPCP/1.1 415 Unsupported Media Type\r\n\r\n")
        processing_request = False

    if requested_pot == "tea":
        connection.send(b"HTCPCP/1.1 418 I'm a Teapot\r\n\r\n")
        processing_request = False

    return processing_request


def process_additions(headers, processing_request, pouring_milk, connection):
    accept_additions = [
        header for header in headers if header.startswith("Accept-Additions")
    ]

    if len(accept_additions) > 0:
        additions = accept_additions[0].split(":")[1].strip().split(";")
        invalid_addition = False

        pouring_milk = ""
        for item in additions:
            if ACCEPTED_ADDITIONS.get(item.lower().strip()) is None:
                invalid_addition = True
            elif item.lower() in MILKS and pouring_milk == "":
                # pour milk in 10 secs, after brew
                pouring_milk = (
                    datetime.datetime.now()
                    + datetime.timedelta(seconds=BREW_TIME)
                ).strftime(TIME_STRING_FORMAT)

        if invalid_addition:
            processing_request = False
    else:
        additions = None

    return additions, processing_request, pouring_milk


def create_request_response(method, message, additions, pouring_milk):
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

            if pouring_milk == None:
                milk_status = ""
            else:
                milk_status = pouring_milk

            record_to_save = json.dumps(
                {
                    "date": now,
                    "beverage_type": "Coffee",
                    "additions": additions,
                    "brew_time_end": end_time,
                    "pouring_milk": milk_status,
                    "coffee_bean": coffee_bean,
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

        pouring_milk = datetime.datetime.strptime(
            pouring_milk, TIME_STRING_FORMAT
        )
        brew_time_end_object = datetime.datetime.strptime(
            response.get("brew_time_end"), TIME_STRING_FORMAT
        )
        now = datetime.datetime.strptime(
            datetime.datetime.now().strftime(TIME_STRING_FORMAT),
            TIME_STRING_FORMAT,
        )
        if now >= brew_time_end_object and pouring_milk != None:
            response = "299"  # "Milk has stopped pouring."
        else:
            response = "298"  # "Milk is not pouring."

        pouring_milk = None

    return response


if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        print("Exiting Ducky's Coffeepot Server, Bye!")
        exit()
