import itertools
import random
from copy import deepcopy
from typing import List

from models import Note, NoteLength, TempoAndMeter, MusicScale, MusicScaleType
from midi_data import midi_note_from_name_and_octave, all_midi_data


def get_key_frequency(key_in_octave: int, octave: int = 4) -> float:
    """
    Returns key frequency in Hz.
    :param key_in_octave: key in octave, 0-c, 11-b
    :param octave: number of octave, from 0 to 7
    :return: Key frequency.
    """
    k = octave * 12 + key_in_octave
    return (2 ** ((k - 49) / 12)) * 440


def get_scale(music_scale: MusicScale) -> (dict, list, int):
    """
    Returns tuple (hash, list) where:
    - first is hash with all 12 notes and boolean flag indicating if note is in scale,
    - second is list with notes available in scale.

    Example:
    >>> print(get_scale(MusicScale(tonic='c', scale=MusicScaleType.MAJOR)))
    ({'c': True, 'c#': False, 'd': True, 'd#': False, 'e': True, 'f': True, 'f#': False, 'g': True, 'g#': False, 'a': True, 'a#': False, 'b': True}, ['c', 'd', 'e', 'f', 'g', 'a', 'b', 'c']), 7

    :param music_scale: root note and scale
    :return: dict of all octave notes with status if such note is in scale, list of scale notes, index on which octave increase
    """
    keys = [
        'c',
        'c#',
        'd',
        'd#',
        'e',
        'f',
        'f#',
        'g',
        'g#',
        'a',
        'a#',
        'b',
    ]

    if music_scale.tonic.lower() not in keys:
        raise ValueError(f"{music_scale.tonic} is not a key!")

    step = 2
    idx = keys.index(music_scale.tonic.lower())
    scale_notes = []

    prev_idx = 0
    octave_change_at = None
    for i in range(0, 8):
        scale_notes.append(keys[idx % 12])

        if idx % 12 < prev_idx % 12:
            octave_change_at = len(scale_notes) - 1

        if music_scale.scale == MusicScaleType.MAJOR:
            if len(scale_notes) == 3 or len(scale_notes) == 7:
                step = 1
            else:
                step = 2

        elif music_scale.scale == MusicScaleType.NATURAL_MINOR:
            if len(scale_notes) == 2 or len(scale_notes) == 5:
                step = 1
            else:
                step = 2

        elif music_scale.scale == MusicScaleType.HARMONIC_MINOR:
            if len(scale_notes) == 2 or len(scale_notes) == 5 or len(scale_notes) == 7:
                step = 1
            elif len(scale_notes) == 6:
                step = 3
            else:
                step = 2

        elif music_scale.scale == MusicScaleType.MELODIC_MINOR:
            if len(scale_notes) == 2 or len(scale_notes) == 7:
                step = 1
            else:
                step = 2

        prev_idx = idx
        idx = idx + step

    notes_with_scale_status = {}
    idx = keys.index(music_scale.tonic.lower())
    for i in range(0, 12):
        notes_with_scale_status[keys[idx % 12]] = keys[idx % 12] in scale_notes
        idx = idx + 1

    return notes_with_scale_status, scale_notes, octave_change_at


def get_all_octaves_in_scale(music_scale: MusicScale) -> List[Note]:
    _, scale_notes, _ = get_scale(music_scale)

    all_notes = list()
    for full_note_name, midi_data in all_midi_data().items():
        if midi_data.name.lower() in scale_notes:
            all_notes.append(midi_data)

    return all_notes


def get_all_octaves_in_pentatonic_scale(music_scale: MusicScale) -> List[Note]:
    _, scale_notes, _ = get_scale(music_scale)
    scale_notes.pop(3)
    scale_notes = scale_notes[0:5]

    all_notes = list()
    for full_note_name, midi_data in all_midi_data().items():
        if midi_data.name.lower() in scale_notes:
            all_notes.append(midi_data)

    return all_notes


def get_closes_note(note: str, notes_with_scale_status: dict) -> (str, str):
    """
    Return closes note to provided note and scale notes.

    >>> notes_with_scale_status, scale = get_scale(MusicScale(tonic='c', scale=MusicScaleType.MAJOR))
    >>> print(get_closes_note('g#', notes_with_scale_status))
    ('g', 'a')

    :param note:
    :param notes_with_scale_status:
    :return:
    """
    if note not in notes_with_scale_status.keys():
        raise ValueError('Invalid note!')

    note_status = notes_with_scale_status[note]
    if note_status:
        return note, note

    notes_with_scale_status_list = list(notes_with_scale_status.items())
    notes_with_scale_status_list.append(notes_with_scale_status_list[0])

    note_idx = notes_with_scale_status_list.index((note, False))
    notes_with_scale_status_down = notes_with_scale_status_list[:note_idx]
    notes_with_scale_status_up = notes_with_scale_status_list[note_idx:]

    down_note = None
    for i in range(0, len(notes_with_scale_status_down)):
        if notes_with_scale_status_down[len(notes_with_scale_status_down) - 1 - i][1]:
            down_note = notes_with_scale_status_down[len(notes_with_scale_status_down) - 1 - i][0]
            break

    up_note = None
    for i in range(0, len(notes_with_scale_status_up)):
        if notes_with_scale_status_up[i][1]:
            up_note = notes_with_scale_status_up[i][0]
            break

    return down_note, up_note


def quantize(note: Note, music_scale: MusicScale, down=True) -> Note:
    notes_with_scale_status, scale_notes, _ = get_scale(music_scale)
    down_note, up_note = get_closes_note(note.name.lower(), notes_with_scale_status)
    if down:
        return midi_note_from_name_and_octave(down_note, note.octave)
    else:
        return midi_note_from_name_and_octave(up_note, note.octave)


def get_next_scale_from_circle(music_scale: MusicScale) -> MusicScale:
    """
    Circle of fifth clockwise
    :param music_scale:
    :return:
    """
    notes_with_scale_status, scale_notes, _ = get_scale(music_scale)
    return MusicScale(tonic=scale_notes[4], scale=music_scale.scale)


def get_prev_scale_from_circle(music_scale: MusicScale) -> MusicScale:
    """
    Circle of fifth counterclockwise
    :param music_scale:
    :return:
    """
    notes_with_scale_status, scale_notes, _ = get_scale(music_scale)
    return MusicScale(tonic=scale_notes[-5], scale=music_scale.scale)


def generate_arpeggio_in_same_octave(root_note: str, music_scale: MusicScale, mode="3th up", total_notes=4,
                                     main_octave=4) -> List[Note]:
    """
    Generates simple arpeggio melody.

    :param root_note: arpegio root note
    :param music_scale: tonic and scale root note
    :param mode: arpeggio steps (offset, distance between notes like 2th, 3th, 5th, 7th) and direction (up, down),
                 1th will not have effect
    :param total_notes: total notes in arpeggio
    :param main_octave: arpeggio octave

    :return: list of notes
    """
    notes_with_scale_status, scale_notes, octave_change_after_idx = get_scale(music_scale)
    closes_note_down, closes_note_up = get_closes_note(root_note, notes_with_scale_status)
    mode_parts = mode.split(' ')
    direction = mode_parts[1].strip() if len(mode_parts) == 2 else 'up'
    mode_offset = int(mode_parts[0].replace("th", ""))

    if direction not in ['up', 'down']:
        raise ValueError(f'Unsupported direction: {direction}')

    print(
        f'{scale_notes} -> {mode_offset}th -> {direction} from {closes_note_down} -> {total_notes} in octave {main_octave}')
    arpeggio_notes = []

    if direction == 'down':
        scale_notes.pop(0)
        scale_notes.reverse()
    else:
        scale_notes.pop(-1)

    start_note_idx = scale_notes.index(closes_note_down)

    for note in itertools.islice(itertools.cycle(scale_notes), start_note_idx,
                                 start_note_idx + ((mode_offset - 1) * total_notes), mode_offset - 1):
        midi_data = midi_note_from_name_and_octave(note, main_octave)

        arpeggio_notes.append(midi_data)

    return arpeggio_notes


def generate_arpeggio(root_note: str, music_scale: MusicScale, mode="3th up", total_notes=4, root_octave=4) -> List[
    Note]:
    """
    Generates simple arpeggio melody.

    :param root_note: arpegio root note
    :param music_scale: tonic and scale root note
    :param mode: arpeggio steps (offset, distance between notes like 2th, 3th, 5th, 7th) and direction (up, down),
                 1th will not have effect
    :param total_notes: total notes in arpeggio
    :param root_octave: arpeggio starting octave

    :return: list of notes
    """
    notes_with_scale_status, scale_notes, octave_change_after_idx = get_scale(music_scale)
    all_midi_octaves_in_scale = get_all_octaves_in_scale(music_scale)
    closes_note_down, closes_note_up = get_closes_note(root_note, notes_with_scale_status)
    mode_parts = mode.split(' ')
    direction = mode_parts[1].strip() if len(mode_parts) == 2 else 'up'
    mode_offset = int(mode_parts[0].replace("th", ""))

    if direction == 'up':
        all_midi_octaves_in_scale.reverse()

    print(f'Arpeggio: {scale_notes} -> {mode_offset}th -> {direction} from {closes_note_down} -> {total_notes} notes starting '
          f'in octave {root_octave}')

    root_note_idx = None
    for idx, note in enumerate(all_midi_octaves_in_scale):
        if note.name == closes_note_down.upper() and note.octave == root_octave:
            root_note_idx = idx
            break

    return list(
        itertools.islice(all_midi_octaves_in_scale, root_note_idx, root_note_idx + ((mode_offset - 1) * total_notes),
                         mode_offset - 1))


def generate_arpeggio_in_tempo(
        root_note,
        music_scale: MusicScale,
        tempo_and_meter: TempoAndMeter = TempoAndMeter(),
        bars=1,
        mode="3th",
        total_notes=4,
        root_octave=4
):
    arpeggio_notes = generate_arpeggio(root_note, music_scale, mode, total_notes, root_octave)
    note_and_bar_length = tempo_and_meter.to_bar_and_note_length()

    full_melody = list()

    arp_note_idx = 0
    for bar_id in range(0, bars):
        bar_melody = list()

        for note_idx in range(0, tempo_and_meter.upper_meter):
            note = arpeggio_notes[arp_note_idx]
            arp_note_idx = arp_note_idx + 1
            if arp_note_idx >= len(arpeggio_notes):
                arp_note_idx = 0
            bar_melody.append(
                NoteLength(note=note, note_length=note_and_bar_length.note_length)
            )

        full_melody.append(bar_melody)

    return full_melody


def generate_random_melody(
        music_scale: MusicScale,
        octave=4,
        bars=1,
        tempo_and_meter: TempoAndMeter = TempoAndMeter(),
        pause_fn=lambda: random.randint(0, 1) == 0,
        velocity_fn=lambda n, t: get_random_velocity(n, t)
) -> List[List[NoteLength]]:
    """
    Generates random melody in a given scale starting in specified octave.
    Note generated from the scale with: random.randint(0, len(scale_notes) - 1)

    :param music_scale: tonic and scale
    :param octave: octave no
    :param bars: melody length in bars
    :param tempo_and_meter: melody tempo and meter (used to calculate note length)
    :param pause_fn: function which determine if there will be a note or pause
    :param velocity_fn: function which generate velocity
    :return:list of size=bars where every bar has a list of random notes of size = upper meter
    """
    _, scale_notes, octave_change_at = get_scale(music_scale)
    full_melody = list()
    note_and_bar_length = tempo_and_meter.to_bar_and_note_length()
    for step in range(0, bars):
        bar_melody = list()
        for note_no in range(0, tempo_and_meter.upper_meter):
            if pause_fn():
                bar_melody.append(
                    NoteLength(note=None, note_length=note_and_bar_length.note_length)
                )
                continue

            random_note_idx = random.randint(0, len(scale_notes) - 1)
            if random_note_idx >= octave_change_at:
                octave_offset = 1
            else:
                octave_offset = 0

            note = midi_note_from_name_and_octave(scale_notes[random_note_idx], octave + octave_offset)

            if velocity_fn:
                note.velocity = velocity_fn(note_no + 1, tempo_and_meter)

            bar_melody.append(
                NoteLength(note=note, note_length=note_and_bar_length.note_length)
            )
        full_melody.append(bar_melody)

    return full_melody


def generate_random_melody_sequences(
        music_scale: MusicScale,
        bars_per_seq,
        octave_fn,
        tempo_fn,
        base_tempo=60,
        base_octave=4,
        pause_factor=80
):
    """
    Generate sequences, size=len(bars_per_seq), where every seq has bars_per_seq[seq_no] bar length with
    generate_random_melody inside the bar.

    :param music_scale: tonic and scale
    :param bars_per_seq: amount of bars per sequence
    :param octave_fn: function returning octave in which random melody will be operating
    :param tempo_fn: function returning tempo in which random melody will be operating
    :param base_tempo: base tempo from which the tempo_fn will deviate
    :param base_octave: base octave from which octave_fn will deviate
    :param pause_factor: pause will be triggered if rand(0,100) will be above this value

    :return: list[(TEMPO, list[list[notes]])]
    """
    sequence = list()

    for seq_no in range(0, len(bars_per_seq)):
        tempo_and_meter = TempoAndMeter()
        tempo_and_meter.tempo = tempo_fn(base_tempo)

        sequence.append(
            (tempo_and_meter,
             generate_random_melody(
                 music_scale,
                 octave=octave_fn(base_octave),
                 tempo_and_meter=tempo_and_meter,
                 pause_fn=lambda: random.randint(0, 100) < pause_factor,
                 bars=bars_per_seq[seq_no]
             )
             )
        )

    return sequence


def generate_random_walk_melody(
        music_scale: MusicScale,
        octave=4,
        bars=1,
        tempo_and_meter: TempoAndMeter = TempoAndMeter(),
        steps_deviation=3,
        velocity_fn=lambda n, t: get_random_velocity(n, t)
):
    """
    Generate melody with "random walk" algorithm, uses random gauss function:
    random.gauss(mu=1, sigma=steps_deviation)

    :param music_scale: Music scale
    :param octave: initial octave
    :param bars: amount of bars
    :param tempo_and_meter: tempo and meter
    :param steps_deviation: deviation for random steps
    :param velocity_fn: function to generate velocity
    :return: list[list[notes]]
    """
    full_scale_notes = get_all_octaves_in_scale(music_scale)
    note_and_bar_length = tempo_and_meter.to_bar_and_note_length()

    full_melody = list()

    start_idx = 0
    full_scale_notes.reverse()
    for note in full_scale_notes:
        if note.octave == octave and note.name == music_scale.tonic.upper():
            break
        start_idx = start_idx + 1

    steps = start_idx
    for bar in range(0, bars):
        bar_melody = list()
        for note_no in range(0, tempo_and_meter.upper_meter):
            note = deepcopy(full_scale_notes[steps]) if len(full_scale_notes) > steps else None

            if note and velocity_fn:
                note.velocity = velocity_fn(note_no + 1, tempo_and_meter)

            bar_melody.append(
                NoteLength(note=note, note_length=note_and_bar_length.note_length)
            )
            gg = int(random.gauss(mu=1, sigma=steps_deviation))

            steps = steps + gg

        full_melody.append(bar_melody)

    return full_melody


def generate_random_walk_melody_in_range(
        music_scale: MusicScale,
        octave=4,
        bars=1,
        min_pitch=-8,
        max_pitch=8,
        tempo_and_meter: TempoAndMeter = TempoAndMeter(),
        steps_deviation=3,
        velocity_fn=lambda n, t: get_random_velocity(n, t)
):
    """
    Generate melody with "random walk" algorithm but keeps notes in the given range.
    Step with function: random.randint(-1, 1) * steps_deviation

    :param music_scale: Music scale
    :param octave: initial octave
    :param bars: amount of bars
    :param min_pitch: min pitch from music scale tonic
    :param max_pitch: max pitch from music scale tonic
    :param tempo_and_meter: tempo and meter
    :param steps_deviation: deviation for random steps
    :param velocity_fn: function to generate velocity
    :return: list[list[notes]]
    """
    full_scale_notes = get_all_octaves_in_scale(music_scale)
    note_and_bar_length = tempo_and_meter.to_bar_and_note_length()

    start_idx = 0
    full_scale_notes.reverse()
    for note in full_scale_notes:
        if note.octave == octave and note.name == music_scale.tonic.upper():
            break
        start_idx = start_idx + 1

    full_melody = list()

    min_pitch_idx = start_idx + min_pitch
    if min_pitch_idx < 0:
        min_pitch_idx = 0

    max_pitch_idx = start_idx + max_pitch
    if max_pitch_idx > len(full_scale_notes):
        max_pitch_idx = len(full_scale_notes)

    steps = start_idx
    for bar in range(0, bars):
        bar_melody = list()
        for note_no in range(0, tempo_and_meter.upper_meter):
            note = deepcopy(full_scale_notes[steps]) if len(full_scale_notes) > steps else None

            if note and velocity_fn:
                note.velocity = velocity_fn(note_no + 1, tempo_and_meter)

            bar_melody.append(
                NoteLength(note=note, note_length=note_and_bar_length.note_length)
            )

            gg = random.randint(-1, 1) * steps_deviation

            steps = steps + gg
            if steps > max_pitch_idx:
                steps = max_pitch_idx
            if steps < min_pitch_idx:
                steps = min_pitch_idx

        full_melody.append(bar_melody)

    return full_melody


def generate_random_walk_melody_in_range_and_mean(
        music_scale: MusicScale,
        octave=4,
        bars=1,
        min_pitch=-8,
        max_pitch=8,
        tempo_and_meter: TempoAndMeter = TempoAndMeter(),
        steps_deviation=3,
        velocity_fn=lambda n, t: get_random_velocity(n, t)
):
    """
    Generate melody with "random walk" algorithm but keeps notes in the given range.
    Nest step is taken by random from mean value selected between the previous step and the middle of the range and
    step deviation.

    :param music_scale: Music scale
    :param octave: initial octave
    :param bars: amount of bars
    :param min_pitch: min pitch from music scale tonic
    :param max_pitch: max pitch from music scale tonic
    :param tempo_and_meter: tempo and meter
    :param steps_deviation: deviation for random steps
    :param velocity_fn: deviation for random steps
    :return: list[list[notes]]
    """
    full_scale_notes = get_all_octaves_in_scale(music_scale)
    note_and_bar_length = tempo_and_meter.to_bar_and_note_length()

    start_idx = 0
    full_scale_notes.reverse()
    for note in full_scale_notes:
        if note.octave == octave and note.name == music_scale.tonic.upper():
            break
        start_idx = start_idx + 1

    min_pitch_idx = start_idx + min_pitch
    if min_pitch_idx < 0:
        min_pitch_idx = 0

    max_pitch_idx = start_idx + max_pitch
    if max_pitch_idx > len(full_scale_notes):
        max_pitch_idx = len(full_scale_notes)

    middle_pitch_idx = int((min_pitch_idx + max_pitch_idx) / 2.0)

    print(f'min note: {full_scale_notes[min_pitch_idx]}')
    print(f'max note: {full_scale_notes[max_pitch_idx]}')
    print(f'middle note: {full_scale_notes[middle_pitch_idx]}')
    print(f'start note: {full_scale_notes[start_idx]}')

    note = deepcopy(full_scale_notes[start_idx])
    note.velocity = velocity_fn(1, tempo_and_meter)
    full_melody = list()
    full_melody.append(
        NoteLength(
            note=note,
            note_length=note_and_bar_length.note_length,
        )
    )
    for note_no in range(1, bars * tempo_and_meter.upper_meter):
        prev_note = full_melody[-1]
        prev_note_idx = full_scale_notes.index(prev_note.note)

        step_idx = random.randint(
            int((prev_note_idx + middle_pitch_idx) / 2.0),
            int((prev_note_idx + middle_pitch_idx) / 2.0) + steps_deviation
        )

        if step_idx > max_pitch_idx:
            step_idx = max_pitch_idx
        if step_idx < min_pitch_idx:
            step_idx = min_pitch_idx

        note = deepcopy(full_scale_notes[step_idx])

        if velocity_fn:
            note.velocity = velocity_fn(((note_no + 1) % bars), tempo_and_meter)

        full_melody.append(
            NoteLength(note=note, note_length=note_and_bar_length.note_length)
        )

    return [full_melody[x:x + bars] for x in range(0, len(full_melody), bars)]


def get_random_velocity(
        note_in_bar_idx: int,
        tempo_and_meter: TempoAndMeter,
        velocity: int = 64,
        min_deviation: int = 0,
        max_deviation: int = 10,
        accent_fn=lambda n, t: get_accent(n, t)
):
    acc_value = accent_fn(note_in_bar_idx, tempo_and_meter)
    velocity = velocity + random.randint(min_deviation, max_deviation) + acc_value
    if velocity > 127:
        velocity = 127
    return velocity


def get_accent(note_in_bar_idx: int, tempo_and_meter: TempoAndMeter, accent_value=30) -> int:
    """
    Returns accent_value if a note_in_bar_idx is considered strong note.

    :param note_in_bar_idx:
    :param tempo_and_meter:
    :param accent_value:
    :return:
    """
    if note_in_bar_idx > tempo_and_meter.upper_meter:
        return 0
    beats = []
    for i in range(0, tempo_and_meter.upper_meter):
        beats.append(1 if not i % 2 else 0)
    return accent_value if beats[note_in_bar_idx - 1] == 1 else 0
