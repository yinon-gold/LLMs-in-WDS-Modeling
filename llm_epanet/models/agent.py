from typing import List, Tuple, Dict, Optional
from llm_epanet.models.retriever import Retriever
from llm_epanet.models.llm import LanguageModel
from llm_epanet.utils.logger import logger
from llm_epanet.utils.settings import MAX_ITERATIONS
from llm_epanet.utils.data_model import ReviewResult, EPANETAgentResult
from llm_epanet.utils.code_execution import execute_code_util
from llm_epanet.utils.utils import DEFAULT_SANDBOX_NETWORK_LOCATION, _check_if_external_epanet_inp_file

import json
import re
from datetime import datetime

from dataclasses import dataclass, field

@dataclass
class AgentState:
    """State container for the agentic loop"""
    # Input
    query: str
    epanet_network: str
    prompt: str
    k: int
    args: Optional[Dict]
    exec_script: bool
    code_exec_prompt: Optional[str]
    code_fix_prompt: Optional[str]
    code_review_prompt: Optional[str]

    # Generation state
    func_name: Optional[str] = None
    func_code: Optional[str] = None
    eval_script: Optional[str] = None
    code_to_execute: Optional[str] = None

    # Tracking
    prompts_used: List[str] = field(default_factory=list)
    iteration: int = 0
    max_iterations: int = MAX_ITERATIONS
    execution_attempts: int = 0
    max_execution_attempts: int = 3
    usage_tokens: int = 0
    usage_price: float = 0.0

    # Execution state
    query_result: Optional[str] = None
    execution_error: Optional[str] = None
    execution_successful: bool = False
    # Timing
    execution_time: Optional[float] = None

    # Review state
    review_result: Optional[ReviewResult] = None

    # Control flow
    next_action: str = "generate_function"
    state_history: List[str] = field(default_factory=list)

class CodeExecutor:
    """Handles code execution and related functionality"""
    def __init__(self, num_retries: int = 3, timeout: int = 60):
        self.num_retries = num_retries
        self.timeout = timeout
        self.DEFAULT_NETWORK_LOCATION = DEFAULT_SANDBOX_NETWORK_LOCATION

    def build_code_to_execute(self, epanet_network: str, func_code: str, eval_script: Optional[str]) -> str:
        """Builds the complete code block to execute"""
        network_path = epanet_network if not _check_if_external_epanet_inp_file(
            epanet_network) else f"{self.DEFAULT_NETWORK_LOCATION}"
        # Extract only the function definition, remove any trailing calls
        clean_func_code = self._extract_function_definition(func_code)

        try:
            code = (
                "from epyt import epanet\n"
                f"d = epanet('{network_path}', display_msg=False)\n"
                f"{clean_func_code}\n"
                f"return_val = {eval_script}\n"
                "print(f'{return_val}')\n"
            )
            return code
        except Exception as e:
            logger.error(f"Failed to build code block: {str(e)}")
            raise

    def _extract_function_definition(self, func_code: str) -> str:
        """Extract only the function definition, removing any trailing calls or prints."""
        lines = func_code.strip().split('\n')
        result_lines = []
        in_function = False
        function_indent = 0

        for line in lines:
            stripped = line.lstrip()
            current_indent = len(line) - len(stripped)

            if stripped.startswith('def '):
                in_function = True
                function_indent = current_indent
                result_lines.append(line)
            elif in_function:
                # Check if we're still inside the function (indented) or have exited
                if stripped == '' or current_indent > function_indent:
                    result_lines.append(line)
                elif stripped.startswith('#'):
                    result_lines.append(line)
                else:
                    break

        return '\n'.join(result_lines)

    def execute_code(self, code_to_execute: str, fast_mode: bool = False, **kwargs) -> Tuple[Optional[str], Optional[str]]:
        """Executes the code and returns (stdout, stderr)"""
        return execute_code_util(code=code_to_execute, fast_mode=fast_mode, timeout=self.timeout, **kwargs)


class EPANETAgent:
    def __init__(self, 
                 retriever: Retriever, 
                 language_model: LanguageModel, 
                 eval_language_model: LanguageModel,
                 review_language_model: LanguageModel = None,
                 num_retries: int = 3,
                 code_exec_fast_mode: bool = False):
        try:
            self.retriever = retriever
            self.language_model = language_model
            self.eval_language_model = eval_language_model
            self.review_language_model = review_language_model
            self.code_executor = CodeExecutor(num_retries=num_retries)
            self.code_exec_fast_mode = code_exec_fast_mode
            logger.info("Successfully initialized EPANETAgent")
        except Exception as e:
            logger.error(f"Failed to initialize EPANETAgent: {str(e)}")
            raise

    def _remove_context_section(self, prompt: str) -> str:
        """Removes the context section from a prompt when k=0 (no RAG).

        Handles various context marker patterns:
        - [CONTEXT_START]...[CONTEXT_END]
        - <CONTEXT_START>...<CONTEXT_END>
        - [CONTEXT]...[/CONTEXT]
        """
        patterns = [
            r'\[CONTEXT_START\].*?\[CONTEXT_END\]',
            r'<CONTEXT_START>.*?<CONTEXT_END>',
            r'\[CONTEXT\].*?\[/CONTEXT\]',
        ]

        result = prompt
        for pattern in patterns:
            result = re.sub(pattern, '', result, flags=re.DOTALL)

        # Clean up multiple consecutive newlines
        result = re.sub(r'\n{3,}', '\n\n', result)

        return result

    def build_prompt(self, prompt: str, task: str, docs: List[Tuple[str, str]] = None) -> str:
        """Builds the prompt for function generation.

        When docs is empty (k=0), the context section is removed from the prompt entirely.
        """
        try:
            if docs:
                context = "\n\n".join(doc[1] for doc in docs)
                return prompt.format(context=context, task=task)
            else:
                # k=0 case: remove context section entirely from prompt
                logger.debug("No docs provided (k=0), removing context section from prompt")
                prompt_without_context = self._remove_context_section(prompt)
                return prompt_without_context.format(task=task)
        except Exception as e:
            logger.error(f"Failed to build prompt: {str(e)}")
            raise
    
    def build_eval_prompt(self, prompt: str, task: str, context: str, args: Dict = None) -> str:
        """Builds the prompt for generating function call"""
        try:
            return prompt.format(task=task, context=context, args=args)
        except Exception as e:
            logger.error(f"Failed to build eval prompt: {str(e)}")
            raise

    def extract_func_name(self, response: str) -> Tuple[str, str]:
        """Extracts function name from generated code"""
        try:
            func_name = response.split("def")[1].split("(")[0].strip()
            return func_name, response.strip()
        except Exception as e:
            logger.error(f"Error extracting function name: {str(e)}")
            logger.error(f"Response: {response}")
            raise ValueError("Could not extract function name")

    def create_function_call(self, query: str, prompt: str, k: int = 10) -> Tuple[str, str, str]:
        """Generates function code using RAG"""
        try:
            # Skip retrieval when k=0 (no RAG context)
            if k > 0:
                logger.debug(f"Retrieving {k} documents for query: {query}")
                docs = self.retriever(query, k=k)
            else:
                logger.debug("Skipping retrieval (k=0), no RAG context will be used")
                docs = []

            prompt = self.build_prompt(prompt, query, docs)
            logger.debug(f"Generated prompt for function creation")

            func_code, usage = self.language_model(prompt)

            func_name, func_code = self.extract_func_name(func_code)
            logger.info(f"Successfully generated function '{func_name}'")
            return func_name, func_code, prompt, usage
        except Exception as e:
            logger.error(f"Failed to create function call: {str(e)}")
            raise

    def review_code(self, task: str, func_code: str, eval_code: str, code_review_prompt: str) -> ReviewResult:
        """Reviews generated code using the review LLM"""
        if not self.review_language_model:
            logger.debug("No review language model available, skipping code review")
            return ReviewResult(
                needs_revision=False,
                revision_type="none",
                function_issues=[],
                eval_issues=[]
            ), None

        try:
            prompt = code_review_prompt.format(
                task=task,
                function_code=func_code,
                eval_code=eval_code,
                review_result_schema=json.dumps(ReviewResult.model_json_schema())
            )

            review_response, usage = self.review_language_model(prompt)
            review_response = review_response.replace('```json', '').replace('```', '').replace('json', '').strip()
            try:
                review_result = ReviewResult.model_validate_json(review_response)
            except Exception as e:
                logger.error(f"Failed to parse review result JSON: {str(e)}")
                logger.error(f"### Review response: \n{review_response}")
                return ReviewResult(), usage
            logger.info(f"Code review completed: {review_result}")
            return review_result, usage
        except Exception as e:
            logger.error(f"Error in code review: {str(e)}")
            return ReviewResult(
                needs_revision=False,
                revision_type="none",
                function_issues=[str(e)],
                eval_issues=[]
            ), None

    def fix_exception(self, state: AgentState, language_model: LanguageModel) -> Tuple[str, str]:
        """Attempts to fix code that raised an exception"""
        try:
            code = '\n'.join([state.func_code, state.eval_script])
            prompt = state.prompts_used[0]  # Original prompt
            error = state.execution_error
            code_fix_prompt = state.code_fix_prompt
            final_prompt = code_fix_prompt.format(code=code, exception=error, context=prompt)
            func_code_to_execute, usage = language_model(final_prompt)
            logger.info("Successfully generated fixed code")
            return func_code_to_execute, final_prompt, usage
        except Exception as e:
            logger.error(f"Failed to fix code exception: {str(e)}")
            logger.error(f"Prompt used: {final_prompt}")
            raise

    def _generate_function(self, state: AgentState) -> AgentState:
        """Action: Generate function code using RAG"""
        logger.info(f"[Action: generate_function] Iteration {state.iteration}")
        state.state_history.append(f"generate_function (iter={state.iteration})")

        # Reset execution attempts for the new function - each function gets fresh retries
        state.execution_attempts = 0

        try:
            query = state.query
            if state.args:
                query = query.format(**state.args)
                logger.debug(f"Formatted query with args: {query}")

            func_name, func_code, prompt, usage = self.create_function_call(query, state.prompt, k=state.k)
            state.func_name = func_name
            state.func_code = func_code
            logger.info(f'{state.usage_tokens=} {state.usage_price=} {usage.total_tokens=} {usage.cost=}')
            state.usage_tokens += usage.total_tokens if usage else 0
            state.usage_price += usage.cost if usage else 0
            state.prompts_used.append(prompt)

            # Determine next action
            if state.exec_script:
                state.next_action = "generate_eval"
            else:
                state.next_action = "done"

            logger.info(f"Generated function '{func_name}', next action: {state.next_action}")
            return state
        except Exception as e:
            logger.error(f"Failed in _generate_function: {str(e)}")
            state.next_action = "done"
            return state

    def build_eval_script_programmatic(self, func_name: str, args: Dict) -> str:
        """
        Build eval script programmatically without LLM.
        This ensures the function name is always correct.

        Args:
            func_name: The extracted function name from generated code
            args: Dictionary of argument names to values

        Returns:
            A one-liner like: func_name(d, arg1, arg2, ...)
        """
        if not args:
            return f"{func_name}(d)"

        # Format each argument value appropriately
        formatted_args = []
        for key, value in args.items():
            if isinstance(value, str):
                # String values need quotes
                formatted_args.append(f"'{value}'")
            elif isinstance(value, bool):
                # Python booleans: True/False
                formatted_args.append(str(value))
            elif isinstance(value, (int, float)):
                # Numeric values as-is
                formatted_args.append(str(value))
            else:
                # Fallback: repr for safety
                formatted_args.append(repr(value))

        args_str = ", ".join(formatted_args)
        return f"{func_name}(d, {args_str})"

    def _generate_eval(self, state: AgentState) -> AgentState:
        """Action: Generate evaluation script"""
        logger.info(f"[Action: generate_eval] Iteration {state.iteration}")
        state.state_history.append(f"generate_eval (iter={state.iteration})")

        try:
            # ROBUST APPROACH: Build eval script programmatically
            # This guarantees the correct function name is used
            eval_script = self.build_eval_script_programmatic(state.func_name, state.args)

            logger.info(f"Built evaluation script programmatically: {eval_script}")
            state.eval_script = eval_script

            # No LLM usage for this step anymore
            # (Remove or keep token tracking as needed)

            # Determine next action
            if state.code_review_prompt and self.review_language_model:
                state.next_action = "review"
            else:
                state.next_action = "execute"

            logger.info(f"Generated eval script, next action: {state.next_action}")
            return state
        except Exception as e:
            logger.error(f"Failed in _generate_eval: {str(e)}")
            # Fallback to LLM-based generation if programmatic fails
            try:
                logger.warning("Falling back to LLM-based eval script generation")
                eval_script, usage = self.eval_language_model(
                    self.build_eval_prompt(state.code_exec_prompt, state.query, state.func_code, state.args)
                )
                # Validate that the function name appears in the eval script
                if state.func_name not in eval_script:
                    logger.warning(f"LLM eval script doesn't contain '{state.func_name}', attempting fix")
                    # Try to fix by replacing any function call pattern with correct name
                    import re
                    eval_script = re.sub(r'^(\w+)\(', f'{state.func_name}(', eval_script.strip())

                state.eval_script = eval_script.strip().strip('`')
                state.usage_tokens += usage.total_tokens if usage else 0
                state.usage_price += usage.cost if usage else 0

                if state.code_review_prompt and self.review_language_model:
                    state.next_action = "review"
                else:
                    state.next_action = "execute"
                return state
            except Exception as e2:
                logger.error(f"Fallback also failed in _generate_eval: {str(e2)}")
                state.next_action = "done"
                return state

    def _review_code(self, state: AgentState) -> AgentState:
        """Action: Review generated code"""
        logger.info(f"[Action: review] Iteration {state.iteration}")
        state.state_history.append(f"review (iter={state.iteration})")

        try:
            review_result, usage = self.review_code(
                state.query,
                state.func_code,
                state.eval_script,
                state.code_review_prompt
            )
            state.usage_tokens += usage.total_tokens if usage else 0
            state.usage_price += usage.cost if usage else 0
            state.review_result = review_result
            logger.info(f"Code review result: {review_result}")

            # Determine next action based on review
            if review_result.needs_revision:
                if review_result.revision_type in ["function", "both"]:
                    logger.info("Review flagged function code issues, regenerating function")
                    state.next_action = "generate_function"
                elif review_result.revision_type == "eval":
                    logger.info("Review flagged eval code issues, regenerating eval")
                    state.next_action = "generate_eval"
                else:
                    state.next_action = "execute"
            else:
                state.next_action = "execute"

            logger.info(f"Review complete, next action: {state.next_action}")
            return state
        except Exception as e:
            logger.error(f"Failed in _review_code: {str(e)}")
            state.next_action = "execute"
            return state

    def _execute_code(self, state: AgentState) -> AgentState:
        """Action: Execute the generated code"""
        logger.info(f"[Action: execute] Iteration {state.iteration}, Attempt {state.execution_attempts + 1}/{state.max_execution_attempts}")
        state.state_history.append(f"execute (iter={state.iteration}, attempt={state.execution_attempts + 1})")

        try:
            # Build code to execute
            code_to_execute = self.code_executor.build_code_to_execute(
                state.epanet_network,
                state.func_code,
                state.eval_script
            )
            state.code_to_execute = code_to_execute

            # Execute
            start_time = datetime.now()
            query_result, error = self.code_executor.execute_code(code_to_execute, 
                                                                  epanet_network=state.epanet_network, 
                                                                  fast_mode=self.code_exec_fast_mode)
            end_time = datetime.now()
            state.execution_time = (end_time - start_time).total_seconds()
            state.execution_attempts += 1

            if query_result is not None and query_result.strip() != "":
                # Execution successful
                state.query_result = query_result
                state.execution_successful = True
                state.next_action = "done"
                logger.info(f"Code executed successfully with result: {query_result}")
            else:
                # Execution failed
                error = error[:5000] if error and len(error) > 5000 else error
                logger.error(f"Execution failed with error: {error}")
                state.execution_error = error

                # Check if we should retry
                if state.execution_attempts < state.max_execution_attempts:
                    state.next_action = "fix"
                    logger.info("Will attempt to fix code")
                else:
                    state.next_action = "done"
                    logger.warning("Max execution attempts reached, giving up")

            return state
        except Exception as e:
            logger.error(f"Failed in _execute_code: {str(e)}")
            logger.error(f'Code to execute:\n{state.code_to_execute}')
            state.execution_error = str(e)
            state.next_action = "done"
            return state

    def _fix_code(self, state: AgentState) -> AgentState:
        """Action: Fix code after execution error"""
        logger.info(f"[Action: fix] Iteration {state.iteration}")
        state.state_history.append(f"fix (iter={state.iteration})")

        try:
            func_code, fixed_prompt, usage = self.fix_exception(state, self.language_model)
            state.func_code = func_code
            state.prompts_used.append(fixed_prompt)
            state.usage_tokens += usage.total_tokens if usage else 0
            state.usage_price += usage.cost if usage else 0
            logger.info("Successfully generated fixed code")

            # Determine next action - go directly to execute to preserve error context
            # (reviewing after fix can trigger regeneration which loses the error context)
            state.next_action = "execute"
            logger.info("Will execute fixed code")

            return state
        except Exception as e:
            logger.error(f"Failed to fix code: {str(e)}")
            # If fixing fails, try executing again anyway
            state.next_action = "execute"
            return state

    def __call__(self,
                 query: str,
                 prompt: str,
                 k: int = 10,
                 args: Dict = None,
                 exec_script: bool = False,
                 code_exec_prompt: str = None,
                 code_fix_prompt: str = None,
                 code_review_prompt: str = None,
                 epanet_network: str = 'Net1.inp') -> EPANETAgentResult:
        """
        Execute the RAG pipeline using a LangGraph-like agentic loop.

        The agent transitions through states:
        generate_function -> generate_eval -> review -> execute -> fix -> done
        """

        logger.info(f"Starting RAG pipeline for query: {query}")

        start_time = datetime.now()

        try:
            # Initialize state
            state = AgentState(
                query=query,
                epanet_network=epanet_network,
                prompt=prompt,
                k=k,
                args=args,
                exec_script=exec_script,
                code_exec_prompt=code_exec_prompt,
                code_fix_prompt=code_fix_prompt,
                code_review_prompt=code_review_prompt,
                max_execution_attempts=self.code_executor.num_retries,
                usage_tokens=0,
                usage_price=0.0
            )

            # Agentic loop - single while loop for all logic
            while state.iteration < state.max_iterations and state.next_action != "done":
                logger.info(f"ITERATION {state.iteration + 1}/{state.max_iterations} | Next action: {state.next_action}")

                # State machine: dispatch to appropriate action
                if state.next_action == "generate_function":
                    state = self._generate_function(state)
                elif state.next_action == "generate_eval":
                    state = self._generate_eval(state)
                elif state.next_action == "review":
                    state = self._review_code(state)
                elif state.next_action == "execute":
                    state = self._execute_code(state)
                elif state.next_action == "fix":
                    state = self._fix_code(state)
                else:
                    logger.warning(f"Unknown action: {state.next_action}, terminating")
                    break

                state.iteration += 1

            # Check if we hit max iterations
            if state.iteration >= state.max_iterations and state.next_action != "done":
                logger.warning(f"Reached max iterations ({state.max_iterations}) without completion")

            end_time = datetime.now()
            total_time = (end_time - start_time)
            logger.info(f"Total RAG pipeline time: {total_time.total_seconds():.2f} seconds")

            result = EPANETAgentResult(
                func_name=state.func_name or "unknown",
                func_code=state.func_code or "",
                eval_script=state.eval_script,
                prompts_used=state.prompts_used,
                code_to_execute=state.code_to_execute,
                query_result=state.query_result,
                execution_error=state.execution_error,
                execution_successful=state.execution_successful,
                attempt=state.execution_attempts,
                execution_time=state.execution_time,
                query_time=total_time.total_seconds(),
                usage_tokens=state.usage_tokens,
                cost=state.usage_price
            )

            logger.info(f"RAG pipeline completed. Success: {result.execution_successful}")
            logger.info(f'Result: {result.model_dump()}')
            return result

        except Exception as e:
            logger.error(f"Unexpected error in RAG pipeline: {str(e)}")
            raise
