from geopy.geocoders import Nominatim
import urllib.request
import json

def main():
    locator = Nominatim(user_agent="mycroft-covid-update-skill")
    location = locator.geocode("münchen, Germany", addressdetails=True)
    print(location.raw)

if __name__ == "__main__":
    main()
