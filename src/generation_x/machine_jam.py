import mido

tracker_midi_notes = [
    [104, 96, 88, 80, 72, 64, 56, 48],
    [105, 97, 89, 81, 73, 65, 57, 49],
    [106, 98, 90, 82, 74, 66, 58, 50],
    [107, 99, 91, 83, 75, 67, 59, 51],
    [108, 100, 92, 84, 76, 68, 60, 52],
    [109, 101, 93, 85, 77, 69, 61, 53],
]

velocity = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

mute = [1, 1, 1, 1, 1, 1]

_outport_jam = None
try:
    _outport_jam = mido.open_output('Maschine Jam - 1 Output')
except Exception:
    _outport_jam = None
    print('No Machine JAM for controlling connected!')


def get_outport_jam():
    return _outport_jam


def refresh_col(outport_jam, midi_notes, values):
    if not outport_jam:
        return

    if len(midi_notes) != len(values) and len(values) != 8:
        return

    for idx, midi_no in enumerate(midi_notes):
        msg = mido.Message(
            'note_on',
            note=midi_no,
            velocity=127 if values[idx] > 0 else 0,
        )
        outport_jam.send(msg)


def reset_jam(outport_jam):
    if not outport_jam:
        return

    # reset visualisation
    refresh_col(outport_jam, tracker_midi_notes[0], velocity[0])
    refresh_col(outport_jam, tracker_midi_notes[1], velocity[1])
    refresh_col(outport_jam, tracker_midi_notes[2], velocity[2])
    refresh_col(outport_jam, tracker_midi_notes[3], velocity[3])
    refresh_col(outport_jam, tracker_midi_notes[4], velocity[4])
    refresh_col(outport_jam, tracker_midi_notes[5], velocity[5])
    # play off
    msg = mido.Message(
        'control_change',
        control=94,
        value=0,
    )
    outport_jam.send(msg)
    # mute sequences
    msg = mido.Message(
        'control_change',
        control=8,
        value=0 if mute[0] == 0 else 127,
    )
    outport_jam.send(msg)
    msg = mido.Message(
        'control_change',
        control=9,
        value=0 if mute[1] == 0 else 127,
    )
    outport_jam.send(msg)
    msg = mido.Message(
        'control_change',
        control=10,
        value=0 if mute[2] == 0 else 127,
    )
    outport_jam.send(msg)
    msg = mido.Message(
        'control_change',
        control=11,
        value=0 if mute[3] == 0 else 127,
    )
    outport_jam.send(msg)
    msg = mido.Message(
        'control_change',
        control=12,
        value=0 if mute[4] == 0 else 127,
    )
    outport_jam.send(msg)
    msg = mido.Message(
        'control_change',
        control=13,
        value=0 if mute[5] == 0 else 127,
    )
    outport_jam.send(msg)

    # set knob
    msg = mido.Message(
        'control_change',
        control=42,
        value=63,
    )
    outport_jam.send(msg)
