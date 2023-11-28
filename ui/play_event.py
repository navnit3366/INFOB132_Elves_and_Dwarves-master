# -*- coding: utf-8 -*-
import pyaudio
import wave
from IPython.display import clear_output
import time


def play_event(sound, player, player_name, event):
    """Play a selected sound
    Parameters:
    -----------
    sound: argument who active or deactivate the sound, true or false (bool)
    sound_name:the name of the sound file that will be played (str)
    Versions:
    ---------
    spécification: Maroit Jonathan (v.1 17/02/16)
    implémentation: Maroit Jonathan(v.1 17/02/16)
    """
    if sound:
        sound_name = event + '.wav'
        chunk = 1024
        wf = wave.open(sound_name, 'rb')
        p = pyaudio.PyAudio()

        stream = p.open(
            format=p.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            output=True)

        data = wf.readframes(chunk)
        time_count = 0
        count_line = 0

        while data != '':
            time_count += 1
            if time_count == 18:
                time_count = 0
                display_event(player, player_name, event) #Cannot have 4 arguments, count_line has been deleted.
                count_line += 1
            stream.write(data)
            data = wf.readframes(chunk)

        stream.stop_stream()
        stream.close()
        wf.close()
        p.terminate()
    else:
        for count_line in range(20):
            event_display(player, player_name, event)
            time.sleep(0)
    time.sleep(2)
    clear_output()
