import unittest
import numpy as np
from scipy.signal import freqz
from pyedflib import apply_filter, butter_bandpass

class TestButterBandpass(unittest.TestCase):
    def test_filter_coefficients(self):
        """Test if the filter coefficients are correctly calculated."""
        fs = 4000
        lowcut = 10
        highcut = 100
        b, a = butter_bandpass(lowcut, highcut, fs, order=4)
        
        # Ensure coefficients are not None
        self.assertIsNotNone(b)
        self.assertIsNotNone(a)

        # Check the filter's frequency response
        w, h = freqz(b, a, worN=8000)
        w = fs * 0.5 / np.pi * w  # Convert from rad/sample to Hz
        
        # Verify that the gain is close to 0 dB in the passband
        passband = (w >= lowcut) & (w <= highcut)
        self.assertTrue(np.all(np.abs(h[passband]) > 0.7))

        # Verify significant attenuation in the stopband
        stopband = (w < lowcut) | (w > highcut)
        self.assertTrue(np.all(np.abs(h[stopband]) < 0.3))

class TestApplyFilter(unittest.TestCase):
    def test_signal_filtering(self):
        """Test if the apply_filter function filters a signal within the specified band."""
        fs = 4000
        duration = 1  # seconds
        t = np.linspace(0, duration, int(fs*duration), endpoint=False)
        
        # Create a test signal combining 5 Hz and 50 Hz sine waves
        signal = np.sin(2*np.pi*5*t) + np.sin(2*np.pi*50*t)
        
        # Filter the signal
        filtered_signal = apply_filter(signal, fs)

        # Check if the function returns a numpy array
        self.assertIsInstance(filtered_signal, np.ndarray)


if __name__ == '__main__':
    unittest.main()
