"""
Conversation Manager - LLM-based conversational AI for Reachy

Enables natural conversation using an LLM backend with context awareness
of recognized individuals and conversation history.
"""

import logging
from typing import Optional, List, Dict
from dataclasses import dataclass
import asyncio
from openai import AsyncOpenAI
import os

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)


@dataclass
class ConversationMessage:
    """A single message in the conversation."""
    role: str  # 'system', 'user', or 'assistant'
    content: str
    name: Optional[str] = None  # Speaker's name if known


class ConversationManager:
    """
    Manages conversational AI for Reachy with context awareness.
    
    Features:
    - Person-aware conversations (knows who it's talking to)
    - Conversation history management
    - Personality-driven responses
    - Quick response generation for natural interaction
    """
    
    def __init__(
        self,
        personality: str = "friendly",
        max_history: int = 10,
        model: str = "gpt-4o-mini"  # Fast, cheap model for conversation
    ):
        """
        Initialize conversation manager.
        
        Args:
            personality: Conversation personality (friendly, professional, playful)
            max_history: Maximum conversation history to maintain
            model: OpenAI model to use for conversation
        """
        self.personality = personality
        self.max_history = max_history
        self.model = model
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = AsyncOpenAI(api_key=api_key)
        
        # Conversation history per person
        self.conversations: Dict[str, List[ConversationMessage]] = {}
        
        # System prompt based on personality
        self.system_prompts = {
            'friendly': (
                "You are Reachy, a friendly and helpful robot assistant. "
                "You greet people warmly and engage in natural conversation. "
                "Keep responses concise (1-2 sentences) for natural dialogue. "
                "Be enthusiastic and personable."
            ),
            'professional': (
                "You are Reachy, a professional robot assistant. "
                "You provide helpful information clearly and efficiently. "
                "Keep responses concise (1-2 sentences) for natural dialogue. "
                "Be polite and professional."
            ),
            'playful': (
                "You are Reachy, a playful and fun robot assistant. "
                "You enjoy engaging with people and making conversations fun. "
                "Keep responses concise (1-2 sentences) for natural dialogue. "
                "Be cheerful and entertaining."
            )
        }
        
        logger.info(f"ConversationManager initialized: personality={personality}, model={model}")
    
    async def get_response(
        self,
        user_input: str,
        person_name: Optional[str] = None,
        context: Optional[str] = None
    ) -> str:
        """
        Get conversational response to user input.
        
        Args:
            user_input: What the user said
            person_name: Name of the person (if recognized)
            context: Additional context (e.g., "just greeted", "returning visitor")
            
        Returns:
            Response text from Reachy
        """
        # Get or create conversation history for this person
        conversation_key = person_name or "unknown"
        if conversation_key not in self.conversations:
            self.conversations[conversation_key] = []
        
        history = self.conversations[conversation_key]
        
        # Build messages for API
        messages = [
            {"role": "system", "content": self.system_prompts[self.personality]}
        ]
        
        # Add context if provided
        if context:
            messages.append({
                "role": "system",
                "content": f"Context: {context}"
            })
        
        # Add person's name if known
        if person_name:
            messages.append({
                "role": "system",
                "content": f"You are speaking with {person_name}."
            })
        
        # Add conversation history
        for msg in history[-self.max_history:]:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add current user input
        messages.append({
            "role": "user",
            "content": user_input
        })
        
        try:
            # Get response from LLM - optimized for speed
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=35,  # Even shorter for faster responses (reduced from 50)
                temperature=0.7  # Slightly less creative, more predictable/faster
            )
            
            assistant_response = response.choices[0].message.content.strip()
            
            # Update conversation history
            history.append(ConversationMessage(role="user", content=user_input, name=person_name))
            history.append(ConversationMessage(role="assistant", content=assistant_response))
            
            # Trim history if too long
            if len(history) > self.max_history * 2:
                self.conversations[conversation_key] = history[-self.max_history * 2:]
            
            logger.info(f"Generated response for {person_name or 'unknown'}: {assistant_response[:50]}...")
            return assistant_response
            
        except Exception as e:
            logger.error(f"Conversation error: {e}")
            return "I'm having trouble understanding right now. Could you repeat that?"
    
    def clear_history(self, person_name: Optional[str] = None):
        """
        Clear conversation history.
        
        Args:
            person_name: Clear history for specific person, or all if None
        """
        if person_name:
            if person_name in self.conversations:
                del self.conversations[person_name]
                logger.info(f"Cleared conversation history for {person_name}")
        else:
            self.conversations.clear()
            logger.info("Cleared all conversation history")
    
    def get_conversation_stats(self) -> Dict:
        """Get conversation statistics."""
        return {
            "active_conversations": len(self.conversations),
            "total_messages": sum(len(msgs) for msgs in self.conversations.values()),
            "personalities": list(self.system_prompts.keys()),
            "current_personality": self.personality
        }


# Demo/Testing
async def main():
    """Demo conversation manager."""
    print("=" * 70)
    print("Conversation Manager Demo")
    print("=" * 70)
    print()
    
    manager = ConversationManager(personality="friendly")
    
    # Simulate conversation with Michelle
    print("Conversation with Michelle:")
    print("-" * 70)
    
    exchanges = [
        ("Hello Reachy!", None),
        ("How are you today?", "just greeted"),
        ("What can you help me with?", None),
        ("Tell me a joke!", None),
    ]
    
    for user_input, context in exchanges:
        print(f"\nMichelle: {user_input}")
        response = await manager.get_response(
            user_input,
            person_name="Michelle",
            context=context
        )
        print(f"Reachy: {response}")
    
    print("\n" + "=" * 70)
    print("Stats:")
    stats = manager.get_conversation_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n✅ Demo complete!")


if __name__ == "__main__":
    asyncio.run(main())
