from pyannote.audio import Pipeline
import re
from pydub import AudioSegment
import whisper
import json

SPEAKER_NAME = 'sonali'
AUDIOFILE_NAME = 'Sonali Das 7-8.wav'
NUM_SPEAKERS = 3


# # 1. Identify and store diarization intervals

# pipeline = Pipeline.from_pretrained('pyannote/speaker-diarization', use_auth_token='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')

# diarization = pipeline(AUDIOFILE_NAME, num_speakers=NUM_SPEAKERS)

# with open(f"diarization_{SPEAKER_NAME}.txt", "w") as text_file:
#     text_file.write(str(diarization))

# print("Diarization complete.")


# # 2. Use diarization intervals to split audio into new clips. 

# audio = AudioSegment.from_wav(AUDIOFILE_NAME)

# def millisec(timeStr):
#   spl = timeStr.split(":")
#   s = (int)((int(spl[0]) * 60 * 60 + int(spl[1]) * 60 + float(spl[2]) )* 1000)
#   return s

dz = open(f'diarization_{SPEAKER_NAME}.txt').read().splitlines()
# gidx = 0
# dzList = []
# for l in dz:
#   start, end =  tuple(re.findall('[0-9]+:[0-9]+:[0-9]+\.[0-9]+', string=l))
#   start = millisec(start)
#   end = millisec(end)
#   gidx += 1
#   audio[start:end].export(f'{SPEAKER_NAME}_{gidx}.wav', format='wav')
  
# print("Generated audio files from diarization.")


# 3. Use Whisper to get transcriptions for each audio clip. 

model = whisper.load_model("large")

# TODO: change output to [{“time_start”:, “time_end”:, “speaker_id”: , “num_words”: , “is_interviewee”: True},…]

res = []
for i in range(0, len(dz), 8):
  batch = dz[i:i+8]

  
  results = model.transcribe([f'{SPEAKER_NAME}_{j+1}.wav' for j in range(i, min(i+8, len(dz)))], language='en')

  for i, item in enumerate(batch):
    start, end =  tuple(re.findall('[0-9]+:[0-9]+:[0-9]+\.[0-9]+', string=item))
    speaker = re.findall('\w+$', string=item)[0]
    text = results[i]['text']
    obj = {
      'time_start': start,
      'time_end': end,
      'speaker_id': speaker,
      'text': text,
      'num_words': len(text.split()),
    }
    print(f'[{start} --> {end}] [{speaker}]')
    print(text)
    res.append(obj)

with open('data.json', 'w', encoding='utf-8') as f:
  json.dump(res, f, ensure_ascii=False, indent=4)