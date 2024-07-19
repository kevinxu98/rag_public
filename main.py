import io
import shutil
from fastapi import FastAPI, APIRouter, UploadFile, HTTPException, Depends, BackgroundTasks
import os
import uvicorn
from background_tasks import TextProcessor, client
from file_parser import FileParser
from schemas.data_models import AskModel, QuestionModel
from dotenv import load_dotenv
import openai
from database.db import get_db, File, FileChunk
from sqlalchemy import select
from sqlalchemy.orm import Session


app = FastAPI(title="Retrieval Augmented Generation (RAG) Microservice", version="0.0.1")
router = APIRouter()
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


@app.get('/', tags=["Main Controllers"])
async def root(db: Session = Depends(get_db)):
    files_query = select(File)
    files = db.scalars(files_query).all()
    files_list = [{"file_id": file.file_id, "file_name": file.file_name} for file in files]
    return files_list


@app.post("/upload_file/", tags=['Main Controllers'])
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile, db: Session = Depends(get_db)):
    # allowed file extensions
    allowed_extensions = ["txt", "pdf"]
    file_extension = file.filename.split('.')[-1]
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="File type not allowed")

    folder = "sources"
    try:
        os.makedirs(folder, exist_ok=True)
        file_location = os.path.join(folder, file.filename)
        file_content = await file.read()  
        with open(file_location, "wb+") as file_object:
            file_like_object = io.BytesIO(file_content)
            shutil.copyfileobj(file_like_object, file_object)

        content_parser = FileParser(file_location)
        file_text_content = content_parser.parse()
        new_file = File(file_name=file.filename, file_content=file_text_content)
        db.add(new_file)
        db.commit()
        db.refresh(new_file)

        background_tasks.add_task(TextProcessor(db, new_file.file_id).chunk_and_embed, file_text_content)
        return {"info": "File saved", "filename": file.filename}
    except Exception as e:
        print(f"Error saving file: {e}.")
        raise HTTPException(status_code=500, detail="Error saving file.")
  

@app.post("/ask_question/", tags=["Main Controllers"])
async def ask_question(request: AskModel, db: Session = Depends(get_db)):
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    openai.api_key = OPENAI_API_KEY

    if OPENAI_API_KEY is None:
        raise HTTPException(status_code=500, detail="OpenAI API key is not set.")
    try:
        similar_chunks = await get_similar_chunks(request.document_id, request.question, db)
        context_texts = [chunk.chunk_text for chunk in similar_chunks]
        context = " ".join(context_texts)

        system_message = f"You are a helpful assistant. Here is the context to use to reply to questions: {context}."
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": request.question},
            ])
        return {"response": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/find_similar_chunks/{file_id}", tags=["Main Controllers"])
async def find_similar_chunks_endpoint(file_id: int, question_data: QuestionModel, db: Session = Depends(get_db)):
    try:
        similar_chunks = await get_similar_chunks(file_id, question_data.question, db)
        formatted_response = [
            {"chunk_id": chunk.chunk_id, "chunk_text": chunk.chunk_text}
            for chunk in similar_chunks
        ]
        return formatted_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


async def get_similar_chunks(file_id: int, question: str, db: Session):
    try:
        response = client.embeddings.create(input=question, model="text-embedding-ada-002")
        question_embedding = response.data[0].embedding

        similar_chunks_query = select(FileChunk).where(FileChunk.file_id == file_id).order_by(FileChunk.embedding_vector.l2_distance(question_embedding)).limit(10)
        similar_chunks = db.scalars(similar_chunks_query).all()
        return similar_chunks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)