import random
from pprint import pprint
from typing import List

import mido

from generators import NoteGeneratorFromSequence
from midi_data import midi_note_from_name_and_octave
from models import NoteLength, TempoAndMeter, MusicScale, MusicScaleType, Index
from music_utils import generate_random_melody, generate_random_melody_sequences, generate_arpeggio, \
    generate_random_walk_melody, generate_arpeggio_in_tempo, get_all_octaves_in_scale, \
    generate_random_walk_melody_in_range, generate_random_walk_melody_in_range_and_mean, get_accent, \
    get_random_velocity, get_all_octaves_in_pentatonic_scale, get_scale, get_next_scale_from_circle, \
    get_prev_scale_from_circle, quantize
from sequencer import Sequencer
from config import sequences_config_parser

output_device = 'Elektron Model:Cycles'

onn = mido.get_output_names()
print(f'All available outputs: {onn}')

if output_device not in onn:
    print(f'No midi device: {output_device} on the output midi list!')
    output_device = None

outport = None
if output_device:
    try:
        outport = mido.open_output(output_device)
    except Exception as e:
        print(f'Could not open MIDI port')
        outport = None

inn = mido.get_input_names()
print(f'All available inputs: {inn}')

print('=====================================================')

base_tempo = 10

sequences_config = [
    f'a|3|6|4|{base_tempo}|3th down|c|8/16',
    f'a|3|5|6|{int(base_tempo/2)}|3th down|d|8/16',
    f'a|3|6|4|{int(base_tempo/4)}|5th up|f|12/16',
    f'r|3|3|{base_tempo}:-10.10|70|5/4',
    f'r|3|4|{base_tempo}:-10.10|80|4/4',
    f'r|1|3|{base_tempo+10}:-10.10|80|13/8',
]

music_scale = MusicScale(scale=MusicScaleType.NATURAL_MINOR, tonic='c')
pause_factor = 70

print(f'music_scale={music_scale}')
print(f'base_tempo={base_tempo}')
print(f'pause_factor={pause_factor}')


def octave_fn(octave):
    return octave + random.randint(0, 2) - 2


def tempo_fn(tempo):
    return tempo + random.randint(0, int(base_tempo / 2) + 1) - base_tempo / 2


generated_sequences = list()
sequences_config_params = sequences_config_parser(sequences_config)
for seq_cfg in sequences_config_params:
    if seq_cfg.get('generation_type') == 'arpeggio':
        tempo = seq_cfg['tempo_fn']()
        arp_tempo = TempoAndMeter(
            tempo=tempo,
            upper_meter=seq_cfg['upper_meter'],
            lower_meter=seq_cfg['lower_meter'],
        )
        generated_sequences.append(
            (
                arp_tempo,
                generate_arpeggio_in_tempo(
                    root_note=seq_cfg['start_note'],
                    music_scale=music_scale,
                    tempo_and_meter=arp_tempo,
                    bars=seq_cfg['bars_length_fn'](),
                    mode=seq_cfg['mode'],
                    total_notes=seq_cfg['total_notes_fn'](),
                    root_octave=seq_cfg['root_octave_fn'](),
                )
            )
        )
    if seq_cfg.get('generation_type') == 'random':
        tempo = seq_cfg['tempo_fn']()
        ran_tempo = TempoAndMeter(
            tempo=tempo,
            upper_meter=seq_cfg['upper_meter'],
            lower_meter=seq_cfg['lower_meter'],
        )
        generated_sequences.append(
            (ran_tempo,
             generate_random_melody(
                 music_scale,
                 octave=seq_cfg['root_octave_fn'](),
                 tempo_and_meter=ran_tempo,
                 pause_fn=lambda: random.randint(0, 100) < seq_cfg['pause_factor'],
                 bars=seq_cfg['bars_length_fn']()
             )
             )
        )


print('===================================================== MUSIC GENERATED')
pprint(generated_sequences)
print('=====================================================')

try:
    outport_jam = mido.open_output('Maschine Jam - 1 Output')
except Exception:
    outport_jam = None
    print('No Machine JAM for controlling connected!')


def refresh_col(midi_notes, values):
    if len(midi_notes) != len(values) and len(values) != 8:
        return
    for idx, midi_no in enumerate(midi_notes):
        msg = mido.Message(
            'note_on',
            note=midi_no,
            velocity=127 if values[idx] > 0 else 0,
        )
        outport_jam.send(msg)


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


def reset_jam():
    if outport_jam:
        # reset visualisation
        refresh_col(tracker_midi_notes[0], velocity[0])
        refresh_col(tracker_midi_notes[1], velocity[1])
        refresh_col(tracker_midi_notes[2], velocity[2])
        refresh_col(tracker_midi_notes[3], velocity[3])
        refresh_col(tracker_midi_notes[4], velocity[4])
        refresh_col(tracker_midi_notes[5], velocity[5])
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


sequence_play = False


def play_note_from_sequence_to_midi_msg(seq_no: int, note: NoteLength):
    global outport, quantize_to_scale
    i_play = note

    pp = f"{seq_no * 10 * ' '}"
    if i_play and i_play.note:
        note = i_play.note

        if quantize_to_scale:
            p_note = quantize(note, quantize_to_scale)
        else:
            p_note = note

        q_info = f"{note.name} quantized to {p_note.name}" if quantize_to_scale else ""

        if outport and mute[seq_no]:
            msg = mido.Message(
                'note_on',
                channel=seq_no,
                note=p_note.midi_no,
                time=i_play.note_length,
                velocity=p_note.velocity,
            )
            outport.send(msg)
            print(f"\n{pp}S{seq_no}: {msg} {q_info}")
        else:
            print(f"\n{pp}S{seq_no}: {p_note.full_name} {i_play.note_length} {' muted' if not mute[seq_no] else ''} {q_info}")
            # pass
    else:
        print(f"\n{pp}S{seq_no}: -")
        # pass

    if outport_jam:
        velocity[seq_no].insert(0, i_play.note.velocity if i_play.note else 0)
        velocity[seq_no].pop(-1)
        refresh_col(tracker_midi_notes[seq_no], velocity[seq_no])


sequencers: List[Sequencer] = list()
quantize_to_scale = None


def flat_generated_notes(notes_with_lengths: List[List[NoteLength]]) -> List[str]:
    notes = []
    for bar in range(0, len(notes_with_lengths)):
        notes.append(','.join([nl.note.full_name if nl.note else '-' for nl in notes_with_lengths[bar]]))
    return notes


def regenerate_seq(generated_sequences_no: int):
    global sequences_config, generated_sequences, pause_factor

    if not len(sequencers) >= generated_sequences_no:
        return

    if sequences_config_params[generated_sequences_no]['generation_type'] != "random":
        print(f'{generated_sequences_no} is not a random, unsupported type!')
        return

    sequencer_instance = sequencers[generated_sequences_no]

    curr_notes = flat_generated_notes(generated_sequences[generated_sequences_no][1])

    seq_cfg: dict = sequences_config_params[generated_sequences_no]
    tempo_and_meter = TempoAndMeter(
        tempo=tempo,
        upper_meter=seq_cfg['upper_meter'],
        lower_meter=seq_cfg['lower_meter'],
    )

    generated_sequences[generated_sequences_no] = \
        (
            tempo_and_meter.tempo,
            generate_random_melody(
                music_scale,
                octave=seq_cfg['root_octave_fn'](),
                tempo_and_meter=tempo_and_meter,
                pause_fn=lambda: random.randint(0, 100) < seq_cfg['pause_factor'],
                bars=seq_cfg['bars_length_fn']()
            )
        )

    new_notes = flat_generated_notes(generated_sequences[generated_sequences_no][1])
    sequencer_instance.set_generator_bars_notes(generated_sequences[generated_sequences_no][1])
    print(f'----------- regenerated {generated_sequences_no+1}: {curr_notes} to {new_notes}')


def register_jam_control():
    def jam_in_callback(message: mido.Message):
        global sequence_play, quantize_to_scale

        # play on / off
        # control_change channel=0 control=94 value=127 time=0
        # control_change channel=0 control=94 value=0 time=0
        if message.is_cc(94):
            if message.value == 127:
                sequence_play = True
            if message.value == 0:
                sequence_play = False

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
                regenerate_seq(0)
            if message.is_cc(1):
                regenerate_seq(1)
            if message.is_cc(2):
                regenerate_seq(2)
            if message.is_cc(3):
                regenerate_seq(3)
            if message.is_cc(4):
                regenerate_seq(4)
            if message.is_cc(5):
                regenerate_seq(5)
        except Exception as e:
            print(e)

        # <<
        # control_change channel=0 control=91 value=127 time=0
        # control_change channel=0 control=91 value=0 time=0
        if message.is_cc(91):
            if message.value == 127:
                quantize_to_scale = get_prev_scale_from_circle(music_scale if not quantize_to_scale else quantize_to_scale)
                print(f'<< {quantize_to_scale}')
                if quantize_to_scale == music_scale:
                    quantize_to_scale = None

        # >>
        # control_change channel=0 control=92 value=127 time=0
        # control_change channel=0 control=92 value=0 time=0
        if message.is_cc(92):
            if message.value == 127:
                quantize_to_scale = get_next_scale_from_circle(music_scale if not quantize_to_scale else quantize_to_scale)
                print(f'>> {quantize_to_scale}')
                if quantize_to_scale == music_scale:
                    quantize_to_scale = None

        # tempo (63 = 0%) (0 = -X%) (127 = +X%)
        # control_change channel=0 control=42 value=0 time=0
        for seq in sequencers:
            if not seq:
                continue
            if message.is_cc(42):
                value = message.value - 63
                value_perc = value*100/63
                new_tempo = seq.original_tempo + int(value_perc*seq.original_tempo/100)
                seq.tempo = new_tempo
                print(f'{seq.desc} - {message.value} - {value} -> {new_tempo} | {seq.original_tempo}')

    midi_in_jam = 'Maschine Jam - 1 Input'
    try:
        mido.open_input(name=midi_in_jam, callback=jam_in_callback)
        return True
    except Exception as e:
        print(f'Could not open input to: {midi_in_jam} or other error: {e}')
        return False


def test_in_sequences():
    global sequence_play
    global sequencers

    play_fn = lambda: sequence_play

    for idx in range(0, len(sequences_config)):
        tempo_and_meter = generated_sequences[idx][0]
        generator = NoteGeneratorFromSequence(bars=generated_sequences[idx][1])
        sequencers.append(
            Sequencer(
                generator=generator,
                play_target=lambda note, _id=idx: play_note_from_sequence_to_midi_msg(seq_no=_id, note=note),
                play_fn=play_fn,
                tempo_and_meter=tempo_and_meter,
                desc=f'SEQ{idx} [{generator.bars_length}]',
            )
        )

    print('=====================================================')
    if not register_jam_control():
        sequence_play = True  # FIXME for manual testing

    while True:
        pass


def test_input_midi(midi_in_name):
    def midi_in_callback(message):
        print(message)

    try:
        mido.open_input(name=midi_in_name, callback=midi_in_callback)
    except Exception as e:
        print(f'Could not open input to: {midi_in_name} or other error: {e}')
        return

    while True:
        pass


print('=====================================================')

# pprint(get_all_octaves_in_scale(MusicScale(tonic='a', scale=MusicScaleType.MAJOR)))
# pprint(generate_random_walk_melody(MusicScale(tonic='a', scale=MusicScaleType.MAJOR), bars=4))
# print('=====================================================')

# pprint(
#     generate_random_walk_melody_in_range_and_mean(
#         MusicScale(tonic='c#', scale='major'),
#         bars=4,
#         min_pitch=-3,
#         max_pitch=12,
#     )
# )
#
# print('=====================================================')

# pprint(generate_arpeggio('c', MusicScale(tonic='c#', scale=MusicScaleType.MAJOR), total_notes=8, mode="7th down"))
# pprint(get_all_octaves_in_pentatonic_scale(MusicScale(tonic='c', scale=MusicScaleType.MAJOR)))
# pprint(get_scale(MusicScale(tonic='c', scale=MusicScaleType.MELODIC_MINOR)))

reset_jam()
test_in_sequences()

# print(get_next_scale_from_circle(MusicScale(tonic='f#', scale=MusicScaleType.NATURAL_MINOR)))
# print(get_prev_scale_from_circle(MusicScale(tonic='d#', scale=MusicScaleType.NATURAL_MINOR)))

# test_input_midi('Maschine Jam - 1 Input')
