<?php

namespace App\Services;

class PromptBuilderService
{
    /**
     * Build complete prompt for AI
     */
    public static function buildPrompt($documentText, $userQuestion)
    {
        $systemInstruction = "You are a document question-answering assistant.
Answer only from the provided document.
If the answer is not clearly stated in the document, say:
\"This is not clearly stated in the uploaded document.\"
Keep answers clear, concise, and professional.";

        $prompt = $systemInstruction . "\n\n";
        $prompt .= "DOCUMENT CONTENT:\n";
        $prompt .= "==================================================\n";
        $prompt .= $documentText . "\n";
        $prompt .= "==================================================\n\n";
        $prompt .= "USER QUESTION:\n";
        $prompt .= $userQuestion . "\n\n";
        $prompt .= "ANSWER:\n";

        return $prompt;
    }
}
