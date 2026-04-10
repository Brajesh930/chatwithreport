<?php

namespace App\Helpers;

use App\Config\Config;

class Logger
{
    const DEBUG = 'DEBUG';
    const INFO = 'INFO';
    const WARNING = 'WARNING';
    const ERROR = 'ERROR';

    private static $logFile = null;

    /**
     * Initialize logger
     */
    public static function init()
    {
        if (self::$logFile === null) {
            $storagePath = Config::get('STORAGE_PATH', './storage');
            self::$logFile = $storagePath . '/logs/app.log';
        }
    }

    /**
     * Log a message
     */
    public static function log($message, $level = self::INFO, $data = [])
    {
        self::init();

        $timestamp = date('Y-m-d H:i:s');
        $logMessage = "[$timestamp] [$level] $message";

        if (!empty($data)) {
            $logMessage .= " | Data: " . json_encode($data);
        }

        $logMessage .= "\n";

        // Ensure log directory exists
        $logDir = dirname(self::$logFile);
        if (!is_dir($logDir)) {
            @mkdir($logDir, 0755, true);
        }

        error_log($logMessage, 3, self::$logFile);
    }

    /**
     * Log debug message
     */
    public static function debug($message, $data = [])
    {
        self::log($message, self::DEBUG, $data);
    }

    /**
     * Log info message
     */
    public static function info($message, $data = [])
    {
        self::log($message, self::INFO, $data);
    }

    /**
     * Log warning message
     */
    public static function warning($message, $data = [])
    {
        self::log($message, self::WARNING, $data);
    }

    /**
     * Log error message
     */
    public static function error($message, $data = [])
    {
        self::log($message, self::ERROR, $data);
    }
}
