
import random
from googletrans import Translator
from typing import Any, Text, Dict, List
from rasa_sdk import Action
from rasa_sdk.events import SlotSet, AllSlotsReset, UserUtteranceReverted
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.interfaces import Tracker



    
class MentalHealthAssessment:
    QUESTIONS = [
        {"question": "How often have you felt down, depressed, or hopeless in the last two weeks?", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
        {"question": "How often have you had little interest or pleasure in doing things?", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
        {"question": "How often do you feel fatigued or have low energy?", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
        {"question": "Do you have trouble sleeping or sleeping too much?", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
        {"question": "How often do you feel bad about yourself or that you are a failure?", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
        {"question": "Do you often feel anxious or overwhelmed?", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
        {"question": "How often do you find it difficult to concentrate on daily activities?", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]}
    ]
    
    SCORES = {"Not at all": 0, "Several days": 1, "More than half the days": 2, "Nearly every day": 3}
    
    RISK_LEVELS = {
        "happy": (0, 25),
        "normal": (25, 50),
        "sad": (50, 75),
        "depressed": (75, 100)
    }
    
    QUOTES = {
        "happy": ["Happiness is not out there, it’s in you!", "Enjoy the little things, for one day you may look back and realize they were the big things."],
        "normal": ["Keep pushing forward, your efforts will pay off!", "Believe in yourself and all that you are."]
    }
    
    
    SONGS = {
        "normal": ["Listen to this relaxing music."]
    }

    VIDEOS = {
        "sad": ["Watch this helpful video."]
    }

    SONG_LINKS = {
        "normal": "https://open.spotify.com/album/7E8bF2pGdAV2Ect0XGbt9H?si=Dl7KkL4BR_m5Wvh6vYWqdA"
    }
 
    VIDEO_LINKS = {
        "sad": "https://www.youtube.com/watch?v=nqye02H_H6I"
    }

    
    RESOURCES = {
        "depressed": {
            "consultation": "It's highly recommended to consult a mental health professional.",
            "doctors": ["Dr. John Doe - Psychologist", "Dr. Jane Smith - Psychiatrist"],
            "helplines": ["Mental Health Helpline: 123-456-7890"]
        }
    }
    
    @classmethod
    def assess_mental_health(cls, responses: List[str]) -> Dict[str, Any]:
        total_score = sum(cls.SCORES[response] for response in responses)
        max_possible_score = len(cls.QUESTIONS) * 3
        score_percentage = (total_score / max_possible_score) * 100
        
        risk_level = "happy"
        for level, (low, high) in cls.RISK_LEVELS.items():
            if low <= score_percentage < high:
                risk_level = level
                break
        
        return {
            "total_score": total_score,
            "max_possible_score": max_possible_score,
            "score_percentage": score_percentage,
            "risk_level": risk_level
        }



class ActionMentalHealthAssessment(Action):
    def name(self) -> str:
        return "action_mental_health_assessment"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        translator = Translator()
        user_language = tracker.get_slot("user_language") or "en"
        responses = tracker.get_slot("assessment_responses") or []

        if len(responses) < len(MentalHealthAssessment.QUESTIONS):
            current_question = MentalHealthAssessment.QUESTIONS[len(responses)]
            
            # Translate question and options dynamically
            translated_question = translator.translate(current_question["question"], dest=user_language).text
            translated_options = [translator.translate(opt, dest=user_language).text for opt in current_question["options"]]

            dispatcher.utter_message(text=translated_question)
            dispatcher.utter_message(text="Options: " + ", ".join(f"{i+1}. {opt}" for i, opt in enumerate(translated_options)))
            return [SlotSet("current_question_index", len(responses))]

        # Assess mental health
        assessment = MentalHealthAssessment.assess_mental_health(responses)
        risk_level = assessment["risk_level"]
        result_message = f"Assessment Results: {assessment['total_score']}/{assessment['max_possible_score']} ({assessment['score_percentage']:.1f}%)\nRisk Level: {risk_level.capitalize()}"

        # Translate result message dynamically
        translated_result = translator.translate(result_message, dest=user_language).text
        dispatcher.utter_message(text=translated_result)

        # Provide appropriate recommendations
        message = ""
        link = ""

        if risk_level == "happy":
            message = random.choice(MentalHealthAssessment.QUOTES[risk_level])
        elif risk_level == "normal":
            message = random.choice(MentalHealthAssessment.SONGS[risk_level])
            link = MentalHealthAssessment.SONG_LINKS['normal']  # Keep link separate
        elif risk_level == "sad":
            message = random.choice(MentalHealthAssessment.VIDEOS[risk_level])
            link = MentalHealthAssessment.VIDEO_LINKS['sad']  # Keep link separate
        elif risk_level == "depressed":
            message = "\n".join([MentalHealthAssessment.RESOURCES[risk_level]["consultation"]] +
                                ["Recommended Doctors:"] + MentalHealthAssessment.RESOURCES[risk_level]["doctors"] +
                                ["Emergency Contacts:"] + MentalHealthAssessment.RESOURCES[risk_level]["helplines"])

        # Translate the message **before** adding the link
        translated_message = translator.translate(message, dest=user_language).text

        # Send translated message
        dispatcher.utter_message(text=translated_message)

        # Send the link separately to avoid translation issues
        if link:
            dispatcher.utter_message(text=f"{link}")

        return [AllSlotsReset()]


class ActionRecordResponse(Action):
    def name(self) -> Text:
        return "action_record_response"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_message = tracker.latest_message.get("text", "").strip()
        user_language = tracker.get_slot("user_language") or "en"

        translator = Translator()
        if user_language != "en":
            translated_message = translator.translate(user_message, src=user_language, dest="en").text
        else:
            translated_message = user_message

        responses = tracker.get_slot("assessment_responses") or []

        if translated_message.isdigit():
            option_index = int(translated_message) - 1
            if 0 <= option_index < len(MentalHealthAssessment.QUESTIONS[len(responses)]["options"]):
                responses.append(MentalHealthAssessment.QUESTIONS[len(responses)]["options"][option_index])
                return [SlotSet("assessment_responses", responses), SlotSet("current_question_index", None)]

        dispatcher.utter_message(text="Invalid response. Please choose a valid option.")
        return []
