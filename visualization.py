from typing import Mapping, Tuple, Sequence
import matplotlib.pyplot as plt
import math

from filtering import LPF


def nearest_sample(data: Sequence[Sequence[float]],
                   target: float
                   ) -> int:
    times = data[:, 0]
    closest_idx = None
    closest_dist = float('inf')
    for i, time in enumerate(times):
        dist = abs(time - target)
        if dist < closest_dist:
            closest_idx = i
            closest_dist = dist
    return closest_idx


class EventPlotter:

    def __init__(self,
                 data: Sequence[Sequence[float]],
                 events: Sequence[Mapping[str, str]],
                 dpi: int = 100):
        self._times = data[:, 0]
        self._data = data
        self._events = events
        self._dpi = dpi
        self.example = "example"

    def plot(self,
             sensor_id: int,
             event_id: int,
             duration: float,
             filter: LPF = None,
             title: str = '',
             xlabel: str = "Elapsed Time (sec)",
             ylabel: str = '',
             legend: str = "Raw",
             num_xticks: int = 6,
             dif_yticks: float = 100,
             color: str = "tab:blue"
             ) -> None:
        time_start = float(self._events[event_id]["secs"])
        print(time_start)
        time_end = time_start + duration
        sample_start = nearest_sample(self._data, time_start)
        print(sample_start)
        sample_end = nearest_sample(self._data, time_end)

        times_event = [t - time_start for t in self._times[sample_start : sample_end]]
        data_event = self._data[sample_start : sample_end, sensor_id]
        print(data_event)

        plt.figure(dpi=self._dpi)
        plt.plot(times_event, data_event, label=legend, c=color)
        if filter is not None:
            plt.plot(times_event[filter._length : -filter._length],
                     filter.apply(data_event)[filter._length : -filter._length],
                     label="Running Avg", c="tab:orange")
            plt.legend()
        plt.title(title); plt.xlabel(xlabel); plt.ylabel(ylabel); plt.grid()

        plt.xlim((0, duration))
        plt.xticks([i * duration / (num_xticks - 1) for i in range(num_xticks)])
        ymin = math.floor(min(data_event) / dif_yticks - 0.25) * dif_yticks
        ymax = math.ceil(max(data_event) / dif_yticks + 0.25) * dif_yticks
        yticks = [y for y in range(ymin, ymax+dif_yticks, dif_yticks)]
        plt.ylim((ymin, ymax))
        plt.yticks(yticks)


    def add_curve(self,
                  sensor_id: int,
                  event_id: int,
                  duration: float,
                  legend: str = '',
                  color: str = "tab:orange"
                  ) -> None:
        time_start = float(self._events[event_id]["secs"])
        time_end = time_start + duration
        sample_start = nearest_sample(self._data, time_start)
        sample_end = nearest_sample(self._data, time_end)

        times_event = [t - time_start for t in self._times[sample_start : sample_end]]
        data_event = self._data[sample_start : sample_end, sensor_id]

        plt.plot(times_event, data_event, label=legend, c=color)
        plt.legend()
