# Multi-Step Agentic Orchestrator for V.A.U.L.T.
# Plan-and-Execute architecture optimized for 6GB VRAM (RTX 3050)
import json
import re
import traceback
from typing import Dict, Any, List, Optional, Generator

from app.core.ollama_client import ollama_client
from app.core.model_router import (
    model_router, MODEL_ORCHESTRATOR, MODEL_CODER, MODEL_VISION
)
from app.agents.prompt_templates import (
    ORCHESTRATOR_SYSTEM_PROMPT,
    SYNTHESIZER_SYSTEM_PROMPT,
    CODE_GENERATION_PROMPT,
    DOCUMENT_DRAFTING_PROMPT,
)
from app.tools.local_search import search_knowledge_base, format_context_for_llm
from app.tools.code_sandbox import execute_code
from app.tools.doc_generator import create_approval_note, create_calculation_sheet
from app.tools.vision_ocr import analyze_image_b64

MAX_PLAN_STEPS = 5


# ──────────────────────────────────────────────
#  JSON Extraction Helper
# ──────────────────────────────────────────────

def _extract_json(text: str) -> Optional[Dict]:
    """
    Robustly extract a JSON object from LLM output.
    Handles markdown fences, leading prose, and common malformations.
    """
    # Try direct parse first
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown code fences
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fenced:
        try:
            return json.loads(fenced.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Find the first { ... } block
    brace_match = re.search(r"\{[\s\S]*\}", text)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


# ──────────────────────────────────────────────
#  Tool Dispatch Functions
# ──────────────────────────────────────────────

def _tool_rag_search(tool_input: str, **kwargs) -> Dict[str, Any]:
    """Search the local SOP / manual knowledge base."""
    results = search_knowledge_base(query=tool_input, n_results=3)
    context_text = format_context_for_llm(results)
    return {
        "tool": "rag_search",
        "success": True,
        "result": context_text,
        "num_results": len(results)
    }


def _tool_code_execute(tool_input: str, **kwargs) -> Dict[str, Any]:
    """
    Generate code with the coder model, then execute in sandbox.
    If tool_input looks like raw Python, skip generation.
    """
    code = tool_input

    # If the input is a natural-language description, generate code first
    if not _looks_like_code(tool_input):
        model_router.switch_model_if_needed(MODEL_CODER)
        response = ollama_client.generate(
            model=MODEL_CODER,
            prompt=tool_input,
            system_prompt=CODE_GENERATION_PROMPT,
            stream=False,
            temperature=0.1
        )
        raw = response.get("response", "")
        code = _extract_code_block(raw)

    # Execute in Docker sandbox
    sandbox_result = execute_code(code, timeout=30)

    return {
        "tool": "code_execute",
        "success": sandbox_result["exit_code"] == 0,
        "code": code,
        "stdout": sandbox_result["stdout"],
        "stderr": sandbox_result["stderr"],
        "timed_out": sandbox_result["timed_out"],
        "result": sandbox_result["stdout"] if sandbox_result["exit_code"] == 0
                  else f"Error: {sandbox_result['stderr']}"
    }


def _tool_doc_generate(tool_input: str, **kwargs) -> Dict[str, Any]:
    """Generate an industrial document (Approval Note or Calc Sheet)."""
    # Parse tool_input as JSON if possible
    doc_spec = _extract_json(tool_input) if isinstance(tool_input, str) else tool_input
    if not doc_spec or not isinstance(doc_spec, dict):
        doc_spec = {"type": "approval_note", "title": "Generated Document", "content": tool_input}

    doc_type = doc_spec.get("type", "approval_note")
    title = doc_spec.get("title", "Untitled Document")

    # If content is missing or thin, draft it with the orchestrator model
    content = doc_spec.get("content", "")
    if not content or len(content) < 50:
        model_router.switch_model_if_needed(MODEL_ORCHESTRATOR)
        draft_prompt = f"Draft content for an industrial {doc_type} titled: '{title}'"
        if content:
            draft_prompt += f"\nContext/data to include:\n{content}"
        # Include any prior step results passed through kwargs
        step_results = kwargs.get("prior_results", [])
        if step_results:
            context_parts = []
            for sr in step_results:
                context_parts.append(f"[{sr.get('tool', 'unknown')}]: {sr.get('result', '')}")
            draft_prompt += "\n\nPrevious analysis results to incorporate:\n" + "\n".join(context_parts)

        response = ollama_client.generate(
            model=MODEL_ORCHESTRATOR,
            prompt=draft_prompt,
            system_prompt=DOCUMENT_DRAFTING_PROMPT,
            stream=False,
            temperature=0.3
        )
        content = response.get("response", content)

    if doc_type == "calc_sheet":
        data = doc_spec.get("data", {"Result": content})
        filepath = create_calculation_sheet(title=title, data=data, notes=content)
    else:
        filepath = create_approval_note(title=title, content=content)

    return {
        "tool": "doc_generate",
        "success": True,
        "doc_type": doc_type,
        "filepath": filepath,
        "result": f"Document generated: {filepath}"
    }


def _tool_vision_analyze(tool_input: str, images: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
    """Analyze attached images with the vision model."""
    if not images:
        return {
            "tool": "vision_analyze",
            "success": False,
            "result": "No images were provided for vision analysis."
        }

    # Analyze the first image (VRAM swap handled inside analyze_image_b64)
    analysis = analyze_image_b64(images[0], custom_prompt=tool_input)
    return {
        "tool": "vision_analyze",
        "success": True,
        "result": analysis
    }


def _tool_direct_answer(tool_input: str, **kwargs) -> Dict[str, Any]:
    """Use the orchestrator model for a direct text answer."""
    model_router.switch_model_if_needed(MODEL_ORCHESTRATOR)

    # Enrich with RAG context if available
    rag_results = search_knowledge_base(query=tool_input, n_results=2)
    context = format_context_for_llm(rag_results)

    prompt = tool_input
    if rag_results:
        prompt = f"Context from knowledge base:\n{context}\n\nQuestion: {tool_input}"

    response = ollama_client.generate(
        model=MODEL_ORCHESTRATOR,
        prompt=prompt,
        stream=False,
        temperature=0.3
    )
    return {
        "tool": "direct_answer",
        "success": True,
        "result": response.get("response", "")
    }


# Tool registry
TOOL_DISPATCH = {
    "rag_search": _tool_rag_search,
    "code_execute": _tool_code_execute,
    "doc_generate": _tool_doc_generate,
    "vision_analyze": _tool_vision_analyze,
    "direct_answer": _tool_direct_answer,
}


# ──────────────────────────────────────────────
#  Helper Utilities
# ──────────────────────────────────────────────

def _looks_like_code(text: str) -> bool:
    """Heuristic: does this string look like Python code?"""
    code_indicators = ["import ", "def ", "print(", "for ", "while ", "if __name__", "=", "class "]
    lines = text.strip().split("\n")
    matches = sum(1 for line in lines if any(kw in line for kw in code_indicators))
    return matches >= 2 or (len(lines) == 1 and any(kw in text for kw in ["print(", "import "]))


def _extract_code_block(text: str) -> str:
    """Extract Python code from an LLM response that may include markdown fences."""
    fenced = re.search(r"```(?:python)?\s*([\s\S]*?)```", text)
    if fenced:
        return fenced.group(1).strip()
    return text.strip()


# ──────────────────────────────────────────────
#  The Orchestrator
# ──────────────────────────────────────────────

class Orchestrator:
    """
    Plan-and-Execute agentic pipeline for V.A.U.L.T.

    Phase 1 — PLAN:   llama3.1:8b decomposes the prompt into tool steps.
    Phase 2 — EXECUTE: Dispatcher runs each tool with VRAM-safe swapping.
    Phase 3 — SYNTHESIZE: llama3.1:8b compiles results into a final answer.
    """

    def run(
        self,
        prompt: str,
        images: Optional[List[str]] = None,
        file_types: Optional[List[str]] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Main entry point. Processes a complex prompt end-to-end.

        Args:
            prompt: The user's natural language request.
            images: Optional list of base64-encoded image strings.
            file_types: Optional list of file extensions involved.
            stream: If True, returns a streaming generator (future use).

        Returns:
            {
                "response": str,          # Final synthesized answer
                "plan": dict,             # The execution plan
                "step_results": list,     # Results from each tool step
                "documents": list,        # Paths to any generated docs
                "model": str              # Final model used
            }
        """
        step_results = []
        generated_docs = []

        # ── Phase 1: PLAN ──────────────────────────
        print("[ORCHESTRATOR] Phase 1: Planning...")
        plan = self._create_plan(prompt, has_images=bool(images))

        if plan is None:
            # Planning failed — fall back to direct answer
            print("[ORCHESTRATOR] Plan generation failed, falling back to direct answer.")
            result = _tool_direct_answer(prompt)
            return {
                "response": result["result"],
                "plan": {"analysis": "Direct answer (planning failed)", "steps": []},
                "step_results": [result],
                "documents": [],
                "model": MODEL_ORCHESTRATOR
            }

        steps = plan.get("steps", [])
        if not steps:
            result = _tool_direct_answer(prompt)
            return {
                "response": result["result"],
                "plan": plan,
                "step_results": [result],
                "documents": [],
                "model": MODEL_ORCHESTRATOR
            }

        # ── Phase 2: EXECUTE ───────────────────────
        print(f"[ORCHESTRATOR] Phase 2: Executing {len(steps)} steps...")
        for step in steps[:MAX_PLAN_STEPS]:
            step_num = step.get("step", "?")
            tool_name = step.get("tool", "direct_answer")
            tool_input = step.get("input", prompt)

            print(f"  [STEP {step_num}] Tool: {tool_name}")

            dispatch_fn = TOOL_DISPATCH.get(tool_name)
            if dispatch_fn is None:
                step_results.append({
                    "tool": tool_name,
                    "success": False,
                    "result": f"Unknown tool: {tool_name}"
                })
                continue

            try:
                result = dispatch_fn(
                    tool_input,
                    images=images,
                    prior_results=step_results
                )
                step_results.append(result)
                print(f"  [STEP {step_num}] {'OK' if result.get('success') else 'FAILED'}")

                # Collect document paths
                if result.get("filepath"):
                    generated_docs.append(result["filepath"])

            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                print(f"  [STEP {step_num}] ERROR: {error_msg}")
                step_results.append({
                    "tool": tool_name,
                    "success": False,
                    "result": f"Tool error: {error_msg}"
                })

        # ── Phase 3: SYNTHESIZE ────────────────────
        print("[ORCHESTRATOR] Phase 3: Synthesizing final response...")
        final_response = self._synthesize(prompt, plan, step_results)

        # Append document references
        if generated_docs:
            doc_list = "\n".join(f"- {path}" for path in generated_docs)
            final_response += f"\n\n**Generated Documents:**\n{doc_list}"

        return {
            "response": final_response,
            "plan": plan,
            "step_results": step_results,
            "documents": generated_docs,
            "model": MODEL_ORCHESTRATOR
        }

    def run_stream(
        self,
        prompt: str,
        images: Optional[List[str]] = None,
        file_types: Optional[List[str]] = None
    ) -> Generator[str, None, None]:
        """
        Streaming variant that yields status updates and tokens formatted for Server-Sent Events (SSE).
        """
        yield f"data: {json.dumps({'status': 'Phase 1: Planning multi-step industrial workflow...'})}\n\n"

        plan = self._create_plan(prompt, has_images=bool(images))
        if plan is None or not plan.get("steps"):
            yield f"data: {json.dumps({'status': 'Direct response mode'})}\n\n"
            result = _tool_direct_answer(prompt)
            for char in result.get("result", ""):
                yield f"data: {json.dumps({'token': char})}\n\n"
            return

        steps = plan.get("steps", [])
        step_results = []

        for step in steps[:MAX_PLAN_STEPS]:
            tool_name = step.get("tool", "direct_answer")
            tool_input = step.get("input", prompt)
            reason = step.get("reason", "Processing step")
            yield f"data: {json.dumps({'status': f'Phase 2 [{tool_name}]: {reason}'})}\n\n"

            dispatch_fn = TOOL_DISPATCH.get(tool_name, _tool_direct_answer)
            try:
                result = dispatch_fn(tool_input, images=images, prior_results=step_results)
                step_results.append(result)
                if result.get("filepath"):
                    yield f"data: {json.dumps({'file_generated': result['filepath']})}\n\n"
            except Exception as e:
                step_results.append({
                    "tool": tool_name,
                    "success": False,
                    "result": str(e)
                })

        yield f"data: {json.dumps({'status': 'Phase 3: Synthesizing final technical report...'})}\n\n"
        final = self._synthesize(prompt, plan, step_results)
        
        # Yield final answer tokens
        for char in final:
            yield f"data: {json.dumps({'token': char})}\n\n"


    # ──────────────────────────────────────────
    #  Internal Methods
    # ──────────────────────────────────────────

    def _create_plan(self, prompt: str, has_images: bool = False) -> Optional[Dict]:
        """Ask the orchestrator LLM to decompose the prompt into a tool plan."""
        model_router.switch_model_if_needed(MODEL_ORCHESTRATOR)

        planning_prompt = f"User request: {prompt}"
        if has_images:
            planning_prompt += "\n\nNote: The user has attached image(s) for analysis."

        response = ollama_client.generate(
            model=MODEL_ORCHESTRATOR,
            prompt=planning_prompt,
            system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
            stream=False,
            temperature=0.1,
            format="json"
        )

        raw_plan = response.get("response", "")
        print(f"[ORCHESTRATOR] Raw plan output:\n{raw_plan[:500]}")

        plan = _extract_json(raw_plan)
        if plan and "steps" in plan:
            # Validate: override if the LLM chose the wrong tool
            plan = self._validate_plan(plan, prompt, has_images)
            return plan

        # Smart fallback: detect intent from keywords instead of always using direct_answer
        print("[ORCHESTRATOR] Could not parse plan JSON, using smart fallback plan.")
        fallback_steps = self._build_fallback_steps(prompt, has_images)
        return {
            "analysis": "Could not decompose into structured steps; using keyword-based fallback.",
            "steps": fallback_steps
        }

    def _validate_plan(self, plan: Dict, prompt: str, has_images: bool = False) -> Dict:
        """
        Post-validation: catch cases where the LLM chose direct_answer
        when the user clearly needs a specific tool (doc_generate, code_execute, etc.).
        """
        steps = plan.get("steps", [])
        tools_used = {s.get("tool") for s in steps}
        prompt_lower = prompt.lower()

        # If the only tool is direct_answer, check if a better tool should be used
        if tools_used == {"direct_answer"}:
            doc_keywords = [
                "draft", "approval note", "document", "report", "memo",
                "calculation sheet", "generate", "create doc", "write",
                "formal", "prepare", "download", "docx", "xlsx"
            ]
            calc_keywords = [
                "calculate", "formula", "compute", "barlow", "stress",
                "pressure", "thickness", "burst", "flow rate"
            ]

            needs_doc = any(kw in prompt_lower for kw in doc_keywords)
            needs_calc = any(kw in prompt_lower for kw in calc_keywords)

            if needs_doc or needs_calc:
                print("[ORCHESTRATOR] Plan validation: overriding direct_answer with correct tools.")
                corrected_steps = self._build_fallback_steps(prompt, has_images)
                plan["steps"] = corrected_steps
                plan["analysis"] = plan.get("analysis", "") + " (corrected by plan validator)"

        # If images are attached but no vision_analyze step exists, inject one
        if has_images and "vision_analyze" not in tools_used:
            print("[ORCHESTRATOR] Plan validation: injecting vision_analyze step for attached images.")
            vision_step = {
                "step": 0, "tool": "vision_analyze",
                "input": prompt, "reason": "Image attached by user"
            }
            steps.insert(0, vision_step)
            # Re-number steps
            for i, step in enumerate(steps):
                step["step"] = i + 1
            plan["steps"] = steps

        return plan

    def _build_fallback_steps(self, prompt: str, has_images: bool = False) -> List[Dict]:
        """Build a reasonable execution plan from keywords when JSON planning fails."""
        prompt_lower = prompt.lower()
        steps = []
        step_num = 1

        # Vision analysis if images are attached
        if has_images:
            steps.append({
                "step": step_num, "tool": "vision_analyze",
                "input": prompt, "reason": "User attached image(s)"
            })
            step_num += 1

        # RAG search for SOP/procedure references
        rag_keywords = ["sop", "procedure", "standard", "specification", "policy",
                        "manual", "guideline", "code", "regulation", "is ", "api ", "asme"]
        if any(kw in prompt_lower for kw in rag_keywords):
            steps.append({
                "step": step_num, "tool": "rag_search",
                "input": prompt, "reason": "Reference to standards/SOPs detected"
            })
            step_num += 1

        # Code execution for calculations
        calc_keywords = ["calculate", "formula", "compute", "math", "pressure",
                         "temperature", "flow rate", "barlow", "stress", "thickness",
                         "conversion", "density", "velocity"]
        if any(kw in prompt_lower for kw in calc_keywords):
            steps.append({
                "step": step_num, "tool": "code_execute",
                "input": prompt, "reason": "Calculation/formula detected"
            })
            step_num += 1

        # Document generation
        doc_keywords = ["draft", "approval note", "document", "report", "memo",
                        "calculation sheet", "generate doc", "create doc", "write a",
                        "formal", "prepare"]
        if any(kw in prompt_lower for kw in doc_keywords):
            doc_type = "calc_sheet" if "calculation" in prompt_lower or "calc sheet" in prompt_lower else "approval_note"
            steps.append({
                "step": step_num, "tool": "doc_generate",
                "input": json.dumps({"type": doc_type, "title": prompt[:80], "content": prompt}),
                "reason": "Document generation requested"
            })
            step_num += 1

        # Default: direct answer if nothing else matched
        if not steps:
            steps.append({
                "step": 1, "tool": "direct_answer",
                "input": prompt, "reason": "General query"
            })

        return steps

    def _synthesize(
        self,
        original_prompt: str,
        plan: Dict,
        step_results: List[Dict]
    ) -> str:
        """Compile all tool results into a coherent final answer."""
        model_router.switch_model_if_needed(MODEL_ORCHESTRATOR)

        # Build context from step results
        results_text = []
        for i, result in enumerate(step_results, 1):
            tool = result.get("tool", "unknown")
            success = "SUCCESS" if result.get("success") else "FAILED"
            output = result.get("result", "No output")
            # Truncate very long outputs to stay within context window
            if len(output) > 2000:
                output = output[:2000] + "\n...[truncated]"
            results_text.append(f"Step {i} [{tool}] ({success}):\n{output}")

        synthesis_prompt = (
            f"Original user request: {original_prompt}\n\n"
            f"Plan analysis: {plan.get('analysis', 'N/A')}\n\n"
            f"Execution results:\n" + "\n\n".join(results_text)
        )

        response = ollama_client.generate(
            model=MODEL_ORCHESTRATOR,
            prompt=synthesis_prompt,
            system_prompt=SYNTHESIZER_SYSTEM_PROMPT,
            stream=False,
            temperature=0.3
        )

        return response.get("response", "Unable to synthesize a response from tool results.")


# Singleton
orchestrator = Orchestrator()
