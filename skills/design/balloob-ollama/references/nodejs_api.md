# Ollama Node.js API Reference

This reference provides comprehensive examples for integrating Ollama into Node.js projects using the official `ollama` npm package.

**IMPORTANT**: Always use streaming responses for better user experience.

## Table of Contents

1. [Package Setup](#package-setup)
2. [Installation & Setup](#installation--setup)
3. [Verifying Ollama Connection](#verifying-ollama-connection)
4. [Model Selection](#model-selection)
5. [Generate API (Text Completion)](#generate-api-text-completion)
6. [Chat API (Conversational)](#chat-api-conversational)
7. [Embeddings](#embeddings)
8. [Error Handling](#error-handling)

## Package Setup

### ES Modules (package.json)

When creating Node.js scripts for users, always use ES modules. Create a `package.json` with:

```json
{
  "type": "module",
  "dependencies": {
    "ollama": "^0.5.0"
  }
}
```

This allows using modern `import` syntax instead of `require`.

### Running Scripts

```bash
# Install dependencies
npm install

# Run script
node script.js
```

## Installation & Setup

### Installation

```bash
npm install ollama
```

### Import

```javascript
import { Ollama } from 'ollama';
```

### Configuration

**IMPORTANT**: Always ask users for their Ollama URL. Do not assume localhost.

```javascript
import { Ollama } from 'ollama';

// Create client with custom URL
const ollama = new Ollama({ host: 'http://localhost:11434' });

// Or for remote Ollama instance
// const ollama = new Ollama({ host: 'http://192.168.1.100:11434' });
```

## Verifying Ollama Connection

### Check Connection (Development)

During development, verify Ollama is running and check available models using curl:

```bash
# Check Ollama is running and get version
curl http://localhost:11434/api/version

# List available models
curl http://localhost:11434/api/tags
```

### Check Ollama Version (Node.js)

```javascript
import { Ollama } from 'ollama';

const ollama = new Ollama();

async function checkOllama() {
  try {
    // Simple way to verify connection
    const models = await ollama.list();
    console.log('✓ Connected to Ollama');
    console.log(`  Available models: ${models.models.length}`);
    return true;
  } catch (error) {
    console.log(`✗ Failed to connect to Ollama: ${error.message}`);
    return false;
  }
}

// Usage
await checkOllama();
```

## Model Selection

**IMPORTANT**: Always ask users which model they want to use. Don't assume a default.

### Listing Available Models

```javascript
import { Ollama } from 'ollama';

const ollama = new Ollama();

async function listAvailableModels() {
  const { models } = await ollama.list();
  return models.map(m => m.name);
}

// Usage - show available models to user
const available = await listAvailableModels();
console.log('Available models:');
available.forEach(model => {
  console.log(`  - ${model}`);
});
```

### Finding Models

If the user doesn't have a model installed or wants to use a different one:
- **Browse models**: Direct them to https://ollama.com/search
- **Popular choices**: llama3.2, llama3.1, mistral, phi3, qwen2.5
- **Specialized models**: codellama (coding), llava (vision), nomic-embed-text (embeddings)

### Model Selection Flow

```javascript
async function selectModel() {
  const available = await listAvailableModels();

  if (available.length === 0) {
    console.log('No models installed!');
    console.log('Visit https://ollama.com/search to find models');
    console.log('Then run: ollama pull <model-name>');
    return null;
  }

  console.log('Available models:');
  available.forEach((model, i) => {
    console.log(`  ${i + 1}. ${model}`);
  });

  // In practice, you'd ask the user to choose
  return available[0];  // Default to first available
}
```

## Generate API (Text Completion)

### Streaming Text Generation

```javascript
import { Ollama } from 'ollama';

const ollama = new Ollama();

async function generateStream(prompt, model = 'llama3.2') {
  const response = await ollama.generate({
    model: model,
    prompt: prompt,
    stream: true
  });

  for await (const chunk of response) {
    process.stdout.write(chunk.response);
  }
}

// Usage
process.stdout.write('Response: ');
await generateStream('Why is the sky blue?', 'llama3.2');
process.stdout.write('\n');
```

### With Options (Temperature, Top-P, etc.)

```javascript
async function generateWithOptions(prompt, model = 'llama3.2') {
  const response = await ollama.generate({
    model: model,
    prompt: prompt,
    stream: true,
    options: {
      temperature: 0.7,
      top_p: 0.9,
      top_k: 40,
      num_predict: 100  // Max tokens
    }
  });

  for await (const chunk of response) {
    process.stdout.write(chunk.response);
  }
}

// Usage
process.stdout.write('Response: ');
await generateWithOptions('Write a haiku about programming');
process.stdout.write('\n');
```

## Chat API (Conversational)

### Streaming Chat

```javascript
import { Ollama } from 'ollama';

const ollama = new Ollama();

async function chatStream(messages, model = 'llama3.2') {
  /*
   * Chat with a model using conversation history with streaming.
   *
   * Args:
   *   messages: Array of message objects with 'role' and 'content'
   *            role can be 'system', 'user', or 'assistant'
   */
  const response = await ollama.chat({
    model: model,
    messages: messages,
    stream: true
  });

  for await (const chunk of response) {
    process.stdout.write(chunk.message.content);
  }
}

// Usage
const messages = [
  { role: 'system', content: 'You are a helpful assistant.' },
  { role: 'user', content: 'What is the capital of France?' }
];

process.stdout.write('Response: ');
await chatStream(messages);
process.stdout.write('\n');
```

### Multi-turn Conversation

```javascript
import * as readline from 'readline';

async function conversationLoop(model = 'llama3.2') {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  const messages = [
    { role: 'system', content: 'You are a helpful assistant.' }
  ];

  const askQuestion = () => {
    rl.question('\nYou: ', async (input) => {
      if (input.toLowerCase() === 'exit' || input.toLowerCase() === 'quit') {
        rl.close();
        return;
      }

      // Add user message
      messages.push({ role: 'user', content: input });

      // Stream response
      process.stdout.write('Assistant: ');
      let fullResponse = '';

      const response = await ollama.chat({
        model: model,
        messages: messages,
        stream: true
      });

      for await (const chunk of response) {
        const content = chunk.message.content;
        process.stdout.write(content);
        fullResponse += content;
      }
      process.stdout.write('\n');

      // Add assistant response to history
      messages.push({ role: 'assistant', content: fullResponse });

      askQuestion();
    });
  };

  askQuestion();
}

// Usage
await conversationLoop();
```

## Embeddings

### Generate Embeddings

```javascript
import { Ollama } from 'ollama';

const ollama = new Ollama();

async function getEmbeddings(text, model = 'nomic-embed-text') {
  /*
   * Generate embeddings for text.
   *
   * Note: Use an embedding-specific model like 'nomic-embed-text'
   * Regular models can generate embeddings, but dedicated models work better.
   */
  const response = await ollama.embeddings({
    model: model,
    prompt: text
  });

  return response.embedding;
}

// Usage
const embedding = await getEmbeddings('Hello, world!');
console.log(`Embedding dimension: ${embedding.length}`);
console.log(`First 5 values: ${embedding.slice(0, 5)}`);
```

### Semantic Similarity

```javascript
function cosineSimilarity(vec1, vec2) {
  const dotProduct = vec1.reduce((sum, val, i) => sum + val * vec2[i], 0);
  const magnitude1 = Math.sqrt(vec1.reduce((sum, val) => sum + val * val, 0));
  const magnitude2 = Math.sqrt(vec2.reduce((sum, val) => sum + val * val, 0));
  return dotProduct / (magnitude1 * magnitude2);
}

// Usage
const text1 = 'The cat sat on the mat';
const text2 = 'A feline rested on a rug';
const text3 = 'JavaScript is a programming language';

const emb1 = await getEmbeddings(text1);
const emb2 = await getEmbeddings(text2);
const emb3 = await getEmbeddings(text3);

console.log(`Similarity 1-2: ${cosineSimilarity(emb1, emb2).toFixed(3)}`);  // High
console.log(`Similarity 1-3: ${cosineSimilarity(emb1, emb3).toFixed(3)}`);  // Low
```

## Error Handling

### Comprehensive Error Handling

```javascript
import { Ollama } from 'ollama';

const ollama = new Ollama();

async function* safeGenerateStream(prompt, model = 'llama3.2') {
  try {
    const response = await ollama.generate({
      model: model,
      prompt: prompt,
      stream: true
    });

    for await (const chunk of response) {
      yield chunk.response;
    }

  } catch (error) {
    // Model not found or other API errors
    if (error.message.toLowerCase().includes('not found')) {
      console.log(`\n✗ Model '${model}' not found`);
      console.log(`  Run: ollama pull ${model}`);
      console.log(`  Or browse models at: https://ollama.com/search`);
    } else if (error.code === 'ECONNREFUSED') {
      console.log('\n✗ Connection failed. Is Ollama running?');
      console.log('  Start Ollama with: ollama serve');
    } else {
      console.log(`\n✗ Unexpected error: ${error.message}`);
    }
  }
}

// Usage
process.stdout.write('Response: ');
for await (const token of safeGenerateStream('Hello, world!', 'llama3.2')) {
  process.stdout.write(token);
}
process.stdout.write('\n');
```

### Checking Model Availability

```javascript
async function ensureModelAvailable(model) {
  try {
    const { models } = await ollama.list();
    const modelNames = models.map(m => m.name);

    if (!modelNames.includes(model)) {
      console.log(`Model '${model}' not available locally`);
      console.log(`Available models: ${modelNames.join(', ')}`);
      console.log(`\nTo download: ollama pull ${model}`);
      console.log(`Browse models: https://ollama.com/search`);
      return false;
    }

    return true;

  } catch (error) {
    console.log(`Failed to check models: ${error.message}`);
    return false;
  }
}

// Usage
if (await ensureModelAvailable('llama3.2')) {
  // Proceed with using the model
}
```

## Best Practices

1. **Always Use Streaming**: Stream responses for better user experience
2. **Ask About Models**: Don't assume models - ask users which model they want to use
3. **Verify Connection**: Check Ollama connection during development with curl
4. **Error Handling**: Handle model not found and connection errors gracefully
5. **Context Management**: Manage conversation history to avoid token limits
6. **Model Selection**: Direct users to https://ollama.com/search to find models
7. **Custom Hosts**: Always ask users for their Ollama URL, don't assume localhost
8. **ES Modules**: Use `"type": "module"` in package.json for modern import syntax

## Complete Example Script

```javascript
// script.js
import { Ollama } from 'ollama';

const ollama = new Ollama();

async function main() {
  const model = 'llama3.2';

  // Check connection
  try {
    await ollama.list();
  } catch (error) {
    console.log(`Error: Cannot connect to Ollama - ${error.message}`);
    console.log('Make sure Ollama is running: ollama serve');
    return;
  }

  // Stream a response
  console.log('Asking about JavaScript...\n');

  const response = await ollama.generate({
    model: model,
    prompt: 'Explain JavaScript in one sentence',
    stream: true
  });

  process.stdout.write('Response: ');
  for await (const chunk of response) {
    process.stdout.write(chunk.response);
  }
  process.stdout.write('\n');
}

main();
```

### package.json

```json
{
  "type": "module",
  "dependencies": {
    "ollama": "^0.5.0"
  }
}
```

### Running

```bash
npm install
node script.js
```
