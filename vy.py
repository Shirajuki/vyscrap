#!/usr/bin/env python3
import os # access to curl
import argparse # beautiful CLI program
from datetime import datetime, date, timedelta # handles time
import time # handles timeout and wait
import json # parse json data
import random
import textwrap

# Hardcoded locations
LOCATION = {
    "trondheim": {"location": "Trondheim S", "latitude": "63.436279","longitude": "10.399123"},
    "lillehammer": {"location": "Lillehammer stasjon", "latitude": "61.114912","longitude": "10.461479"},
    "oslo": {"location": "Oslo S", "latitude": "59.910357","longitude": "10.753051"},
    "gardermoen": {"location": "Oslo lufthavn", "latitude": "60.193361","longitude": "11.097887"}
}
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Parse inputs
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description='A python CLI for vy.no, effectively displaying train/bus tickets from location A to B', epilog=textwrap.dedent('''
    Get tickets from-to: python3 vy.py -f trondheim -t lillehammer -d 2021-06-09 -n 3
    Get tickets weekday filtered: python3 vy.py -f trondheim -t lillehammer -d 2021-06-09 -n 5 -w mon tue fri
    Made by me, for me c:'''))
parser.add_argument('-f','--from', help='the location you will travel from', type=str, required=True)
parser.add_argument('-t','--to', help='the location you will travel to', type=str, required=True)
parser.add_argument('-d','--departure-date', help='the departure date in format "YYYY-mm-dd"', type=str, required=True)
parser.add_argument('-n','--n', help='the amount of days you want to search', type=int)
parser.add_argument('-w','--weekdays', help='filter on weekdays (mon tue wed thu fri sat sun)', nargs="+")
parser.add_argument('-v','--verbose', help='displays parsed debug', action="store_true")
args = vars(parser.parse_args())
if args['verbose']:
    print("Parsed:", args)

# Parsed inputs
afrom = args['from'] or "lillehammer"
ato = args['to'] or "trondheim"
n = args['n'] or 1
datestring = args['departure_date'] or "2021-09-25"
fweekdays = args['weekdays'] or []

# Specific user information, cookie and useragent
# datadome = "datadome=MveZCgDI-LYTM-cAYSRAdJ_Qq8u~UxFweM6XEmGjbm8gkucCk6oNH-wg4mrG7gPn-_Szk0Z36hgAOuqHcnimgad1h9_qOK9hzur658ddqp"
datadome = os.popen("curl -i -s 'https://www.vy.no/'| grep -Eo 'datadome=.*;' | tr '; ' $'\n' | head -1").read().strip()
useragent = "Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0"

# Run the program n-times
i = 0
while i < n:
    timestamp = datetime.strptime(datestring, "%Y-%m-%d").isoformat()+"Z"
    day = WEEKDAYS[datetime.strptime(datestring, "%Y-%m-%d").weekday()]
    if len(fweekdays) > 0 and day.lower()[:3] not in fweekdays:
        datestring = timestamp.split("T")[0]
        datestring = datetime.strptime(datestring, "%Y-%m-%d")
        datestring += timedelta(days=1)
        datestring = datetime.strftime(datestring, "%Y-%m-%d")
        continue
    i += 1
    print()
    print(datestring, end=" (")
    print(day, end=")\n")
    # Save data, from, to and date
    data = json.dumps({
        "from":{
            "latitude": LOCATION[afrom]['latitude'],
            "longitude": LOCATION[afrom]['longitude'],
            "userQuery":{"searchTerm":LOCATION[afrom]['location']},
            "externalReferences":[]
        },
        "to":{
            "latitude": LOCATION[ato]['latitude'],
            "longitude": LOCATION[ato]['longitude'],
            "userQuery":{"searchTerm":LOCATION[ato]['location']},
            "externalReferences":[]
        },
        "date": timestamp,
        "filter":{"includeModes":["TRAIN","BUS","TRAM","METRO","WATER"]},
        "searchContext":"FIND_JOURNEY_INITIAL"
    })

    # Get id for date
    curl = f"curl -s 'https://www.vy.no/services/itinerary/api/travel-planner/search' -H 'User-Agent: {useragent}' -H 'Accept: application/json' -H 'Accept-Language: en-US,en;q=0.5' --compressed -H 'X-language: no' -H 'terminal-type: WEB' -H 'Content-Type: application/json' -H 'Origin: https://www.vy.no' -H 'DNT: 1' -H 'Connection: keep-alive' -H 'Cookie: {datadome}' -H 'Cache-Control: max-age=0' -H 'TE: Trailers' --data-raw '{data}'"

    data = os.popen(curl).read()
    data = json.loads(data)["suggestions"]
    ids = []
    times = {}
    for suggestion in data:
        suggestion_id = suggestion['id']
        ids.append(suggestion_id)
        parsed_time_value = {"arrival": datetime.fromisoformat(suggestion['arrival']), "departure": datetime.fromisoformat(suggestion['departure']), "duration": suggestion['totalDuration']}
        times[suggestion_id] = parsed_time_value

    # Get price from id
    # ids = json.dumps(["c3a50580-43fb-487d-9bf6-5ea7605a6c2f","c3437810-7628-4de4-9507-f9f2244ac388","2880b942-ee4a-4ece-9bab-fb529fc7e1aa","1ee47292-6958-426e-8bd3-6ad466152c7b","445d8d8b-0a78-4bc1-adca-6640501512b3","3afbbb3c-1087-4cb8-be57-2fddfc2153fb","9bb035f6-1f50-47c1-86c8-c82aad07952b","972ace71-a14f-4072-9820-87ad16701e29"])
    ids = json.dumps(ids)
    curl = f"curl -s 'https://www.vy.no/services/booking/api/offer' -H 'User-Agent: {useragent}' -H 'Accept: application/json' -H 'Accept-Language: en-US,en;q=0.5' --compressed -H 'X-language: no' -H 'terminal-type: WEB' -H 'X-currency: nok' -H 'Content-Type: application/json' -H 'Origin: https://www.vy.no' -H 'DNT: 1' -H 'Connection: keep-alive' -H 'Cookie: "+datadome+"""' -H 'TE: Trailers' --data-raw '{"itineraryIds":"""+ids+""","passengers":[],"addons":[]}'"""
    data = os.popen(curl).read()
    data = json.loads(data)['itineraryOffers']

    prices = []
    suggestions = []
    for suggestion in data:
        time = times[suggestion['itineraryId']]
        price = int(int(suggestion['minimumPrice']['value'])/100)
        updated_suggestion = {"departure": time['departure'], "arrival": time['arrival'], "duration": time['duration'], "price": f"{price},-"}
        suggestions.append(updated_suggestion)

    # Outputs the information of the tickets
    suggestions.sort(key=lambda item:item['departure'], reverse=False)
    for ticket in suggestions:
        departure = datetime.strftime(ticket['departure'], "%H:%M")
        arrival = datetime.strftime(ticket['arrival'], "%H:%M")
        duration = f"({ticket['duration']['hours']}t {ticket['duration']['minutes']}min)"
        price = ticket['price']
        if int(price[:-2]) > 0:
            prices.append(int(price[:-2]))
        print(f"{departure} - {arrival}, {duration.rjust(10)} - {price.rjust(6)}")

    # Outputs the cheapest ticket
    prices.sort()
    cheapest = prices[0]
    cheapest_formatted= '\x1b[93;4m' + str(cheapest)+',-'+ '\x1b[0m'
    print(f">>> Cheapest ticket: {cheapest_formatted}")

    # Update the date to the next day
    datestring = timestamp.split("T")[0]
    datestring = datetime.strptime(datestring, "%Y-%m-%d")
    datestring += timedelta(days=1)
    datestring = datetime.strftime(datestring, "%Y-%m-%d")
