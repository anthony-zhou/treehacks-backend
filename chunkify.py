

def clean_json(data):
    new_data = []
    last_speaker = None
    for d in data:
        d["text"] = d["text"].strip()
        if len(d["text"]) == 0:
            continue
        if d["speaker_id"] == last_speaker:
            d_prev = new_data[-1]
            d_prev["text"] = d_prev["text"] + " " + d["text"]
            d_prev["time_end"] = d["time_end"]
            d_prev["num_words"] += d["num_words"]
            new_data[-1] = d_prev
        else:
            new_data.append(d)
        last_speaker = d["speaker_id"]
    return new_data

def json_to_transcript(data):
    transcript = ""
    i = 0 
    last_speaker = None
    for d in data:
        if len(d["text"]) == 0:
            continue
        if d["speaker_id"] == last_speaker:
            transcript += " " + d["text"].strip()
        else:
            # transcript += "\n\n" + d["speaker_id"] + ":\n" + d["text"].strip()
            transcript += "\n\n" + d["role"] + ":\n" + d["text"].strip()
            i+=1
        last_speaker = d["speaker_id"]
    print(i)
    return transcript

def create_chunk(data, chunk_size="small", end_index = None):
    """Create chunks of conversation exchanges based on chunk_size from the end of the data."""
    if end_index is None:
        end_index = len(data)

    if chunk_size == "small":
        # 1 interviewer followed by 1 interviewee potentially followed by 1 interviewer
        # or enough for 300 words
        interviewee_speak = 0
        interviewer_speak = 0
        chunk_start = 0
        num_words = 0
        success = False
        for i, d in enumerate(reversed(data[:end_index])):
            if d["role"] == "INTERVIEWEE":
                interviewee_speak += 1
            else:
                interviewer_speak += 1

            num_words += d["num_words"]

            if interviewee_speak >= 1 and interviewer_speak >= 1 and num_words >= 300:
                # End on with this being the last paragraph
                chunk_start = end_index - i - 1
                success = True
                break
        
        return success, chunk_start, end_index

def chunkify(data, chunk_size, max_chunks = None):
    chunks_idxs = []

    success = True
    next_chunk_end = len(data)
    while success:
        success, chunk_start, chunk_end = create_chunk(data, chunk_size, end_index = next_chunk_end)
        if success:
            chunks_idxs.append((chunk_start, chunk_end))
            next_chunk_end = chunk_start
        else:
            # If we can't find a chunk, then we just expand the most recently calculated chunk to the beginning of the data
            chunks_idxs[-1] = (0, chunks_idxs[-1][1])
            success = False

    if max_chunks is not None:
        chunks_idxs = chunks_idxs[-max_chunks:]
    return chunks_idxs


# chunk_segments = chunkify(data_clean, "small")
# [json_to_transcript(data_clean[s:e]) for s,e in chunk_segments]



# if main
if __name__ == "main":
    import json
    file_name = "lauren_brooks"
    with open(f"data/{file_name}.json") as f:
        data = json.load(f)