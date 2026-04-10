<?php

namespace App\Config;

class Config
{
    private static $config = [];
    private static $loaded = false;

    /**
     * Load environment configuration from .env file
     */
    public static function load()
    {
        if (self::$loaded) {
            return;
        }

        $envFile = __DIR__ . '/../../.env';
        
        if (!file_exists($envFile)) {
            // Use .env.example as fallback
            $envFile = __DIR__ . '/../../.env.example';
        }

        if (file_exists($envFile)) {
            $lines = file($envFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
            
            foreach ($lines as $line) {
                // Skip comments
                if (strpos(trim($line), '#') === 0) {
                    continue;
                }

                if (strpos($line, '=') !== false) {
                    list($key, $value) = explode('=', $line, 2);
                    $key = trim($key);
                    $value = trim($value);
                    
                    // Convert relative storage path to absolute
                    if ($key === 'STORAGE_PATH' && strpos($value, './') === 0) {
                        $value = __DIR__ . '/../../' . substr($value, 2);
                    }
                    
                    self::$config[$key] = $value;
                }
            }
        }

        self::$loaded = true;
    }

    /**
     * Get configuration value
     */
    public static function get($key, $default = null)
    {
        self::load();
        return self::$config[$key] ?? $default;
    }

    /**
     * Get all configuration
     */
    public static function all()
    {
        self::load();
        return self::$config;
    }
}
