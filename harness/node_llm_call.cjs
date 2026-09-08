// Node.js LLM caller — wraps any LLM API (Anthropic-native or OpenAI-compatible)
const fs = require('fs');
const https = require('https');
const http = require('http');

const inputFile = process.argv[2];
if (!inputFile) {
  console.error('Usage: node node_llm_call.cjs <input.json>');
  process.exit(1);
}

const config = JSON.parse(fs.readFileSync(inputFile, 'utf8'));
const { model, messages, tools, max_tokens, api_key } = config;

// Determine provider and key — prefer explicit api_key from input, then env fallback
const providers = {
  bynara: { baseUrl: 'https://router.bynara.id', modelKey: null, defaultModel: 'agnes-2.5-flash', apiType: 'anthropic' },
  groq: { baseUrl: 'https://api.groq.com/openai/v1', modelKey: 'GROQ_API_KEY', defaultModel: 'llama-3.1-8b-instant', apiType: 'openai' },
  cerebras: { baseUrl: 'https://api.cerebras.ai/v1', modelKey: 'CEREBRAS_API_KEY', defaultModel: 'gpt-oss-120b', apiType: 'openai' },
  gemini: { baseUrl: 'https://generativelanguage.googleapis.com/v1beta/openai', modelKey: 'GEMINI_API_KEY', defaultModel: 'gemini-2.0-flash-exp', apiType: 'openai' },
  openrouter: { baseUrl: 'https://openrouter.ai/api/v1', modelKey: 'OPENROUTER_API_KEY', defaultModel: 'google/gemma-4-31b-it:free', apiType: 'openai' },
};

let provider = 'bylby';
let apiKey = api_key || '';
let baseUrl = 'https://router.bynara.id';
let apiType = 'anthropic';
let finalModel = model || 'agnes-2.5-flash';

// Fallback chain if no explicit api_key provided
if (!apiKey || apiKey.length < 10) {
  for (const [name, cfg] of Object.entries(providers)) {
    if (cfg.modelKey === null) continue;
    const key = process.env[cfg.modelKey];
    if (key && key.length > 10) {
      provider = name;
      apiKey = key;
      baseUrl = cfg.baseUrl;
      apiType = cfg.apiType;
      finalModel = model || cfg.defaultModel;
      break;
    }
  }
  // Try common env keys as last resort
  if (!apiKey || apiKey.length < 10) {
    for (const keyName of ['ANTHROPIC_API_KEY', 'OPENAI_API_KEY']) {
      const val = process.env[keyName];
      if (val && val.length > 10) {
        apiKey = val;
        break;
      }
    }
  }
}

if (!apiKey || apiKey.length < 10) {
  console.log(JSON.stringify({ error: 'No API key found. Pass api_key in input JSON or set ANTHROPIC_API_KEY env var.' }));
  process.exit(1);
}

// --- Anthropic-native format (router.bynara.id) ---
function makeAnthropicRequest() {
  const anthropicMessages = messages.map(m => ({ role: m.role, content: m.content }));
  const body = {
    model: finalModel,
    max_tokens: max_tokens || 2000,
    messages: anthropicMessages,
  };
  if (tools && tools.length > 0) {
    body.tools = tools.map(t => ({
      name: t.name,
      description: t.description,
      input_schema: t.input_schema,
    }));
  }
  // Extract system prompt if present
  const sysMsg = anthropicMessages.find(m => m.role === 'system');
  if (sysMsg) {
    body.system = sysMsg.content;
  }

  const bodyStr = JSON.stringify(body);
  const reqOptions = {
    hostname: 'router.bynara.id',
    port: 443,
    path: '/v1/messages',
    method: 'POST',
    headers: {
      'x-api-key': apiKey,
      'Content-Type': 'application/json',
      'anthropic-version': '2023-06-01',
      'Content-Length': Buffer.byteLength(bodyStr),
    },
  };

  const req = https.request(reqOptions, (res) => {
    let data = '';
    res.on('data', chunk => data += chunk);
    res.on('end', () => {
      try {
        const result = JSON.parse(data);
        if (result.type === 'error') {
          console.log(JSON.stringify({ error: result.message || JSON.stringify(result) }));
          return;
        }
        const textParts = (result.content || [])
          .filter(b => b.type === 'text')
          .map(b => b.text)
          .join('\n');
        const toolCalls = (result.content || [])
          .filter(b => b.type === 'tool_use')
          .map(b => ({ id: b.id, name: b.name, input: b.input || {} }));
        const done = result.stop_reason !== 'tool_use';
        const usage = result.usage || {};
        console.log(JSON.stringify({
          text: textParts,
          tool_calls: toolCalls,
          done,
          usage: {
            input_tokens: usage.input_tokens || 0,
            output_tokens: usage.output_tokens || 0,
          }
        }));
      } catch(e) {
        console.log(JSON.stringify({ error: 'Failed to parse response: ' + e.message, raw: data.substring(0, 200) }));
      }
    });
  });
  req.on('error', e => console.log(JSON.stringify({ error: e.message })));
  req.write(bodyStr);
  req.end();
}

// --- OpenAI-compatible format ---
function makeOpenAIRequest() {
  const openaiMessages = messages.filter(m => m.role !== 'system');
  const openaiSystem = messages.find(m => m.role === 'system');

  const body = {
    model: finalModel,
    messages: openaiSystem ? [{ role: 'system', content: openaiSystem.content }, ...openaiMessages] : openaiMessages,
    max_tokens: max_tokens || 2000,
  };
  if (tools && tools.length > 0) {
    body.tools = tools.map(t => ({
      type: 'function',
      function: { name: t.name, description: t.description, parameters: t.input_schema }
    }));
  }

  const bodyStr = JSON.stringify(body);
  const parsedUrl = new URL(baseUrl + '/chat/completions');
  const options = {
    hostname: parsedUrl.hostname,
    port: 443,
    path: parsedUrl.pathname,
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(bodyStr),
    }
  };

  const mod = parsedUrl.protocol === 'https:' ? https : http;
  const req = mod.request(options, (res) => {
    let data = '';
    res.on('data', chunk => data += chunk);
    res.on('end', () => {
      try {
        const result = JSON.parse(data);
        if (result.error) {
          console.log(JSON.stringify({ error: result.error.message || JSON.stringify(result.error) }));
          return;
        }
        const msg = result.choices?.[0]?.message || {};
        const text = msg.content || '';
        const toolCalls = (msg.tool_calls || []).map(tc => ({
          id: tc.id,
          name: tc.function.name,
          input: JSON.parse(tc.function.arguments || '{}')
        }));
        console.log(JSON.stringify({
          text,
          tool_calls: toolCalls,
          done: !toolCalls.length,
          usage: {
            input_tokens: result.usage?.prompt_tokens || 0,
            output_tokens: result.usage?.completion_tokens || 0,
          }
        }));
      } catch(e) {
        console.log(JSON.stringify({ error: 'Failed to parse response: ' + e.message, raw: data.substring(0, 200) }));
      }
    });
  });
  req.on('error', e => console.log(JSON.stringify({ error: e.message })));
  req.write(bodyStr);
  req.end();
}

if (apiType === 'anthropic') {
  makeAnthropicRequest();
} else {
  makeOpenAIRequest();
}
