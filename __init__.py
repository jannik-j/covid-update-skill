from mycroft import MycroftSkill, intent_file_handler, intent_handler
from adapt.intent import IntentBuilder
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

    @intent_handler(IntentBuilder('CovidUpdate')
                                        .require('Covid')
                                        .require('Update')
                                        .optionally('MyLocation')
                                        .optionally('Location'))
    def handle_update_covid(self, message):
        code, level = self._get_loc_and_level(message)
        self.log.info('Got code '+code+' and level '+level+' for the requested location and level')
        covid_data = self._get_covid_data(code, level)
        dialog_dict = self._build_update_dialog(covid_data)
        if level is 'germany':
            rvalue = str(covid_data['r']['value']).split('.')
            dialog_dict['rvalueWhole'] = rvalue[0]
            dialog_dict['rvalueDecimal'] = rvalue[1]
            dialog_dict['name'] = 'Deutschland'
        self.speak_dialog('update.covid', dialog_dict)
        self.speak_dialog('new.cases', dialog_dict)
        self.speak_dialog('week.incidence', dialog_dict)
        if 'rvalueWhole' in dialog_dict:
            self.speak_dialog('rvalue', dialog_dict)


    def _get_covid_data(self, code: str, level: str):
        url = "https://api.corona-zahlen.org/"+level+'/'+code
        self.log.info('Trying to access api at '+url)
        with urllib.request.urlopen(url) as api_data:
            covid_data = json.load(api_data)
        
        if level is 'germany':
            return covid_data
        else:
            return covid_data['data'][code]
    
    def _build_update_dialog(self, covid_data: dict):
        data_dict = {}
        if 'name' in covid_data:
            data_dict['name'] = covid_data['name']
        if covid_data['weekIncidence'] > 0:
            data_dict['weekIncidenceWhole'] = str(covid_data['weekIncidence']).split('.')[0]
            data_dict['weekIncidenceDecimal'] = str(covid_data['weekIncidence']).split('.')[1][:1]
        else:
            data_dict['weekIncidenceWhole'] = '0'
            data_dict['weekIncidenceDecimal'] = '0'
        data_dict['deltaCases'] = covid_data['delta']['cases']
        data_dict['deltaDeaths'] = covid_data['delta']['deaths']
        return data_dict
    
    def _get_loc_and_level(self, message):
        if self.voc_match(message.data.get('utterance'), 'MyLocation', exact=True):
            self.log.info('Got Keyword for MyLocation')
            return self.location_config.county_code, 'districts'
        
        elif message.data.get('Location'):
            location = message.data.get('Location')
            self.log.info('Got Location '+location)
            # If the given Location is Germany, the skill shall respond with the statistics for the whole country
            if self.location_handler.is_germany(location):
                return '', 'germany'
            
            else:
                # If the given Location is one of the states, the skill should respond with the statistics for that state
                matched_state, conf = self.location_handler.match_states(location)
                if conf > 0.75:
                    self.log.info('Location is matched with the state '+matched_state)
                    return matched_state, 'states'
                
                # Else, we search for the Location and give the statistics for the respective county
                else:
                    county = self.location_handler.get_county(location)
                    self.log.info('Gelocation yielded the county '+county+' for the location')
                    matched_county, county_code, conf = self.location_handler.get_county_code(county)
                    self.log.info('Matched '+county+' to '+matched_county+' with confidence '+str(conf))
                    return county_code, 'districts'
        
        # If no Location is provided, the skill should give an update for Germany
        else:
            return '', 'germany'
            
            

def create_skill():
    return CovidUpdate()

