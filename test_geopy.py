from geopy.geocoders import Nominatim
import urllib.request
import json

def main():
    # locator = Nominatim(user_agent="mycroft-covid-update-skill")
    # location = locator.geocode("Schleswig-Flensburg", addressdetails=True)
    # print(location.raw)
    with urllib.request.urlopen("https://api.corona-zahlen.org/districts/02000") as url:
        data = json.load(url)
        print(data)

if __name__ == "__main__":
    main()
