<?php

namespace App\Helpers;

class ResponseBuilder
{
    /**
     * Build success response
     */
    public static function success($message = 'Success', $data = [])
    {
        return [
            'success' => true,
            'message' => $message,
            'data' => $data
        ];
    }

    /**
     * Build error response
     */
    public static function error($message = 'Error', $code = 400)
    {
        http_response_code($code);
        return [
            'success' => false,
            'message' => $message,
            'code' => $code
        ];
    }

    /**
     * Return JSON response and exit
     */
    public static function json($response)
    {
        header('Content-Type: application/json');
        echo json_encode($response);
        exit;
    }
}
