import json
import openai
import dotenv
import os
import re
from pyannote.audio import Pipeline
import re
import torch
import whisper
import json

from utils import diarize_text
from chunkify import clean_json, chunkify, json_to_transcript

dotenv.load_dotenv()
openai.api_key = os.environ.get("OPENAI_KEY1")
pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization", use_auth_token=os.environ.get("PYANNOTE_KEY")
)
model = whisper.load_model(
    "tiny",
    device="cuda"
    if torch.cuda.is_available()
    else "mps"
    if torch.backends.mps.is_available()
    else "cpu",
)


# speaker_name = 'lauren'
# audiofile_name = 'Lauren brooks.wav'
def create_convo_json(speaker_name, audiofile_name, num_speakers=None):
    # Get ASR result
    asr_result = model.transcribe(audiofile_name, language="en")

    # Get diarization result
    if num_speakers is not None:
        diarization_result = pipeline(audiofile_name, num_speakers=num_speakers)
    else:
        diarization_result = pipeline(audiofile_name)

    final_result = diarize_text(asr_result, diarization_result)

    transcripts = []
    for seg, spk, sent in final_result:
        obj = {
            "time_start": seg.start,
            "time_end": seg.end,
            "speaker_id": spk,
            "text": sent,
            "num_words": len(sent.split()),
        }
        transcripts.append(obj)

    # Clean up the json
    transcripts = clean_json(transcripts)

    # Save the json
    with open(f"data/{audiofile_name}.json", "w", encoding="utf-8") as f:
        json.dump(transcripts, f, ensure_ascii=False, indent=4)

    return transcripts


PROMPT = "I am going to share a chunk of a user interview. This is an exploratory interview where our general learning objective is to learn more about how the interviewee uses talent sharing. Could you please come up with a formal, numbered, list of follow up questions that we can ask the interviewer relating to what we are talking about at the end?  Please make the question be a natural response directly related to what the interviewee just said.\nHere is the interview:"

# Function that given a recording json, return a either a list of questions
def get_questions(file_name="lauren_brooks"):
    with open(f"data/{file_name}.json") as f:
        data = json.load(f)

    data_clean = clean_json(data)
    chunks = chunkify(data_clean, "medium", 1)
    assert len(chunks) == 1
    chunk_start, chunk_end = chunks[0]
    chunk = data_clean[chunk_start:chunk_end]
    transcript = json_to_transcript(chunk)
    print(transcript)

    gpt_prompt = PROMPT + "\n\n" + transcript.strip()

    completion = openai.Completion.create(
        model="text-davinci-003",
        prompt=gpt_prompt,
        temperature=0.7,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )
    gpt_output = completion.choices[0].text.strip()
    print(gpt_output)

    # We will have to modify regex for other output types
    # \n1. ... \n2. ... \n3. ...
    pattern_number = r"\d\..+\n"

    questions = [x.strip() for x in re.findall(pattern_number, gpt_output)]

    return questions


if __name__ == "__main__":
    get_questions()
