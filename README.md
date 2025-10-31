# Lexsy Document Automation

An intelligent document automation system that uses AI-powered conversational agents to help users complete legal documents by filling in placeholders through an interactive Q&A interface.

## Overview

Lexsy Document Automation is a web application that automates the process of filling legal document templates. Instead of manually searching for placeholders and understanding their context, users are guided through an intelligent conversation where an AI assistant asks contextual questions about each placeholder, validates responses, and generates a completed document.

### Key Features

- **Smart Placeholder Detection**: Automatically detects placeholders in various formats (`{placeholder}`, `[PLACEHOLDER]`, `{{placeholder}}`, etc.)
- **AI-Powered Question Generation**: Uses GPT-4 to generate contextual, conversational questions based on document content
- **Response Validation**: Validates and formats user responses to ensure data quality
- **Interactive Chat Interface**: Modern, user-friendly chat UI with progress tracking
- **Document Preview**: View completed documents in HTML format before downloading
- **Edit & Regenerate**: Modify collected values and regenerate documents instantly
- **Multiple Format Support**: Supports various placeholder formats commonly used in legal documents

## Architecture

The application consists of three main components:

1. **Backend (FastAPI)**: RESTful API handling document processing, workflow orchestration, and session management
2. **Frontend (Vanilla JS)**: Single-page application with modern UI for document upload and interactive chat
3. **LangGraph Workflow**: Multi agent workflow that generates questions and validates responses using OpenAI's GPT-4

### Technology Stack

- **Backend**: FastAPI, Uvicorn
- **AI/ML**: LangChain, LangGraph, OpenAI GPT-4
- **Document Processing**: python-docx, mammoth
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Deployment**: AWS Elastic Beanstalk ready

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+** (Python 3.9+ recommended)
- **pip** (Python package installer)
- **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <folder_name>
```

### 2. Create a Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root directory:

```bash
touch .env
```

Add your OpenAI API key to the `.env` file:

```env
OPENAI_API_KEY=<your_openai_api_key_here>
```

** Important**: Never commit the `.env` file to version control. It's already included in `.gitignore`.

### 5. Create Required Directories

The application will automatically create these directories on first run, but you can create them manually:

```bash
mkdir -p uploads output static
```

## 🏃 Running the Application

### Development Mode

Run the FastAPI application using Uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or simply run the main file:

```bash
python main.py
```

The application will be available at:
- **API**: `http://localhost:8000`
- **Web Interface**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs` (FastAPI auto-generated docs)

### Production Mode

For production deployments, use the Procfile command:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📖 Usage Guide

### Step 1: Upload Document Template

1. Open the application in your browser (`http://localhost:8000`)
2. Click "Upload .docx Template"
3. Select a Word document (`.docx`) containing placeholders

**Supported Placeholder Formats**:
- `{placeholder_name}`
- `[PLACEHOLDER_NAME]`
- `{{placeholder_name}}`
- `___PLACEHOLDER___`
- `${placeholder_name}`

### Step 2: Answer Questions

1. The AI will analyze your document and ask questions about each placeholder
2. Read each question carefully and provide your answer
3. The system validates your response and may ask for clarification if needed
4. Track your progress using the progress bar at the top

### Step 3: Review and Download

1. Once all placeholders are filled, the document will be automatically generated
2. Review the HTML preview of your completed document
3. Use "Edit Values" to modify any collected information
4. Click "Download Document" to save the completed `.docx` file

## 🔌 API Endpoints

### `POST /api/upload`

Upload a document template for processing.

**Request**:
- `file`: `.docx` file (multipart/form-data)

**Response**:
```json
{
  "session_id": "uuid",
  "total_placeholders": 5,
  "first_question": "What is the company name?",
  "current_placeholder": "COMPANY_NAME",
  "progress": "1/5"
}
```

### `POST /api/chat`

Send a response to the current question.

**Request**:
```json
{
  "session_id": "uuid",
  "message": "Acme Corporation",
  "placeholder": "COMPANY_NAME"
}
```

**Response**:
```json
{
  "type": "next_question",
  "question": "What is the investment amount?",
  "current_placeholder": "INVESTMENT_AMOUNT",
  "progress": "2/5"
}
```

### `POST /api/generate`

Generate the final document after all placeholders are collected.

**Request**:
- `session_id`: Query parameter

**Response**:
```json
{
  "preview_html": "<div>...</div>",
  "collected_values": {"COMPANY_NAME": "Acme Corp", ...},
  "filename": "completed_document.docx"
}
```

### `POST /api/update-values`

Update collected values and regenerate document.

**Request**:
- `session_id`: Query parameter
- `updated_values`: JSON object with key-value pairs

### `GET /api/download/{session_id}`

Download the completed document.

**Response**: `.docx` file download

## Project Structure

```
lexsy_assignment/
├── main.py                 # FastAPI application and API endpoints
├── document_processor.py   # Document processing and placeholder handling
├── langgraph_agents.py    # LangGraph workflow and AI agent nodes
├── requirements.txt       # Python dependencies
├── Procfile              # AWS Elastic Beanstalk startup command
├── .env                  # Environment variables (create this, not committed)
├── .ebignore             # Files excluded from EB deployment
├── static/
│   ├── index.html        # Main frontend HTML
│   ├── app.js           # Frontend JavaScript
│   └── style.css        # Frontend styling
├── .elasticbeanstalk/    # EB CLI configuration (auto-generated)
├── uploads/             # Uploaded document templates (auto-created)
└── output/              # Generated completed documents (auto-created)
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key for GPT-4 access | Yes |

### Model Configuration

The application uses OpenAI's `gpt-4o` model by default. To change the model, edit `langgraph_agents.py`:

```python
llm = ChatOpenAI(
    model="gpt-4o",  # Change this to your preferred model
    temperature=0.7,
    api_key=OPENAI_API_KEY
)
```

## Deployment

### AWS Elastic Beanstalk

This application is deployed using AWS Elastic Beanstalk with EB CLI. Follow these steps to deploy:

#### Prerequisites

1. **Install AWS EB CLI**:
   ```bash
   pip install awsebcli
   ```

2. **Configure AWS Credentials**:
   - Install AWS CLI: `pip install awscli`
   - Configure credentials: `aws configure`
   - Enter your AWS Access Key ID, Secret Access Key, and region

#### Initial Setup

1. **Initialize Elastic Beanstalk Application**:
   ```bash
   eb init -p python-3.9 <your-application-name>
   ```
   - Select your preferred region
   - Choose whether to use AWS CodeCommit (optional)

2. **Create Environment**:
   ```bash
   eb create lexsy-production --single --instance-type t3.micro
   ```
   - `--single`: Creates a single-instance environment (no load balancer) - ideal for development/testing or cost-effective production
   - `--instance-type t3.micro`: Specifies EC2 instance type (t3.micro is cost-effective for small applications)
   - This creates a new Elastic Beanstalk environment
   - First deployment may take 5-10 minutes

3. **Set Environment Variables**:
   ```bash
   eb setenv OPENAI_API_KEY=sk-your-actual-key-here
   ```
   - Replace `sk-your-actual-key-here` with your actual OpenAI API key
   - Environment variables are set on the Elastic Beanstalk environment
   
   Or set multiple environment variables:
   ```bash
   eb setenv OPENAI_API_KEY=sk-your-key PORT=8000
   ```

#### Quick Deployment (Complete Workflow)

After initializing with `eb init`, here's the complete deployment workflow:

```bash
# 1. Create production environment (single instance, t3.micro)
eb create lexsy-production --single --instance-type t3.micro

# 2. Set your OpenAI API key
eb setenv OPENAI_API_KEY=sk-your-actual-key-here

# 3. Deploy your app
eb deploy
```

#### Deployment Workflow

1. **Deploy Application**:
   ```bash
   eb deploy
   ```
   - This packages and deploys your application to Elastic Beanstalk
   - Uploads your code and triggers a deployment
   - Monitor progress in the terminal or via `eb status`

2. **Open Application in Browser**:
   ```bash
   eb open
   ```
   - Opens your deployed application URL

3. **View Logs**:
   ```bash
   eb logs
   ```
   - Downloads recent logs for debugging

4. **Check Application Status**:
   ```bash
   eb status
   ```
   - Shows current environment status and health

#### Useful EB CLI Commands

- **List all environments**: `eb list`
- **Check environment health**: `eb health`
- **SSH into EC2 instance**: `eb ssh`
- **Terminate environment**: `eb terminate <environment-name>`
- **Scale up/down**: `eb scale <number>`
- **Update environment configuration**: `eb config`

#### Environment Configuration

The application uses Elastic Beanstalk's default Python platform configuration. The Procfile is used to specify the startup command:

```
web: uvicorn main:app --host 0.0.0.0 --port 8000
```

#### Troubleshooting Deployment

1. **View Detailed Logs**:
   ```bash
   eb logs --all
   ```

2. **Check Environment Events**:
   ```bash
   eb events
   ```

3. **Rebuild Environment** (if deployment fails):
   ```bash
   eb rebuild
   ```

4. **SSH and Debug**:
   ```bash
   eb ssh
   # Once connected, check Python version, installed packages, etc.
   ```

#### Production Considerations

- **Single Instance vs Load Balanced**: Using `--single` creates a cost-effective single-instance environment. For high availability, create environments without `--single` flag to enable load balancing and auto-scaling
- **Instance Types**: `t3.micro` is suitable for development/testing. For production workloads, consider `t3.small` or larger based on traffic
- **Auto Scaling**: For single-instance environments, auto-scaling is not available. Remove `--single` flag and configure auto-scaling groups in EB console for high availability
- **HTTPS**: Set up SSL certificate in AWS Certificate Manager and configure in EB console under "Configuration" > "Load Balancer"
- **Database**: Consider using RDS for persistent session storage in production (current implementation uses in-memory sessions)
- **File Storage**: Use S3 for file uploads instead of EC2 instance storage for better persistence and scalability

#### Configuration Files

The project structure supports Elastic Beanstalk:
- `Procfile`: Defines the web server command
- `.ebignore`: Excludes files from deployment (similar to .gitignore)
- `.elasticbeanstalk/`: Contains EB CLI configuration (auto-generated)


## Troubleshooting

### Common Issues

**Issue**: `OPENAI_API_KEY not found in environment variables!`
- **Solution**: Ensure `.env` file exists in project root with `OPENAI_API_KEY=your_key`

**Issue**: `No placeholders found in document`
- **Solution**: Ensure your document uses supported placeholder formats (see Usage Guide)

**Issue**: Document preview not displaying
- **Solution**: Check that `mammoth` library is installed correctly: `pip install mammoth`

**Issue**: Port already in use
- **Solution**: Change port: `uvicorn main:app --port 8001`

## Security Considerations

- **API Keys**: Never commit `.env` files or expose API keys in code
- **File Uploads**: Currently accepts any `.docx` file - consider adding file size limits and validation
- **CORS**: Configure CORS settings for production (currently allows all origins)
- **Session Management**: Sessions are stored in memory - consider using Redis/database for production


## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- AI capabilities powered by [OpenAI](https://openai.com/) and [LangChain](https://www.langchain.com/)
- Document processing with [python-docx](https://python-docx.readthedocs.io/)

