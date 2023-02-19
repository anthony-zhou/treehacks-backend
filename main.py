# import uvicorn

# if __name__ == "__main__":
#     uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)


from typing import Union
from uuid import uuid4
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import firebase_admin
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

cred = firebase_admin.credentials.Certificate("treehacks-4f8e9-firebase-adminsdk-n3s06-007871e3c5.json")

default_app = firebase_admin.initialize_app(cred, {"storageBucket": "treehacks-4f8e9.appspot.com"})
db = firebase_admin.firestore.client()

@app.get("/")
async def read_root():
    return {"message": "Welcome to the API!!!"}


from pydantic import BaseModel


class Conversation(BaseModel):
    audio_file_path: str
    interviewee_name: str


@app.post("/conversation/")
async def create_convo(audio_file: UploadFile = File(...)):
    # generate uuid
    _uuid = uuid4()
    blob = firebase_admin.storage.bucket().blob("audio_files/" + _uuid + ".m4a")
    blob.upload_from_file(audio_file.file)
    blob.make_public()
    return {"message": "Successfully uploaded {conversation.audio_file.filename}", "url": blob.public_url, "uuid": _uuid}

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

def get_all_chunks():
    return db.collection(u'chunks').get()

@app.post("/search")
def search(query: str):
    chunks = get_all_chunks()
    output = nlp_search(query, chunks)
    return {"output": output}

@app.post("/upload")
def upload(file: UploadFile = File(...)):
    try:
        contents = file.file.read()
        with open('temp.webm', "wb") as buffer:
            buffer.write(contents)
    except Exception:
        return {"message": "There was an error uploading the file"}
    finally:
        file.file.close()

    return {"message": f"Successfully uploaded {file.filename}"}
