class LocationConfig():
    def __init__(self, core_config: dict):
        self.core_config = core_config
        self.county = None
        self.county_code = None
        
    @property
    def city(self):
        """The current value of the city name in the device configuration."""
        return self.core_config["location"]["city"]["name"]

    @property
    def country(self):
        """The current value of the country name in the device configuration."""
        return self.core_config["location"]["city"]["state"]["country"]["name"]

    @property
    def latitude(self):
        """The current value of the latitude location configuration"""
        return self.core_config["location"]["coordinate"]["latitude"]

    @property
    def longitude(self):
        """The current value of the longitude location configuration"""
        return self.core_config["location"]["coordinate"]["longitude"]

    @property
    def state(self):
        """The current value of the state name in the device configuration."""
        return self.core_config["location"]["city"]["state"]["name"]
