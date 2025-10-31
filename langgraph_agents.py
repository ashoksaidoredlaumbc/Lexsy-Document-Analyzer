from typing import TypedDict, Annotated, List, Dict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import operator
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Verify API key is loaded
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables!")

class DocumentState(TypedDict):
    document_text: str
    placeholders: List[str]
    current_placeholder: str
    current_index: int
    collected_values: Dict[str, str]
    user_response: str
    question: str
    validation_result: Dict
    messages: Annotated[List, operator.add]

def question_generator_node(state: DocumentState) -> DocumentState:
    """Generate contextual questions for placeholders"""
    
    llm = ChatOpenAI(
        model="gpt-4o", 
        temperature=0.7,
        api_key=OPENAI_API_KEY
    )
    
    current_index = state['current_index']
    placeholders = state['placeholders']
    
    if current_index >= len(placeholders):
        return state
    
    current_placeholder = placeholders[current_index]
    
    system_prompt = """You are a legal assistant specializing in document completion.
    Generate clear, specific questions that help users understand exactly what information is needed.
    
    For legal documents like SAFE agreements, NDAs, contracts:
    - For dollar amounts: Ask for specific currency and amount
    - For dates: Request specific format
    - For names: Clarify if individual or company name
    - For legal terms: Provide brief explanations
    
    Make questions conversational yet professional."""
    
    # Extract context around placeholder
    doc_text = state['document_text']
    context = ""
    
    search_patterns = [f"{{{current_placeholder}}}", f"[{current_placeholder}]", current_placeholder]
    for pattern in search_patterns:
        if pattern in doc_text:
            pos = doc_text.find(pattern)
            start = max(0, pos - 200)
            end = min(len(doc_text), pos + len(pattern) + 200)
            context = doc_text[start:end]
            break
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"""
        Placeholder: {current_placeholder}
        Document context: {context if context else doc_text[:300]}
        
        Generate ONE clear question to collect this information. Return only the question.
        """)
    ]
    
    response = llm.invoke(messages)
    question = response.content.strip()
    
    return {
        **state,
        "question": question,
        "current_placeholder": current_placeholder,
        "messages": [AIMessage(content=question)]
    }

def validation_node(state: DocumentState) -> DocumentState:
    """Validate user response and format appropriately"""
    
    llm = ChatOpenAI(
        model="gpt-4o", 
        temperature=0.3,
        api_key=OPENAI_API_KEY 
    )
    
    system_prompt = """You are a data validation expert for legal documents.
    Validate user responses and format them appropriately.
    
    Check for:
    - Appropriate data types (numbers, dates, text)
    - Reasonable values (e.g., investment amounts should be positive)
    - Proper formatting (dates, currencies, names)
    - Completeness (no missing critical information)
    
    Return ONLY valid JSON with: {"valid": true/false, "formatted_value": "...", "feedback": "..."}
    """
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"""
        Placeholder: {state['current_placeholder']}
        User response: {state['user_response']}
        
        Validate and format this response. Return valid JSON only.
        """)
    ]
    
    response = llm.invoke(messages)
    
    try:
        validation_result = json.loads(response.content)
    except:
        validation_result = {
            "valid": True,
            "formatted_value": state['user_response'],
            "feedback": "Accepted"
        }
    
    updated_values = state['collected_values'].copy()
   
    if validation_result['valid']:
        updated_values[state['current_placeholder']] = validation_result['formatted_value']
        new_index = state['current_index'] + 1
    else:
        new_index = state['current_index']
    
    return {
        **state,
        "validation_result": validation_result,
        "collected_values": updated_values,
        "current_index": new_index,
        "messages": [AIMessage(content=validation_result.get('feedback', 'Validated'))]
    }

def continue_process(state: DocumentState) -> str:
    """Determine if we should continue or end"""
    if state['current_index'] >= len(state['placeholders']):
        return "complete"
    return "continue"

def ask_again(state: DocumentState) -> str:
    """Determine if we need to ask the question again"""
    validation = state.get('validation_result', {})
    if not validation.get('valid', True):
        return "ask_again"
    return "next_question"

# Build the LangGraph workflow
def create_document_workflow():
    
    # Create state graph
    workflow = StateGraph(DocumentState)
    
    # Add nodes
    workflow.add_node("question_generator", question_generator_node)
    workflow.add_node("validator", validation_node)
    
    # Set entry point
    workflow.set_entry_point("question_generator")
    
    # Add edges
    workflow.add_edge("question_generator", END)
    
    workflow.add_conditional_edges(
        "validator",
        continue_process,
        {
            "continue": "question_generator",
            "complete": END
        }
    )
    
    return workflow.compile()
