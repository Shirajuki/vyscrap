import os # access to curl
import argparse # beautiful CLI program
from datetime import datetime, date, timedelta # handles time
import time # handles timeout and wait
import json # parse json data
import random

# Hardcoded locations
LOCATION = {
    "trondheim": {"location": "Trondheim S", "latitude": "63.436279","longitude": "10.399123"},
    "lillehammer": {"location": "Lillehammer stasjon", "latitude": "61.114912","longitude": "10.461479"}
}
useragents = []
with open("user-agents.txt", "r") as f:
    useragents = [x[:-1] for x in f.readlines()]

# Parse inputs
parser = argparse.ArgumentParser(description='A python CLI for vy.no, effectively displaying train/bus tickets from location A to B')
#parser.add_argument('-f','--foo', help='Description for foo argument', required=True)
parser.add_argument('-f','--from', help='Description for bar argument')
parser.add_argument('-t','--to', help='Description for bar argument')
parser.add_argument('-s','--start-date', help='Description for bar argument')
parser.add_argument('-n','--n', help='Description for bar argument')
args = vars(parser.parse_args())
print(args)

# Parsed inputs
afrom = "lillehammer"
ato = "trondheim"
n = 2
datestring = "2021-09-25"

# Get cookie
datadome = "datadome=W_Oh65wv_0r7vM~6ZdcAKYyKJZ_6ney.-PTVpLI3PrSzT9NlNUO4w~Xb8dODYdjEvPdL7xEgjXpqV.13HKUwHVJ~8xarc.rZoVcfbUaJ19;"

# Run the program n-times
for i in range(n):
    print()
    print(datestring)
    useragent = random.choice(useragents) # doesn't seem to work some of the time, overwrite with working useragent
    useragent = "Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0"

    timestamp = datetime.strptime(datestring, "%Y-%m-%d").isoformat()+"Z"
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
        print(f"{departure} - {arrival}, {duration.rjust(10)} - {price.rjust(6)}")

    # Update the date to the next day
    datestring = timestamp.split("T")[0]
    datestring = datetime.strptime(datestring, "%Y-%m-%d")
    datestring += timedelta(days=1)
    datestring = datetime.strftime(datestring, "%Y-%m-%d")
