<?php

namespace App\Services;

use App\Config\Config;
use App\Helpers\FileHelper;
use App\Helpers\Logger;

class FileUploadService
{
    private $maxSize;
    private $allowedExtensions;
    private $uploadDir;

    public function __construct()
    {
        $this->maxSize = (int) Config::get('MAX_UPLOAD_SIZE', 10485760); // 10MB default
        $allowedStr = Config::get('ALLOWED_EXTENSIONS', 'txt,pdf,docx,md');
        $this->allowedExtensions = array_map('trim', explode(',', $allowedStr));
        
        $storagePath = Config::get('STORAGE_PATH', __DIR__ . '/../../storage');
        $this->uploadDir = $storagePath . '/uploads';
        
        // Ensure upload directory exists
        if (!is_dir($this->uploadDir)) {
            @mkdir($this->uploadDir, 0755, true);
        }
    }

    /**
     * Validate uploaded file
     */
    public function validate()
    {
        if (!isset($_FILES['file'])) {
            return ['valid' => false, 'error' => 'No file uploaded'];
        }

        $file = $_FILES['file'];

        // Check for upload errors
        if ($file['error'] !== UPLOAD_ERR_OK) {
            $errors = [
                UPLOAD_ERR_INI_SIZE => 'File exceeds max size',
                UPLOAD_ERR_FORM_SIZE => 'File exceeds form size limit',
                UPLOAD_ERR_PARTIAL => 'File upload was incomplete',
                UPLOAD_ERR_NO_FILE => 'No file was uploaded',
                UPLOAD_ERR_NO_TMP_DIR => 'Missing temporary folder',
                UPLOAD_ERR_CANT_WRITE => 'Failed to write file to disk',
                UPLOAD_ERR_EXTENSION => 'Upload blocked by extension'
            ];
            $error = $errors[$file['error']] ?? 'Unknown upload error';
            return ['valid' => false, 'error' => $error];
        }

        // Check file size
        if ($file['size'] > $this->maxSize) {
            return ['valid' => false, 'error' => 'File exceeds maximum size of ' . FileHelper::formatFileSize($this->maxSize)];
        }

        // Check file extension
        $extension = FileHelper::getExtension($file['name']);
        if (!in_array($extension, $this->allowedExtensions)) {
            return ['valid' => false, 'error' => 'File type not allowed. Allowed types: ' . implode(', ', $this->allowedExtensions)];
        }

        return ['valid' => true];
    }

    /**
     * Process uploaded file
     */
    public function process()
    {
        $validation = $this->validate();
        if (!$validation['valid']) {
            return ['success' => false, 'error' => $validation['error']];
        }

        $file = $_FILES['file'];
        
        // Verify upload directory is writable
        if (!is_dir($this->uploadDir)) {
            if (!@mkdir($this->uploadDir, 0755, true)) {
                return ['success' => false, 'error' => 'Cannot create upload directory: ' . $this->uploadDir];
            }
        }

        if (!is_writable($this->uploadDir)) {
            return ['success' => false, 'error' => 'Upload directory is not writable: ' . $this->uploadDir];
        }

        // Generate safe filename
        $originalName = $file['name'];
        $safeName = FileHelper::sanitizeFilename($originalName);
        $uniqueName = FileHelper::generateUniqueFilename($safeName);
        $uploadPath = $this->uploadDir . '/' . $uniqueName;

        // Debug: Log attempt
        Logger::info('Attempting to move uploaded file', [
            'tmp_name' => $file['tmp_name'],
            'target' => $uploadPath,
            'exists_tmp' => file_exists($file['tmp_name']),
            'is_uploaded' => is_uploaded_file($file['tmp_name'])
        ]);

        // Move uploaded file
        if (!is_uploaded_file($file['tmp_name'])) {
            Logger::error('File is not a valid uploaded file', ['tmp_name' => $file['tmp_name']]);
            return ['success' => false, 'error' => 'Invalid uploaded file'];
        }

        if (!move_uploaded_file($file['tmp_name'], $uploadPath)) {
            Logger::error('Failed to move uploaded file', [
                'original' => $originalName,
                'path' => $uploadPath,
                'tmp_name' => $file['tmp_name']
            ]);
            return ['success' => false, 'error' => 'Failed to save uploaded file to: ' . $uploadPath];
        }

        Logger::info('File uploaded successfully', [
            'original' => $originalName,
            'stored' => $uniqueName,
            'size' => $file['size']
        ]);

        return [
            'success' => true,
            'originalName' => $originalName,
            'storedName' => $uniqueName,
            'size' => $file['size'],
            'extension' => FileHelper::getExtension($originalName),
            'path' => $uploadPath
        ];
    }

    /**
     * Process multiple uploaded files
     */
    public function processMultiple()
    {
        if (!isset($_FILES['files'])) {
            return ['success' => false, 'error' => 'No files uploaded'];
        }

        $files = $_FILES['files'];
        $uploadedFiles = [];
        $totalSize = 0;
        $errors = [];

        // Handle both single and multiple file inputs
        $fileCount = is_array($files['name']) ? count($files['name']) : 1;

        for ($i = 0; $i < $fileCount; $i++) {
            $file = [
                'name' => is_array($files['name']) ? $files['name'][$i] : $files['name'],
                'tmp_name' => is_array($files['tmp_name']) ? $files['tmp_name'][$i] : $files['tmp_name'],
                'size' => is_array($files['size']) ? $files['size'][$i] : $files['size'],
                'error' => is_array($files['error']) ? $files['error'][$i] : $files['error'],
                'type' => is_array($files['type']) ? $files['type'][$i] : $files['type']
            ];

            // Validate individual file
            $this->validateSingleFile($file);
            
            if ($file['error'] !== UPLOAD_ERR_OK) {
                $errors[] = 'File "' . $file['name'] . '": Upload error';
                continue;
            }

            if ($file['size'] > $this->maxSize) {
                $errors[] = 'File "' . $file['name'] . '": Exceeds maximum size';
                continue;
            }

            $extension = FileHelper::getExtension($file['name']);
            if (!in_array($extension, $this->allowedExtensions)) {
                $errors[] = 'File "' . $file['name'] . '": File type not allowed';
                continue;
            }

            // Process this file
            if (!is_uploaded_file($file['tmp_name'])) {
                $errors[] = 'File "' . $file['name'] . '": Invalid upload';
                continue;
            }

            $originalName = $file['name'];
            $safeName = FileHelper::sanitizeFilename($originalName);
            $uniqueName = FileHelper::generateUniqueFilename($safeName);
            $uploadPath = $this->uploadDir . '/' . $uniqueName;

            if (!move_uploaded_file($file['tmp_name'], $uploadPath)) {
                $errors[] = 'File "' . $file['name'] . '": Failed to save';
                continue;
            }

            $uploadedFiles[] = [
                'originalName' => $originalName,
                'storedName' => $uniqueName,
                'path' => $uploadPath,
                'size' => $file['size'],
                'extension' => $extension
            ];

            $totalSize += $file['size'];

            Logger::info('File uploaded in batch', [
                'original' => $originalName,
                'stored' => $uniqueName,
                'size' => $file['size']
            ]);
        }

        if (empty($uploadedFiles)) {
            $errorMsg = !empty($errors) ? implode('; ', array_slice($errors, 0, 3)) : 'No files were uploaded successfully';
            return ['success' => false, 'error' => $errorMsg];
        }

        $originalNames = array_map(function($f) { return $f['originalName']; }, $uploadedFiles);
        $paths = array_map(function($f) { return $f['path']; }, $uploadedFiles);

        return [
            'success' => true,
            'originalNames' => $originalNames,
            'paths' => $paths,
            'totalSize' => $totalSize,
            'uploadedCount' => count($uploadedFiles),
            'errors' => $errors
        ];
    }

    /**
     * Validate a single file
     */
    private function validateSingleFile(&$file)
    {
        // File is passed by reference, validation happens before processing
    }

    /**
     * Get latest uploaded file info
     */
    public function getLatestFile()
    {
        if (!is_dir($this->uploadDir)) {
            return null;
        }

        $files = array_diff(scandir($this->uploadDir, SCANDIR_SORT_DESCENDING), ['.', '..']);
        
        if (empty($files)) {
            return null;
        }

        $latestFile = current($files);
        $filepath = $this->uploadDir . '/' . $latestFile;

        return [
            'filename' => $latestFile,
            'path' => $filepath,
            'size' => filesize($filepath),
            'extension' => FileHelper::getExtension($latestFile),
            'uploadTime' => filemtime($filepath)
        ];
    }
}
