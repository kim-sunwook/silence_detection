from enum import Enum
import os

from tqdm import tqdm 
import moviepy.editor as mp
from pydub import AudioSegment
from pydub.silence import detect_silence


class AudioExtractMethod(Enum):
    METHOD_1 = "Run silence detection directly on mp4 file"
    METHOD_2 = "Extract audio from mp4 file, save it as wav file and run silence detection on wav file"
    METHOD_3 = "Extract audio from mp4 file, convert it to bytes and run silence detection on bytes"

def detect_silence_at_end_of_mp4(file_path, silence_threshold, min_silence_len):

    audio_extract_method  = AudioExtractMethod.METHOD_1
    
    if audio_extract_method == AudioExtractMethod.METHOD_1:
        audio_segment = AudioSegment.from_file(file_path)
    elif audio_extract_method == AudioExtractMethod.METHOD_2:
        # Extract audio from the MP4 file
        video = mp.VideoFileClip(file_path)
        audio = video.audio
    
        audio.write_audiofile("temp_audio.wav")

        # Load the extracted audio with pydub
        audio_segment = AudioSegment.from_wav("temp_audio.wav")
    elif audio_extract_method == AudioExtractMethod.METHOD_3:
        # Extract audio from the MP4 file
        video = mp.VideoFileClip(file_path)
        audio = video.audio
    
        # Export audio data to a bytes object
        audio_data = audio.to_soundarray(fps=44100)
        samples = audio_data.mean(axis=1)
        samples = (samples * 32767).astype("int16")

        # Create a pydub AudioSegment using the raw data
        audio_segment = AudioSegment(
            samples.tobytes(),
            frame_rate=44100,
            sample_width=samples.dtype.itemsize,
            channels=1
        )

    # Detect silence at the end of the audio
    silence_intervals = detect_silence(audio_segment, min_silence_len, silence_threshold, 1)
    if len(silence_intervals) > 0 and silence_intervals[-1][1] == len(audio_segment):
        return True, silence_intervals[-1]
    else:
        return False, None

folder_path = "./all_existing_aic_videos"
output_file = "silence_data_directly_from_mp4_write_threshold_-100.txt"

silence_lengths = []

video_count = 0
video_with_silence = 0
video_without_silence = 0
median_silence_length = 0

for file in tqdm(os.listdir(folder_path)):
    if file.endswith(".mp4"):
        video_count += 1
        file_path = os.path.join(folder_path, file)
        is_silence, silence_interval = detect_silence_at_end_of_mp4(file_path, silence_threshold=-100, min_silence_len=100)

        if is_silence:
            silence_length = silence_interval[1] - silence_interval[0]
            silence_lengths.append(silence_length)
            video_with_silence += 1
            
            # update median
            # median_silence_length = (median_silence_length * (video_with_silence - 1) + silence_length) / video_with_silence

            # print(f"{file}: Silence detected at the end of the video ({silence_length}ms)")

        else:
            video_without_silence += 1

if silence_lengths:
    average_silence_length = sum(silence_lengths) / len(silence_lengths)
    max_silence_length = max(silence_lengths)
    min_silence_length = min(silence_lengths)
    total_silence_length = sum(silence_lengths)

    with open(output_file, "w") as f:
        f.write(f"Number of videos: {video_count}\n")
        f.write(f"Number of videos with silence: {video_with_silence}\n")
        f.write(f"Number of videos without silence: {video_without_silence}\n")
        f.write(f"Average silence length: {average_silence_length}ms\n")
        f.write(f"Max silence length: {max_silence_length}ms\n")
        f.write(f"Min silence length: {min_silence_length}ms\n")
        f.write(f"Total silence length: {total_silence_length}ms\n")
else:
    print("No silence detected in any of the videos.")