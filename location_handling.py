import json
from mycroft.util.parse import match_one
from geopy.geocoders import Nominatim
import urllib.request
import requests
import json


class LocationHandler():
    def __init__(self):
        self.admunit_dict, self.state_dict = self._build_dict()
        self.locator = Nominatim(user_agent="mycroft-covid-update-skill")

    
    def get_county(self, query: str):
        location = self.locator.geocode(query+', Deutschland', addressdetails=True)
        # Exception for the city states and larger cities that are their own counties in Germany
        if 'county' not in location.raw['address']:
            return location.raw['address']['city']
        else:
            return location.raw['address']['county']
    
    def get_admunit_code(self, name: str):
        matched_county, conf = match_one(name, list(self.admunit_dict.keys()))
        return matched_county, self.admunit_dict[matched_county], conf
    
    def is_germany(self, query: str):
        return query=='deutschland'
    
    def match_admunits(self, query: str):
        return match_one(query, self.admunit_dict)

    def match_states(self, query: str):
        return match_one(query, self.state_dict)
    
    def _build_dict(self):
        """
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
        """
        url = "https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/rki_admunit_v/FeatureServer/0/query?"
        parameter = {
            'referer':'mycroft-covid-update-skill',
            'user-agent':'python-requests/3.7',
            'where': '1=1',
            'outFields': '*', # Rückgabe aller Felder
            'returnGeometry': False, # Keine Geometrien
            'f':'json', # Rückgabeformat, hier JSON
            'cacheHint': True # Zugriff über CDN anfragen
        }
        result = requests.get(url=url, params=parameter) #Anfrage absetzen
        resultjson = json.loads(result.text) # Das Ergebnis JSON als Python Dictionary laden
        admunit_dict = {}
        state_dict = {}
        for admunit in resultjson['features']:
            admunit_data = admunit['attributes']
            admunit_dict[admunit_data['Name']] = admunit_data['AdmUnitId']
            if admunit_data['AdmUnitId'] > 0 and admunit_data['AdmUnitId'] < 17:
                state_dict[admunit_data['Name']] = admunit_data['AdmUnitId']
        return admunit_dict, state_dict