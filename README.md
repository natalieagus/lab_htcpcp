# 🐣's Coffee Pot Server ☕️

This project implements the [HTCPCP](https://datatracker.ietf.org/doc/html/rfc2324), a protocol defined by the IETF for controlling, monitoring, and diagnosing coffee pots. This is particularly useful to operate coffee pots remotely. There are two main parts to run:

1. A HTCPCP compliant Coffee Pot **Server**: implemented in Python using the socket library that accepts requests from `coffee://` URI scheme (instead of http or https).
2. A full-stack web application (using Python Flask) that serves a regular HTTP-based web client and also help you send HTCPCP requests to the coffee pot server using your web browser.

## System requirements

A decently working computer with Python 3.10 or above installed + pip. It is assumed that `python` command is aliased to run python 3.10 or above. Otherwise, please change the commands accordingly.

## How to run

Install the requirements, spawn the server:

```
pip install -r requirements.txt
python server/server_pot.py
```

Open another session, then run the client. Afterwards, open your browser at `http://127.0.0.1:5031` to interact with the coffee pot.

```
python webapp/webapp_coffee.py
```

If you want to enable `https`, run it with the `-https` option:

```
python webapp/webapp_coffee.py -https
```

Since we are using self-signed cert with this, you might need to **manually** whitelist the site in your browser.

## Coffee Pot Server

As per the RFC, The Coffee Pot Server accepts these request headers:

1. `BREW`: Brew a coffee. If a coffee is already brewing, no new coffee will be scheduled to brew.
2. `POST`: Same as BREW. However, POST is deprecated and support is only maintained for backwards compatability.
3. `WHEN`: Stop pouring milk.
4. `GET`: Return information about the coffee currently brewing.
5. `PROPFIND`: Return information about the coffee beans that are currently used for brewing. The Coffee Pot server selects this at random from 10 premium beans.

It will take 30 seconds to brew a coffee pot, and the server can only brew one pot at a time. If the server is restarted in the middle of brewing, the coffee is gone (poof!), but etched in the log.

### How it works

The server opens up a regular `socket` and accepts any requests sent to `coffee://ducky`. For a request to be processed, a valid `HTTP`-formatted style request must be sent with any required headers above, for instance:

```
GET coffee://ducky HTTP/1.1
Content-Type: application/coffee-pot-command
```

or:

```
BREW coffee://ducky HTTP/1.1
Content-Type: application/coffee-pot-command
Accept-Additions: cream
Use-Pot: ducky
start
```

## Database

A simple `json` file is used as our database to store information about all coffee requests:

1. `currently_brewing.json`: Stores one record with information on the coffee that is currently brewing.
2. `past_coffees.json`: Stores a log of all coffees brewed with the pot. This feature is useful to help monitor usage of your coffee pot and also to understand the rate at which you brew coffee.

If a `GET` request is made, the contents of the `currently_brewing.json` file are returned. If there's no coffee that's currently browing, an empty JSON object ("{}") is returned.

## The Web Server

Since we want something nice to visualise our interaction with the coffee server, a web interface is built. We use Flask to build this simple interface. This web interface relays `HTTP` (or `HTTPS`) requests formatted in a specific way to the frontend server, and the frontend server will pack our requests via `socket` to our Coffee Pot Server. The web interface allows you to interact with the digital coffee pot. You can **request** the coffee pot make a coffee, **stop** a coffee brewing any further, view the beans used to brew your current coffee and **stop** the pouring of milk if milk is presently being poured.

It also **shows** the status of any coffee currently brewing, and it can "connect to the database" to show the log of coffees made with the coffee pot. Since Coffee Pot Server (our backend) and the Web Server is hosted at the same machine, they can both view `past_coffee.json` (our simple database).

## `config.py`

This config file can be accessed by both the frontend and backend servers. This is not usually the case in production, but used in this mini project for convenience. It contains many configurations about: host port, coffee beans, milk type, accepted methods, coffee chemes, etc.

## Credits

[The base code for project was originally taken from here](https://jamesg.blog/2021/11/18/hypertext-coffee-pot/), refactored, styled and adapted with more functionalities added to suit our learning experience in the lab. Special thanks to CSE TAs Cassie and Ryan for the inspiration, ideas, and contribution to create this lab.
