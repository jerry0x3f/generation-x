import random
from pprint import pprint
from typing import List, Tuple

import mido

from generators import NoteGeneratorFromSequence
from midi_data import midi_note_from_name_and_octave
from models import NoteLength, TempoAndMeter, MusicScale, MusicScaleType, Index, RunSettings
from music_utils import generate_random_melody, generate_random_melody_sequences, generate_arpeggio, \
    generate_random_walk_melody, generate_arpeggio_in_tempo, get_all_octaves_in_scale, \
    generate_random_walk_melody_in_range, generate_random_walk_melody_in_range_and_mean, get_accent, \
    get_random_velocity, get_all_octaves_in_pentatonic_scale, get_scale, get_next_scale_from_circle, \
    get_prev_scale_from_circle, quantize
from sequencer import Sequencer
from config import sequences_config_parser
from machine_jam import reset_jam, refresh_col, velocity, tracker_midi_notes, mute, get_outport_jam


def generate_sequences_by_config_params(
        config_params: List[dict],
        music_scale: MusicScale
) -> List[Tuple[TempoAndMeter, List[List[NoteLength]]]]:
    sequences = list()
    for seq_cfg in config_params:
        if seq_cfg.get('generation_type') == 'arpeggio':
            tempo = seq_cfg['tempo_fn']()
            arp_tempo = TempoAndMeter(
                tempo=tempo,
                upper_meter=seq_cfg['upper_meter'],
                lower_meter=seq_cfg['lower_meter'],
            )
            sequences.append(
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
            sequences.append(
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
    return sequences


def play_note_from_sequence_to_midi_msg(seq_no: int, note: NoteLength, outport, run_settings: RunSettings):
    i_play = note

    pp = f"{seq_no * 10 * ' '}"
    if i_play and i_play.note:
        note = i_play.note

        if run_settings.quantize_to_scale:
            p_note = quantize(note, run_settings.quantize_to_scale)
        else:
            p_note = note

        q_info = f"{note.name} quantized to {p_note.name}" if run_settings.quantize_to_scale else ""

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
            print(
                f"\n{pp}S{seq_no}: {p_note.full_name} {i_play.note_length} "
                f"{' muted' if not mute[seq_no] else ''} {q_info}")
    else:
        print(f"\n{pp}S{seq_no}: -")

    outport_jam = get_outport_jam()
    if outport_jam:
        velocity[seq_no].insert(0, i_play.note.velocity if i_play.note else 0)
        velocity[seq_no].pop(-1)
        refresh_col(outport_jam, tracker_midi_notes[seq_no], velocity[seq_no])


def flat_generated_notes(notes_with_lengths: List[List[NoteLength]]) -> List[str]:
    notes = []
    for bar in range(0, len(notes_with_lengths)):
        notes.append(','.join([nl.note.full_name if nl.note else '-' for nl in notes_with_lengths[bar]]))
    return notes


def regenerate_seq(generated_sequences_no: int, run_settings: RunSettings):
    if not len(run_settings.sequencers) >= generated_sequences_no:
        return

    if run_settings.sequences_config_params[generated_sequences_no]['generation_type'] != "random":
        print(f'{generated_sequences_no} is not a random, unsupported type!')
        return

    sequencer_instance = run_settings.sequencers[generated_sequences_no]

    curr_notes = flat_generated_notes(run_settings.generated_sequences[generated_sequences_no][1])

    seq_cfg: dict = run_settings.sequences_config_params[generated_sequences_no]
    tempo_and_meter = TempoAndMeter(
        tempo=seq_cfg['tempo_fn'](),
        upper_meter=seq_cfg['upper_meter'],
        lower_meter=seq_cfg['lower_meter'],
    )

    run_settings.generated_sequences[generated_sequences_no] = \
        (
            tempo_and_meter,
            generate_random_melody(
                run_settings.music_scale,
                octave=seq_cfg['root_octave_fn'](),
                tempo_and_meter=tempo_and_meter,
                pause_fn=lambda: random.randint(0, 100) < seq_cfg['pause_factor'],
                bars=seq_cfg['bars_length_fn']()
            )
        )

    new_notes = flat_generated_notes(run_settings.generated_sequences[generated_sequences_no][1])
    sequencer_instance.set_generator_bars_notes(run_settings.generated_sequences[generated_sequences_no][1])
    print(f'----------- regenerated {generated_sequences_no + 1}: {curr_notes} to {new_notes}')


def register_jam_control(run_settings: RunSettings):
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
                regenerate_seq(0, run_settings)
            if message.is_cc(1):
                regenerate_seq(1, run_settings)
            if message.is_cc(2):
                regenerate_seq(2, run_settings)
            if message.is_cc(3):
                regenerate_seq(3, run_settings)
            if message.is_cc(4):
                regenerate_seq(4, run_settings)
            if message.is_cc(5):
                regenerate_seq(5, run_settings)
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

    midi_in_jam = 'Maschine Jam - 1 Input'
    try:
        mido.open_input(name=midi_in_jam, callback=jam_in_callback)
        return True
    except Exception as e:
        print(f'Could not open input to: {midi_in_jam} or other error: {e}')
        return False


def test_in_sequences(outport, run_settings: RunSettings):
    play_fn = lambda: run_settings.sequence_play

    for idx in range(0, len(sequences_config)):
        tempo_and_meter = run_settings.generated_sequences[idx][0]
        generator = NoteGeneratorFromSequence(bars=run_settings.generated_sequences[idx][1])
        run_settings.sequencers.append(
            Sequencer(
                generator=generator,
                play_target=lambda note, _id=idx: play_note_from_sequence_to_midi_msg(
                    seq_no=_id,
                    note=note,
                    outport=outport,
                    run_settings=run_settings
                ),
                play_fn=play_fn,
                tempo_and_meter=tempo_and_meter,
                desc=f'SEQ{idx} [{generator.bars_length}]',
            )
        )

    print('=====================================================')
    if not register_jam_control(run_settings):
        run_settings.sequence_play = True  # FIXME for manual testing

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

output_device = 'Elektron Model:Cycles'

onn = mido.get_output_names()
print(f'All available outputs: {onn}')

if output_device not in onn:
    print(f'No midi device: {output_device} on the output midi list!')
    output_device = None

elektron_outport = None
if output_device:
    try:
        elektron_outport = mido.open_output(output_device)
    except Exception as e:
        print(f'Could not open MIDI port')
        elektron_outport = None

inn = mido.get_input_names()
print(f'All available inputs: {inn}')

print('=====================================================')

prj_base_tempo = 10
sequences_config = [
    f'a|3|6|4|{prj_base_tempo}|3th down|c|8/16',
    f'a|3|5|6|{int(prj_base_tempo / 2)}|3th down|d|8/16',
    f'a|3|6|4|{int(prj_base_tempo / 4)}|5th up|f|12/16',
    f'r|3|3|{prj_base_tempo}:-10.10|70|5/4',
    f'r|3|4|{prj_base_tempo}:-10.10|80|4/4',
    f'r|1|3|{prj_base_tempo + 10}:-10.10|80|13/8',
]

prj_music_scale = MusicScale(scale=MusicScaleType.NATURAL_MINOR, tonic='c')
prj_sequences_config_params = sequences_config_parser(sequences_config)
prj_generated_sequences = generate_sequences_by_config_params(prj_sequences_config_params, prj_music_scale)

prj_run_settings = RunSettings(
    sequencers=list(),
    sequence_play=False,
    quantize_to_scale=None,
    music_scale=prj_music_scale,
    sequences_config_params=prj_sequences_config_params,
    generated_sequences=prj_generated_sequences,
)

print(f'music_scale={prj_run_settings.music_scale}')

print('===================================================== MUSIC GENERATED')
pprint(prj_generated_sequences)
print('=====================================================')

reset_jam(get_outport_jam())
test_in_sequences(elektron_outport, prj_run_settings)
