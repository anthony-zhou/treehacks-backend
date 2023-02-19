import json
import openai
from chunkify import clean_json, chunkify, json_to_transcript
import dotenv
import os
import re 
import sys

dotenv.load_dotenv()
openai.api_key = os.environ.get("OPENAI_KEY1")

PROMPT = "I am going to share a chunk of a user interview. This is an exploratory interview where our general learning objective is to learn more about how the interviewee uses talent sharing. Could you please come up with a formal, numbered, list of follow up questions that we can ask the interviewer relating to what we are talking about at the end?  Please make the question be a natural response directly related to what the interviewee just said.\nHere is the interview:"

# Function that given a recording json, return a either a list of questions
def get_questions(file_name="lauren_brooks"):
    with open(f"{file_name}.json") as f:
        data = json.load(f)
    

    data_clean = clean_json(data)
    chunks = chunkify(data_clean, "small", 1)
    assert len(chunks) == 1
    chunk_start, chunk_end = chunks[0]
    chunk = data_clean[chunk_start:chunk_end]
    transcript = json_to_transcript(chunk)
    print(transcript)

    gpt_prompt = PROMPT + "\n\n" + transcript.strip()


    completion = openai.Completion.create(
        model="text-davinci-003",
        prompt=gpt_prompt,
        temperature=.7,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    gpt_output = completion.choices[0].text.strip()
    print(gpt_output)

    # We will have to modify regex for other output types
    # \n1. ... \n2. ... \n3. ...
    pattern_number = r"\d\..+\n"

    questions = [x.strip() for x in re.findall(pattern_number, gpt_output)]

    for question in questions:
        print(question)

    return questions