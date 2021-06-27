import json
from mycroft.util.parse import match_one
from geopy.geocoders import Nominatim
import urllib.request
import json


class LocationHandler():
    def __init__(self):
        self.state_dict, self.county_dict = self._build_dict()
        self.locator = Nominatim(user_agent="mycroft-covid-update-skill")

    
    def get_county(self, query: str):
        location = self.locator.geocode(query, addressdetails=True)
        # Exception for the city states in Germany. They are states and counties simultaneously. Nominatim does not return a county for an address in them
        # but the Covid Data API needs them as Counties
        if location.raw['address']['state'] in ['Hamburg', 'Berlin', 'Bremen']:
            return location.raw['address']['state']
        else:
            return location.raw['address']['county']
    
    def get_county_code(self, name: str):
        matched_code, conf = match_one(name, self.county_dict)
        return matched_code
    
    def _build_dict(self):
        with urllib.request.urlopen("https://api.corona-zahlen.org/states/") as url:
            state_data = json.load(url)['data']
        state_dict = {}
        for key in state_data.keys():
            if key != 'meta':
                state_dict[state_data[key]['name']] = key
        
        with urllib.request.urlopen("https://api.corona-zahlen.org/districts/") as url:
            county_data = json.load(url)['data']
        county_dict = {}
        for key in county_data.keys():
            if key != 'meta':
                county_dict[county_data[key]['name']] = key
        
        return state_dict, county_dict