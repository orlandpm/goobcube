from time import sleep
import mido
from mido import Message, open_output

outport = None
# Print available outputs
for port in mido.get_output_names():
    print(port) 
    outport = port
    break


# # Open FluidSynth port (adjust name as needed)
with open_output(outport) as outport:
    outport.send(Message('program_change', program=81, channel=0))
    outport.send(Message('note_on', note=60, velocity=81, channel=0))
    sleep(1)
    outport.send(Message('note_off', note=60, channel=0))
