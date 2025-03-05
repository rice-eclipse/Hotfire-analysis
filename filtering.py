from typing import Sequence
import numpy as np
from scipy import signal

class LPF:
    def __init__(self, fs: int, length: int, cutoff: float, window: str) -> None:
        self._fs = fs; self._length = length; self._cutoff = cutoff; self._window = window
        self._filter = signal.firwin(numtaps=length, cutoff=cutoff, window=window, 
                                     pass_zero="lowpass", scale=False, fs=fs)
        
    def apply(self, raw_signal: Sequence[float]) -> list[float]:
        return signal.convolve(raw_signal, self._filter, mode="same")
        