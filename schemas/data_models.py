from pydantic import BaseModel, Field

class QuestionInput(BaseModel):
  text: str = Field(..., title="Input Text", description="The input text to be processed.")

class QuestionModel(BaseModel):
    question: str

class AskModel(BaseModel):
    document_id: int
    question: str
