from mycroft import MycroftSkill, intent_file_handler
from .location_config import LocationConfig
from .location_handling import LocationHandler
import urllib.request
import json


class CovidUpdate(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    def initialize(self):
        self.location_config = LocationConfig(self.config_core)
        self.location_handler = LocationHandler()
        
        self.location_config.county = self.location_handler.get_county(self.location_config.city + ", " + self.location_config.state)
        self.location_config.county_code = self.location_handler.get_county_code(self.location_config.county)

    @intent_file_handler('update.covid.intent')
    def handle_update_covid(self, message):
        covid_data = self._get_covid_data_county(self.location_config.county_code)
        self.speak_dialog('update.covid', self._build_county_dialog(covid_data))


    def _get_covid_data_county(self, county_code: str):
        with urllib.request.urlopen("https://api.corona-zahlen.org/districts/"+county_code) as url:
            covid_data = json.load(url)
        return covid_data['data'][county_code]
    
    def _build_county_dialog(self, covid_data: dict):
        data_dict = {}
        data_dict['name'] = covid_data['name']
        data_dict['weekIncidenceWhole'] = str(covid_data['weekIncidence']).split('.')[0]
        data_dict['weekIncidenceDecimal'] = str(covid_data['weekIncidence']).split('.')[1][:1]
        data_dict['deltaCases'] = covid_data['delta']['cases']
        data_dict['deltaDeaths'] = covid_data['delta']['deaths']
        return data_dict


def create_skill():
    return CovidUpdate()

