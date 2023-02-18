from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pyannote.audio import Pipeline
import re
import whisper
import json
from utils import diarize_text

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



SPEAKER_NAME = 'sonali'
AUDIOFILE_NAME = 'Sonali Das 7-8.wav'
NUM_SPEAKERS = 3

def get_diarized_transcript():
  pipeline = Pipeline.from_pretrained('pyannote/speaker-diarization', use_auth_token='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')

  model = whisper.load_model("medium.en")
  asr_result = model.transcribe(AUDIOFILE_NAME, language='en')
  diarization_result = pipeline(AUDIOFILE_NAME)
  final_result = diarize_text(asr_result, diarization_result)

  transcripts = []
  for seg, spk, sent in final_result:
      obj = {
        'time_start': seg.start,
        'time_end': seg.end,
        'speaker_id': spk,
        'text': sent,
        'num_words': len(sent.split()),
      }
      transcripts.append(obj)

  with open(f'{AUDIOFILE_NAME}.json', 'w', encoding='utf-8') as f:
    json.dump(transcripts, f, ensure_ascii=False, indent=4)
    
  return transcripts
    

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the API!"}