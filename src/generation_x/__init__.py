from pprint import pprint

import mido

from app import generate_sequences_by_config_params, run_sequences
from elektron_cycles import get_outport_elektron
from models import MusicScale, MusicScaleType, RunSettings
from config import sequences_config_parser
from machine_jam import reset_jam, get_outport_jam

print('=====================================================')

onn = mido.get_output_names()
print(f'All available outputs: {onn}')

inn = mido.get_input_names()
print(f'All available inputs: {inn}')

print('=====================================================')

prj_base_tempo = 20
sequences_config = [
    f'a|3|6|4|{prj_base_tempo}|3th down|c|8/16',
    f'a|3|5|6|{int(prj_base_tempo / 2)}|3th down|d|8/16',
    f'a|3|6|4|{int(prj_base_tempo / 4)}|5th up|f|12/16',
    f'r|3|3|{prj_base_tempo}:-5.5|70|5/4',
    f'r|3|4|{prj_base_tempo}:-5.5|80|4/4',
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
run_sequences(get_outport_elektron(), prj_run_settings)
