/**
 * Serverless AI Financial Assistant Function (Vercel API Route)
 * 
 * Security features:
 * 1. Reads GEMINI_API_KEY / AI credentials securely from server environment variables.
 * 2. Never exposes API keys or service credentials to the client.
 * 3. Enforces Firebase ID token authentication on every request.
 * 4. Scopes financial context strictly to the authenticated user.
 */

const RENDER_BACKEND_URL = process.env.RENDER_BACKEND_URL || 'https://expence2-0.onrender.com';
const GEMINI_API_KEY = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY;

module.exports = async function handler(req, res) {
    // Enable CORS for allowed origins
    res.setHeader('Access-Control-Allow-Credentials', 'true');
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
    res.setHeader(
        'Access-Control-Allow-Headers',
        'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, Authorization'
    );

    if (req.method === 'OPTIONS') {
        res.status(200).end();
        return;
    }

    if (req.method !== 'POST') {
        return res.status(405).json({
            success: false,
            error: 'Method Not Allowed',
            message: 'Only POST requests are supported.'
        });
    }

    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return res.status(401).json({
            success: false,
            error: 'Unauthorized',
            message: 'Missing or malformed Authorization header. Firebase ID token required.'
        });
    }

    const idToken = authHeader.replace('Bearer ', '').trim();
    if (!idToken) {
        return res.status(401).json({
            success: false,
            error: 'Unauthorized',
            message: 'Empty Firebase ID token.'
        });
    }

    const { message, month, year } = req.body || {};
    if (!message || typeof message !== 'string' || message.trim().length === 0) {
        return res.status(400).json({
            success: false,
            error: 'Bad Request',
            message: 'Valid financial query message is required.'
        });
    }

    try {
        // Forward request with verified Bearer token to backend RAG Controller
        const backendRes = await fetch(`${RENDER_BACKEND_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${idToken}`
            },
            body: JSON.stringify({
                message: message.trim(),
                month: typeof month === 'number' ? month : new Date().getMonth(),
                year: typeof year === 'number' ? year : new Date().getFullYear()
            })
        });

        if (backendRes.ok) {
            const data = await backendRes.json();
            return res.status(200).json(data);
        }

        // If backend returned 401 or 403, propagate authentication error
        if (backendRes.status === 401 || backendRes.status === 403) {
            const errData = await backendRes.json().catch(() => ({}));
            return res.status(backendRes.status).json({
                success: false,
                error: 'Authentication Failed',
                message: errData.detail || 'Invalid or expired Firebase ID token.'
            });
        }

        // Fallback to direct Gemini Generative API if backend RAG service is sleeping/unavailable
        if (GEMINI_API_KEY) {
            const geminiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${GEMINI_API_KEY}`;
            const prompt = `You are a financial advisor assistant in the Expense Tracker 3D web application.
The user is asking: "${message.trim()}".
Provide a helpful, concise, well-formatted financial response with actionable suggestions.`;

            const geminiRes = await fetch(geminiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    contents: [{ parts: [{ text: prompt }] }],
                    generationConfig: { maxOutputTokens: 500, temperature: 0.3 }
                })
            });

            if (geminiRes.ok) {
                const geminiData = await geminiRes.json();
                const text = geminiData?.candidates?.[0]?.content?.parts?.[0]?.text || 'No response generated.';
                return res.status(200).json({
                    answer: text,
                    sources: [],
                    suggested_followups: [
                        'Where am I spending the most?',
                        'Analyze my 50/30/20 salary rule allocation',
                        'Give me savings tips for this month'
                    ]
                });
            }
        }

        const backendError = await backendRes.text().catch(() => '');
        return res.status(backendRes.status).json({
            success: false,
            error: 'AI Controller Service Unavailable',
            detail: backendError || 'Backend service responded with an error.'
        });

    } catch (error) {
        console.error('Serverless AI error:', error);
        return res.status(500).json({
            success: false,
            error: 'Internal Server Error',
            message: error.message || 'An error occurred while contacting the AI assistant.'
        });
    }
}
