<?php

namespace App\Services;

use App\Config\Config;
use App\Helpers\Logger;

class AIService
{
    private $provider;
    private $apiKey;
    private $model;

    public function __construct()
    {
        $this->provider = Config::get('AI_PROVIDER', 'gemini');
        $this->apiKey = Config::get('AI_API_KEY', '');
        $this->model = Config::get('AI_MODEL', 'gemini-1.5-pro');

        if (empty($this->apiKey)) {
            Logger::warning('AI API Key not configured');
        }
    }

    /**
     * Send prompt to AI and get response
     */
    public function askQuestion($prompt)
    {
        if (empty($this->apiKey)) {
            Logger::error('AI API Key not configured');
            return ['success' => false, 'error' => 'AI service not configured'];
        }

        try {
            $response = $this->callGeminiAPI($prompt);
            return $response;
        } catch (\Exception $e) {
            Logger::error('AI API error', ['error' => $e->getMessage()]);
            return ['success' => false, 'error' => 'Failed to get response from AI service'];
        }
    }

    /**
     * Call Gemini API
     */
    private function callGeminiAPI($prompt)
    {
        $url = "https://generativelanguage.googleapis.com/v1beta/models/{$this->model}:generateContent?key={$this->apiKey}";

        $payload = [
            'contents' => [
                [
                    'parts' => [
                        ['text' => $prompt]
                    ]
                ]
            ]
        ];

        $options = [
            'http' => [
                'method' => 'POST',
                'header' => "Content-Type: application/json\r\n",
                'content' => json_encode($payload),
                'timeout' => 30
            ]
        ];

        $context = stream_context_create($options);
        $response = @file_get_contents($url, false, $context);

        if ($response === false) {
            throw new \Exception('Failed to connect to Gemini API');
        }

        $decoded = json_decode($response, true);

        if (isset($decoded['error'])) {
            throw new \Exception('Gemini API error: ' . $decoded['error']['message']);
        }

        if (!isset($decoded['candidates'][0]['content']['parts'][0]['text'])) {
            throw new \Exception('Unexpected API response format');
        }

        $answer = $decoded['candidates'][0]['content']['parts'][0]['text'];

        Logger::info('AI response generated successfully');

        return ['success' => true, 'answer' => $answer];
    }
}
