from email import message_from_file
from typing import Mapping, Tuple, Sequence
from datetime import datetime
import numpy as np
import ast
from copy import deepcopy

EVENT_HEADERS = ["secs", "delta", "elapsed", "type", "info"]


def process_data(dir: str,
                 sensors: Mapping[str, str]
                 ) -> None:
    all_labels = []
    all_data = []

    with open(f"{dir}/data-raw/raw.csv", 'r') as file:
        all_labels = file.readline()[:-1].split(',')
        while True:
            sample = file.readline()[:-1].split(',')
            if len(sample) < len(all_labels):
                break
            all_data.append([float(val) for val in sample])
    all_data = np.array(all_data)

    labels = [all_labels[0]]
    data = all_data[:, (0,)]
    for i, label in enumerate(all_labels):
        if label in sensors:
            labels.append(sensors[label])
            data = np.hstack((data, all_data[:, (i,)]))

    np.savez_compressed(f"{dir}/data.npz", labels=labels, data=data)
    np.savetxt(f"{dir}/data.csv", data, delimiter=", ", fmt="%1f",
               header=str(labels)[1:-1], comments='')


def import_data(dir: str, 
                events: Sequence[Mapping[str, str]]
                ) -> Tuple[list[str], np.ndarray[float]]:
    contents = np.load(f"{dir}/data.npz")
    labels = contents["labels"]
    data = contents["data"]
    last_valid_time = float(events[-1]["secs"])

    for i, sample in enumerate(contents["data"]):
        if float(sample[0]) > last_valid_time:
            data = data[:i]

    return labels, data

"""
New function for Processing events for HF4 since no timestamps are in console.log 
"""
def process_events_hf4(dir: str,
                              drivers: Mapping[int, Mapping[str,str]]
                              ) -> None:
    contents = []
    with open(f"{dir}/data-raw/console.log", 'r') as file:
        while True:
            line = file.readline()
            if len(line) <= 1:
                break
            contents.append(line)
    #determines when the connection with quonkboard is established
    dt_connect = 0
    for message in contents:
        if "connection is OPEN" in message:
            connection_idx = contents.index(message)
            dt_connect = _parse_duration_hf4(contents, connection_idx)
            type="Connect"
        break
    #gets all time stamps for all the commands sent from the dashboard
    events = []
    contents_copy = deepcopy(contents)
    for message in contents_copy:
        content_idx = contents_copy.index(message)
        secs = _parse_duration_hf4(contents_copy, content_idx)
        elapsed = _format_time(secs - dt_connect)
        delta = _format_time(secs - events[-1]["secs"]) if len(events) > 0 else None
        info = None
        type = None

        if "connection is OPEN" in message:
            type="Connect"

        elif "Running..." in message:
            type="Start"
        
        elif "Received command: {'type': 'Actuate'," in message:
            driver_idx = int(ast.literal_eval(message[message.index('{'): message.index('}')+1])['driver_id'])
            state = str(ast.literal_eval(message[message.index('{'): message.index('}')+1])['value'])
            info = drivers[driver_idx]["name"]
            type = drivers[driver_idx][state]
        
        elif "Received command: {'type': 'Ignition'," in message:
            type = "Ignition"
        else:
            continue
        
        events.append({"secs": secs, "elapsed": elapsed, "delta": delta, "type": type, 
                       "info": info})
        contents_copy[contents_copy.index(message)] = ""
        
        text = ""
        for header in EVENT_HEADERS:
            text += f"{header}, "
        text = f"{text[:-2]}\n"
        for event in events:
            for header in EVENT_HEADERS:
                text += f"{event[header]}, "
            text = f"{text[:-2]}\n"
        
        with open(f"{dir}/events.csv", 'w') as file:
            file.write(text)
        
def process_events(dir: str,
                   drivers: Mapping[int, Mapping[str, str]]
                   ) -> None:
    contents = []
    with open(f"{dir}/data-raw/console.log", 'r') as file:
        while True:
            line = file.readline()
            if len(line) <= 1:
                break
            contents.append(line)


    dt_connect = None
    for message in contents:
        if "Connection established to controller" in message:
            dt_connect = datetime.fromisoformat(message.split(" [INFO]: ", 1)[0])
            break

    events = []
    for message in contents:
        if "[INFO]:" not in message:
            continue

        dt_current = datetime.fromisoformat(message.split(" [INFO]: ", 1)[0])
        secs = int((dt_current - dt_connect).total_seconds())
        elapsed = _format_time(secs)
        delta = _format_time(secs - events[-1]["secs"]) if len(events) > 0 else None
        
        type = info = ""
        if "Initializing slonkboard" in message:
            type = "Start"
        elif "Connection established to controller" in message:
            type = "Connect"
        elif "Sent command {\"type\":\"Actuate\"" in message:
            driver_id = int(message.split("driver_id\":", 1)[1].split(',', 1)[0])
            state = message.split("value\":", 1)[1].split('}', 1)[0]
            type = drivers[driver_id][state]
            info = drivers[driver_id]["name"]
        elif "Sent command {\"type\":\"Ignition\"}" in message:
            type = "Ignition"
        elif "Connection to controller closed" in message:
            type = "Disconnect"
        else:
            continue

        events.append({"secs": secs, "elapsed": elapsed, "delta": delta, "type": type, 
                       "info": info})
        
    text = ""
    for header in EVENT_HEADERS:
        text += f"{header}, "
    text = f"{text[:-2]}\n"
    for event in events:
        for header in EVENT_HEADERS:
            text += f"{event[header]}, "
        text = f"{text[:-2]}\n"
    
    with open(f"{dir}/events.csv", 'w') as file:
        file.write(text)


def import_events(dir: str) -> list[dict[str, str]]:
    events = []
    with open(f"{dir}/events.csv", 'r') as file:
        file.readline()
        while True:
            line = file.readline()
            if len(line) <= 1:
                break
            line = line[:-1].split(", ")
            events.append({"secs": line[0], "elapsed": line[1], "delta": line[2], "type": line[3], 
                           "info": line[4]})
    return events


def _format_time(time: int) -> str:
    if time is None:
        return str(None)
    sign = '-' if time < 0 else ''
    mins = abs(time) // 60
    secs = abs(time) % 60
    return f"{sign}{mins}:{secs:0>2}"

def _parse_duration_hf4(contents: list, event_index: int) -> int:
    samples_before_event = 0
    time_since_start = 0
    for idx in range(event_index, 0, -1):
        if "samples obtained" in contents[idx]:
            samples_before_event = int(contents[idx].split(':')[2].split()[0])
            temp_index = contents.index(contents[idx])
            message_count = 0
            for i in range(temp_index, event_index, 1):
                if "Sending data to" in contents[i]:
                    message_count += 1   
            time_since_start_approx = round(samples_before_event/300)
            time_since_start = time_since_start_approx + round(message_count/2)
            break
    return time_since_start