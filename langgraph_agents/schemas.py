from pydantic import BaseModel, Field

from typing import List


class Reflection(BaseModel):
    """Schema to be used by the actor agent to respond"""

    missing: str = Field(description="Critique of what is missing")
    superfluous: str = Field(description="Critique of what is superfluous")

class AnswerQuestion(BaseModel):
    """Schema to be used to answer a question"""
    answer: str = Field(description="Answer")
    reflection: Reflection = Field(description="Reflection on the initial answer")
    search_queries: List[str] = Field(
        description="1-3 search queries for researching improvements too address the critique of your current answer "
    )

class ReviseAnswer(AnswerQuestion):
    """Revise your original answer to your question"""

    references: List[str] = Field(
        description="Citations motivating your updated answer"
    )