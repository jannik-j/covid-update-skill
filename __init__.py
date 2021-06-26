from mycroft import MycroftSkill, intent_file_handler


class CovidUpdate(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('update.covid.intent')
    def handle_update_covid(self, message):
        self.speak_dialog('update.covid')


def create_skill():
    return CovidUpdate()

