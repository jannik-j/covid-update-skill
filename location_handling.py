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
        location = self.locator.geocode(query+', Deutschland', addressdetails=True)
        # Exception for the city states and larger cities that are their own counties in Germany
        if 'county' not in location.raw['address']:
            return location.raw['address']['city']
        else:
            return location.raw['address']['county']
    
    def get_county_code(self, name: str):
        matched_county, conf = match_one(name, list(self.county_dict.keys()))
        return matched_county, self.county_dict[matched_county], conf
    
    def is_germany(self, query: str):
        return query=='deutschland'
    
    def match_states(self, query: str):
        return match_one(query, self.state_dict)
    
    def match_counties(self, query: str):
        return match_one(query, self.county_dict)
    
    def _build_dict(self):
        with urllib.request.urlopen("https://api.corona-zahlen.org/states") as url:
            state_data = json.load(url)['data']
        state_dict = {}
        for key in state_data.keys():
            if key != 'meta':
                state_dict[state_data[key]['name']] = key
        
        with urllib.request.urlopen("https://api.corona-zahlen.org/districts") as url:
            county_data = json.load(url)['data']
        county_dict = {}
        for key in county_data.keys():
            if key != 'meta':
                county_dict[county_data[key]['name']] = key
        
        return state_dict, county_dict