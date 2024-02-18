import numpy as np
import pyedflib
from scipy.signal import butter, filtfilt

def butter_bandpass(lowcut, highcut, fs, order=5):
    """
    Create a Butterworth bandpass filter.

    Parameters:
    - lowcut: The lower frequency bound of the passband (Hz).
    - highcut: The upper frequency bound of the passband (Hz).
    - fs: The sampling rate of the signal (Hz).
    - order: The order of the filter.

    Returns:
    - b, a: Numerator (b) and denominator (a) polynomials of the filter.
    """
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def apply_filter(data, fs, lowcut=10, highcut=100, order=4):
    """
    Apply a zero-phase Butterworth bandpass filter to a signal.

    Parameters:
    - data: The input signal data (1D numpy array).
    - fs: The sampling rate of the signal (Hz).
    - lowcut: The lower frequency bound of the passband (Hz).
    - highcut: The upper frequency bound of the passband (Hz).
    - order: The order of the filter.

    Returns:
    - y: The filtered signal.
    """
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = filtfilt(b, a, data)
    return y

def process_edf(input_file, output_file):
    """
    Process an EDF file, applying a bandpass filter to EMG channels, and write the result to a new EDF file.

    Parameters:
    - input_file: Path to the input EDF file.
    - output_file: Path to the output EDF file where the processed data will be saved.
    """
    try:
        with pyedflib.EdfReader(input_file) as edf:
            print("Input file opened successfully.")
            n = edf.signals_in_file
            signal_headers = [edf.getSignalHeader(i) for i in range(n)]
            signals = [edf.readSignal(i) for i in range(n)]
            
            # Prepare new signals and headers for filtered EMG channels
            new_signals = []
            new_headers = []
            for i, signal in enumerate(signals):
                fs = signal_headers[i]['sample_rate']
                if 'EMG' in signal_headers[i]['label'].upper():
                    filtered_signal = apply_filter(signal, fs)
                    new_signals.append(filtered_signal)
                    new_header = signal_headers[i].copy()
                    new_header['label'] = 'Filtered_' + signal_headers[i]['label']
                    new_headers.append(new_header)
                else:
                    new_signals.append(signal)
                    new_headers.append(signal_headers[i])
            
            print("Signals processed. Writing to output file...")

        with pyedflib.EdfWriter(output_file, len(new_signals)) as writer:
            for i, signal in enumerate(new_signals):
                writer.setSignalHeader(i, new_headers[i])
                writer.writePhysicalSamples(signal)
            print("Output file written successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    process_edf('./201223_218_2014_night_result.xf2.EDF', './filtered_output.EDF')
