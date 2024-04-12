from typing import Optional

from models import NoteLength


class NoteGenerator:

    def next(self) -> Optional[NoteLength]:
        pass


class NoteGeneratorFromSequence(NoteGenerator):

    def __init__(self, bars):
        """
        Create simple generator which just reads notes from bars and iterate in loop.
        :param bars: list of list
        """
        self.bars = bars
        self.bars_length = len(bars)
        self.current_bar = None
        self.current_length = None
        self.current_bar_idx = 0 if bars else None
        self.current_note = None
        self.current_note_idx = 0 if bars else None

    def set_new_bars(self, new_bars):
        self.bars = new_bars

    def next(self) -> Optional[NoteLength]:
        if not self.bars:
            return None

        self.current_bar = self.bars[self.current_bar_idx]
        self.current_note = self.current_bar[self.current_note_idx]

        self.current_note_idx = self.current_note_idx + 1
        if self.current_note_idx >= len(self.current_bar):
            self.current_note_idx = 0

            self.current_bar_idx = self.current_bar_idx + 1
            if self.current_bar_idx >= self.bars_length:
                self.current_bar_idx = 0

        return self.current_note
