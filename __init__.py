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
        self.speak_dialog('update.covid', dialog_dict)
        self.speak_dialog('new.cases', dialog_dict)
        self.speak_dialog('week.incidence', dialog_dict)
        if 'rvalueWhole' in dialog_dict:
            self.speak_dialog('rvalue', dialog_dict)
    
    @intent_handler(IntentBuilder('VaccinationProgress')
                                        .require('Vaccination')
                                        .require('Progress')
                                        .optionally('Covid')
                                        .optionally('MyLocation')
                                        .optionally('Location'))
    def handle_vaccination_progress(self, message):
        code, level = self._get_loc_and_level(message)
        self.log.info('Got code '+code+' and level '+level+' for the requested location and level')
        if level is 'districts':
            self.speak_dialog('vacc.not.at.district.level')
        else:
            vacc_data = self._get_vaccination_data()
            if level is not 'germany':
                vacc_data = vacc_data['states'][code]
            data_dict = self._build_vaccination_dialog(vacc_data)
            self.speak_dialog('vaccination.progress', data_dict)
            self.speak_dialog('vaccination.quota.first', data_dict)
            self.speak_dialog('vaccination.quota.second', data_dict)
            self.speak_dialog('vaccination.delta', data_dict)


    def _get_covid_data(self, code: str, level: str):
        url = "https://api.corona-zahlen.org/"+level+'/'+code
        self.log.info('Trying to access api at '+url)
        with urllib.request.urlopen(url) as api_data:
            covid_data = json.load(api_data)
        
        if level is 'germany':
            return covid_data
        else:
            return covid_data['data'][code]
    
    def _get_vaccination_data(self):
        url = 'https://api.corona-zahlen.org/vaccinations'
        self.log.info('Trying to access api at '+url)
        with urllib.request.urlopen(url) as api_data:
            vacc_data = json.load(api_data)['data']
        return vacc_data
    
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
    
    def _build_update_dialog(self, covid_data: dict):
        data_dict = {}
        if 'name' in covid_data:
            data_dict['name'] = covid_data['name']
        else:
            data_dict['name'] = 'deutschland'
        if covid_data['weekIncidence'] > 0:
            data_dict['weekIncidenceWhole'] = str(covid_data['weekIncidence']).split('.')[0]
            data_dict['weekIncidenceDecimal'] = str(covid_data['weekIncidence']).split('.')[1][:1]
        else:
            data_dict['weekIncidenceWhole'] = '0'
            data_dict['weekIncidenceDecimal'] = '0'
        data_dict['deltaCases'] = covid_data['delta']['cases']
        data_dict['deltaDeaths'] = covid_data['delta']['deaths']
        return data_dict

    def _build_vaccination_dialog(self, vacc_data: dict):
        data_dict = {}
        if 'name' in vacc_data:
            data_dict['name'] = vacc_data['name']
        else:
            data_dict['name'] = 'deutschland'
        quota_first_vacc = round(vacc_data['quote'], 3)
        data_dict['quotaFirstVaccWhole'] = str(quota_first_vacc)[2:4]
        data_dict['quotaFirstVaccDecimal'] = str(quota_first_vacc)[4]
        quota_second_vacc = round(vacc_data['secondVaccination']['quote'], 3)
        data_dict['quotaSecondVaccWhole'] = str(quota_second_vacc)[2:4]
        data_dict['quotaSecondVaccDecimal'] = str(quota_second_vacc)[4]
        data_dict['newFirstVaccs'] = vacc_data['delta']
        data_dict['newSecondVaccs'] = vacc_data['secondVaccination']['delta']
        return data_dict


def create_skill():
    return CovidUpdate()

