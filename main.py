import mido
from mido import MidiFile

time_at_ticks_in_ms_map = {}
tempo_at_ticks_map = {}

def note_number_to_name(note_number):
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = note_number // 12 - 1
    note_name = notes[note_number % 12]
    return f"{note_name}{octave}"

def get_ticks_per_beat(midi_file_path):
    midi_file = MidiFile(midi_file_path)
    return midi_file.ticks_per_beat

def create_tempo_event_timing_map(midi_file_path):
    midi_file = MidiFile(midi_file_path)

    current_tempo = 500000 #MIDI default
    last_event_timing = 0
    last_event_ticks = 0
    ticks_per_beat = get_ticks_per_beat(midi_file_path)

    # Check if the first track has tempo change events
    if len(midi_file.tracks) > 0:
        tempo_track = midi_file.tracks[0]

        current_ticks = 0

        for msg in tempo_track:
            if msg.type == 'set_tempo':
                # Find duration and update last ticks
                elapsed_ticks = current_ticks - last_event_ticks # See if this works with just msg.time
                last_event_ticks = current_ticks

                # Using current (old) tempo, calculate this elapsed time
                elapsed_beats = elapsed_ticks / ticks_per_beat
                elapsed_time_microseconds = current_tempo * elapsed_beats
                elapsed_time_ms = elapsed_time_microseconds / 1000

                current_time_ms = last_event_timing + elapsed_time_ms

                time_at_ticks_in_ms_map[current_ticks] = current_time_ms
                tempo_at_ticks_map[current_ticks] = msg.tempo

                last_event_timing = current_time_ms
                current_tempo = msg.tempo

                tempo_in_microseconds_per_beat = msg.tempo
                tempo_in_beats_per_minute = 60000000 / tempo_in_microseconds_per_beat
                print(f"Tempo Change Event: Tempo={tempo_in_beats_per_minute:.2f} BPM  Time={current_time_ms} ms")

            current_ticks += msg.time

def build_note_list_from_midi(midi_file_path):
    midi_file = MidiFile(midi_file_path)

    all_notes = []
    note_on_events = {}

    for i, track in enumerate(midi_file.tracks[1:]):
        # print(f"Track {i + 1}:")

        current_time = 0

        for msg in track:
            if msg.type == 'note_on' and msg.velocity != 0:
                note_on_events[msg.note] = {'velocity': msg.velocity, 'time': current_time}

            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                if msg.note in note_on_events:
                    note_on_event = note_on_events.pop(msg.note)
                    # duration = current_time - note_on_event['time']

                    thisNote = {'track': i, 'note': msg.note, 'pitch': note_number_to_name(msg.note), 'velocity': note_on_event['velocity'], 'end_time': current_time, 'start_time': note_on_event['time']}
                    all_notes.append(thisNote)
                    # print(f"  Note: Note={msg.note}  Pitch={note_number_to_name(msg.note)}  Velocity={note_on_event['velocity']}  Duration={duration}  Time={current_time}")

            current_time += msg.time

    return all_notes

def find_greatest_key(dictionary, value):
    keys = [key for key in dictionary.keys() if key <= value]
    if keys:
        return max(keys)
    else:
        return None  # No key is smaller than or equal to the given value

def convert_ticks_to_ms(ticks_per_beat, tick):
    nearest_calculated_time = find_greatest_key(time_at_ticks_in_ms_map, tick)
    current_tempo = tempo_at_ticks_map[find_greatest_key(tempo_at_ticks_map, tick)]

    elapsed_ticks = tick - nearest_calculated_time
    elapsed_beats = elapsed_ticks / ticks_per_beat
    elapsed_time_microseconds = current_tempo * elapsed_beats
    elapsed_time_ms = elapsed_time_microseconds / 1000

    current_time = time_at_ticks_in_ms_map[nearest_calculated_time] + elapsed_time_ms

    time_at_ticks_in_ms_map[tick] = current_time
    # tempo_at_ticks_map[tick] = current_tempo

    return current_time

def convert_midi_file_to_battleplan(midi_file_path):
    create_tempo_event_timing_map(midi_file_path)
    all_notes = build_note_list_from_midi(midi_file_path)

    ticks_per_beat = get_ticks_per_beat(midi_file_path)

    for thisNote in all_notes:
        start_time_ms = convert_ticks_to_ms(ticks_per_beat, thisNote['start_time'])
        end_time_ms = convert_ticks_to_ms(ticks_per_beat, thisNote['end_time'])
        duration_ms = end_time_ms - start_time_ms
        print(f"  Note: Track={thisNote['track']}  Note={thisNote['note']}  Pitch={thisNote['pitch']}  Velocity={thisNote['velocity']}  Duration={duration_ms}ms  Start={start_time_ms}ms")

if __name__ == "__main__":
    midi_file_path = "1812overture.mid"
    convert_midi_file_to_battleplan(midi_file_path)