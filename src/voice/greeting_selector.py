"""
Greeting Selector Module - Story 3.4 (Voice Enhancement)

Provides intelligent greeting selection with rich variation, context awareness,
and non-repetition tracking for natural, engaging interactions.

Features:
- 15+ templates for recognized persons
- 12+ templates for unknown persons  
- 8+ templates for departed persons
- Context-aware selection (time of day, personality, history)
- Non-repetition tracking (avoids last 5 greetings)
- Prosody hints for natural voice expression
"""

import random
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import config (optional - falls back to defaults if not available)
try:
    from ..config import get_config
    _CONFIG_AVAILABLE = True
except ImportError:
    _CONFIG_AVAILABLE = False
    logger.warning("Config not available, using default values")


class GreetingType(Enum):
    """Types of greetings."""
    RECOGNIZED = "recognized"
    UNKNOWN = "unknown"
    DEPARTED = "departed"
    GENERAL = "general"


@dataclass
class GreetingTemplate:
    """
    Rich greeting template with metadata and prosody hints.
    
    Attributes:
        text: Greeting text (may include {name} placeholder)
        personality: Target personality (warm, professional, playful, neutral)
        time_of_day: Applicable times (morning, afternoon, evening, any)
        context_tags: Context markers (first_meeting, repeat_visitor, etc.)
        emotion: Emotional tone (happy, curious, calm, excited)
        prosody: Voice modulation hints (rate, pitch, emphasis)
        duration_estimate: Expected speech duration in seconds
        energy_level: Enthusiasm level (1-5)
    """
    text: str
    personality: str = "warm"
    time_of_day: List[str] = field(default_factory=lambda: ["any"])
    context_tags: List[str] = field(default_factory=list)
    emotion: str = "happy"
    prosody: Dict[str, str] = field(default_factory=lambda: {
        "rate": "medium",
        "pitch": "medium"
    })
    duration_estimate: float = 2.0
    energy_level: int = 3


@dataclass
class GreetingContext:
    """
    Context information for greeting selection.
    
    Attributes:
        time_of_day: Current time period
        session_duration: Seconds since session start
        is_first_greeting: First greeting of session
        interaction_count: Total greetings this session
        room_occupancy: Number of people present
    """
    time_of_day: str = "any"
    session_duration: float = 0.0
    is_first_greeting: bool = True
    interaction_count: int = 0
    room_occupancy: int = 1


class GreetingSelector:
    """
    Intelligent greeting selector with variation and context awareness.
    
    Selects varied, contextually appropriate greetings while avoiding
    repetition and maintaining natural interaction flow.
    """
    
    # Template library for recognized persons (15+ variations)
    RECOGNIZED_TEMPLATES = [
        # Warm & Friendly
        GreetingTemplate(
            text="Welcome back, {name}!",
            personality="warm",
            time_of_day=["any"],
            context_tags=["repeat_visitor"],
            emotion="happy",
            prosody={"rate": "medium", "pitch": "+8%"},
            duration_estimate=1.5,
            energy_level=4
        ),
        GreetingTemplate(
            text="Hi {name}! Good to see you!",
            personality="warm",
            time_of_day=["any"],
            context_tags=["repeat_visitor"],
            emotion="happy",
            prosody={"rate": "medium", "pitch": "+7%"},
            duration_estimate=1.8,
            energy_level=4
        ),
        GreetingTemplate(
            text="Hey {name}, glad you're here!",
            personality="playful",
            time_of_day=["any"],
            context_tags=["repeat_visitor"],
            emotion="excited",
            prosody={"rate": "fast", "pitch": "+12%"},
            duration_estimate=2.0,
            energy_level=5
        ),
        GreetingTemplate(
            text="Oh hi {name}, welcome back!",
            personality="playful",
            time_of_day=["any"],
            context_tags=["repeat_visitor"],
            emotion="happy",
            prosody={"rate": "fast", "pitch": "+8%"},
            duration_estimate=1.8,
            energy_level=4
        ),
        
        # Time-specific
        GreetingTemplate(
            text="Good morning, {name}!",
            personality="warm",
            time_of_day=["morning"],
            context_tags=["repeat_visitor"],
            emotion="happy",
            prosody={"rate": "medium", "pitch": "+5%"},
            duration_estimate=1.5,
            energy_level=3
        ),
        GreetingTemplate(
            text="Good afternoon, {name}!",
            personality="warm",
            time_of_day=["afternoon"],
            context_tags=["repeat_visitor"],
            emotion="happy",
            prosody={"rate": "medium", "pitch": "+5%"},
            duration_estimate=1.5,
            energy_level=3
        ),
        GreetingTemplate(
            text="Good evening, {name}. Welcome back.",
            personality="professional",
            time_of_day=["evening"],
            context_tags=["repeat_visitor"],
            emotion="calm",
            prosody={"rate": "medium", "pitch": "+3%"},
            duration_estimate=2.0,
            energy_level=2
        ),
        
        # Professional
        GreetingTemplate(
            text="Hello {name}, good to see you again.",
            personality="professional",
            time_of_day=["any"],
            context_tags=["repeat_visitor"],
            emotion="calm",
            prosody={"rate": "medium", "pitch": "medium"},
            duration_estimate=1.8,
            energy_level=2
        ),
        GreetingTemplate(
            text="Hello {name}, nice to see you.",
            personality="professional",
            time_of_day=["any"],
            context_tags=["repeat_visitor"],
            emotion="calm",
            prosody={"rate": "medium", "pitch": "medium"},
            duration_estimate=1.5,
            energy_level=2
        ),
        
        # Casual & Friendly
        GreetingTemplate(
            text="Oh hi {name}, how's it going?",
            personality="playful",
            time_of_day=["afternoon", "evening"],
            context_tags=["repeat_visitor"],
            emotion="curious",
            prosody={"rate": "fast", "pitch": "+6%"},
            duration_estimate=2.0,
            energy_level=3
        ),
        GreetingTemplate(
            text="{name}! How have you been?",
            personality="warm",
            time_of_day=["any"],
            context_tags=["repeat_visitor"],
            emotion="curious",
            prosody={"rate": "medium", "pitch": "+5%"},
            duration_estimate=1.8,
            energy_level=3
        ),
        
        # Gentle/Quiet
        GreetingTemplate(
            text="Hello {name}. Nice to see you.",
            personality="neutral",
            time_of_day=["any"],
            context_tags=["repeat_visitor"],
            emotion="calm",
            prosody={"rate": "slow", "pitch": "+2%"},
            duration_estimate=1.5,
            energy_level=2
        ),
        
        # Surprised/Delighted
        GreetingTemplate(
            text="Oh, {name}! What a nice surprise!",
            personality="warm",
            time_of_day=["any"],
            context_tags=["unexpected_visitor"],
            emotion="excited",
            prosody={"rate": "fast", "pitch": "+15%"},
            duration_estimate=2.5,
            energy_level=5
        ),
        
        # Enthusiastic
        GreetingTemplate(
            text="Hey {name}! Great to see you today!",
            personality="playful",
            time_of_day=["any"],
            context_tags=["repeat_visitor"],
            emotion="excited",
            prosody={"rate": "fast", "pitch": "+10%"},
            duration_estimate=2.2,
            energy_level=5
        ),
        
        # Warm welcome
        GreetingTemplate(
            text="Welcome back, {name}. How are you?",
            personality="warm",
            time_of_day=["any"],
            context_tags=["repeat_visitor"],
            emotion="happy",
            prosody={"rate": "medium", "pitch": "+6%"},
            duration_estimate=2.0,
            energy_level=3
        ),
        
        # Simple & sweet
        GreetingTemplate(
            text="Hi {name}!",
            personality="neutral",
            time_of_day=["any"],
            context_tags=["repeat_visitor"],
            emotion="happy",
            prosody={"rate": "medium", "pitch": "+5%"},
            duration_estimate=0.8,
            energy_level=3
        ),
    ]
    
    # Template library for unknown persons (12+ variations)
    UNKNOWN_TEMPLATES = [
        # Friendly introduction
        GreetingTemplate(
            text="Hello there! I'm Reachy. Nice to meet you!",
            personality="warm",
            time_of_day=["any"],
            context_tags=["first_meeting"],
            emotion="happy",
            prosody={"rate": "medium", "pitch": "+8%"},
            duration_estimate=3.0,
            energy_level=4
        ),
        GreetingTemplate(
            text="Hi there! Nice to meet you!",
            personality="warm",
            time_of_day=["any"],
            context_tags=["first_meeting"],
            emotion="happy",
            prosody={"rate": "medium", "pitch": "+7%"},
            duration_estimate=2.0,
            energy_level=4
        ),
        
        # Curious
        GreetingTemplate(
            text="Oh hello! I don't think we've met. What's your name?",
            personality="playful",
            time_of_day=["any"],
            context_tags=["first_meeting"],
            emotion="curious",
            prosody={"rate": "fast", "pitch": "+10%"},
            duration_estimate=3.5,
            energy_level=4
        ),
        GreetingTemplate(
            text="Hi! I don't think we've met yet.",
            personality="warm",
            time_of_day=["any"],
            context_tags=["first_meeting"],
            emotion="curious",
            prosody={"rate": "medium", "pitch": "+5%"},
            duration_estimate=2.2,
            energy_level=3
        ),
        
        # Enthusiastic welcome
        GreetingTemplate(
            text="Hey there, I'm Reachy. Nice to meet you!",
            personality="playful",
            time_of_day=["any"],
            context_tags=["first_meeting"],
            emotion="excited",
            prosody={"rate": "fast", "pitch": "+12%"},
            duration_estimate=3.0,
            energy_level=5
        ),
        GreetingTemplate(
            text="Oh hello! Are you new here?",
            personality="playful",
            time_of_day=["any"],
            context_tags=["first_meeting"],
            emotion="curious",
            prosody={"rate": "fast", "pitch": "+10%"},
            duration_estimate=2.5,
            energy_level=4
        ),
        
        # Professional welcome
        GreetingTemplate(
            text="Good morning. Welcome. I'm Reachy.",
            personality="professional",
            time_of_day=["morning"],
            context_tags=["first_meeting"],
            emotion="calm",
            prosody={"rate": "medium", "pitch": "+2%"},
            duration_estimate=2.5,
            energy_level=2
        ),
        GreetingTemplate(
            text="Hello, welcome.",
            personality="professional",
            time_of_day=["any"],
            context_tags=["first_meeting"],
            emotion="calm",
            prosody={"rate": "medium", "pitch": "medium"},
            duration_estimate=1.5,
            energy_level=2
        ),
        
        # Warm invitation
        GreetingTemplate(
            text="Hi there! I haven't seen you before. Welcome!",
            personality="warm",
            time_of_day=["any"],
            context_tags=["first_meeting"],
            emotion="happy",
            prosody={"rate": "medium", "pitch": "+7%"},
            duration_estimate=3.0,
            energy_level=3
        ),
        
        # Gentle introduction
        GreetingTemplate(
            text="Hello. I'm Reachy. Nice to meet you.",
            personality="neutral",
            time_of_day=["any"],
            context_tags=["first_meeting"],
            emotion="calm",
            prosody={"rate": "slow", "pitch": "+3%"},
            duration_estimate=2.5,
            energy_level=2
        ),
        
        # Afternoon specific
        GreetingTemplate(
            text="Good afternoon! I don't think we've been introduced. I'm Reachy.",
            personality="professional",
            time_of_day=["afternoon"],
            context_tags=["first_meeting"],
            emotion="calm",
            prosody={"rate": "medium", "pitch": "+4%"},
            duration_estimate=3.5,
            energy_level=3
        ),
        
        # Friendly question
        GreetingTemplate(
            text="Oh hi! You're new here, right? Welcome!",
            personality="warm",
            time_of_day=["any"],
            context_tags=["first_meeting"],
            emotion="curious",
            prosody={"rate": "medium", "pitch": "+6%"},
            duration_estimate=2.8,
            energy_level=3
        ),
    ]
    
    # Template library for departures (8+ variations)
    DEPARTED_TEMPLATES = [
        # Warm goodbye
        GreetingTemplate(
            text="Goodbye, {name}! See you soon!",
            personality="warm",
            time_of_day=["any"],
            context_tags=["known_person"],
            emotion="happy",
            prosody={"rate": "medium", "pitch": "+5%"},
            duration_estimate=2.0,
            energy_level=3
        ),
        GreetingTemplate(
            text="Bye {name}! Take care!",
            personality="warm",
            time_of_day=["any"],
            context_tags=["known_person"],
            emotion="happy",
            prosody={"rate": "medium", "pitch": "+6%"},
            duration_estimate=1.8,
            energy_level=3
        ),
        
        # Evening goodbye
        GreetingTemplate(
            text="Have a great evening, {name}!",
            personality="warm",
            time_of_day=["evening"],
            context_tags=["known_person"],
            emotion="happy",
            prosody={"rate": "medium", "pitch": "+4%"},
            duration_estimate=1.8,
            energy_level=2
        ),
        GreetingTemplate(
            text="Good night, {name}!",
            personality="warm",
            time_of_day=["evening"],
            context_tags=["known_person"],
            emotion="calm",
            prosody={"rate": "slow", "pitch": "+3%"},
            duration_estimate=1.5,
            energy_level=2
        ),
        
        # Playful
        GreetingTemplate(
            text="Bye {name}! Come back soon!",
            personality="playful",
            time_of_day=["any"],
            context_tags=["known_person"],
            emotion="happy",
            prosody={"rate": "fast", "pitch": "+8%"},
            duration_estimate=2.2,
            energy_level=4
        ),
        GreetingTemplate(
            text="See you later, {name}!",
            personality="playful",
            time_of_day=["any"],
            context_tags=["known_person"],
            emotion="happy",
            prosody={"rate": "medium", "pitch": "+7%"},
            duration_estimate=1.5,
            energy_level=3
        ),
        
        # Professional
        GreetingTemplate(
            text="Take care, {name}.",
            personality="professional",
            time_of_day=["any"],
            context_tags=["known_person"],
            emotion="calm",
            prosody={"rate": "medium", "pitch": "medium"},
            duration_estimate=1.2,
            energy_level=2
        ),
        GreetingTemplate(
            text="Goodbye, {name}.",
            personality="professional",
            time_of_day=["any"],
            context_tags=["known_person"],
            emotion="calm",
            prosody={"rate": "medium", "pitch": "medium"},
            duration_estimate=1.0,
            energy_level=2
        ),
    ]
    
    def __init__(
        self,
        personality: Optional[str] = None,
        non_repetition_window: Optional[int] = None
    ):
        """
        Initialize greeting selector.
        
        Args:
            personality: Preferred personality (loaded from config if None)
            non_repetition_window: Number of recent greetings to avoid repeating (loaded from config if None)
        """
        # Load from config if available
        if _CONFIG_AVAILABLE and (personality is None or non_repetition_window is None):
            try:
                config = get_config()
                if personality is None:
                    personality = config.greetings.personality
                if non_repetition_window is None:
                    non_repetition_window = config.greetings.repetition_window
                logger.info("✓ Loaded greeting configuration from config")
            except Exception as e:
                logger.warning(f"Failed to load config: {e}, using defaults")
        
        # Set defaults if still None
        if personality is None:
            personality = "warm"
        if non_repetition_window is None:
            non_repetition_window = 5
        
        self.personality = personality
        self.non_repetition_window = non_repetition_window
        
        # Non-repetition tracking
        self.recent_greetings: deque = deque(maxlen=non_repetition_window)
        
        # Per-person greeting history
        self.person_history: Dict[str, List[str]] = {}
        
        # Statistics
        self.total_selections = 0
        self.selections_by_type: Dict[GreetingType, int] = {
            t: 0 for t in GreetingType
        }
        
        logger.info(
            f"GreetingSelector initialized: personality={personality}, "
            f"window={non_repetition_window}"
        )
    
    def select_greeting(
        self,
        person_name: Optional[str] = None,
        greeting_type: GreetingType = GreetingType.UNKNOWN,
        context: Optional[GreetingContext] = None
    ) -> GreetingTemplate:
        """
        Select contextually appropriate greeting with variation.
        
        Selection process:
        1. Get templates for greeting type
        2. Filter by personality preference
        3. Filter by time of day
        4. Remove recently used greetings
        5. Remove greetings used for this person
        6. Random selection from remaining candidates
        
        Args:
            person_name: Name to insert in greeting (for recognized/departed)
            greeting_type: Type of greeting needed
            context: Additional context for selection
            
        Returns:
            Selected greeting template with name filled in
        """
        context = context or GreetingContext()
        
        # Get base templates for type
        templates = self._get_templates_for_type(greeting_type)
        
        if not templates:
            logger.warning(f"No templates for {greeting_type}")
            return self._get_fallback_template(greeting_type, person_name)
        
        # Apply filters
        filtered = self._filter_by_personality(templates)
        filtered = self._filter_by_time(filtered, context.time_of_day)
        filtered = self._filter_by_recent_use(filtered)
        
        if person_name:
            filtered = self._filter_by_person_history(filtered, person_name)
        
        # If all filtered out, reset and use all templates
        if not filtered:
            logger.debug("All templates filtered out, resetting filters")
            filtered = templates
        
        # Random selection
        selected = random.choice(filtered)
        
        # Track usage
        self.recent_greetings.append(selected.text)
        if person_name:
            if person_name not in self.person_history:
                self.person_history[person_name] = []
            self.person_history[person_name].append(selected.text)
        
        # Update statistics
        self.total_selections += 1
        self.selections_by_type[greeting_type] += 1
        
        # Fill in name if provided
        if person_name and "{name}" in selected.text:
            # Create copy with name filled in
            filled_text = selected.text.format(name=person_name)
            selected = GreetingTemplate(
                text=filled_text,
                personality=selected.personality,
                time_of_day=selected.time_of_day,
                context_tags=selected.context_tags,
                emotion=selected.emotion,
                prosody=selected.prosody.copy(),
                duration_estimate=selected.duration_estimate,
                energy_level=selected.energy_level
            )
        
        logger.debug(
            f"Selected: '{selected.text[:50]}...' "
            f"(personality={selected.personality}, emotion={selected.emotion})"
        )
        
        return selected
    
    def _get_templates_for_type(
        self,
        greeting_type: GreetingType
    ) -> List[GreetingTemplate]:
        """Get template list for greeting type."""
        type_map = {
            GreetingType.RECOGNIZED: self.RECOGNIZED_TEMPLATES,
            GreetingType.UNKNOWN: self.UNKNOWN_TEMPLATES,
            GreetingType.DEPARTED: self.DEPARTED_TEMPLATES,
        }
        return type_map.get(greeting_type, [])
    
    def _filter_by_personality(
        self,
        templates: List[GreetingTemplate]
    ) -> List[GreetingTemplate]:
        """Filter templates by personality preference."""
        filtered = [t for t in templates if t.personality == self.personality]
        
        # If no exact matches, return all (allows diversity)
        return filtered if filtered else templates
    
    def _filter_by_time(
        self,
        templates: List[GreetingTemplate],
        time_of_day: str
    ) -> List[GreetingTemplate]:
        """Filter templates by time of day."""
        if time_of_day == "any":
            return templates
        
        filtered = [
            t for t in templates
            if time_of_day in t.time_of_day or "any" in t.time_of_day
        ]
        
        return filtered if filtered else templates
    
    def _filter_by_recent_use(
        self,
        templates: List[GreetingTemplate]
    ) -> List[GreetingTemplate]:
        """Remove recently used greetings."""
        filtered = [
            t for t in templates
            if t.text not in self.recent_greetings
        ]
        
        return filtered if filtered else templates
    
    def _filter_by_person_history(
        self,
        templates: List[GreetingTemplate],
        person_name: str
    ) -> List[GreetingTemplate]:
        """Remove greetings already used for this person."""
        if person_name not in self.person_history:
            return templates
        
        person_used = self.person_history[person_name]
        
        filtered = [
            t for t in templates
            if t.text not in person_used
        ]
        
        return filtered if filtered else templates
    
    def _get_fallback_template(
        self,
        greeting_type: GreetingType,
        person_name: Optional[str]
    ) -> GreetingTemplate:
        """Get emergency fallback greeting."""
        fallbacks = {
            GreetingType.RECOGNIZED: f"Hello {person_name}!",
            GreetingType.UNKNOWN: "Hello there!",
            GreetingType.DEPARTED: f"Goodbye {person_name}!",
        }
        
        text = fallbacks.get(greeting_type, "Hello!")
        
        return GreetingTemplate(
            text=text,
            personality="neutral",
            time_of_day=["any"],
            emotion="calm"
        )
    
    def get_time_of_day(self) -> str:
        """
        Determine current time of day.
        
        Returns:
            'morning' (5am-12pm), 'afternoon' (12pm-5pm), or 'evening' (5pm-5am)
        """
        hour = datetime.now().hour
        
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        else:
            return "evening"
    
    def reset_session(self):
        """Reset greeting history for new session."""
        self.recent_greetings.clear()
        self.person_history.clear()
        logger.info("Greeting session reset")
    
    def get_statistics(self) -> Dict:
        """Get selection statistics."""
        return {
            'total_selections': self.total_selections,
            'by_type': {
                t.value: count
                for t, count in self.selections_by_type.items()
            },
            'unique_people': len(self.person_history),
            'recent_greetings_count': len(self.recent_greetings),
            'personality': self.personality
        }


def main():
    """Test greeting selector."""
    print("\n" + "="*60)
    print("Greeting Selector Test")
    print("="*60)
    
    selector = GreetingSelector(personality="warm")
    
    # Test recognized person greetings
    print("\n--- Recognized Person (10 greetings) ---")
    for i in range(10):
        context = GreetingContext(
            time_of_day=selector.get_time_of_day(),
            is_first_greeting=(i == 0),
            interaction_count=i
        )
        
        template = selector.select_greeting(
            person_name="Sarah",
            greeting_type=GreetingType.RECOGNIZED,
            context=context
        )
        
        print(f"{i+1}. {template.text}")
        print(f"   → emotion={template.emotion}, energy={template.energy_level}")
    
    # Test unknown person greetings
    print("\n--- Unknown Person (5 greetings) ---")
    for i in range(5):
        context = GreetingContext(
            time_of_day=selector.get_time_of_day(),
            is_first_greeting=True
        )
        
        template = selector.select_greeting(
            greeting_type=GreetingType.UNKNOWN,
            context=context
        )
        
        print(f"{i+1}. {template.text}")
        print(f"   → emotion={template.emotion}, energy={template.energy_level}")
    
    # Test departures
    print("\n--- Departures (5 greetings) ---")
    for i in range(5):
        context = GreetingContext(
            time_of_day=selector.get_time_of_day()
        )
        
        template = selector.select_greeting(
            person_name="Sarah",
            greeting_type=GreetingType.DEPARTED,
            context=context
        )
        
        print(f"{i+1}. {template.text}")
        print(f"   → emotion={template.emotion}, energy={template.energy_level}")
    
    # Statistics
    print("\n--- Statistics ---")
    stats = selector.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print("\n✓ Test complete!")


if __name__ == "__main__":
    main()
