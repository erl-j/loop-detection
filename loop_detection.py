#%%

import pretty_midi
import copy
import IPython.display as ipd

midi_path = "./Self-Supervised-Metrical-Structure/output/tcn_downbeat_unsupervised_v3.0_1024_context_6_tcn/Come as You Are.2.mid_drums1_mel1_others1_raw_shifted.mid_drums1_mel1_others1_crf.mid"
# 
pm = pretty_midi.PrettyMIDI(midi_path)
pm_layers = copy.deepcopy(pm)

# Todo: quantize to 16th notes and remove velocities

for instrument_idx in range(len(pm.instruments)):
    print(pm.instruments[instrument_idx].name)

# remove all instruments with names "Layers0", "Layers1", etc.
for instrument_idx in range(len(pm.instruments)):
    if pm_layers.instruments[instrument_idx].name.startswith("Layers"):
        pm_layers.instruments[instrument_idx].notes = []
        pm_layers.instruments[instrument_idx].pitch_bends = []
        pm_layers.instruments[instrument_idx].control_changes = []

for instrument_idx in range(len(pm.instruments)):
    print(pm.instruments[instrument_idx].name)

import numpy as np
# 
# get the piano roll
print(pm.time_signature_changes)
print(pm.get_tempo_changes())

# check that no time signature changes after duration 0
for time_signature_change in pm.time_signature_changes:
    assert time_signature_change.time < 0.01
assert len(pm.get_tempo_changes()[0]) == 1

# get beats
beats = pm.get_beats()

# add beat
# last_beat = [beats[-1]+beats[1]-beats[0]]
# beats = np.concatenate((beats, last_beat))


beat_duration = beats[1] - beats[0]
beat_division = 1
# linear interpolate quarter notes
ticks = []
for beat in beats:
    ticks.append(beat)
    for i in range(1, beat_division):
        ticks.append(beat + i * beat_duration/beat_division)
ticks = np.array(ticks)

print(list(ticks))

beats_per_bar = pm.time_signature_changes[0].numerator

# print end time

piano_roll = pm.get_piano_roll(times=ticks)

LAYER_NUM = 5
layer_instrument = None
for instrument_idx in range(len(pm.instruments)):
    if pm.instruments[instrument_idx].name.startswith("Layers%d" % LAYER_NUM):
        layer_instrument = pm.instruments[instrument_idx]
        break
assert layer_instrument is not None

# get note onsets and velocities
layer_onsets = [note.start for note in layer_instrument.notes]
layer_vel = [note.velocity for note in layer_instrument.notes]

tick_layer_vel = np.zeros(len(ticks))

# map onsets to ticks
for i in range(len(layer_onsets)):
    onset = layer_onsets[i]
    vel = layer_vel[i]
    # find closest tick
    closest_tick_idx = np.argmin(np.abs(ticks - onset))
    tick_layer_vel[closest_tick_idx] = vel

end_time = pm.get_end_time()
#%%

import matplotlib.pyplot as plt

plt.imshow(piano_roll, aspect='auto', cmap='gray_r')

for i in range(len(ticks)):
    if tick_layer_vel[i] > 0:
        plt.axvline(i, alpha=tick_layer_vel[i]/127, color='r')
plt.show()

import numpy as np
# compute self similarity matrix
# 


# plot piano roll


# Implementation of Correlative Matrix approach presented in:
# Jia Lien Hsu, Chih Chin Liu, and Arbee L.P. Chen. Discovering
# nontrivial repeating patterns in music data. IEEE Transactions on
# Multimedia, 3:311–325, 9 2001.
def calc_correlation(piano_roll):
    corr_size = len(piano_roll)
    print(corr_size)
    corr_mat = np.zeros((corr_size, corr_size), dtype='int32')

    for j in range(1, corr_size):
        if (piano_roll[0] == piano_roll[j]).all():
            corr_mat[0,j] = 1
        else:
            corr_mat[0,j] = 0
    for i in range(1, corr_size-1):
        for j in range(i+1, corr_size):
            if (piano_roll[i] == piano_roll[j]).all():
                corr_mat[i,j] = corr_mat[i-1, j-1] + 1
            else:
                corr_mat[i,j] = 0
    
    return corr_mat

corr_mat = calc_correlation(piano_roll.T)
# %%

print(corr_mat)

print(np.sum(corr_mat))

# show counts of each value in corr_mat
plt.hist(corr_mat.flatten(), bins = np.arange(1, np.max(corr_mat)+1))
plt.show() 

# minimum length of repeated pattern
# 4

def num_notes(pm):
    num_notes = 0
    for instrument in pm.instruments:
        num_notes += len(instrument.notes)
    return num_notes

def crop_pm(pm,start_time,end_time):
    new_pm = copy.deepcopy(pm)
    # crop pm
    for instrument_idx in range(len(pm.instruments)):
            new_pm.instruments[instrument_idx].notes = []
            for note_idx in range(len(pm.instruments[instrument_idx].notes)):
                note = pm.instruments[instrument_idx].notes[note_idx]
                if note.start >= start_time and note.end < end_time:
                    new_pm.instruments[instrument_idx].notes.append(copy.deepcopy(note))
        # if note is inside window, shift it back by window_start
    for instrument_idx in range(len(new_pm.instruments)):
        for note_idx in range(len(new_pm.instruments[instrument_idx].notes)):
            new_pm.instruments[instrument_idx].notes[note_idx].start -= start_time
            new_pm.instruments[instrument_idx].notes[note_idx].end -= start_time
    for instrument_idx in range(len(new_pm.instruments)):
        new_pm.instruments[instrument_idx].pitch_bends = []
        new_pm.instruments[instrument_idx].control_changes = []
    # set end
    # count notes
    new_pm.end_time = end_time - start_time
    return new_pm

seen_loop_piano_rolls = set()
loops = []

# find 4
# min corr
min_corr = 3
loop_bars = [2,4,8]
for i in range(corr_mat.shape[0]):
    for j in range(corr_mat.shape[1]):
        if corr_mat[i,j] >= min_corr:
            n_ticks = j - i
            n_bars = (n_ticks * beat_division) / beats_per_bar
            start_tick = i - min_corr
            end_tick = j - min_corr

            if n_bars in loop_bars:
                if tick_layer_vel[start_tick] > 0.5*127:
                    # if n_bars<=max_bars:
                
                    loop_piano_roll = piano_roll[:,start_tick:end_tick]
                
                    pr_str = loop_piano_roll.tostring()                    

                    if pr_str not in seen_loop_piano_rolls:
                        seen_loop_piano_rolls.add(pr_str)

                        # show piano roll with box around loop
                        plt.imshow(piano_roll, aspect='auto', cmap='gray_r')
                        plt.axvline(start_tick, color='r')
                        plt.axvline(end_tick, color='r')
                        plt.show()
            
                        new_pm = crop_pm(pm,ticks[start_tick],ticks[end_tick])
                        loops.append(new_pm)
                        # write midi
                    else:
                        print("Loop already seen")

#%%
os.makedirs("output", exist_ok=True)
for i  in range(len(loops)):
    print("Loop %d" % i)
    # write midi
    loop = loops[i]
    loop.write("output/loop_%d.mid" % i)

    #               
# %%
