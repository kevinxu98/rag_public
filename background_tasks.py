from sqlalchemy.orm import Session
from database.db import FileChunk
import nltk
from nltk.tokenize import sent_tokenize
from openai import OpenAI
from dotenv import load_dotenv
import ssl

load_dotenv()
client = OpenAI()

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context


nltk.download('punkt')


class TextProcessor:
    def __init__(self, db: Session, file_id: int, chunk_size: int = 2):
        self.db = db
        self.file_id = file_id
        self.chunk_size = chunk_size

    def chunk_and_embed(self, text: str) -> None:

        sentences = sent_tokenize(text)
        chunks = [' '.join(sentences[i:i + self.chunk_size])
                for i in range(0, len(sentences), self.chunk_size)]
        
        for chunk in chunks:
            # embeddings
            res = client.embeddings.create(
                input=chunk,
                model="text-embedding-ada-002"
            )
            embeddings = res.data[0].embedding
            file_chunk = FileChunk(file_id=self.file_id, chunk_text=chunk, embedding_vector=embeddings)
            self.db.add(file_chunk)

        self.db.commit()