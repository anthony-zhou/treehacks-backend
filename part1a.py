import json
import openai
import dotenv
import os
import re
from pyannote.audio import Pipeline
import re
import whisper
import json
import sys

from utils import diarize_text
from chunkify import clean_json

dotenv.load_dotenv()
pipeline = Pipeline.from_pretrained('pyannote/speaker-diarization', use_auth_token=os.environ.get("PYANNOTE_KEY"))
model = whisper.load_model("tiny", device='cuda:0')

# speaker_name = 'lauren'
# audiofile_name = 'Lauren brooks.wav'
def create_convo_json(speaker_name, audiofile_name, num_speakers=None):
    # Get ASR result
    asr_result = model.transcribe(audiofile_name, language='en')

    # Get diarization result
    if num_speakers is not None:
        diarization_result = pipeline(audiofile_name, num_speakers=num_speakers)
    else:
        diarization_result = pipeline(audiofile_name)

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

    # Clean up the json
    transcripts = clean_json(transcripts)

    # Save the json
    # with open(f'data/{audiofile_name}.json', 'w', encoding='utf-8') as f:
    #     json.dump(transcripts, f, ensure_ascii=False, indent=4)
    for transcript in transcripts:
        print(json.dumps(transcript))
        
    return transcripts



create_convo_json('', sys.argv[1])