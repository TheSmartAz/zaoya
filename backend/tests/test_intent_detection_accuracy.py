import asyncio
import os
import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

from app.services.intent_detection import detect_intent, IntentCategory


TEST_CASES = [
    ("We need a wedding invitation page for June 12", IntentCategory.EVENT_INVITATION),
    ("Birthday party RSVP site with ceremony details", IntentCategory.EVENT_INVITATION),
    ("Launch a marketing landing page for our app", IntentCategory.LANDING_PAGE),
    ("Need a waitlist signup page for the product", IntentCategory.LANDING_PAGE),
    ("Create a product page for the upcoming launch", IntentCategory.LANDING_PAGE),
    ("Portfolio site for a freelance designer", IntentCategory.PORTFOLIO),
    ("Personal site with my resume and cv", IntentCategory.PORTFOLIO),
    ("About me profile page for an artist", IntentCategory.PORTFOLIO),
    ("Contact form for client inquiry submissions", IntentCategory.CONTACT_FORM),
    ("Lead form to get in touch with our team", IntentCategory.CONTACT_FORM),
    ("Create a contact page for our studio", IntentCategory.CONTACT_FORM),
    ("Ecommerce store with cart and checkout", IntentCategory.ECOMMERCE),
    ("Online shop with a product catalog", IntentCategory.ECOMMERCE),
    ("Build an e-commerce storefront for apparel", IntentCategory.ECOMMERCE),
    ("Start a blog for writing tips", IntentCategory.BLOG),
    ("Newsletter for articles and posts", IntentCategory.BLOG),
    ("Weekly posts about travel and food", IntentCategory.BLOG),
    ("Analytics dashboard for key metrics", IntentCategory.DASHBOARD),
    ("Admin reporting insights page", IntentCategory.DASHBOARD),
    ("Metrics reporting dashboard for operations", IntentCategory.DASHBOARD),
    ("Need a simple website for my dog walker business", IntentCategory.OTHER),
    ("Create a community forum for local volunteers", IntentCategory.OTHER),
]


class IntentDetectionAccuracyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ["ZAOYA_DISABLE_INTENT_AI"] = "1"
        os.environ["ZAOYA_INTENT_AI"] = "0"

    def test_intent_detection_accuracy(self) -> None:
        async def _evaluate():
            correct = 0
            for message, expected in TEST_CASES:
                result = await detect_intent(message)
                if result.category == expected:
                    correct += 1
            return correct

        correct = asyncio.run(_evaluate())
        accuracy = correct / len(TEST_CASES)
        self.assertGreaterEqual(accuracy, 0.9, f"Intent accuracy {accuracy:.2%} below 90%")


if __name__ == "__main__":
    unittest.main()
