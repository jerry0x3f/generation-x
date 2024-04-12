from enum import Enum
from typing import Optional, List, Tuple

from pydantic import BaseModel


class Index(BaseModel):
    idx: int


class Note(BaseModel):
    midi_no: int
    name: str
    full_name: str
    octave: int
    freq_hz: float
    velocity: int = 64

    def __eq__(self, other):
        return self.midi_no == other.midi_no


class NoteLength(BaseModel):
    note: Optional[Note] = None
    note_length: float


class BarAndNoteLength(BaseModel):
    note_length: float
    bar_length: float

    def __str__(self):
        return f'note length: {round(self.note_length, 2)}, bar length: {round(self.bar_length, 2)}'


class TempoAndMeter(BaseModel):
    tempo: float = 120.0
    upper_meter: int = 4
    lower_meter: int = 4

    def __str__(self):
        return f'{round(self.tempo, 2)}bpm in {self.upper_meter}/{self.lower_meter}'

    def to_bar_and_note_length(self) -> BarAndNoteLength:
        quarter_note = 60 / self.tempo

        if self.lower_meter == 1:
            note_length = quarter_note * 4
        elif self.lower_meter == 2:
            note_length = quarter_note * 2
        elif self.lower_meter == 4:
            note_length = quarter_note
        elif self.lower_meter == 8:
            note_length = quarter_note / 2
        elif self.lower_meter == 16:
            note_length = quarter_note / 4
        else:
            raise ValueError(f'Wrong lower meter value: {self.lower_meter}!')

        bar_length = self.upper_meter * note_length

        return BarAndNoteLength(
            note_length=note_length,
            bar_length=bar_length,
        )


class MusicScaleType(Enum):
    MAJOR = 'major'
    NATURAL_MINOR = 'minor'
    HARMONIC_MINOR = 'harmonic_minor'
    MELODIC_MINOR = 'melodic_minor'


class MusicScale(BaseModel):
    tonic: str = 'c'
    scale: MusicScaleType = MusicScaleType.MAJOR


class RunSettings(BaseModel):
    sequencers: list
    sequence_play: bool
    quantize_to_scale: Optional[MusicScale]
    music_scale: MusicScale
    sequences_config_params: List[dict]
    generated_sequences: List[Tuple[TempoAndMeter, List[List[NoteLength]]]]
