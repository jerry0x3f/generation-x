# Abstract

The concept of chaos theory, experimentation, constraints, and repetitions intertwine as fundamental tools in the realm of generative music. Many artists adhere to the belief that within music created using such methods, every listener can uncover patterns, rhythms, and melodies. Music emerges from experiences, sometimes beyond our control, weaving together moments into a cohesive whole. From the ambient noise that surrounds us to the sporadic tones that arise, these elements can be harnessed and looped, incorporating basic music theory principles. Pioneers like Brian Eno famously crafted compositions by manipulating tape loops, cutting them randomly with scissors, and playing them back from various starting points and times. The addition of sound effects to these looped tracks or to the overall mix opens up further avenues of exploration.

With algorithmically generated music serving as a foundation, the application of controlled randomness, guided by the artist and further manipulated through simulation, creates fertile ground for composers to engage in live sound processing. This process allows them to infuse their creations with personal flair and color, stemming from the inherently unpredictable nature of the source material. Through iterative experimentation, rhythms and patterns gradually emerge, paving the way for composition.

Algorithmic music is not merely a tool; it is a gateway to artistic expression. Embracing randomness as a catalyst for creativity, composers are empowered to explore uncharted sonic territories, shaping unique auditory experiences. Ultimately, there is no inherent limitation to the use of algorithmic methods in music creation—it is simply another avenue for innovation and expression.

I am attaching here music I created with such a mindset. The outcome resonates with me, reaffirming my belief in the power of these methodologies. I am convinced that further exploration of similar techniques, particularly within the domain of artificial intelligence, holds immense potential to revolutionize the way artists express their creativity.

## Requirements and setup

Python 3.11.3
Poetry
rtmidi
Pydantic

```python
poetry install
```

Run:
```shell
poetry run python src/generation_x/__init__.py
```

## Diagram

(random walk &/| random arpeggios * 6->> elektron cycles <-> display on machine jam with some dice and mute control)

![Alt text](./docs/Generation-X-diagram.drawio.png?raw=true "Connection Diagram")

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

## Performance

Run software with initial settings and focus on sound processing with usage of the external guitar effects.
Playing with mute button for enabling / disabling sequences as a function for arrangement as well as dice function for melody changes.  

## Known issues

* every sequence has his own thread, all are weakly synchronized, can be perceived as another chaotic parameter to the general technique but is problematic for rhythm based compositions

## TODO

* randomization for every possible parameter
* exposing control with dice to every parameter, not only notes generation 
* not a clean code ;)
* docs and tests!