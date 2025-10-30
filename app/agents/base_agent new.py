"""
Base Agent Abstract Class

All agents inherit from this base class which provides common functionality.
"""

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

from langchain_core.tools import BaseTool
from langchain_core.messages import SystemMessage, HumanMessage


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.
    
    Subclasses must implement:
    - name(): Return agent's unique identifier
    - system_prompt(): Return agent's system prompt
    - tools(): Return list of available tools (can be empty)
    """
    
    @abstractmethod
    def name(self) -> str:
        """Return the unique name/identifier for this agent"""
        pass
    
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the system prompt that defines this agent's behavior"""
        pass
    
    def tools(self) -> List[BaseTool]:
        """
        Return list of tools available to this agent.
        Override in subclasses that need tools.
        
        Returns:
            List of BaseTool instances (empty list by default)
        """
        return []
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's logic.
        
        This is the main entry point called by the orchestrator.
        Override this method in subclasses for custom execution logic.
        
        Args:
            state: Current conversation state
        
        Returns:
            Updated state dictionary
        """
        # Ensure state is a dictionary
        if not isinstance(state, dict):
            print(f"⚠️ Warning: state is not a dict, got {type(state)}")
            state = {}
        
        # Ensure required keys exist with safe defaults
        user_message = state.get("user_message", "")
        
        # If agent has tools, use tool-calling logic
        if self.tools():
            return self._execute_with_tools(state)
        else:
            # Simple LLM completion without tools
            return self._execute_without_tools(state)
    
    def _execute_with_tools(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent with tool-calling capability.
        
        This method should be overridden by agents that need
        custom tool-calling logic.
        """
        from app.llm import llm_complete
        
        user_message = state.get("user_message", "")
        
        # Build prompt
        prompt = f"""
{self.system_prompt()}

User message: {user_message}

Please analyze the user's message and decide which tools to call (if any).
Available tools: {[tool.name for tool in self.tools()]}
"""
        
        # Get LLM response
        response = llm_complete(prompt)
        
        # Update state with response
        if state is None:
            state = {}
        
        state["reply"] = response
        
                
        return state
    
    def _execute_without_tools(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent without tools (simple LLM completion).
        """
        from app.llm import llm_complete
        
        user_message = state.get("user_message", "")
        
        # Build prompt
        prompt = f"""
{self.system_prompt()}

User message: {user_message}
"""
        
        # Get LLM response
        response = llm_complete(prompt)
        
        # Ensure state is a dict
        if state is None:
            state = {}
        
        state["reply"] = response
        
        return state