"""The coherence rules must reject hand-made incoherent personas."""

import copy
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from vo_personas_simulation.generation.population import generate_persona  # noqa: E402
from vo_personas_simulation.generation.rules import validate  # noqa: E402

REFERENCE = datetime(2026, 9, 1, tzinfo=timezone.utc)


def find(predicate, limit=5000):
    for i in range(limit):
        p = generate_persona(i, 42, REFERENCE)
        if predicate(p):
            return p
    raise LookupError("no persona matches")


def age(p):
    return p["stable_profile"]["demographics"]["age"]


class RulesTest(unittest.TestCase):
    def assertRejected(self, persona, fragment):
        errors = validate(persona)
        self.assertTrue(any(fragment in e for e in errors), f"expected an error containing {fragment!r}, got {errors}")

    def test_generated_persona_is_valid(self):
        self.assertEqual(validate(generate_persona(0, 42, REFERENCE)), [])

    def test_university_student_cannot_hold_postgraduate_degree(self):
        p = copy.deepcopy(find(lambda p: 18 <= age(p) <= 22 and p["stable_profile"]["education"]["enrolled_in"] == "bachelor"))
        p["stable_profile"]["education"]["highest_completed"] = "master"
        self.assertRejected(p, "enrolled in bachelor after completing master")

    def test_twenty_year_old_cannot_have_a_master(self):
        p = copy.deepcopy(find(lambda p: age(p) == 20))
        p["stable_profile"]["education"] = {"highest_completed": "master", "enrolled_in": None}
        self.assertRejected(p, "master cannot be completed at 20")

    def test_minor_cannot_be_divorced(self):
        p = copy.deepcopy(find(lambda p: age(p) < 18))
        p["life_context"]["family_and_relationships"]["romantic_relationship"]["status"] = "divorced"
        self.assertRejected(p, "minor with relationship status divorced")

    def test_minor_cannot_live_alone(self):
        p = copy.deepcopy(find(lambda p: age(p) < 18))
        p["life_context"]["living_situation"]["living_arrangement"] = "alone"
        self.assertRejected(p, "minor not living with parents")

    def test_child_must_be_16_years_younger(self):
        p = copy.deepcopy(find(lambda p: 25 <= age(p) <= 40))
        p["life_context"]["family_and_relationships"]["children"] = [{"age": age(p) - 10}]
        self.assertRejected(p, "parent less than 16 years older than child")

    def test_life_stage_must_match_age(self):
        p = copy.deepcopy(find(lambda p: age(p) >= 40))
        p["stable_profile"]["demographics"]["life_stage"] = "teenager"
        self.assertRejected(p, "life_stage does not match age")

    def test_doctor_needs_the_degree(self):
        p = copy.deepcopy(find(lambda p: p["stable_profile"]["education"]["highest_completed"] == "secondary"
                               and p["work_and_occupation"]["occupation"]["status"] == "employed"))
        p["work_and_occupation"]["occupation"]["occupation"] = "doctor"
        self.assertRejected(p, "doctor requires more education")

    def test_car_audio_only_in_a_car(self):
        p = copy.deepcopy(find(lambda p: p["current_context"]["activity_and_location"]["location_type"] == "home"))
        p["current_context"]["technical_setup"]["audio_output"] = "car_audio"
        self.assertRejected(p, "car_audio vs location")

    def test_exam_event_requires_enrolment(self):
        p = copy.deepcopy(find(lambda p: p["stable_profile"]["education"]["enrolled_in"] is None))
        p["current_context"]["event_of_the_day"]["event_type"] = "exam_today"
        self.assertRejected(p, "event exam_today does not fit")

    def test_retired_teenager(self):
        p = copy.deepcopy(find(lambda p: age(p) < 18))
        p["work_and_occupation"]["occupation"]["status"] = "retired"
        self.assertRejected(p, "retired too young")

    def test_shape_rejects_missing_and_unexpected_fields(self):
        p = copy.deepcopy(generate_persona(0, 42, REFERENCE))
        del p["music_identity"]["listening_functions"]["focus"]
        p["stable_profile"]["education_level"] = "university"
        errors = validate(p)
        self.assertIn("missing field music_identity.listening_functions.focus", errors)
        self.assertIn("unexpected field stable_profile.education_level", errors)


if __name__ == "__main__":
    unittest.main()
