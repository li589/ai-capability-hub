# Ollama Python API Reference

This reference provides comprehensive examples for integrating Ollama into Python projects using the official `ollama` Python library.

**IMPORTANT**: Always use streaming responses for better user experience.

## Table of Contents

1. [PEP 723 Inline Script Metadata](#pep-723-inline-script-metadata)
2. [Installation & Setup](#installation--setup)
3. [Verifying Ollama Connection](#verifying-ollama-connection)
4. [Model Selection](#model-selection)
5. [Generate API (Text Completion)](#generate-api-text-completion)
6. [Chat API (Conversational)](#chat-api-conversational)
7. [Embeddings](#embeddings)
8. [Error Handling](#error-handling)

## Installation & Setup

### Installation

```bash
pip install ollama
```

### Import

```python
import ollama
```

### Configuration

**IMPORTANT**: Always ask users for their Ollama URL. Do not assume localhost.

```python
# Create client with custom URL
client = ollama.Client(host='http://localhost:11434')

# Or for remote Ollama instance
# client = ollama.Client(host='http://192.168.1.100:11434')
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

### Check Ollama Version (Python)

```python
import ollama

def check_ollama():
    """Check if Ollama is running."""
    try:
        # Simple way to verify connection
        models = ollama.list()
        print(f"✓ Connected to Ollama")
        print(f"  Available models: {len(models.get('models', []))}")
        return True
    except Exception as e:
        print(f"✗ Failed to connect to Ollama: {e}")
        return False

# Usage
check_ollama()
```

## Model Selection

**IMPORTANT**: Always ask users which model they want to use. Don't assume a default.

### Listing Available Models

```python
import ollama

def list_available_models():
    """List all locally installed models."""
    models = ollama.list()
    return [model['name'] for model in models.get('models', [])]

# Usage - show available models to user
available = list_available_models()
print("Available models:")
for model in available:
    print(f"  - {model}")
```

### Finding Models

If the user doesn't have a model installed or wants to use a different one:
- **Browse models**: Direct them to https://ollama.com/search
- **Popular choices**: llama3.2, llama3.1, mistral, phi3, qwen2.5
- **Specialized models**: codellama (coding), llava (vision), nomic-embed-text (embeddings)

### Model Selection Flow

```python
def select_model():
    """Interactive model selection."""
    available = list_available_models()

    if not available:
        print("No models installed!")
        print("Visit https://ollama.com/search to find models")
        print("Then run: ollama pull <model-name>")
        return None

    print("Available models:")
    for i, model in enumerate(available, 1):
        print(f"  {i}. {model}")

    # In practice, you'd ask the user to choose
    return available[0]  # Default to first available
```

## Generate API (Text Completion)

### Streaming Text Generation

```python
import ollama

def generate_stream(prompt, model="llama3.2"):
    """Generate text with streaming (yields tokens as they arrive)."""
    stream = ollama.generate(
        model=model,
        prompt=prompt,
        stream=True
    )

    for chunk in stream:
        yield chunk['response']

# Usage
print("Response: ", end="", flush=True)
for token in generate_stream("Why is the sky blue?", model="llama3.2"):
    print(token, end="", flush=True)
print()
```

### With Options (Temperature, Top-P, etc.)

```python
def generate_with_options(prompt, model="llama3.2"):
    """Generate with custom sampling parameters."""
    stream = ollama.generate(
        model=model,
        prompt=prompt,
        stream=True,
        options={
            'temperature': 0.7,
            'top_p': 0.9,
            'top_k': 40,
            'num_predict': 100  # Max tokens
        }
    )

    for chunk in stream:
        yield chunk['response']

# Usage
print("Response: ", end="", flush=True)
for token in generate_with_options("Write a haiku about programming"):
    print(token, end="", flush=True)
print()
```

## Chat API (Conversational)

### Streaming Chat

```python
import ollama

def chat_stream(messages, model="llama3.2"):
    """
    Chat with a model using conversation history with streaming.

    Args:
        messages: List of message dicts with 'role' and 'content'
                 role can be 'system', 'user', or 'assistant'
    """
    stream = ollama.chat(
        model=model,
        messages=messages,
        stream=True
    )

    for chunk in stream:
        yield chunk['message']['content']

# Usage
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the capital of France?"}
]

print("Response: ", end="", flush=True)
for token in chat_stream(messages):
    print(token, end="", flush=True)
print()
```

### Multi-turn Conversation

```python
def conversation_loop(model="llama3.2"):
    """Interactive chat loop with streaming responses."""
    messages = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['exit', 'quit']:
            break

        # Add user message
        messages.append({"role": "user", "content": user_input})

        # Stream response
        print("Assistant: ", end="", flush=True)
        full_response = ""
        for token in chat_stream(messages, model):
            print(token, end="", flush=True)
            full_response += token
        print()

        # Add assistant response to history
        messages.append({"role": "assistant", "content": full_response})

# Usage
conversation_loop()
```


## Embeddings

### Generate Embeddings

```python
import ollama

def get_embeddings(text, model="nomic-embed-text"):
    """
    Generate embeddings for text.

    Note: Use an embedding-specific model like 'nomic-embed-text'
    Regular models can generate embeddings, but dedicated models work better.
    """
    response = ollama.embeddings(
        model=model,
        prompt=text
    )
    return response['embedding']

# Usage
embedding = get_embeddings("Hello, world!")
print(f"Embedding dimension: {len(embedding)}")
print(f"First 5 values: {embedding[:5]}")
```

### Semantic Similarity

```python
import math

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors."""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    return dot_product / (magnitude1 * magnitude2)

# Usage
text1 = "The cat sat on the mat"
text2 = "A feline rested on a rug"
text3 = "Python is a programming language"

emb1 = get_embeddings(text1)
emb2 = get_embeddings(text2)
emb3 = get_embeddings(text3)

print(f"Similarity 1-2: {cosine_similarity(emb1, emb2):.3f}")  # High
print(f"Similarity 1-3: {cosine_similarity(emb1, emb3):.3f}")  # Low
```

## Error Handling

### Comprehensive Error Handling

```python
import ollama

def safe_generate_stream(prompt, model="llama3.2"):
    """Generate with comprehensive error handling."""
    try:
        stream = ollama.generate(
            model=model,
            prompt=prompt,
            stream=True
        )

        for chunk in stream:
            yield chunk['response']

    except ollama.ResponseError as e:
        # Model not found or other API errors
        if "not found" in str(e).lower():
            print(f"\n✗ Model '{model}' not found")
            print(f"  Run: ollama pull {model}")
            print(f"  Or browse models at: https://ollama.com/search")
        else:
            print(f"\n✗ API Error: {e}")

    except ConnectionError:
        print("\n✗ Connection failed. Is Ollama running?")
        print("  Start Ollama with: ollama serve")

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")

# Usage
print("Response: ", end="", flush=True)
for token in safe_generate_stream("Hello, world!", model="llama3.2"):
    print(token, end="", flush=True)
print()
```

### Checking Model Availability

```python
def ensure_model_available(model):
    """Check if model is available, provide guidance if not."""
    try:
        available = ollama.list()
        model_names = [m['name'] for m in available.get('models', [])]

        if model not in model_names:
            print(f"Model '{model}' not available locally")
            print(f"Available models: {', '.join(model_names)}")
            print(f"\nTo download: ollama pull {model}")
            print(f"Browse models: https://ollama.com/search")
            return False

        return True

    except Exception as e:
        print(f"Failed to check models: {e}")
        return False

# Usage
if ensure_model_available("llama3.2"):
    # Proceed with using the model
    pass
```

## Best Practices

1. **Always Use Streaming**: Stream responses for better user experience
2. **Ask About Models**: Don't assume models - ask users which model they want to use
3. **Verify Connection**: Check Ollama connection during development with curl
4. **Error Handling**: Handle model not found and connection errors gracefully
5. **Context Management**: Manage conversation history to avoid token limits
6. **Model Selection**: Direct users to https://ollama.com/search to find models
7. **Custom Hosts**: Always ask users for their Ollama URL, don't assume localhost

## PEP 723 Inline Script Metadata

When creating standalone Python scripts for users, always include inline script metadata at the top of the file using PEP 723 format. This allows tools like `uv` and `pipx` to automatically manage dependencies.

### Format

```python
# /// script
# requires-python = ">=3.8"
# dependencies = [
#   "ollama>=0.1.0",
# ]
# ///

import ollama

# Your code here
```

### Running Scripts

Users can run scripts with PEP 723 metadata using:

```bash
# Using uv (recommended)
uv run script.py

# Using pipx
pipx run script.py

# Traditional approach
pip install ollama
python script.py
```

### Complete Example Script

```python
# /// script
# requires-python = ">=3.8"
# dependencies = [
#   "ollama>=0.1.0",
# ]
# ///

import ollama

def main():
    """Simple streaming chat example."""
    model = "llama3.2"

    # Check connection
    try:
        ollama.list()
    except Exception as e:
        print(f"Error: Cannot connect to Ollama - {e}")
        print("Make sure Ollama is running: ollama serve")
        return

    # Stream a response
    print("Asking about Python...\n")
    stream = ollama.generate(
        model=model,
        prompt="Explain Python in one sentence",
        stream=True
    )

    print("Response: ", end="", flush=True)
    for chunk in stream:
        print(chunk['response'], end="", flush=True)
    print()

if __name__ == "__main__":
    main()
```
