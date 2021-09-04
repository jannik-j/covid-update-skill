from geopy.geocoders import Nominatim
import urllib.request
import json
import requests

def main():
    # locator = Nominatim(user_agent="mycroft-covid-update-skill")
    # location = locator.geocode("münchen, Germany", addressdetails=True)
    # print(location.raw)
    url = "https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/rki_key_data_v/FeatureServer/0/query?"
    parameter = {
        'referer':'mycroft-covid-update-skill',
        'user-agent':'python-requests/3.7',
        'where': 'AdmUnitId = 0', # Welche AdmUnit sollen zurück gegeben werden
        'outFields': '*', # Rückgabe aller Felder
        'returnGeometry': False, # Keine Geometrien
        'f':'json', # Rückgabeformat, hier JSON
        'cacheHint': True # Zugriff über CDN anfragen
    }
    result = requests.get(url=url, params=parameter) #Anfrage absetzen
    resultjson = json.loads(result.text) # Das Ergebnis JSON als Python Dictionary laden
    print(resultjson['features'][0]['attributes']) # Wir erwarten genau einen Datensatz, Ausgabe aller Attribute

if __name__ == "__main__":
    main()
