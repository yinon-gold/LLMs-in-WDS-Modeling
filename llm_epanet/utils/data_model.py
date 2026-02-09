from pydantic import BaseModel, Field
from typing import List, Literal, Optional

RevisionType = Literal["none", "function", "eval", "both"]

class ReviewResult(BaseModel):
    needs_revision: bool = Field(default=False, description="Indicates if the code needs revision")
    revision_type: RevisionType = Field(default="none", description="Type of revision needed")
    function_issues: List[str] = Field(default_factory=list, description="List of function issues")
    eval_issues: List[str] = Field(default_factory=list, description="List of evaluation issues")


class EPANETAgentResult(BaseModel):
    """Container for RAG pipeline results"""
    func_name: str
    func_code: str
    eval_script: Optional[str] = Field(default=None, description="Evaluation script for the function")
    prompts_used: List[str] = Field(default_factory=list, description="List of prompts used during generation")
    code_to_execute: Optional[str] = Field(default=None, description="Code that was executed")
    query_result: Optional[str] = Field(default=None, description="Result from the query")
    execution_error: Optional[str] = Field(default=None, description="Error message from code execution, if any")
    execution_successful: bool = Field(default=False, description="Indicates if code execution was successful")
    attempt: Optional[int] = Field(default=None, description="Attempt number for code execution")
    execution_time: Optional[float] = Field(default=None, description="Time taken for code execution only")
    query_time: Optional[float] = Field(default=None, description="Total time taken for the query process")
    usage_tokens: Optional[int] = Field(default=None, description="Number of tokens used in the process")
    cost: Optional[float] = Field(default=None, description="Cost incurred for the query process")