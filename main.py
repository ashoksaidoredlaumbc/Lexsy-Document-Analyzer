from langgraph_agents import create_document_workflow, DocumentState
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List
import os
import uuid
import shutil
from langgraph_agents import validation_node, question_generator_node
from document_processor import DocumentProcessor

os.makedirs("uploads", exist_ok=True)
os.makedirs("output", exist_ok=True)
os.makedirs("static", exist_ok=True)

app = FastAPI(title="Lexsy Document Automation")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions = {}

# Create LangGraph workflow
document_workflow = create_document_workflow()

class ChatMessage(BaseModel):
    session_id: str
    message: str
    placeholder: str = None

class SessionData(BaseModel):
    session_id: str
    placeholders: List[str]
    collected_values: Dict[str, str]
    current_index: int
    original_filename: str

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process document using LangGraph agents"""
    
    if not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="Only .docx files are supported")
    
    session_id = str(uuid.uuid4())
    file_path = f"uploads/{session_id}_{file.filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    processor = DocumentProcessor(file_path)
    document_text = processor.extract_text()
    placeholders = processor.detect_placeholders()
    
    if not placeholders:
        raise HTTPException(status_code=400, detail="No placeholders found in document")
    
    initial_state: DocumentState = {
        "document_text": document_text,
        "placeholders": placeholders,
        "current_placeholder": "",
        "current_index": 0,
        "collected_values": {},
        "user_response": "",
        "question": "",
        "validation_result": {},
        "messages": []
    }
    
    # Run workflow to generate first question
    result = document_workflow.invoke(initial_state)
    
    sessions[session_id] = {
        "file_path": file_path,
        "workflow_state": result,
        "original_filename": file.filename,
        "processor": processor
    }
    
    current_question_number = result['current_index'] + 1
    
    return {
        "session_id": session_id,
        "total_placeholders": len(placeholders),
        "first_question": result['question'],
        "current_placeholder": result['current_placeholder'],
        "progress": f"{current_question_number}/{len(placeholders)}"
    }

@app.post("/api/chat")
async def chat_response(chat: ChatMessage):    
    session = sessions.get(chat.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
   
    current_state = session["workflow_state"]
    
    # Update state with user response
    validation_state: DocumentState = {
        **current_state,
        "user_response": chat.message
    }
    
    # Run validation node
    validated_state = validation_node(validation_state)
    
    # Update session state
    session["workflow_state"] = validated_state
    
    # Check validation result
    validation_result = validated_state.get('validation_result', {})
    
    if not validation_result.get('valid', True):
        current_position = current_state['current_index'] + 1
        return {
            "type": "validation_error",
            "message": validation_result.get('feedback', 'Please provide a valid response'),
            "current_placeholder": validated_state['current_placeholder'],
            "progress": f"{current_position}/{len(validated_state['placeholders'])}"
        }
    
    # Check if complete
    total_placeholders = len(validated_state['placeholders'])
    if validated_state['current_index'] >= total_placeholders:
        return {
            "type": "complete",
            "message": "All information collected! Generating your document...",
            "total_collected": len(validated_state['collected_values'])
        }
    
    # Generate next question
    next_question_state = question_generator_node(validated_state)
    
    # Update session with new state
    session["workflow_state"] = next_question_state
    
    current_question_number = next_question_state['current_index'] + 1
    
    return {
        "type": "next_question",
        "question": next_question_state['question'],
        "current_placeholder": next_question_state['current_placeholder'],
        "progress": f"{current_question_number}/{total_placeholders}"
    }

@app.post("/api/generate")
async def generate_document(session_id: str):
    """Generate final document and return preview"""
    
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    workflow_state = session["workflow_state"]
    collected_values = workflow_state['collected_values']
    
    # Generate output
    output_filename = f"completed_{session['original_filename']}"
    output_path = f"output/{session_id}_{output_filename}"
    
    # Fill template
    processor = session["processor"]
    processor.fill_template(collected_values, output_path)
    
    # Generate HTML preview
    html_preview = processor.generate_html_preview(output_path)
    
    # Store output path in session
    session["output_path"] = output_path
    session["output_filename"] = output_filename
    
    return {
        "preview_html": html_preview,
        "collected_values": collected_values,
        "filename": output_filename
    }

@app.post("/api/update-values")
async def update_values(session_id: str, updated_values: Dict[str, str]):
    """Update placeholder values and regenerate document"""
    
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get workflow state where collected_values are stored
    workflow_state = session.get("workflow_state")
    if not workflow_state:
        raise HTTPException(status_code=500, detail="Workflow state not found")
    
    # Update collected values in the workflow state
    workflow_state["collected_values"].update(updated_values)
    session["workflow_state"] = workflow_state
    
    # Ensures start from the original template, not a modified version
    original_file_path = session["file_path"]
    processor = DocumentProcessor(original_file_path)
    
    # Regenerate document with updated values
    output_path = session["output_path"]
    
    # Fill template with ALL collected values
    processor.fill_template(workflow_state["collected_values"], output_path)
    
    # Generate new preview from the newly created document
    html_preview = processor.generate_html_preview(output_path)
    
    return {
        "preview_html": html_preview,
        "collected_values": workflow_state["collected_values"],
        "message": "Document updated successfully"
    }

@app.get("/api/download/{session_id}")
async def download_document(session_id: str):
    """Download complete document"""
    
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    output_filename = f"completed_{session['original_filename']}"
    output_path = f"output/{session_id}_{output_filename}"
    
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Generated document not found")
    
    return FileResponse(
        path=output_path,
        filename=output_filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)