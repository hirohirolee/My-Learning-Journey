import wave
import math
import struct

def generate_tone(filename, duration, frequency_func, volume=0.5):
    sample_rate = 44100
    num_samples = int(sample_rate * duration)
    
    with wave.open(filename, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        
        for i in range(num_samples):
            t = float(i) / sample_rate
            freq = frequency_func(t)
            value = int(volume * 32767.0 * math.sin(2.0 * math.pi * freq * t))
            data = struct.pack('<h', value)
            f.writeframesraw(data)

def gameover_freq(t):
    return max(50, 400 - (t * 400))
    
def music_freq(t):
    notes = [220, 261, 329, 392]
    idx = int((t * 4) % len(notes))
    return notes[idx]

if __name__ == '__main__':
    print("Generating assets/gameover.wav...")
    generate_tone('d:/15games/assets/gameover.wav', 1.0, gameover_freq, volume=0.3)
    print("Generating assets/music.wav...")
    generate_tone('d:/15games/assets/music.wav', 4.0, music_freq, volume=0.1)
    print("Done!")
