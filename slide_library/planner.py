"""
Slide Library Planner Agent

LLM-based agent that generates presentation plans from user requirements.
"""

import logging
from typing import Optional
import sys
from pathlib import Path

from .config import vertexai_model
from .schemas import PresentationPlan, SlideOutlineItem
from .prompts import (
    PRESENTATION_PLANNER_SYSTEM_PROMPT,
    PRESENTATION_PLANNER_USER_PROMPT,
    PRESENTATION_PLANNER_SCHEMA
)

logger = logging.getLogger(__name__)


class SlidePlannerAgent:
    """
    LLM-based agent for generating presentation plans.
    
    Takes user context and prompt, generates a structured plan with:
    - Overall theme
    - Target audience
    - Ordered list of slide specifications
    """
    
    def __init__(self):
        """Initialize planner agent."""
        print("SlidePlannerAgent initialized")
    
    async def generate_plan(
        self,
        user_context: str,
        user_prompt: str,
        num_slides: Optional[int] = None
    ) -> PresentationPlan:
        """
        Generate a presentation plan from user input.
        
        Args:
            user_context: Background context/documents
            user_prompt: User's presentation request
            num_slides: Optional desired number of slides
            
        Returns:
            PresentationPlan with structured outline
        """
        print(f"Generating presentation plan (num_slides: {num_slides})")
        
        user_full_prompt = PRESENTATION_PLANNER_USER_PROMPT(
            user_context=user_context,
            user_prompt=user_prompt,
            num_slides=num_slides
        )

        try:
            # Generate plan with structured output
            response = await vertexai_model(
                system=PRESENTATION_PLANNER_SYSTEM_PROMPT,
                user=user_full_prompt,
                temperature=0.7,
                schema=PRESENTATION_PLANNER_SCHEMA
            )
            
            # Parse response
            import json
            plan_dict = json.loads(response)
            
            # Convert to PresentationPlan
            plan = PresentationPlan(
                overall_theme=plan_dict["overall_theme"],
                target_audience=plan_dict["target_audience"],
                slides=[
                    SlideOutlineItem(**slide)
                    for slide in plan_dict["slides"]
                ]
            )
            
            print(f"Generated plan: {len(plan.slides)} slides")
            print(f"Theme: {plan.overall_theme}")
            
            return plan
            
        except Exception as e:
            print(f"Plan generation failed: {e}")
            raise
