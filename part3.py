import openai
import dotenv
import os
from sentence_transformers import SentenceTransformer, util



dotenv.load_dotenv()
openai.api_key = os.environ.get("OPENAI_KEY1")



semantic_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2', device='cuda:3')


def nlp_search(query, chunks):
    docs = [c["text"] for c in chunks]


    # Encode query and documents
    query_emb = semantic_model.encode(query)
    doc_emb = semantic_model.encode(docs)

    #Compute dot score between query and all document embeddings
    scores = util.dot_score(query_emb, doc_emb)[0].cpu().tolist()

    #Combine docs & scores
    chunk_score_pairs = list(zip(chunks, scores))

    #Sort by decreasing score
    chunk_score_pairs = sorted(chunk_score_pairs, key=lambda x: x[1], reverse=True)
    
    
    # Feed into gpt
    # pre_prompt = f"Please answer the following question: {query}\n\nHere is the context:\n\n\n"
    pre_prompt = "Here is clips from a few interview:\n\n"
    post_prompt = f"\n\nUsing the above context, please answer the following question using several paragraph:\n {query}"
    gpt_prompt = pre_prompt

    cur_len = len(pre_prompt.split()) + len(post_prompt.split())
    num_chunks=0
    for chunk, score in chunk_score_pairs:
        if cur_len + len(chunk["text"].split()) > 2000:
            break
        cur_len += len(chunk["text"].split())
        num_chunks += 1
    print(f"Using {num_chunks} chunks")
    chunks_to_include = [c[0] for c in chunk_score_pairs[:num_chunks]]
    chunks_to_include = sorted(chunks_to_include, key=lambda x: x["chunk_start"])
    chunks_to_include = sorted(chunks_to_include, key=lambda x: x["file_name"])

    last_file_name = None
    for chunk in chunks_to_include:
        if chunk["file_name"] != last_file_name:
            gpt_prompt += f"\n\nCoversation with {chunk['file_name']}:\n\n"
        last_file_name = chunk["interviewee_name"]
        gpt_prompt += f"{chunk['text']}\n\n"


    gpt_prompt += post_prompt

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
    return gpt_output


if __name__ == "__main__":
    import json
    from chunkify import clean_json, chunkify, json_to_transcript

    file_names = ["courtney_nelson", "debbie_shotwell", "lauren_brooks", "sonali_das"]
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
        chunks.extend([{"text": json_to_transcript(data_clean[s:e]).strip(), "file_name": file_name, "interviewee_name": file_name.replace('_',' '), "chunk_start": s, "chunk_end": e} for s,e in chunk_segments])
    print(len(chunks))

    out = nlp_search("What is said about referrals?", chunks)
    print(out)