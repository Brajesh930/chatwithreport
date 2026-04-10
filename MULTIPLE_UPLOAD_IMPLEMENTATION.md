# Multiple Document Upload Implementation

## Overview
The backend has been updated to support uploading multiple documents simultaneously and parsing them into a single combined text file.

## Changes Made

### 1. **Frontend (public/app.js)**
- Modified `uploadFile()` function to detect if multiple files are selected
- Updated FormData handling to support multiple files via `files[]` parameter
- Added `updateUploadStatusDisplay()` function to show selected file count
- Updated success messages to distinguish between single and multiple file uploads
- Enhanced chat message to show the count of combined documents
- Uses query parameter `?multiple=true` when uploading multiple files

### 2. **Frontend (public/index.html)**
- Added `multiple` attribute to file input element
- Updated upload section title to "Step 1: Upload Document(s)"
- Updated instructions text to indicate multiple file support
- Modified help text to show maximum size is per file

### 3. **Backend Upload Handler (api/upload.php)**
- Added logic to detect single vs. multiple file uploads
- Routes to different service methods based on upload type
- For multiple files: calls `FileUploadService::processMultiple()`
- For single file: uses existing `FileUploadService::process()`
- Calls `FileParserService::parseMultiple()` for batch processing
- Returns different response structure for multiple uploads including:
  - `uploadedCount`: Number of successfully uploaded files
  - `originalFilenames`: Array of original file names
  - `combinedParsedFilename`: Name of the combined output file

### 4. **FileUploadService (src/Services/FileUploadService.php)**
New method: `processMultiple()`
- Handles array of files from `$_FILES['files']`
- Validates each file individually:
  - Checks for upload errors
  - Validates file size
  - Validates file extension
  - Verifies it's an uploaded file
- Accumulates successfully uploaded files
- Returns:
  - Array of file paths for parsing
  - Array of original filenames
  - Total size of all files
  - Count of uploaded files
  - Array of any errors encountered

### 5. **FileParserService (src/Services/FileParserService.php)**
New method: `parseMultiple($uploadedFilePaths, $originalFilenames, $combinedFilename = null)`
- Processes multiple files in sequence
- Extracts text from each file using appropriate parser:
  - Plain Text Parser (.txt)
  - Markdown Parser (.md)
  - PDF Parser (.pdf)
  - DOCX Parser (.docx)
- Creates a combined text file with:
  - **Header section**: Combined processing report with timestamp
  - **File Summary**: List of all files with their sizes and parsers used
  - **Combined Content**: All file contents separated by clear delimiters
  - **File Headers**: Each file's content is prefixed with metadata

New method: `buildCombinedNormalizedFormat()`
- Formats the combined output with professional headers
- Includes processing timestamp
- Lists all files with their parsers and sizes
- Separates file contents with visual delimiters

New method: `formatFileSize()`
- Converts bytes to human-readable format (B, KB, MB)

## File Structure Changes

### Combined Output File Example
```
COMBINED DOCUMENT PARSING REPORT
================================================================================
Combined Processing Time: 2026-04-09 10:30:45
Total Files Processed: 3
Parsers Used: Plain Text Parser, PDF Parser, DOCX Parser
================================================================================

FILE SUMMARY:
--------------------------------------------------------------------------------
1. document1.txt (Plain Text Parser, 45.23 KB)
2. document2.pdf (PDF Parser, 234.56 KB)
3. document3.docx (DOCX Parser, 123.45 KB)
--------------------------------------------------------------------------------

COMBINED CONTENT:
================================================================================

[FILE: document1.txt]
[PARSER: Plain Text Parser]
[SIZE: 45.23 KB]
[UPLOADED: 2026-04-09 10:30:45]
--------------------------------------------------------------------------------

[Content of document1]

================================================================================

[FILE: document2.pdf]
[PARSER: PDF Parser]
[SIZE: 234.56 KB]
[UPLOADED: 2026-04-09 10:30:45]
--------------------------------------------------------------------------------

[Content of document2]

================================================================================

[FILE: document3.docx]
[PARSER: DOCX Parser]
[SIZE: 123.45 KB]
[UPLOADED: 2026-04-09 10:30:45]
--------------------------------------------------------------------------------

[Content of document3]

================================================================================
```

## API Endpoints

### Single File Upload (Existing)
```
POST /api/upload
Content-Type: multipart/form-data
Body: file (single file)
```

### Multiple Files Upload (New)
```
POST /api/upload?multiple=true
Content-Type: multipart/form-data
Body: files[] (array of files)
```

## Response Examples

### Single File Success
```json
{
  "success": true,
  "message": "File uploaded and parsed successfully",
  "data": {
    "originalFilename": "report.pdf",
    "storedFilename": "report_12345_abc123.pdf",
    "parsedFilename": "report_12345_abc123_parsed.txt",
    "fileSize": 245000,
    "fileType": "pdf",
    "parserUsed": "PDF Parser"
  }
}
```

### Multiple Files Success
```json
{
  "success": true,
  "message": "Files uploaded and combined successfully",
  "data": {
    "uploadedCount": 3,
    "originalFilenames": ["file1.txt", "file2.pdf", "file3.docx"],
    "combinedParsedFilename": "Combined_Documents_1712658645_parsed.txt",
    "totalSize": 403210,
    "parserUsed": "Plain Text Parser, PDF Parser, DOCX Parser"
  }
}
```

## Features

✅ **Single or Multiple Files**: Users can upload one file or multiple files in a single request
✅ **Batch Processing**: All files are processed and combined efficiently
✅ **Combined Output**: All parsed content is merged into one text file
✅ **Metadata Preservation**: Each file's metadata is preserved in the combined output
✅ **Error Handling**: Partial failures are handled (some files may fail while others succeed)
✅ **File Type Support**: Supports .txt, .pdf, .docx, .md files
✅ **Size Validation**: Each file is validated for size and type

## Database/Storage

- **Upload Directory**: `storage/uploads/`
- **Parsed Directory**: `storage/parsed/`
- **Naming Convention**: 
  - Single files: `{filename}_{timestamp}_{hash}_parsed.txt`
  - Combined files: `Combined_Documents_{timestamp}_parsed.txt`

## Logging

- All upload attempts are logged to `storage/logs/`
- Batch processing is logged with file count and parser information
- Errors are tracked with detailed messages per file

## Backward Compatibility

✅ All existing single-file upload functionality remains unchanged and fully compatible
✅ Existing REST API endpoints continue to work as before
✅ No breaking changes to the database or configuration

## Testing Recommendations

1. Test single file uploads (existing functionality)
2. Test multiple file uploads (2-5 files)
3. Test mixed file types in one upload
4. Test file size limits per file
5. Test error scenarios (unsupported types, oversized files)
6. Verify combined output file formatting
7. Test with large file counts (10+ files)
