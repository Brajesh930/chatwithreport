<?php

namespace App\Helpers;

class FileHelper
{
    /**
     * Generate safe filename
     */
    public static function sanitizeFilename($filename)
    {
        // Replace spaces with underscores
        $filename = preg_replace('/\s+/', '_', $filename);
        
        // Remove special characters
        $filename = preg_replace('/[^a-zA-Z0-9._-]/', '', $filename);
        
        // Remove multiple dots
        $filename = preg_replace('/\.+/', '.', $filename);
        
        return $filename;
    }

    /**
     * Get file extension
     */
    public static function getExtension($filename)
    {
        return strtolower(pathinfo($filename, PATHINFO_EXTENSION));
    }

    /**
     * Generate unique filename
     */
    public static function generateUniqueFilename($filename)
    {
        $extension = self::getExtension($filename);
        $basename = pathinfo($filename, PATHINFO_FILENAME);
        $timestamp = time();
        $random = substr(md5(uniqid()), 0, 8);
        
        return "{$basename}_{$timestamp}_{$random}.{$extension}";
    }

    /**
     * Get human readable file size
     */
    public static function formatFileSize($bytes)
    {
        $units = ['B', 'KB', 'MB', 'GB'];
        $bytes = max($bytes, 0);
        $pow = floor(($bytes ? log($bytes) : 0) / log(1024));
        $pow = min($pow, count($units) - 1);
        $bytes /= (1 << (10 * $pow));

        return round($bytes, 2) . ' ' . $units[$pow];
    }
}
