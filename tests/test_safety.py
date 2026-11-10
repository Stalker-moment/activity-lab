from pathlib import Path
import sys, unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from safety import SafetyMonitor
from runtime import AdmissionGate


class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.now = 0.0
        self.m = SafetyMonitor(clock=lambda: self.now)

    def face(self):
        return [
            {
                "box": [0.2, 0.2, 0.6, 0.7],
                "blendshapes": {"eyeBlinkLeft": 0.9, "eyeBlinkRight": 0.9},
            }
        ]

    def test_continuity_and_gap_reset(self):
        self.assertFalse(self.m.drowsiness(self.face(), "a", True)["alert"])
        self.now = 1.5
        self.assertTrue(self.m.drowsiness(self.face(), "a", True)["alert"])
        self.now = 6
        self.assertFalse(self.m.drowsiness(self.face(), "a", True)["alert"])

    def test_sessions_disabled_and_missing_target(self):
        self.m.drowsiness(self.face(), "a", True)
        self.now = 1.5
        self.assertFalse(self.m.drowsiness(self.face(), "b", True)["alert"])
        self.m.drowsiness([], "a", True)
        self.assertFalse(self.m.drowsiness(self.face(), "a", True)["alert"])
        self.m.drowsiness(self.face(), "a", False)
        self.assertNotIn(("eyes", "a"), self.m.states)

    def test_blank_sessions_never_accumulate(self):
        self.m.drowsiness(self.face(), "", True)
        self.now = 1.5
        self.assertFalse(self.m.drowsiness(self.face(), "", True)["alert"])

    def test_lying_is_not_fall_and_aspect_is_pixel_corrected(self):
        pose = [{"box": [0.1, 0.2, 0.9, 0.6], "points": []}]
        self.m.fall(pose, "a", True, 16 / 9)
        self.now = 1
        r = self.m.fall(pose, "a", True, 16 / 9)
        self.assertFalse(r["alert"])
        self.assertAlmostEqual(r["aspect_ratio"], 3.556, places=3)

    def test_bounded_state(self):
        for i in range(200):
            self.m.drowsiness(self.face(), str(i), True)
        self.assertEqual(len(self.m.states), 128)

    def test_gate_is_bounded(self):
        gate = AdmissionGate(1)
        self.assertTrue(gate.acquire())
        self.assertFalse(gate.acquire())
        gate.release()
        self.assertTrue(gate.acquire())


if __name__ == "__main__":
    unittest.main()
