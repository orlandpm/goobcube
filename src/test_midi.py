import mido

print("🎛 Available input ports:")
ports = mido.get_input_names()
for i, name in enumerate(ports):
    print(f"{i + 1}. {name}")

selection = input("Select MIDI input port number: ")
port_name = ports[int(selection) - 1]
with mido.open_input(port_name) as port:
    print(f"Listening on {port_name}...")
    for msg in port:
        print(msg)


# from time import sleep
# import mido
# from mido import Message, open_output

# outport = None
# # Print available outputs
# for port in mido.get_output_names():
#     print(port) 
#     outport = port
#     break


# # # Open FluidSynth port (adjust name as needed)
# with open_output(outport) as outport:
#     outport.send(Message('program_change', program=81, channel=0))
#     outport.send(Message('note_on', note=60, velocity=81, channel=0))
#     sleep(1)
#     outport.send(Message('note_off', note=60, channel=0))
