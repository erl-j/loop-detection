#%%
import pretty_midi
import sys
import argparse
import os

# first unnamed argument is path to midi file
parser = argparse.ArgumentParser()
parser.add_argument("midi_path", help="path to midi file")

original_midi_path = sys.argv[1]

# run raw annotation
os.system(f"python tcn_downbeat_eval.py '{original_midi_path}'")

# get filename with extension
filename = os.path.basename(original_midi_path)

raw_midi_path = "output/tcn_downbeat_unsupervised_v3.0_1024_context_6_tcn/" + filename + "_drums1_mel1_others1_raw.mid"

pm = pretty_midi.PrettyMIDI(raw_midi_path)

# get instrument with name "Layers4"
downbeat_layer = None
for instrument in pm.instruments:
    if instrument.name == "Layers4":
        downbeat_layer = instrument
        break
assert downbeat_layer is not None

print(downbeat_layer.notes)

downbeat_layer_threshold = 0.5
downbeat_layer_threshold_vel = downbeat_layer_threshold * 127

# find first note that is above threshold
velocities = []
for note in downbeat_layer.notes:
    velocities.append(note.velocity)

import matplotlib.pyplot as plt
plt.plot(velocities)
plt.show()

#%%
first_note = None
for note in downbeat_layer.notes:
    if note.velocity > downbeat_layer_threshold_vel:
        first_note = note
        break

assert first_note is not None

first_downbeat = first_note.start

print("first downbeat", first_downbeat)

# shift all notes back by first_note.start

import copy

def crop_pm(pm,start_time,end_time):
    new_pm = copy.deepcopy(pm)
    # crop pm
    for instrument_idx in range(len(pm.instruments)):
            new_pm.instruments[instrument_idx].notes = []
            for note_idx in range(len(pm.instruments[instrument_idx].notes)):
                note = pm.instruments[instrument_idx].notes[note_idx]
                if note.start >= start_time and note.end < end_time:
                    new_pm.instruments[instrument_idx].notes.append(copy.deepcopy(note))

    # same with pitch bends
    for instrument_idx in range(len(pm.instruments)):
        new_pm.instruments[instrument_idx].pitch_bends = []
        for bend_idx in range(len(pm.instruments[instrument_idx].pitch_bends)):
            bend = pm.instruments[instrument_idx].pitch_bends[bend_idx]
            if bend.time >= start_time and bend.time < end_time:
                new_pm.instruments[instrument_idx].pitch_bends.append(copy.deepcopy(bend))
    
    # same with control changes
    for instrument_idx in range(len(pm.instruments)):
        new_pm.instruments[instrument_idx].control_changes = []
        for cc_idx in range(len(pm.instruments[instrument_idx].control_changes)):
            cc = pm.instruments[instrument_idx].control_changes[cc_idx]
            if cc.time >= start_time and cc.time < end_time:
                new_pm.instruments[instrument_idx].control_changes.append(copy.deepcopy(cc))

    # if note is inside window, shift it back by window_start
    for instrument_idx in range(len(new_pm.instruments)):
        for note_idx in range(len(new_pm.instruments[instrument_idx].notes)):
            new_pm.instruments[instrument_idx].notes[note_idx].start -= start_time
            new_pm.instruments[instrument_idx].notes[note_idx].end -= start_time
    # shift pitch bends
    for instrument_idx in range(len(new_pm.instruments)):
        for bend_idx in range(len(new_pm.instruments[instrument_idx].pitch_bends)):
            new_pm.instruments[instrument_idx].pitch_bends[bend_idx].time -= start_time
    
    # shift control changes
    for instrument_idx in range(len(new_pm.instruments)):
        for cc_idx in range(len(new_pm.instruments[instrument_idx].control_changes)):
            new_pm.instruments[instrument_idx].control_changes[cc_idx].time -= start_time

    # set end
    # count notes
    print("end time - start time", end_time - start_time)
    new_pm.end_time = end_time - start_time
    print(new_pm.get_end_time())
    return new_pm

# remove instruments with Layers


new_pm = crop_pm(pm, first_downbeat, pm.get_end_time())

shifted_midi_path = "./output/tcn_downbeat_unsupervised_v3.0_1024_context_6_tcn/" + filename + "_drums1_mel1_others1_raw_shifted.mid"
# save new pm
new_pm.write(shifted_midi_path)

# run annotation on shifted midi
os.system(f"python tcn_downbeat_eval.py '{shifted_midi_path}'")



#%% plot piano roll
# import matplotlib.pyplot as plt
# import numpy as np

# piano_roll = pm.get_piano_roll(fs=100)

# plt.imshow(piano_roll, aspect='auto', cmap='gray_r')
# plt.show()




# %%
