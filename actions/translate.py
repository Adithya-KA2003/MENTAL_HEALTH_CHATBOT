from googletrans import Translator
from typing import Any, Text, Dict, List
from rasa_sdk import Action
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.interfaces import Tracker

class ActionDetectLanguage(Action):
    def name(self) -> Text:
        return "action_detect_language"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_message = tracker.latest_message.get("text", "")
        translator = Translator()

        # Detect the language of the user's input
        detected_lang = translator.detect(user_message).lang

        # If the language is not English, set the slot
        if detected_lang != "en":
            return [SlotSet("user_language", detected_lang)]
        
        return [SlotSet("user_language", "en")]
