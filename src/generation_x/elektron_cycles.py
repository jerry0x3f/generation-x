import mido

output_device = 'Elektron Model:Cycles'

_elektron_outport = None
try:
    _elektron_outport = mido.open_output(output_device)
except Exception as e:
    print(f'warn: could not open {output_device} MIDI output port!')
    elektron_outport = None


def get_outport_elektron():
    return _elektron_outport
