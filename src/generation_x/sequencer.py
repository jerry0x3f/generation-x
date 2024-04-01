import time
from threading import Thread

from models import TempoAndMeter
from generators import NoteGenerator, NoteGeneratorFromSequence


class Sequencer(Thread):

    def __init__(self,
                 generator: NoteGenerator,
                 play_target,
                 play_fn,
                 tempo_and_meter: TempoAndMeter(tempo=120, upper_meter=4, lower_meter=16),
                 desc='Sequencer'):
        """
        Simple sequencer which executes play_target with note from generator.

        :param generator: note generator, returns next note on every sequence cycle
        :param play_target: function responsible for playing note from generator
        :param play_fn: function for indicating stop/play
        :param tempo_and_meter: tempo and meter
        :param desc: description
        """
        super(Sequencer, self).__init__(name=desc)
        self._generator = generator
        self._play_target = play_target
        self._tempo_and_meter = tempo_and_meter
        self.original_tempo = tempo_and_meter.tempo
        self._play = play_fn
        self.desc = desc

        self.daemon = True
        self.start()

    @property
    def tempo(self):
        return self._tempo_and_meter.tempo

    @tempo.setter
    def tempo(self, tempo):
        self._tempo_and_meter.tempo = tempo

    def set_generator_bars_notes(self, bars_with_notes):
        if isinstance(self._generator, NoteGeneratorFromSequence):
            self._generator.set_new_bars(bars_with_notes)

    def inc_tempo(self):
        self._tempo_and_meter.tempo = self._tempo_and_meter.tempo + 1

    def dec_tempo(self):
        self._tempo_and_meter.tempo = self._tempo_and_meter.tempo - 1
        if self._tempo_and_meter.tempo < 0:
            self._tempo_and_meter.tempo = 0

    def run(self):
        note_and_bar_length = self._tempo_and_meter.to_bar_and_note_length()
        print(f'{self.desc} {self._tempo_and_meter}: {note_and_bar_length}')
        while True:
            if self._play():
                next_note = self._generator.next()

                if next_note and self._play_target:
                    if next_note.note_length != note_and_bar_length.note_length:
                        next_note.note_length = note_and_bar_length.note_length
                    self._play_target(next_note)
                    # time.sleep(next_note.note_length)
                    # continue

                time.sleep(note_and_bar_length.note_length)
                note_and_bar_length = self._tempo_and_meter.to_bar_and_note_length()

