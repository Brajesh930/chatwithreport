# Document Chat System - MVP

A simple, modular document-chat system for testing. Upload a document, parse it into a normalized format, and ask questions about it using AI.

## ✨ Features

- **Simple File Upload**: Upload .txt, .pdf, .docx, or .md files
- **Automatic Parsing**: Converts all files to a normalized text format
- **Document Q&A**: Ask questions about the uploaded document
- **Clean Architecture**: Modular PHP backend with service classes
- **Easy Frontend**: Plain HTML/CSS/JavaScript with no frameworks
- **Local Storage**: All files stored securely on the server
- **Logging**: Basic logging for debugging
- **REST API**: Simple REST endpoints for all operations

## 📋 System Requirements

- PHP 7.4 or higher
- Composer (for dependency management)
- A Gemini API key (Google AI Studio) or any supported AI provider
- Web server (e.g., Apache, Nginx)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /path/to/Chat\ Bot\ for\ Reports
composer install
```

This will install:
- `vlucas/phpdotenv` - Environment variable management
- `smalot/pdfparser` - PDF parsing
- `phpoffice/phpword` - DOCX parsing

### 2. Configure API Key

Open `.env` and add your Gemini API key:

```ini
AI_API_KEY=your_actual_gemini_api_key_here
```

**How to get a Gemini API key:**
1. Go to [Google AI Studio](https://aistudio.google.com)
2. Click "Create API Key" or "Get API Key"
3. Create a new API key in Google Cloud Console
4. Copy and paste it into `.env`

### 3. Set File Permissions

Ensure the storage directory is writable:

```bash
chmod -R 755 storage/
chmod -R 755 storage/uploads/
chmod -R 755 storage/parsed/
chmod -R 755 storage/logs/
```

(Windows users: Use File Properties or run as Administrator if needed)

### 4. Start a Local Web Server

**Option A: Using PHP Built-in Server**

```bash
php -S localhost:8000 -t public/
```

Then open: `http://localhost:8000`

**Option B: Using Apache**

Point your web server's DocumentRoot to the `public/` folder in this project.

**Option C: Using Docker**

```dockerfile
FROM php:7.4-apache
WORKDIR /var/www/html
COPY . .
RUN docker-php-ext-install zip
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer
RUN composer install
```

## 📁 Folder Structure

```
/Chat Bot for Reports
├── public/               # Frontend files (webroot)
│   ├── index.html       # Main UI
│   ├── style.css        # Styling
│   └── app.js           # JavaScript logic
├── api/                 # API endpoints
│   ├── upload.php       # File upload endpoint
│   ├── chat.php         # Chat/question endpoint
│   └── file-info.php    # File info endpoint
├── src/                 # Backend source code
│   ├── Services/        # Business logic classes
│   │   ├── FileUploadService.php
│   │   ├── FileParserService.php
│   │   ├── AIService.php
│   │   └── PromptBuilderService.php
│   ├── Helpers/         # Utility classes
│   │   ├── Logger.php
│   │   ├── ResponseBuilder.php
│   │   └── FileHelper.php
│   └── Config/          # Configuration
│       └── Config.php
├── storage/             # Server-side storage
│   ├── uploads/         # Original uploaded files
│   ├── parsed/          # Normalized parsed files
│   └── logs/            # Application logs
├── vendor/              # Composer packages
├── composer.json        # PHP dependencies
├── .env                 # Environment config (KEEP SECRET)
├── .env.example         # Example environment file
└── README.md            # This file
```

## 🎯 How to Use

### Upload a Document

1. Open the web interface (`http://localhost:8000`)
2. In the **"Step 1: Upload Document"** section, drag and drop a file or click to select
3. Click **"Upload File"**
4. Wait for the file to be parsed

### Ask Questions

1. Once a document is uploaded, the **"Step 2: Ask Questions"** section becomes active
2. Type your question in the textarea
3. Click **"Send Question"** or press `Ctrl+Enter`
4. The AI will read the document and answer based on its content

### View File Info

The **"Uploaded Document"** section shows:
- Original filename
- File format
- File size
- Upload timestamp
- Parsed filename

Click **"Refresh Info"** to update the information.

## 📤 API Endpoints

### POST `/api/upload.php`

Upload and parse a file.

**Request:**
```
Content-Type: multipart/form-data

file: <file contents>
```

**Response:**
```json
{
  "success": true,
  "message": "File uploaded and parsed successfully",
  "data": {
    "originalFilename": "report.pdf",
    "storedFilename": "report_1680000000_abc12345.pdf",
    "parsedFilename": "report_1680000000_abc12345_parsed.txt",
    "fileSize": 256000,
    "fileType": "pdf",
    "parserUsed": "PDF Parser"
  }
}
```

### POST `/api/chat.php`

Send a question about the uploaded document.

**Request:**
```json
{
  "question": "What is the main topic of this document?"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Answer generated",
  "data": {
    "question": "What is the main topic?",
    "answer": "The main topic is...",
    "document": "report_1680000000_abc12345_parsed.txt"
  }
}
```

### GET `/api/file-info.php`

Get information about the latest uploaded and parsed file.

**Response:**
```json
{
  "success": true,
  "message": "File info retrieved",
  "data": {
    "uploaded": {
      "filename": "report_1680000000_abc12345.pdf",
      "size": "250 KB",
      "extension": "pdf",
      "uploadTime": "2026-04-08 14:30:45"
    },
    "parsed": {
      "filename": "report_1680000000_abc12345_parsed.txt",
      "size": "248 KB",
      "uploadTime": "2026-04-08 14:30:46"
    }
  }
}
```

## 📝 Parsed File Format

All uploaded files are converted to this normalized text format and stored as `.txt` files:

```
==================================================
DOCUMENT NORMALIZED TEXT
==================================================

[METADATA]
Original File Name: report.pdf
Stored File Name: report_1680000000_abc12345.pdf
File Type: pdf
Upload Time: 2026-04-08 14:30:45
File Size: 250 KB
Parser Used: PDF Parser
Extraction Note: Some characters may not have parsed correctly.

[CONTENT]
<full extracted text from the document>

[END OF DOCUMENT]
```

## 🔧 Configuration

Edit `.env` to customize behavior:

```ini
# Environment mode
APP_ENV=development|production

# AI Provider settings
AI_PROVIDER=gemini
AI_API_KEY=your_key_here
AI_MODEL=gemini-1.5-pro

# File upload limits
MAX_UPLOAD_SIZE=10485760          # 10MB in bytes
ALLOWED_EXTENSIONS=txt,pdf,docx,md

# Storage path
STORAGE_PATH=./storage

# Logging level
LOG_LEVEL=debug|info|warning|error
```

## 🔐 Security Features

- ✅ Filename sanitization (removes special characters)
- ✅ File type validation (only allowed extensions)
- ✅ File size limits (prevents large uploads)
- ✅ API key stored server-side (not exposed in frontend)
- ✅ Safe file storage (outside public webroot)
- ✅ Input validation on all endpoints
- ✅ CORS headers for API access
- ⚠️ **NOTE:** This is an MVP. For production, add authentication, HTTPS, rate limiting, and stricter security measures.

## 📊 File Storage

**Uploaded Files:** `/storage/uploads/`
- Original files with unique timestamps
- Example: `report_1680000000_abc12345.pdf`

**Parsed Files:** `/storage/parsed/`
- Normalized text versions with `_parsed.txt` suffix
- Example: `report_1680000000_abc12345_parsed.txt`

**Logs:** `/storage/logs/`
- `app.log` - Application activity log

## 🐛 Troubleshooting

### "No file uploaded yet" error
- ✓ Upload a file first using the upload form
- ✓ Check that `storage/uploads/` directory exists and is writable

### "AI service not configured" error
- ✓ Ensure `.env` file exists in the project root
- ✓ Add your Gemini API key to `.env`
- ✓ Restart the web server

### "Unsupported file format" error
- ✓ Check that the file extension is in the allowed list (.txt, .pdf, .docx, .md)
- ✓ Update `ALLOWED_EXTENSIONS` in `.env` if needed

### Upload fails silently
- ✓ Check file size (must be under MAX_UPLOAD_SIZE)
- ✓ Check `storage/` directory permissions (must be writable)
- ✓ Check PHP error logs for detailed errors

### Parser fails for PDF/DOCX
- ✓ Ensure Composer dependencies are installed: `composer install`
- ✓ Check that `vendor/` directory exists
- ✓ Check PHP extensions: `php -m | grep zip` (for DOCX parsing)

### Can't read logs
- ✓ Check `storage/logs/app.log`
- ✓ Verify `storage/logs/` is writable

## 🔄 Workflow

1. **User uploads file** → POST `/api/upload.php`
2. **File validated** → Check extension, size, MIME type
3. **File stored** → Saved to `storage/uploads/`
4. **File parsed** → Converted to normalized text format
5. **Parsed file saved** → Stored to `storage/parsed/`
6. **User asks question** → POST `/api/chat.php`
7. **Backend loads parsed file** → Reads from `storage/parsed/`
8. **Prompt built** → System instruction + document + question
9. **AI called** → Gemini API receives prompt
10. **Response returned** → Answer sent to frontend chat

## 💡 Design Decisions

- **No database:** Files only, simpler initial MVP
- **Single document at a time:** Simplifies session management
- **REST API:** Easy to extend later
- **Service classes:** Clean separation of concerns for future features
- **Plain frontend:** No frameworks, easier to understand and modify
- **Environment config:** Easy to change settings without code edits

## 🚧 Next Steps for Production

- [ ] Add user authentication/login
- [ ] Add database (SQLite/MySQL) for persistence
- [ ] Add multi-user support with document management
- [ ] Add file history and versioning
- [ ] Add caching layer (Redis)
- [ ] Add rate limiting on API endpoints
- [ ] Add comprehensive error handling
- [ ] Add unit tests
- [ ] Add HTTPS/SSL
- [ ] Add admin panel
- [ ] Add document tagging/search
- [ ] Support more file formats (Excel, PPT, etc.)
- [ ] Add document preview
- [ ] Add conversation history per document
- [ ] Deploy to production server (AWS, Azure, etc.)

## 📚 Service Classes Overview

### FileUploadService
Handles file upload validation and storage.
- `validate()` - Validate uploaded file
- `process()` - Process and store upload
- `getLatestFile()` - Retrieve latest uploaded file info

### FileParserService
Parses files into normalized text format.
- `parse()` - Parse uploaded file and save normalized version
- `parseTxt()` - Parse .txt files
- `parseMarkdown()` - Parse .md files
- `parsePdf()` - Parse .pdf files
- `parseDocx()` - Parse .docx files
- `getLatestParsedFile()` - Get latest parsed file info

### AIService
Handles AI API calls.
- `askQuestion()` - Send prompt to AI and get response
- `callGeminiAPI()` - Internal method for Gemini API

### PromptBuilderService
Builds structured prompts for AI.
- `buildPrompt()` - Combine system instruction, document, and question

## 📄 License

This is a simple MVP for internal testing. Modify and use as needed.

---

**Questions or issues?** Check the logs at `storage/logs/app.log` for debugging information.

Happy chatting! 🚀
