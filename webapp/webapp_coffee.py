from flask import (
    Flask,
    jsonify,
    request,
    render_template,
    session,
    redirect,
    send_from_directory,
    abort,
)
import sys
import os
import re

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Get the parent directory by going one level up
parent_dir = os.path.dirname(current_dir)

# add the config directory to the system path
config_dir = os.path.join(parent_dir, "config")
sys.path.append(config_dir)

# import from config.py
from config import (
    HOST,
    LOCALHOST,
    COFFEE_SERVER_IP,
    WEBSERVER_PORT,
    COFFEE_SERVER_PORT,
    ERROR_TEMPLATE,
    MILKS,
    ACCEPTED_ADDITIONS,
    COFFEE_POTS,
    TIME_STRING_FORMAT,
)


# Import other libraries
import datetime
import socket
import json

# Manage .env
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Now you can access the environment variables
import os

print("This project is not tested on a real coffee pot.")
print("This project is designed to work with digital (not real) coffee pots.")

app = Flask(__name__)

app.secret_key = os.getenv("APP_SECRET_KEY")
past_coffees_db = "db/past_coffees.json"

# load config from config.py, this is relative to client_coffee.py
app.config.from_pyfile("../config/config.py")


@app.route("/")
def index():
    try:
        additions = request.args.getlist("additions")
        pots = request.args.getlist("pots")
        method = request.args.get("method")
        message_for_server = request.args.get("message")
        if method:
            method = method.lower()

            if not message_for_server:
                message = ""

        if message_for_server:
            message_for_server = message_for_server.lower().strip()

        if (method == "brew" or method == "post") and (
            message_for_server == "start" or message_for_server == "stop"
        ):
            message = "BREW coffee://ducky HTTP/1.1\r\nContent-Type: application/coffee-pot-command"
            if additions:
                message = (
                    message + "\r\nAccept-Additions: " + "; ".join(additions)
                )
            if pots:
                message = message + "\r\nUse-Pot: " + "; ".join(pots)
            message = message + "\r\n\r\n" + message_for_server

        elif method == "when":
            message = "WHEN coffee://ducky HTTP/1.1\r\nContent-Type: application/coffee-pot-command\r\n\r\n"

        elif method == "propfind":
            message = "PROPFIND coffee://ducky HTTP/1.1\r\nContent-Type: application/coffee-pot-command\r\n\r\n"
            return handle_coffee_data(message)

        else:
            return handle_homepage_render()
        print(f"message: {message}")
        return handle_when_brew_post(message)

    except Exception as e:
        return server_error(e)


def connect_to_server(message):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((COFFEE_SERVER_IP, COFFEE_SERVER_PORT))

    server.send(bytes(message.encode()))

    data = server.recv(1024)
    now = datetime.datetime.now().strftime(TIME_STRING_FORMAT)
    print(
        f"\n=======================\nReceived data from server at {now}:\n{data}",
    )
    data = data.decode()
    return data  


def handle_when_brew_post(message):
    # handles the cases when method is when, brew, or post
    # get response from server
    data = connect_to_server(message)

    # filter other error reply cases
    status, response = check_response_status(data)
    if (status != 200):
        return craft_error_template(status, response)

    return redirect("/")


def handle_homepage_render():
    data = connect_to_server("GET coffee://ducky HTTP/1.1\r\nContent-Type: application/coffee-pot-command\r\n\r\n")

    brewing = False
    additions = ""
    contains_milk = False
    brew_time = ""
    brew_time_end = ""
    pour_milk_start = "" 
    finish_brewing_unix = 0
    pour_milk_stop = False

    status, response = check_response_status(data)
    if (status != 200):
        return craft_error_template(status, response)
    
    if data and data.strip():
        response = data.split("\r\n")
        if response[-1].strip() != "{}" and response[-1].strip() != "":
            brewing = True

            brewing_description = json.loads(
                response[-1].strip().replace("'", '"')
            )

            additions = brewing_description["additions"]

            for addition in brewing_description["additions"]:
                if addition.lower() in MILKS:
                    contains_milk = True

            brew_time = brewing_description["date"]
            brew_time_end = brewing_description["brew_time_end"]
            pour_milk_start = brewing_description["pour_milk_start"]

            finish_brewing_unix = datetime.datetime.strptime(
                brew_time_end, TIME_STRING_FORMAT
            ).timestamp()

            # convert pour_milk_start to datetime
            if pour_milk_start != "":
                pour_milk_start = datetime.datetime.strptime(
                    pour_milk_start, TIME_STRING_FORMAT
                )
                brew_time_end_object = datetime.datetime.strptime(
                    brew_time_end, TIME_STRING_FORMAT
                )
                now = datetime.datetime.strptime(
                    datetime.datetime.now().strftime(TIME_STRING_FORMAT),
                    TIME_STRING_FORMAT,
                )

                # is it time to pour milk? has coffee finished brewing?
                if now <= brew_time_end_object:
                    pour_milk_start = ""

                # check if we have stopped pouring milk
                pour_milk_stop = brewing_description.get("pour_milk_stop", False) 

    additions = [addition.strip(" ") for addition in additions]

    # You can inject more illegal additions here
    ACCEPTED_ADDITIONS.update({"tea": "Chamomile"})
    return render_template(
        "index.html",
        header="Welcome to Ducky's CoffeePot",
        accepted_additions=ACCEPTED_ADDITIONS,
        available_pots=COFFEE_POTS,
        additions=additions,
        brew_time=brew_time,
        brew_time_end=brew_time_end,
        contains_milk=contains_milk,
        pour_milk_start=pour_milk_start,
        brewing=brewing,
        finish_brewing_unix=finish_brewing_unix,
        pour_milk_stop=pour_milk_stop,
    )


def handle_coffee_data(message):
    data = connect_to_server(message) 
    response = data.split("\r\n")

    # get the coffee profile response
    coffee_bean = json.loads(response[-1].strip().replace("'", '"'))

    return render_template(
        "coffeedata.html",
        header=coffee_bean.get("name"),
        type=coffee_bean.get("type"),
        origin=coffee_bean.get("origin"),
        profile=coffee_bean.get("profile"),
        strength=coffee_bean.get("strength"),
        roast=coffee_bean.get("roast"),
    )


@app.route("/log")
def coffeepot_log():
    past_coffees = []
    coffees_brewed_count = 0

    with open(past_coffees_db, "r") as f:
        for line in f:
            past_coffees.append(json.loads(line))
            coffees_brewed_count += 1

    past_coffees.reverse()

    return render_template(
        "history.html",
        header="CoffeePot Log",
        past_coffees=past_coffees,
        coffees_brewed_count=coffees_brewed_count,
    )

def check_response_status(data):
    status = 0 
    response = ""
    if data and data.strip():
        response = data.split("\r\n")
        try:               
            status = int(response[0].split()[1])
        except:
            print("The string does not represent an integer.") 
    return status, response

def craft_error_template(status, response):
    if status == 418:
        print("TEAPOT")
        return render_template(
            ERROR_TEMPLATE, title="I'm a Teapot!", error=status
        )
    elif status == 406:
        return render_template(
            ERROR_TEMPLATE, title="Not Acceptable", error=status
        )
    elif status != 200:
        return render_template(
            ERROR_TEMPLATE, title=" ".join(response), error=status
        )  
    else:
        return render_template(
                ERROR_TEMPLATE, title="Other error has occured", error=0
            )   
    
@app.route("/test-400")
def test_400():
    data = connect_to_server("GET caffeine://ducky HTTP/1.1\r\nContent-Type: application/coffee-pot-command\r\n\r\n")
    status, response = check_response_status(data)
    return craft_error_template(status, response)

@app.route("/test-404")
def test_404():
    data = connect_to_server("GET coffee://psyduck HTTP/1.1\r\nContent-Type: application/coffee-pot-command\r\n\r\n")
    status, response = check_response_status(data)
    return craft_error_template(status, response)

@app.route("/test-501")
def test_501():
    data = connect_to_server("MILK coffee://ducky HTTP/1.1\r\nContent-Type: application/coffee-pot-command\r\n\r\n")
    status, response = check_response_status(data)
    return craft_error_template(status, response)

@app.route("/test-415")
def test_415():
    data = connect_to_server("GET coffee://ducky HTTP/1.1\r\nContent-Type: application/tea-pot-command\r\n\r\n")
    status, response = check_response_status(data)
    return craft_error_template(status, response)


## HTTP error handling      
@app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(ERROR_TEMPLATE, title="Page not found", error=404),
        404,
    )


@app.errorhandler(405)
def method_not_allowed(e):
    return (
        render_template(ERROR_TEMPLATE, title="Method not allowed", error=405),
        405,
    )


@app.errorhandler(500)
def server_error(e):
    return (
        render_template(ERROR_TEMPLATE, title="Server error", error=500),
        500,
    )


@app.route("/robots.txt")
def robots():
    return send_from_directory(app.static_folder, "robots.txt")


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(app.static_folder, "favicon.ico")


@app.route("/assets/<path:path>")
def assets(path):
    return send_from_directory("assets", path)


if __name__ == "__main__":
    # total arguments, excluding "python"
    n = len(sys.argv)
    ssl_context = None
    host = HOST
    if "-https" in sys.argv:
        if "-custom" in sys.argv:
            ssl_context = ("cert.pem", "key.pem")
        else:
            ssl_context = "adhoc"
    if "-local" in sys.argv:
        host = LOCALHOST

    app.run(
        debug=True, ssl_context=ssl_context, host=host, port=WEBSERVER_PORT
    )
