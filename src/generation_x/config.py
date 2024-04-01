import random
from typing import List


def parse_sequences_config(config: str) -> dict:
    def parse_range(config_part: str) -> (int, int):
        param_parts = config_part.split(":")
        if len(param_parts) == 2:
            param_parts_range = param_parts[1].split(".")
            if len(param_parts_range) == 2:
                return int(param_parts_range[0]), int(param_parts_range[1])
        return None, None

    default_random = dict(
            generation_type="random",
            bars_length_fn=lambda: 2,
            root_octave_fn=lambda: 4,
            tempo_fn=lambda: 30,
            pause_factor=30,
            upper_meter=4,
            lower_meter=4,
        )

    default_arp = dict(
            generation_type="arpeggio",
            bars_length_fn=lambda: 2,
            total_notes_fn=lambda: 6,
            root_octave_fn=lambda: 4,
            tempo_fn=lambda: 30,
            mode="3th",
            start_note="c",
            upper_meter=4,
            lower_meter=4,
    )

    config_parts = config.split("|")
    if not config_parts:
        return default_random

    config = dict()

    def set_config_param_with_range(idx, param_name) -> None:
        if len(config_parts) > idx:
            config_param_parts = config_parts[idx].split(":")
            left_range, right_range = parse_range(config_parts[idx])
            if left_range is not None and right_range is not None:
                config[param_name] = lambda: int(config_param_parts[0]) + random.randint(left_range, right_range)
            else:
                config[param_name] = lambda: int(config_param_parts[0])

    if config_parts[0] == 'r':
        config['generation_type'] = "random"
        set_config_param_with_range(1, 'bars_length_fn')
        set_config_param_with_range(2, 'root_octave_fn')
        set_config_param_with_range(3, 'tempo_fn')
        if len(config_parts) > 3:
            config['pause_factor'] = int(config_parts[4])
        if len(config_parts) > 4:
            meter_parts = config_parts[5].split('/')
            config['upper_meter'] = meter_parts[0]
            if len(meter_parts) > 1:
                config['lower_meter'] = meter_parts[1]

        return default_random | config

    if config_parts[0] == 'a':
        config['generation_type'] = "arpeggio"
        set_config_param_with_range(1, 'bars_length_fn')
        set_config_param_with_range(2, 'total_notes_fn')
        set_config_param_with_range(3, 'root_octave_fn')
        set_config_param_with_range(4, 'tempo_fn')
        if len(config_parts) > 4:
            config['mode'] = config_parts[5]
        if len(config_parts) > 5:
            config['start_note'] = config_parts[6]
        if len(config_parts) > 6:
            meter_parts = config_parts[7].split('/')
            config['upper_meter'] = meter_parts[0]
            if len(meter_parts) > 1:
                config['lower_meter'] = meter_parts[1]

        return default_arp | config

    raise ValueError('Unsupported sequence type')


def sequences_config_parser(sequences_config: List[str]) -> List[dict]:
    """
    Frames specifying the sequence configuration.

    # r|5:-1.1|4:-1.1|30:-10.10|30|4/4
    # random - octaves_length_fn - root_octave_fn - tempo_fn - pause_factor - meter

    # a|3:-1.1|6:-1.1|2:-1.1|30:-5.5|3th|g|4/4
    # arpeggio - bars_length_fn - total_notes_fn - root_octave_fn - tempo_fn - mode - start_note - meter

    # -x.x specify optional randomization for the value

    :param sequences_config:
    :return: dict with config values and functions
    """
    result = list()
    for c in sequences_config:
        result.append(parse_sequences_config(c))
    return result
