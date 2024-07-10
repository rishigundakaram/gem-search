import pandas as pd
from rank_bm25 import BM25Okapi
import nltk
import pickle

# Load the CSV file
df = pd.read_csv('./scrapers/output.csv')
documents = df['extracted text'].tolist()

# Download NLTK data files (only the first time)
nltk.download('punkt')

# Tokenize the documents
tokenized_documents = [nltk.word_tokenize(doc.lower()) for doc in documents]

# Train the BM25 model
bm25 = BM25Okapi(tokenized_documents)

with open('bm25_tokenized_documents.pkl', 'wb') as f:
    pickle.dump(tokenized_documents, f)
