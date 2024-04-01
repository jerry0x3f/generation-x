# (random walk &/| random arpeggios * 6->> elektron cycles <-> display on machine jam with some dice and mute control)

and focus on sound processing with usage of the external guitar effects.

## Example initial settings

```python
from models import MusicScale, MusicScaleType
base_tempo = 10
pause_factor = 70
sequences_config = [
    f'a|3|5:-1.1|2:-1.1|{base_tempo}|3th|d|7/8',
    f'a|2|3|2:-1.1|{base_tempo}|3th down|f|6/8',
    f'a|2|2|2:-1.1|{base_tempo}|2th down|g|4/4',
    f'r|3|4|{int(base_tempo/2)}|{pause_factor}|6/8',
    f'r|3|3|{base_tempo}:-10.10|{pause_factor}|5/4',
    f'r|3|4|{base_tempo}:-10.10|{pause_factor}+10|4/4'
]
music_scale = MusicScale(scale=MusicScaleType.NATURAL_MINOR, tonic='c')
```

where:

```
    """
    # r|5:-1.1|4:-1.1|30:-10.10|30|4/4
    # stays for: random | octaves_length_fn | root_octave_fn | tempo_fn | pause_factor | meter

    # a|3:-1.1|6:-1.1|2:-1.1|30:-5.5|3th|g|4/4
    # stays for: arpeggio | bars_length_fn | total_notes_fn | root_octave_fn | tempo_fn | mode | start_note | meter

    # x.y specify optional randomization where: x=min, y=max, value=value+random(min, max)
    """
```

## Diagram

![Alt text](./docs/Generation-X-diagram.drawio.png?raw=true "Connection Diagram")

## Known issues

* every sequence has his own thread, all are weakly synchronized, can be perceived as another chaotic parameter to the general technique but is problematic for rhythm based compositions

## TODO

* randomization for every possible parameter
* exposing control with dice to every parameter, not only notes generation 
* not a clean code ;)
* docs and tests!