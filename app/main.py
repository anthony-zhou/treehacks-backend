# import uvicorn

# if __name__ == "__main__":
#     uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)


from uuid import uuid4
from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import firebase_admin
from firebase_admin import firestore, storage
import requests
import json
import subprocess
import base64
from part1 import get_questions, create_convo_json
from chunkify import clean_json, chunkify, json_to_transcript
import os


from part3 import nlp_search

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cred = firebase_admin.credentials.Certificate(
    "treehacks-4f8e9-firebase-adminsdk-n3s06-007871e3c5.json"
)

default_app = firebase_admin.initialize_app(
    cred, {"storageBucket": "treehacks-4f8e9.appspot.com"}
)
db = firestore.client()


@app.get("/")
async def read_root():
    return {"message": "Welcome to the API!!!"}


from pydantic import BaseModel


class Conversation(BaseModel):
    audio_file_path: str
    interviewee_name: str


async def analyze_conversation_background(url: str, docId: str, final: bool = True):
    print("request received")
    # download the file temporarily
    # r = requests.get(url)
    url = base64.b64decode(url).decode("utf-8")

    r = requests.get(url)
    print(len(r.content))
    with open("temp.wav", "wb") as f:
        f.write(r.content)

    # run the analysis
    print("running analysis")
    transcripts = subprocess.run(
        ["python", "part1a.py", "temp.wav"], capture_output=True
    )
    transcripts = transcripts.stdout.decode("utf-8").splitlines()

    results = []
    for transcript in transcripts:
        if transcript.startswith("{"):
            transcript = json.loads(transcript)
            results.append(transcript)

    ppl_words = dict()
    for r in results:
        if r["speaker_id"] not in ppl_words:
            ppl_words[r["speaker_id"]] = 0
        ppl_words[r["speaker_id"]] += r["num_words"]

    # find max ppl words

    max_ppl = max(ppl_words, key=ppl_words.get)

    processed_data = [
        {
            **row,
            "role": "INTERVIEWEE" if row["speaker_id"] == max_ppl else "INTERVIEWER",
        }
        for row in results
    ]

    print(processed_data)

    stored = False
    if final and docId is not None:
        stored = True
        # store json in firebase
        # upload the results to firebase
        db.collection("conversations").document(docId).update(
            {"transcripts": processed_data, "questions": questions}
        )

        interviewee_name = (
            db.collection("conversations").document(docId).get().to_dict()["title"]
        )
        # Generate chunks
        chunks = get_chunks_from_json(processed_data, interviewee_name, docId)
        # Store chunks in firebase
        for chunk in chunks:
            db.collection("chunks").add(chunk)

    questions = get_questions("temp")

    return {
        "transcripts": processed_data,
        "questions": questions,
        "stored_json": stored,
        "stored_chunks": stored,
    }


# Given a download URL (wav file), download the URL and return the analysis
@app.post("/conversation_analysis")
async def get_convo_analysis(url: str, docId: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(analyze_conversation_background, url, docId)
    return {"message": "Request received, processing in the background"}


@app.post("/conversation/")
async def create_convo(audio_file: UploadFile = File(...)):
    # generate uuid
    _uuid = uuid4()
    blob = firebase_admin.storage.bucket().blob("audio_files/" + _uuid + ".m4a")
    blob.upload_from_file(audio_file.file)
    blob.make_public()
    return {
        "message": "Successfully uploaded {conversation.audio_file.filename}",
        "url": blob.public_url,
        "uuid": _uuid,
    }


# @app.post("/conversation/{uuid}")
# async def add_convo_deets(convo_dataset:):


# @app.post("/convo_index")
# async def add_convo_index(convo_location: str):
#     db.


class Chunk(BaseModel):
    text: str
    file_name: str
    interviewee_name: str
    chunk_start: str
    chunk_end: str


def get_chunks_from_json(convos_json, interviewee_name, file_name):
    """Returns all chunks from the database"""

    chunks = []
    convos_json_clean = clean_json(convos_json)
    chunk_segments = chunkify(convos_json_clean, "medium")
    chunks = [
        {
            "text": json_to_transcript(convos_json_clean[s:e]).strip(),
            "file_name": file_name,
            "interviewee_name": interviewee_name,
            "chunk_start": s,
            "chunk_end": e,
        }
        for s, e in chunk_segments
    ]
    return chunks


def get_all_chunks_from_json():
    """Returns all chunks from the json in the database"""
    convos = db.collection("conversations").get()
    transcripts_jsons = []
    interviewee_names = []
    uuids = []
    for convo in convos:
        convo_d = convo.to_dict()

        if "transcripts" in convo_d and "title" in convo_d and convo_d["title"] != "":
            transcripts_jsons.append(convo_d["transcripts"])
            interviewee_names.append(convo_d["title"])
            uuids.append(convo.id)

    chunks = []
    for data, file_name, interviewee_name in zip(
        transcripts_jsons, uuids, interviewee_names
    ):
        chunks.extend(get_chunks_from_json(data, interviewee_name, file_name))
    return chunks


def get_all_chunks_from_db():
    """Returns all chunks from the database"""
    chunks = db.collection("chunks").get()
    chunks = [c.to_dict() for c in chunks]
    return chunks


def get_all_chunks_from_disk():
    """Returns all chunks from the data directory on disk"""
    the_dir = "data"
    file_names = [
        f for f in os.listdir(the_dir) if os.path.isfile(os.path.join(the_dir, f))
    ]
    file_names = [f[:-5] for f in file_names if f.endswith(".json")]
    # file_names = ["courtney_nelson", "debbie_shotwell", "lauren_brooks", "sonali_das"]

    datas = []
    for file_name in file_names:
        with open(f"data/{file_name}.json") as f:
            datas.append(json.load(f))

    datas_clean = []

    chunks = []
    for data, file_name in zip(datas, file_names):
        data_clean = clean_json(data)
        datas_clean.append(data_clean)
        chunk_segments = chunkify(data_clean, "medium")
        chunks.extend(
            [
                {
                    "text": json_to_transcript(data_clean[s:e]).strip(),
                    "file_name": file_name,
                    "interviewee_name": file_name.replace("_", " "),
                    "chunk_start": s,
                    "chunk_end": e,
                }
                for s, e in chunk_segments
            ]
        )
    return chunks


@app.get("/search")
def search(query: str):
    chunks = get_all_chunks_from_db()
    # chunks = get_all_chunks_from_disk()
    output, chunks_to_include = nlp_search(query, chunks)
    return {"output": output, "chunks_to_include": chunks_to_include, "query": query}


@app.post("/upload")
def upload(file: UploadFile = File(...)):
    try:
        contents = file.file.read()
        with open("temp.webm", "wb") as buffer:
            buffer.write(contents)
    except Exception:
        return {"message": "There was an error uploading the file"}
    finally:
        file.file.close()

    return {"message": f"Successfully uploaded {file.filename}"}
