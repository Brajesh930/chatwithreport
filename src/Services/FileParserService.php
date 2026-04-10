<?php

namespace App\Services;

use App\Config\Config;
use App\Helpers\Logger;

class FileParserService
{
    private $uploadDir;
    private $parsedDir;

    public function __construct()
    {
        $storagePath = Config::get('STORAGE_PATH', __DIR__ . '/../../storage');
        $this->uploadDir = $storagePath . '/uploads';
        $this->parsedDir = $storagePath . '/parsed';

        // Create parsed directory if needed
        if (!is_dir($this->parsedDir)) {
            @mkdir($this->parsedDir, 0755, true);
        }
    }

    /**
     * Parse uploaded file and save as normalized text
     */
    public function parse($uploadedFilePath, $originalFilename)
    {
        if (!file_exists($uploadedFilePath)) {
            return ['success' => false, 'error' => 'Uploaded file not found'];
        }

        $extension = strtolower(pathinfo($originalFilename, PATHINFO_EXTENSION));
        
        // Extract text based on file type
        $text = null;
        $parserUsed = '';
        $extractionNote = '';

        try {
            switch ($extension) {
                case 'txt':
                    $text = $this->parseTxt($uploadedFilePath);
                    $parserUsed = 'Plain Text Parser';
                    break;
                case 'md':
                    $text = $this->parseMarkdown($uploadedFilePath);
                    $parserUsed = 'Markdown Parser';
                    break;
                case 'pdf':
                    $result = $this->parsePdf($uploadedFilePath);
                    $text = $result['text'];
                    $parserUsed = 'PDF Parser';
                    $extractionNote = $result['note'] ?? '';
                    break;
                case 'docx':
                    $result = $this->parseDocx($uploadedFilePath);
                    $text = $result['text'];
                    $parserUsed = 'DOCX Parser';
                    $extractionNote = $result['note'] ?? '';
                    break;
                default:
                    return ['success' => false, 'error' => 'Unsupported file format: ' . $extension];
            }
        } catch (\Exception $e) {
            Logger::error('Parse error for file: ' . $originalFilename, ['error' => $e->getMessage()]);
            return ['success' => false, 'error' => 'Failed to parse file: ' . $e->getMessage()];
        }

        if ($text === null || $text === '') {
            return ['success' => false, 'error' => 'No text could be extracted from file'];
        }

        // Create normalized text file
        $fileSize = filesize($uploadedFilePath);
        $uploadTime = date('Y-m-d H:i:s', filemtime($uploadedFilePath));
        $storedFileName = pathinfo($uploadedFilePath, PATHINFO_BASENAME);

        $normalizedContent = $this->buildNormalizedFormat(
            $originalFilename,
            $storedFileName,
            $extension,
            $uploadTime,
            $fileSize,
            $parserUsed,
            $text,
            $extractionNote
        );

        // Save normalized file
        $parsedFilename = pathinfo($storedFileName, PATHINFO_FILENAME) . '_parsed.txt';
        $parsedFilePath = $this->parsedDir . '/' . $parsedFilename;

        if (!file_put_contents($parsedFilePath, $normalizedContent)) {
            Logger::error('Failed to save parsed file', ['path' => $parsedFilePath]);
            return ['success' => false, 'error' => 'Failed to save parsed file'];
        }

        Logger::info('File parsed successfully', [
            'original' => $originalFilename,
            'parsed' => $parsedFilename,
            'parser' => $parserUsed
        ]);

        return [
            'success' => true,
            'originalFilename' => $originalFilename,
            'parsedFilename' => $parsedFilename,
            'parserUsed' => $parserUsed,
            'parsedPath' => $parsedFilePath
        ];
    }

    /**
     * Parse multiple files and combine them into a single file
     */
    public function parseMultiple($uploadedFilePaths, $originalFilenames, $combinedFilename = null)
    {
        if (empty($uploadedFilePaths)) {
            return ['success' => false, 'error' => 'No files to parse'];
        }

        $combinedText = "";
        $fileDetails = [];
        $parsers = [];
        $timestamp = date('Y-m-d H:i:s');

        // Parse each file and collect content
        foreach ($uploadedFilePaths as $index => $filePath) {
            if (!file_exists($filePath)) {
                Logger::warning('File not found during batch parsing', ['path' => $filePath]);
                continue;
            }

            $originalFilename = $originalFilenames[$index] ?? 'Unknown';
            $extension = strtolower(pathinfo($originalFilename, PATHINFO_EXTENSION));
            $fileSize = filesize($filePath);
            $uploadTime = date('Y-m-d H:i:s', filemtime($filePath));

            // Extract text based on file type
            $text = null;
            $parserUsed = '';

            try {
                switch ($extension) {
                    case 'txt':
                        $text = $this->parseTxt($filePath);
                        $parserUsed = 'Plain Text Parser';
                        break;
                    case 'md':
                        $text = $this->parseMarkdown($filePath);
                        $parserUsed = 'Markdown Parser';
                        break;
                    case 'pdf':
                        $result = $this->parsePdf($filePath);
                        $text = $result['text'];
                        $parserUsed = 'PDF Parser';
                        break;
                    case 'docx':
                        $result = $this->parseDocx($filePath);
                        $text = $result['text'];
                        $parserUsed = 'DOCX Parser';
                        break;
                    default:
                        Logger::warning('Unsupported file format in batch', ['filename' => $originalFilename]);
                        continue 2;
                }
            } catch (\Exception $e) {
                Logger::error('Parse error in batch', ['filename' => $originalFilename, 'error' => $e->getMessage()]);
                continue;
            }

            if ($text === null || $text === '') {
                Logger::warning('No text extracted from file', ['filename' => $originalFilename]);
                continue;
            }

            // Add separator and file header
            if (!empty($combinedText)) {
                $combinedText .= "\n" . str_repeat("=", 80) . "\n";
            }

            $combinedText .= "\n[FILE: $originalFilename]\n";
            $combinedText .= "[PARSER: $parserUsed]\n";
            $combinedText .= "[SIZE: " . $this->formatFileSize($fileSize) . "]\n";
            $combinedText .= "[UPLOADED: $uploadTime]\n";
            $combinedText .= str_repeat("-", 80) . "\n\n";
            $combinedText .= $text . "\n";

            $fileDetails[] = [
                'filename' => $originalFilename,
                'parser' => $parserUsed,
                'size' => $fileSize
            ];

            if (!in_array($parserUsed, $parsers)) {
                $parsers[] = $parserUsed;
            }
        }

        if (empty($fileDetails)) {
            return ['success' => false, 'error' => 'No files could be parsed successfully'];
        }

        // Create combined normalized content
        $parsedFilename = $combinedFilename ?? 'Combined_Documents_' . time() . '_parsed.txt';
        if (substr($parsedFilename, -4) !== '.txt') {
            $parsedFilename .= '_parsed.txt';
        } elseif (strpos($parsedFilename, '_parsed.txt') === false) {
            $parsedFilename = str_replace('.txt', '_parsed.txt', $parsedFilename);
        }

        $normalizedContent = $this->buildCombinedNormalizedFormat(
            $fileDetails,
            $parsers,
            count($fileDetails),
            $combinedText,
            $timestamp
        );

        // Save combined file
        $parsedFilePath = $this->parsedDir . '/' . $parsedFilename;

        if (!file_put_contents($parsedFilePath, $normalizedContent)) {
            Logger::error('Failed to save combined parsed file', ['path' => $parsedFilePath]);
            return ['success' => false, 'error' => 'Failed to save combined parsed file'];
        }

        Logger::info('Multiple files parsed and combined successfully', [
            'fileCount' => count($fileDetails),
            'combinedFile' => $parsedFilename,
            'parsers' => $parsers
        ]);

        return [
            'success' => true,
            'parsedFilename' => $parsedFilename,
            'parserUsed' => implode(', ', $parsers),
            'fileCount' => count($fileDetails),
            'parsedPath' => $parsedFilePath
        ];
    }

    /**
     * Build normalized format for combined files
     */
    private function buildCombinedNormalizedFormat(&$fileDetails, &$parsers, $fileCount, &$text, $timestamp)
    {
        $header = "COMBINED DOCUMENT PARSING REPORT\n";
        $header .= "=" . str_repeat("=", 78) . "\n";
        $header .= "Combined Processing Time: $timestamp\n";
        $header .= "Total Files Processed: $fileCount\n";
        $header .= "Parsers Used: " . implode(', ', $parsers) . "\n";
        $header .= "=" . str_repeat("=", 78) . "\n\n";

        $header .= "FILE SUMMARY:\n";
        $header .= "-" . str_repeat("-", 78) . "\n";
        foreach ($fileDetails as $index => $detail) {
            $header .= ($index + 1) . ". " . $detail['filename'] . " (" . $detail['parser'] . ", " . $this->formatFileSize($detail['size']) . ")\n";
        }
        $header .= "-" . str_repeat("-", 78) . "\n\n";

        $header .= "COMBINED CONTENT:\n";
        $header .= "=" . str_repeat("=", 78) . "\n\n";

        return $header . $text . "\n\n" . "=" . str_repeat("=", 78) . "\n";
    }

    /**
     * Format file size in human readable format
     */
    private function formatFileSize($bytes)
    {
        if ($bytes < 1024) return $bytes . ' B';
        if ($bytes < 1024 * 1024) return round($bytes / 1024, 2) . ' KB';
        return round($bytes / (1024 * 1024), 2) . ' MB';
    }

    /**
     * Parse plain text file
     */
    private function parseTxt($filePath)
    {
        return file_get_contents($filePath);
    }

    /**
     * Parse markdown file
     */
    private function parseMarkdown($filePath)
    {
        return file_get_contents($filePath);
    }

    /**
     * Parse PDF file
     */
    private function parsePdf($filePath)
    {
        $text = '';
        $note = 'Basic PDF extraction used (some content may be lost)';

        try {
            $text = $this->basicPdfTextExtraction($filePath);
        } catch (\Exception $e) {
            $note = 'PDF parsing had issues: ' . $e->getMessage();
        }

        return ['text' => $text, 'note' => $note];
    }

    /**
     * Basic PDF text extraction as fallback
     */
    private function basicPdfTextExtraction($filePath)
    {
        // Simple regex-based extraction for basic PDFs
        $content = file_get_contents($filePath);
        
        // Remove binary PDF markers
        $content = preg_replace('/%.*/', '', $content);
        $content = preg_replace('/[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]/', '', $content);
        
        return trim($content);
    }

    /**
     * Parse DOCX file
     */
    private function parseDocx($filePath)
    {
        $text = '';
        $note = '';

        try {
            // Check if ZipArchive is available
            if (!class_exists('ZipArchive')) {
                $note = 'ZipArchive not available - extracting text as fallback';
                $text = $this->basicDocxTextExtraction($filePath);
            } else {
                $text = $this->basicDocxTextExtraction($filePath);
            }
        } catch (\Exception $e) {
            $note = 'DOCX parsing had issues: ' . $e->getMessage();
        }

        return ['text' => $text, 'note' => $note];
    }

    /**
     * Basic DOCX text extraction as fallback
     */
    private function basicDocxTextExtraction($filePath)
    {
        $text = '';
        
        // If ZipArchive is available, use it
        if (class_exists('ZipArchive')) {
            try {
                $zip = new \ZipArchive();
                if ($zip->open($filePath) === true) {
                    $xml = $zip->getFromName('word/document.xml');
                    $zip->close();

                    if ($xml !== false) {
                        // Extract text from XML
                        $xml = preg_replace('/<[^>]*>/', ' ', $xml);
                        $text = html_entity_decode($xml, ENT_QUOTES, 'UTF-8');
                        $text = preg_replace('/\s+/', ' ', trim($text));
                    }
                }
            } catch (\Exception $e) {
                // Try fallback to binary extraction
                $text = $this->extractTextFromBinary($filePath);
            }
        } else {
            // ZipArchive not available, try binary extraction
            $text = $this->extractTextFromBinary($filePath);
        }
        
        return $text;
    }

    /**
     * Extract text from binary DOCX file without ZipArchive
     */
    private function extractTextFromBinary($filePath)
    {
        $text = '';
        
        try {
            $content = file_get_contents($filePath);
            if ($content === false) {
                return '';
            }

            // Remove binary/non-printable characters but keep text
            $content = preg_replace('/[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]/', '', $content);
            
            // Look for text patterns in DOCX (they're typically English text in XML)
            // Extract common readable text
            $matches = preg_findall('/>[^<]{4,}</mi', $content, $m);
            
            if (!empty($matches[0])) {
                foreach ($matches[0] as $match) {
                    $clean = trim(strip_tags($match));
                    if (!empty($clean) && strlen($clean) > 3) {
                        $text .= $clean . ' ';
                    }
                }
            }
            
            // Fallback: just get all non-XML content
            if (empty($text)) {
                $text = preg_replace('/<[^>]*>/', ' ', $content);
                $text = substr($text, 0, 1000); // Limit to 1000 chars
            }
        } catch (\Exception $e) {
            // Silent fail
        }
        
        return trim($text);
    }

    /**
     * Build normalized text format
     */
    private function buildNormalizedFormat(
        $originalFilename,
        $storedFilename,
        $extension,
        $uploadTime,
        $fileSize,
        $parserUsed,
        $text,
        $extractionNote
    ) {
        $output = "==================================================\n";
        $output .= "DOCUMENT NORMALIZED TEXT\n";
        $output .= "==================================================\n\n";

        $output .= "[METADATA]\n";
        $output .= "Original File Name: " . $originalFilename . "\n";
        $output .= "Stored File Name: " . $storedFilename . "\n";
        $output .= "File Type: " . $extension . "\n";
        $output .= "Upload Time: " . $uploadTime . "\n";
        $output .= "File Size: " . $this->formatFileSize($fileSize) . "\n";
        $output .= "Parser Used: " . $parserUsed . "\n";
        
        if ($extractionNote) {
            $output .= "Extraction Note: " . $extractionNote . "\n";
        }

        $output .= "\n[CONTENT]\n";
        $output .= trim($text) . "\n";

        $output .= "\n[END OF DOCUMENT]\n";

        return $output;
    }

    /**
     * Format file size
     */
    private function formatFileSize($bytes)
    {
        $units = ['B', 'KB', 'MB', 'GB'];
        $bytes = max($bytes, 0);
        $pow = floor(($bytes ? log($bytes) : 0) / log(1024));
        $pow = min($pow, count($units) - 1);
        $bytes /= (1 << (10 * $pow));

        return round($bytes, 2) . ' ' . $units[$pow];
    }

    /**
     * Get latest parsed file
     */
    public function getLatestParsedFile()
    {
        if (!is_dir($this->parsedDir)) {
            return null;
        }

        $files = array_diff(scandir($this->parsedDir, SCANDIR_SORT_DESCENDING), ['.', '..']);
        
        if (empty($files)) {
            return null;
        }

        $latestFile = current($files);
        $filepath = $this->parsedDir . '/' . $latestFile;

        return [
            'filename' => $latestFile,
            'path' => $filepath,
            'size' => filesize($filepath),
            'uploadTime' => filemtime($filepath)
        ];
    }
}
