from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import pandas as pd
import pickle
from rank_bm25 import BM25Okapi
import nltk

# Load the CSV file
df = pd.read_csv('./scrapers/output.csv')

# Load tokenized documents
with open('bm25_tokenized_documents.pkl', 'rb') as f:
    tokenized_documents = pickle.load(f)

# Initialize the BM25 model
bm25 = BM25Okapi(tokenized_documents)


# Define request and response models
class SearchQuery(BaseModel):
    query: str

class SearchResult(BaseModel):
    title: str
    url: str
# Initialize the FastAPI application
app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/search", response_model=List[SearchResult])
async def search(search_query: SearchQuery):
    tokenized_query = nltk.word_tokenize(search_query.query.lower())
    scores = bm25.get_top_n(tokenized_query, df['extracted text'].tolist(), n=10)
    results = [
        {"title": df.loc[df['extracted text'] == result]['title'].values[0],
         "url": df.loc[df['extracted text'] == result]['url'].values[0]}
        for result in scores
    ]
    return results
