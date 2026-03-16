"""
Prompts API routes.

Implements: prompt template listing, viewing, and editing.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .schemas import ResponseEnvelope

router = APIRouter(tags=["prompts"])

# Prompts directory
PROMPTS_DIR = Path("src/prompts")

# Supported task types and strategies
TASK_TYPES = ["text_exam", "text_qa", "image_mcq", "api_calling"]
STRATEGIES = ["direct", "cot", "long_cot", "tot", "react", "self_refine", "self_consistency"]


# =========================================================================
# Schemas
# =========================================================================

class PromptInfo(BaseModel):
    """Basic info about a prompt template."""
    task_type: str
    strategy: str
    file_path: str
    exists: bool = True


class PromptListResponse(BaseModel):
    """Response for listing all prompts."""
    prompts: List[PromptInfo] = Field(default_factory=list)
    task_types: List[str] = Field(default_factory=list)
    strategies: List[str] = Field(default_factory=list)


class PromptContent(BaseModel):
    """Full prompt template content."""
    task_type: str
    strategy: str
    file_path: str
    content: str
    variables: List[str] = Field(default_factory=list, description="Detected template variables like {problem}")


class PromptUpdateRequest(BaseModel):
    """Request to update a prompt template."""
    content: str = Field(..., description="New YAML content for the prompt template")


# =========================================================================
# Helpers
# =========================================================================

def _get_prompt_path(task_type: str, strategy: str) -> Path:
    """Get the path to a prompt template file."""
    return PROMPTS_DIR / task_type / f"{strategy}.yaml"


def _extract_variables(content: str) -> List[str]:
    """Extract template variables like {problem}, {thoughts} from content."""
    import re
    # Match {variable_name} patterns, excluding {{ escaped braces
    pattern = r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
    matches = re.findall(pattern, content)
    # Return unique variables in order of first appearance
    seen = set()
    result = []
    for var in matches:
        if var not in seen:
            seen.add(var)
            result.append(var)
    return result


def _load_prompt_content(task_type: str, strategy: str) -> Optional[str]:
    """Load prompt template content from file."""
    path = _get_prompt_path(task_type, strategy)
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return None


def _save_prompt_content(task_type: str, strategy: str, content: str) -> bool:
    """Save prompt template content to file."""
    path = _get_prompt_path(task_type, strategy)
    try:
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return True
    except Exception:
        return False


# =========================================================================
# Endpoints
# =========================================================================

@router.get(
    "",
    response_model=ResponseEnvelope[PromptListResponse],
    summary="List all prompt templates",
)
async def list_prompts():
    """
    List all available prompt templates organized by task type and strategy.
    """
    prompts = []
    
    for task_type in TASK_TYPES:
        task_dir = PROMPTS_DIR / task_type
        if not task_dir.exists():
            continue
        
        for yaml_file in task_dir.glob("*.yaml"):
            strategy = yaml_file.stem
            prompts.append(PromptInfo(
                task_type=task_type,
                strategy=strategy,
                file_path=str(yaml_file),
                exists=True,
            ))
    
    # Sort by task_type then strategy
    prompts.sort(key=lambda p: (p.task_type, p.strategy))
    
    return ResponseEnvelope(
        data=PromptListResponse(
            prompts=prompts,
            task_types=TASK_TYPES,
            strategies=STRATEGIES,
        )
    )


@router.get(
    "/{task_type}/{strategy}",
    response_model=ResponseEnvelope[PromptContent],
    summary="Get prompt template content",
)
async def get_prompt(task_type: str, strategy: str):
    """
    Get the full content of a prompt template.
    """
    if task_type not in TASK_TYPES:
        raise HTTPException(status_code=404, detail=f"Unknown task type: {task_type}")
    
    content = _load_prompt_content(task_type, strategy)
    if content is None:
        raise HTTPException(
            status_code=404,
            detail=f"Prompt template not found: {task_type}/{strategy}.yaml"
        )
    
    path = _get_prompt_path(task_type, strategy)
    variables = _extract_variables(content)
    
    return ResponseEnvelope(
        data=PromptContent(
            task_type=task_type,
            strategy=strategy,
            file_path=str(path),
            content=content,
            variables=variables,
        )
    )


@router.put(
    "/{task_type}/{strategy}",
    response_model=ResponseEnvelope[Dict[str, Any]],
    summary="Update prompt template content",
)
async def update_prompt(task_type: str, strategy: str, req: PromptUpdateRequest):
    """
    Update the content of a prompt template.
    
    The content should be valid YAML format.
    """
    if task_type not in TASK_TYPES:
        raise HTTPException(status_code=400, detail=f"Unknown task type: {task_type}")
    
    # Validate YAML syntax
    try:
        yaml.safe_load(req.content)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML syntax: {str(e)}")
    
    # Save the content
    if not _save_prompt_content(task_type, strategy, req.content):
        raise HTTPException(status_code=500, detail="Failed to save prompt template")
    
    variables = _extract_variables(req.content)
    
    return ResponseEnvelope(
        data={
            "task_type": task_type,
            "strategy": strategy,
            "status": "saved",
            "variables": variables,
        }
    )


@router.post(
    "/{task_type}/{strategy}/validate",
    response_model=ResponseEnvelope[Dict[str, Any]],
    summary="Validate prompt template syntax",
)
async def validate_prompt(task_type: str, strategy: str, req: PromptUpdateRequest):
    """
    Validate prompt template YAML syntax without saving.
    """
    errors = []
    warnings = []
    
    # Check YAML syntax
    try:
        data = yaml.safe_load(req.content)
    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML syntax: {str(e)}")
        return ResponseEnvelope(
            data={
                "valid": False,
                "errors": errors,
                "warnings": warnings,
                "variables": [],
            }
        )
    
    # Check required fields based on strategy
    if data is None:
        errors.append("Empty YAML content")
    elif isinstance(data, dict):
        # Check for common template keys
        expected_keys = ["system_prompt", "user_prompt"]
        if strategy in ["cot", "long_cot"]:
            expected_keys.append("cot_instruction")
        
        for key in expected_keys:
            if key not in data:
                warnings.append(f"Missing recommended key: {key}")
    
    variables = _extract_variables(req.content)
    
    return ResponseEnvelope(
        data={
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "variables": variables,
        }
    )
