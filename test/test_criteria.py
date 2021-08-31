import unittest
import numpy as np

from fat_eval.multiaxial_fatigue.haigh import evaluate_haigh

stress_history = np.array([
    [[1000, 0, 0, 0., 0, 0], [1000, 0, 0, 0., 0, 0]],    # Static loading
    [[1000, 0, 0, 0., 0, 0], [0, 0, 0, 0., 0, 0]],       # Pulsating tension
    [[-1000, 0, 0, 0., 0, 0], [0, 0, 0, 0., 0, 0]],      # Pulsating compression
    [[-1000, 0, 0, 0., 0, 0], [1000, 0, 0, 0., 0, 0]],   # Alternating tension
    [[0, 0, 0, 1000., 0, 0], [0, 0, 0, 0, 0, 0]],        # pulsating shear
    [[0, 0, 0, 1000., 0, 0], [0, 0, 0, -1000., 0, 0]],   # Alternating shear
])

stress_history = np.moveaxis(stress_history, 1, 0)
sh_0 = evaluate_haigh(stress_history, 0*stress_history[0, :, 0])
sh_1 = evaluate_haigh(stress_history, 0*stress_history[0, :, 0])


class TestHaighAmplitude(unittest.TestCase):
    def test_uniaxial_loading_static(self):
        self.assertTrue(abs(sh_0[0] - 0) < 1e-6)

    def test_uniaxial_pulsating_tension(self):
        self.assertTrue(abs(sh_0[1] - 500) < 1e-6)

    def test_uniaxial_loading_compression(self):
        self.assertTrue(abs(sh_0[2] - 500) < 1e-6)
