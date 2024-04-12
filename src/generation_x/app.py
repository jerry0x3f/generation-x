import random
from typing import List, Tuple

import mido

from generators import NoteGeneratorFromSequence
from machine_jam import mute, get_outport_jam, velocity, refresh_col, tracker_midi_notes, register_jam_control
from models import RunSettings, TempoAndMeter, NoteLength, MusicScale
from music_utils import generate_random_melody, generate_arpeggio_in_tempo, quantize
from sequencer import Sequencer


def _flat_generated_notes(notes_with_lengths: List[List[NoteLength]]) -> List[str]:
    notes = []
    for bar in range(0, len(notes_with_lengths)):
        notes.append(','.join([nl.note.full_name if nl.note else '-' for nl in notes_with_lengths[bar]]))
    return notes


def regenerate_seq(run_settings: RunSettings, generated_sequences_no: int):
    if not len(run_settings.sequencers) >= generated_sequences_no:
        return

    if run_settings.sequences_config_params[generated_sequences_no]['generation_type'] != "random":
        print(f'{generated_sequences_no} is not a random, unsupported type!')
        return

    sequencer_instance = run_settings.sequencers[generated_sequences_no]

    curr_notes = _flat_generated_notes(run_settings.generated_sequences[generated_sequences_no][1])

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

    new_notes = _flat_generated_notes(run_settings.generated_sequences[generated_sequences_no][1])
    sequencer_instance.set_generator_bars_notes(run_settings.generated_sequences[generated_sequences_no][1])
    print(f'----------- regenerated {generated_sequences_no + 1}: {curr_notes} to {new_notes}')


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


def run_sequences(outport, run_settings: RunSettings):
    play_fn = lambda: run_settings.sequence_play

    for idx in range(0, len(run_settings.sequences_config_params)):
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
    jam_register_result = register_jam_control(
        run_settings,
        functions={
            'regenerate_seq': lambda seq_no: regenerate_seq(run_settings, seq_no),
        }
    )
    if not jam_register_result:
        # no JAM, we start automatically
        run_settings.sequence_play = True

    while True:
        pass
