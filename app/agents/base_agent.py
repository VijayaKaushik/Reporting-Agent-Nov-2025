import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Callable

from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.tools import BaseTool

from app.config import settings


class BaseAgent(ABC):
    """All feature agent should inherit this class"""

    @abstractmethod
    def name(self) -> str:
        """Unique name of the agent (used as a node in the langgraph)"""
        pass

    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt that help Agent routing"""
        pass


    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # """Main logic of the agent node""" # direct logic, or it can call a list of tools or MCP client
        # pass
        # An agent will have list of tools we'll decide which tool to call using LLM
        llm = init_chat_model(settings.GEMINI_MODEL, model_provider="google_genai")
        tools = self.tools()
        
         # 🧩 DEBUG 1: Confirm which agent is running and which tools are available
        print(f"\n🧠 Executing agent: {self.name()}")
        print(f"🧰 Tools attached: {[t.name for t in tools] if tools else 'No tools found!'}")
        print(f"💬 User message: {state.get('user_message')}\n")
        
        if tools:
            # For function navigate Mac (CMD + CLICK), Window (CTRL + CLICK)
            agent = create_agent(llm, tools, system_prompt=self.system_prompt())
            # This will select the right tool based on the user message and execute the tool as well
            message = {"messages": [{"role": "user", "content": state.get("user_message")}]}
            result = agent.invoke(message) # This has a stream function as well that will emit all the internal thing graph is doing
            
            print(f"📨 Raw LLM+Tool result: {result}\n")
           
            # ✅ Extract response safely
            try:
                state["reply"] = result["messages"][-1].text
            except Exception as e:
                print(f"⚠️ Unexpected output format from agent: {e}")
                state["reply"] = str(result)
        else:
            print("⚠️ No tools defined for this agent.")
            state["reply"] = "(No tools attached)"

        return state

    def tools(self) -> List[BaseTool]: # Callable anything that I can execute as a function List[fetch_template_tool] List[0]()
        return []

    def pre_hook(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Optional pre-processing hook""" # Check if token usage is under limit, guardrails to reject the execution, custom event emitter
        pass

    def post_hook(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Optional post-processing hook""" # Token usage update, bulk upload of custom event to langgraph state, guardrails to reject the execution
        pass

    def on_error(self, state: Dict[str, Any], error: Exception) -> Dict[str, Any]:
        """Error handling hook"""
        state["error"] = str(error)
        return state


