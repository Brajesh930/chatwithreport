# Quick Start Guide - Python Version

## Prerequisites
- Python 3.7 or higher installed
- pip package manager

## 1. Install Dependencies

Open terminal/PowerShell in the project directory and run:

```bash
pip install -r requirements.txt
```

## 2. Configure Environment

Create a `.env` file in the project root with your configuration:

```
APP_ENV=development
APP_NAME=Document Chat System
AI_PROVIDER=gemini
AI_API_KEY=your-gemini-api-key-here
AI_MODEL=gemini-1.5-pro
MAX_UPLOAD_SIZE=10485760
ALLOWED_EXTENSIONS=txt,pdf,docx,md
STORAGE_PATH=./storage
LOG_LEVEL=debug
```

**Important**: Get your Gemini API key from: https://ai.google.dev/

## 3. Run the Application

In the project directory:

```bash
python app.py
```

You should see output like:
```
Starting Document Chat System - development environment
Frontend admin pages at: http://localhost:8000/frontend
  Admin login:    http://localhost:8000/admin/login.php
  Employee login: http://localhost:8000/employee/login.php
  Client login:   http://localhost:8000/client/login.php
```

## 4. Access the Application

### Main Application
- **URL**: http://localhost:8000/
- **Features**:
  - Upload documents (TXT, PDF, DOCX, MD)
  - Ask AI questions about documents
  - View parsed content

### Admin Panel (Preview)
- **URL**: http://localhost:8000/frontend
- **Features**:
  - Admin management
  - Employee management
  - Client management
  - Project management

## API Endpoints

### Upload Files
```
POST /api/upload
- Field: file (file object)
- Supports single or multiple files
- Returns: original filename, parsed filename, parser used
```

### Ask Questions
```
POST /api/chat
Body: {"question": "your question here"}
Returns: {"success": true, "answer": "AI response"}
```

### Get File Info
```
GET /api/file-info
Returns: Currently loaded file information with parsed content
```

### Reset Application
```
POST /api/reset
Returns: {"success": true, "message": "Application reset successfully"}
```

## Troubleshooting

### Issue: "No module named 'flask'"
**Solution**: Run `pip install -r requirements.txt`

### Issue: "AI API Key not configured"
**Solution**: Set `AI_API_KEY` in your `.env` file

### Issue: "Port 8000 already in use"
**Solution**: Modify the port in `app.py` line: `app.run(host='localhost', port=8001, ...)`

### Issue: "Permission denied" on file upload
**Solution**: Ensure `storage/` directory exists and is writable
```bash
mkdir storage/uploads storage/parsed storage/logs
```

## File Locations

- **Uploaded files**: `storage/uploads/`
- **Parsed content**: `storage/parsed/`
- **Application logs**: `storage/logs/app.log`
- **Configuration**: `.env` (in project root)

## Development Notes

- Application auto-reloads on code changes (development mode)
- CORS enabled for cross-origin requests
- All logs written to both file and console
- Database is in-memory (mock data) - suitable for preview/demo

## Next Steps

1. ✅ All PHP has been converted to Python
2. ✅ Dependencies are listed in `requirements.txt`
3. ✅ Configuration managed via `.env`
4. ✅ Complete API documentation in responses
5. 📝 Configure your Gemini API key
6. 🚀 Run `python app.py` and start using!

## Questions or Issues?

Check the logs in `storage/logs/app.log` for detailed debugging information.
