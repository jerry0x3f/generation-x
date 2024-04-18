from argparse import ArgumentParser, Namespace
from pprint import pprint

import mido

from app import generate_sequences_by_config_params, run_sequences
from elektron_cycles import get_outport_elektron
from models import MusicScale, MusicScaleType, RunSettings
from config import sequences_config_parser
from machine_jam import reset_jam, get_outport_jam


def _get_input_args() -> Namespace:
    parser = ArgumentParser(
        prog='Generation-X',
        description='Symbolic music data generator for Elektron Model:Cycles and Maschine Jam',
    )

    parser.add_argument(
        "-mst",
        "--music_scale_tonic",
        type=str,
        default='c',
        help="Music scale tonic",
        choices=['c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'a#', 'b']
    )
    parser.add_argument(
        "-mss",
        "--music_scale_type",
        type=str,
        default='minor',
        help="Music scale type",
        choices=MusicScaleType.all_values()
    )
    parser.add_argument(
        "-t",
        "--tempo_bpm",
        type=int,
        default=60,
        help="Main tempo from which different sequences will be generated. "
             "Sequences can be generated with different tempos based on this value.",
        choices=range(10, 300),
        metavar='10-300'
    )
    parser.add_argument(
        "-r",
        "--rest_factor",
        type=int,
        default=70,
        help="Rest probability factor for random type generated sequences",
        choices=range(0, 100),
        metavar='0-100'
    )

    return parser.parse_args()


def _log_input_output_devices():
    onn = mido.get_output_names()
    print(f'all available outputs: {onn}')

    inn = mido.get_input_names()
    print(f'all available inputs: {inn}')


def _setup_and_run(input_args):
    prj_base_tempo = input_args.tempo_bpm
    sequences_config = [
        f'a|3|6|4|{prj_base_tempo}|3th down|c|8/16',
        f'a|3|5|6|{int(prj_base_tempo / 2)}|3th down|d|8/16',
        f'a|3|6|4|{int(prj_base_tempo / 4)}|5th up|f|12/16',
        f'r|3|3|{prj_base_tempo}:-5.5|{input_args.rest_factor}|5/4',
        f'r|3|4|{prj_base_tempo}:-5.5|{input_args.rest_factor}|4/4',
        f'r|1|3|{prj_base_tempo + 10}:-10.10|{input_args.rest_factor}|13/8',
    ]

    prj_music_scale = MusicScale(
        scale=MusicScaleType(input_args.music_scale_type),
        tonic=input_args.music_scale_tonic,
    )
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

    print(f'music scale={prj_run_settings.music_scale}')
    print(f'root tempo={prj_base_tempo}')
    print(f'rest factor={input_args.rest_factor}')

    print('===================================================== MUSIC GENERATED')
    pprint(prj_generated_sequences)
    print('=====================================================')

    reset_jam(get_outport_jam())
    run_sequences(get_outport_elektron(), prj_run_settings)


_log_input_output_devices()
input_arguments = _get_input_args()
_setup_and_run(input_arguments)
