HOST = "0.0.0.0"
COFFEE_SERVER_IP = "127.0.0.1"
LOCALHOST = "localhost"
COFFEE_SERVER_PORT = 5030
WEBSERVER_PORT = 5031
BREW_TIME = 30
ERROR_TEMPLATE = "error.html"
TIME_STRING_FORMAT = "%a, %d %b %Y %H:%M:%S"
ACCEPTED_METHODS = ["BREW", "POST", "GET", "PROPFIND", "WHEN"]
ACCEPTED_COFFEE_SCHEMES = [
    "koffie",
    "q%C3%A6hv%C3%A6",
    "%D9%82%D9%87%D9%88%D8%A9",
    "akeita",
    "koffee",
    "kahva",
    "kafe",
    "caf%C3%E8",
    "%E5%92%96%E5%95%A1",
    "kava",
    "k%C3%A1va",
    "kaffe",
    "coffee",
    "kafo",
    "kohv",
    "kahvi",
    "%4Baffee",
    "%CE%BA%CE%B1%CF%86%CE%AD",
    "%E0%A4%95%E0%A5%8C%E0%A4%AB%E0%A5%80",
    "%E3%82%B3%E3%83%BC%E3%83%92%E3%83%BC",
    "%EC%BB%A4%ED%94%BC",
    "%D0%BA%D0%BE%D1%84%D0%B5",
    "%E0%B8%81%E0%B8%B2%E0%B9%81%E0%B8%9F",
]

MILKS = [
    "cream",
    "half-and-half",
    "whole-milk",
    "part-skim",
    "skim",
    "oat milk",
    "almond milk",
    "soya milk",
    "coconut milk",
    "non-dairy",
]

ACCEPTED_ADDITIONS = {
    "cream": "Cream",
    "half-and-half": "Half-and-half",
    "whole-milk": "Whole milk",
    "part-skim": "Part skimmed milk",
    "skim": "Skimmed milk",
    "non-dairy": "Non-dairy milk",
    "vanilla": "Vanilla syrup",
    "almond": "Almond syrup",
    "raspberry": "Raspberry syrup",
    "chocolate": "Chocolate syrup",
    "whisky": "Whisky",
    "rum": "Rum",
    "kahlua": "Kahlua",
    "aquavit": "Aquavit",
    "oat milk": "Oat milk",
    "soya milk": "Soya milk",
    "coconut milk": "Coconut milk",
    "almond milk": "Almond milk",
}

COFFEE_POTS = {"ducky": "Ducky's Coffee Pot", "tea": "Ducky's Tea Pot"}

COFFEE_BEANS = {
    0: {
        "name": "Sidamo Mountain Coffee",
        "profile": "Chocolate, Floral, Spice",
        "origin": "Ethiopia, Africa",
        "type": "Single Origin",
        "strength": "3/5",
        "roast": "Medium Dark",
    },
    1: {
        "name": "Yirgacheffe Heirloom Coffee",
        "profile": "Citrus, Malty",
        "origin": "Ethiopia, Africa",
        "strength": "1/5",
        "roast": "Medium",
    },
    2: {
        "name": "Milano Morning Coffee",
        "profile": "Chocolate, Malty, Nutty",
        "origin": "N/A",
        "type": "Fine Flavoured",
        "strength": "2/5",
        "roast": "Medium",
    },
    3: {
        "name": "Star of Hanoi Coffee",
        "profile": "Spice",
        "origin": "Vietnam, Asia",
        "type": "Single Origin",
        "strength": "2.5/5",
        "roast": "Medium dark",
    },
    4: {
        "name": "Black Pearl Coffee",
        "profile": "Chocolate, Spice",
        "origin": "Kenya, Africa",
        "type": "Single Origin",
        "strength": "3/5",
        "roast": "Medium dark",
    },
    5: {
        "name": "Turquino Coffee",
        "profile": "Spice",
        "origin": "Cuba, Central America And The Caribbean",
        "type": "Single Origin",
        "strength": "1.5/5",
        "roast": "Medium dark",
    },
    6: {
        "name": "1910 Coffee",
        "profile": "Fruity",
        "origin": "N/A",
        "type": "Fine Flavoured",
        "strength": "1.5/5",
        "roast": "Medium",
    },
    7: {
        "name": "Flores del Café Superior Coffee",
        "profile": "Floral, Fruity, Malty",
        "origin": "Nicaragua, Central America And The Caribbean",
        "type": "Single Origin",
        "strength": "1.5/5",
        "roast": "Medium light",
    },
    8: {
        "name": "Paraíso Gold Coffee",
        "profile": "Chocolate, Floral, Fruity, Malty, Nutty",
        "origin": "Brazil, South America",
        "type": "Single Origin",
        "strength": "2/5",
        "roast": "Medium light",
    },
    9: {
        "name": "Honey Dragon Coffee",
        "profile": "Fruity, Malty, Nutty",
        "origin": "China, Asia",
        "type": "Single Origin",
        "strength": "2.5/5",
        "roast": "Medium dark",
    },
}

COFFEE_BEANS_VARIETY = len(COFFEE_BEANS) - 1
