from mycroft import MycroftSkill, intent_file_handler, intent_handler
from adapt.intent import IntentBuilder
from .location_config import LocationConfig
from .location_handling import LocationHandler
import urllib.request
import requests
import json


class CovidUpdate(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    def initialize(self):
        self.location_config = LocationConfig(self.config_core)
        self.location_handler = LocationHandler()
        
        self.location_config.county = self.location_handler.get_county(self.location_config.city + ", " + self.location_config.state)
        self.location_config.admunit_code = self.location_handler.get_admunit_code(self.location_config.county)[1]

    @intent_handler(IntentBuilder('CovidUpdate')
                                        .require('Covid')
                                        .require('Update')
                                        .optionally('MyLocation')
                                        .optionally('Location'))
    def handle_update_covid(self, message):
        code, name = self._get_loc(message)
        self.log.info('Got code '+code+' and name '+name+' for the requested location and level')
        covid_data = self._get_covid_data(code)
        covid_data['name'] = name
        #history_data = self._get_incidence_history(code, level)
        dialog_dict = self._build_incidence_dialog(covid_data)
        dialog_dict = self._build_delta_dialog(covid_data, dialog_dict)
        #dialog_dict = self._build_incidence_history_dialog(history_data, dialog_dict)
        self.speak_dialog('update.covid', dialog_dict)
        self.speak_dialog('new.cases', dialog_dict)
        self.speak_dialog('week.incidence', dialog_dict)
        #self.speak_dialog('last.week.incidence', dialog_dict)
    
    @intent_handler(IntentBuilder('Incidence')
                                        .require('Incidence')
                                        .optionally('Covid')
                                        .optionally('Location')
                                        .optionally('MyLocation'))
    def handle_incidence(self, message):
        code, name = self._get_loc(message)
        self.log.info('Got code '+code+' and name '+name+' for the requested location and level')
        covid_data = self._get_covid_data(code)
        covid_data['name'] = name
        #history_data = self._get_incidence_history(code, level)
        dialog_dict = self._build_incidence_dialog(covid_data)
        #dialog_dict = self._build_incidence_history_dialog(history_data, dialog_dict)
        self.speak_dialog('week.incidence.loc', dialog_dict)
        #self.speak_dialog('last.week.incidence', dialog_dict)
    
    """
    @intent_handler(IntentBuilder('VaccinationProgress')
                                        .require('Vaccination')
                                        .require('Progress')
                                        .optionally('Covid')
                                        .optionally('MyLocation')
                                        .optionally('Location'))
    def handle_vaccination_progress(self, message):
        code, level = self._get_loc_and_level(message, 'states')
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
    """


    def _get_covid_data(self, code: str):
        url = "https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/rki_key_data_v/FeatureServer/0/query?"
        self.log.info('Trying to access api at '+url)
        parameter = {
            'referer':'mycroft-covid-update-skill',
            'user-agent':'python-requests/3.7',
            'where': 'AdmUnitId = '+code, # Welche AdmUnit sollen zurück gegeben werden
            'outFields': '*', # Rückgabe aller Felder
            'returnGeometry': False, # Keine Geometrien
            'f':'json', # Rückgabeformat, hier JSON
            'cacheHint': True # Zugriff über CDN anfragen
        }
        result = requests.get(url=url, params=parameter) #Anfrage absetzen
        resultjson = json.loads(result.text) # Das Ergebnis JSON als Python Dictionary laden
        return resultjson['features'][0]['attributes']
    
    """
    def _get_incidence_history(self, code: str, level: str):
        if level is 'germany':
            url = "https://api.corona-zahlen.org/germany/history/incidence/7"
        else:
            url = "https://api.corona-zahlen.org/"+level+'/'+code+'/'+'history/incidence/7'
        self.log.info('Trying to access api at '+url)
        with urllib.request.urlopen(url) as api_data:
            history_data = json.load(api_data)['data']
        if level is 'germany':
            return history_data
        else:
            return history_data[code]['history']
    """
    """
    def _get_vaccination_data(self):
        url = 'https://api.corona-zahlen.org/vaccinations'
        self.log.info('Trying to access api at '+url)
        with urllib.request.urlopen(url) as api_data:
            vacc_data = json.load(api_data)['data']
        return vacc_data
    """
    
    def _get_loc(self, message):
        if self.voc_match(message.data.get('utterance'), 'MyLocation'):
            self.log.info('Got Keyword for MyLocation')
            return str(self.location_config.admunit_code), self.location_config.county
        
        elif message.data.get('Location'):
            location = message.data.get('Location')
            self.log.info('Got Location '+location)
            # If the given Location is Germany, the skill shall respond with the statistics for the whole country
            if self.location_handler.is_germany(location):
                return '0', 'deutschland'
            
            else:
                # If the given Location is one of the states, the skill should respond with the statistics for that state
                matched_state, conf = self.location_handler.match_states(location)
                if conf > 0.75:
                    self.log.info('Location is matched with the state '+str(matched_state))
                    return str(matched_state), list(self.location_handler.state_dict.keys())[matched_state-1]
                else:
                    county = self.location_handler.get_county(location)
                    self.log.info('Gelocation yielded the county '+county+' for the location')
                    matched_admunit, admunit_code, conf = self.location_handler.get_admunit_code(county)
                    self.log.info('Matched '+county+' to '+matched_admunit+' with confidence '+str(conf))
                    return str(admunit_code), matched_admunit
        
        # If no Location is provided, the skill should give an update for Germany
        else:
            return '0', 'deutschland'
    
    def _build_incidence_dialog(self, covid_data: dict, data_dict={}):
        data_dict['name'] = covid_data['name']
        if covid_data['Inz7T'] > 0:
            data_dict['weekIncidenceWhole'] = str(covid_data['Inz7T']).split('.')[0]
            data_dict['weekIncidenceDecimal'] = str(covid_data['Inz7T']).split('.')[1][:1]
        else:
            data_dict['weekIncidenceWhole'] = '0'
            data_dict['weekIncidenceDecimal'] = '0'
        return data_dict
    
    def _build_delta_dialog(self, covid_data: dict, data_dict={}):
        data_dict['deltaCases'] = covid_data['AnzFallNeu']
        data_dict['deltaDeaths'] = covid_data['AnzTodesfallNeu']
        return data_dict
    
    """
    def _build_incidence_history_dialog(self, history_data: dict, dialog_dict: dict):
        dialog_dict['incidenceLastWeekWhole'] = str(history_data[0]['weekIncidence']).split('.')[0]
        dialog_dict['incidenceLastWeekDecimal'] = str(history_data[0]['weekIncidence']).split('.')[1][:1]
        return dialog_dict
    """

    """
    def _build_vaccination_dialog(self, vacc_data: dict):
        data_dict = {}
        if 'name' in vacc_data:
            data_dict['name'] = vacc_data['name']
        else:
            data_dict['name'] = 'deutschland'
        quota_first_vacc = round(vacc_data['quote'], 3)*1000
        data_dict['quotaFirstVaccWhole'] = str(quota_first_vacc)[:2]
        data_dict['quotaFirstVaccDecimal'] = str(quota_first_vacc)[2]
        quota_second_vacc = round(vacc_data['secondVaccination']['quote'], 3)*1000
        data_dict['quotaSecondVaccWhole'] = str(quota_second_vacc)[:2]
        data_dict['quotaSecondVaccDecimal'] = str(quota_second_vacc)[2]
        data_dict['newFirstVaccs'] = vacc_data['delta']
        data_dict['newSecondVaccs'] = vacc_data['secondVaccination']['delta']
        return data_dict
    """

def create_skill():
    return CovidUpdate()

