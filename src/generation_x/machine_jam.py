from typing import Dict, Callable

import mido

from models import RunSettings
from music_utils import get_prev_scale_from_circle, get_next_scale_from_circle

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
    print(f'warn: could not open Maschine Jam - 1 Output MIDI output port!')


def get_outport_jam():
    return _outport_jam


def register_callback_on_input_jam(callback):
    midi_in_jam = 'Maschine Jam - 1 Input'
    try:
        mido.open_input(name=midi_in_jam, callback=callback)
        return True
    except Exception as e:
        print(f'Could not open input to: {midi_in_jam} or other error: {e}')
        return False


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


def register_jam_control(run_settings: RunSettings, functions: Dict[str, Callable]):
    def jam_in_callback(message: mido.Message):
        # play on / off
        # control_change channel=0 control=94 value=127 time=0
        # control_change channel=0 control=94 value=0 time=0
        if message.is_cc(94):
            if message.value == 127:
                run_settings.sequence_play = True
            if message.value == 0:
                run_settings.sequence_play = False

        # channel unmute / mute
        # A
        # control_change channel=0 control=8 value=127 time=0
        # control_change channel=0 control=8 value=0 time=0
        if message.is_cc(8):
            if message.value == 127:
                mute[0] = 1
            else:
                mute[0] = 0

        # B
        # control_change channel=0 control=9 value=127 time=0
        # control_change channel=0 control=9 value=0 time=0
        if message.is_cc(9):
            if message.value == 127:
                mute[1] = 1
            else:
                mute[1] = 0

        # C
        # control_change channel=0 control=10 value=127 time=0
        # control_change channel=0 control=10 value=0 time=0
        if message.is_cc(10):
            if message.value == 127:
                mute[2] = 1
            else:
                mute[2] = 0

        # D
        # control_change channel=0 control=11 value=127 time=0
        # control_change channel=0 control=11 value=0 time=0
        if message.is_cc(11):
            if message.value == 127:
                mute[3] = 1
            else:
                mute[3] = 0

        # E
        # control_change channel=0 control=12 value=127 time=0
        # control_change channel=0 control=12 value=0 time=0
        if message.is_cc(12):
            if message.value == 127:
                mute[4] = 1
            else:
                mute[4] = 0

        # F
        # control_change channel=0 control=13 value=127 time=0
        # control_change channel=0 control=13 value=0 time=0
        if message.is_cc(13):
            if message.value == 127:
                mute[5] = 1
            else:
                mute[5] = 0

        # 1,2,3,4,5 triggers
        # control_change channel=0 control=0..5 value=127 time=0
        try:
            if message.is_cc(0):
                functions.get("regenerate_seq", lambda s: None)(0)
            if message.is_cc(1):
                functions.get("regenerate_seq", lambda s: None)(1)
            if message.is_cc(2):
                functions.get("regenerate_seq", lambda s: None)(2)
            if message.is_cc(3):
                functions.get("regenerate_seq", lambda s: None)(3)
            if message.is_cc(4):
                functions.get("regenerate_seq", lambda s: None)(4)
            if message.is_cc(5):
                functions.get("regenerate_seq", lambda s: None)(5)
        except Exception as e:
            print(e)

        # <<
        # control_change channel=0 control=91 value=127 time=0
        # control_change channel=0 control=91 value=0 time=0
        if message.is_cc(91):
            if message.value == 127:
                run_settings.quantize_to_scale = get_prev_scale_from_circle(
                    run_settings.music_scale if not run_settings.quantize_to_scale else run_settings.quantize_to_scale
                )
                print(f'<< {run_settings.quantize_to_scale}')
                if run_settings.quantize_to_scale == run_settings.music_scale:
                    run_settings.quantize_to_scale = None

        # >>
        # control_change channel=0 control=92 value=127 time=0
        # control_change channel=0 control=92 value=0 time=0
        if message.is_cc(92):
            if message.value == 127:
                run_settings.quantize_to_scale = get_next_scale_from_circle(
                    run_settings.music_scale if not run_settings.quantize_to_scale else run_settings.quantize_to_scale
                )
                print(f'>> {run_settings.quantize_to_scale}')
                if run_settings.quantize_to_scale == run_settings.music_scale:
                    run_settings.quantize_to_scale = None

        # tempo (63 = 0%) (0 = -X%) (127 = +X%)
        # control_change channel=0 control=42 value=0 time=0
        for seq in run_settings.sequencers:
            if not seq:
                continue
            if message.is_cc(42):
                value = message.value - 63
                value_perc = value * 100 / 63
                new_tempo = seq.original_tempo + int(value_perc * seq.original_tempo / 100)
                seq.tempo = new_tempo
                print(f'{seq.desc} - {message.value} - {value} -> {new_tempo} | {seq.original_tempo}')

    return register_callback_on_input_jam(jam_in_callback)
