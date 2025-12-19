# QA Agent - Gemini LLM Integration

🤖 **Dynamic QA Graph Generation powered by Google Gemini**

Following the UNO-MCP pattern for LLM-driven workflow generation.

## 🚀 Features

- **Dynamic Graph Generation**: Gemini LLM creates custom QA workflows based on test objectives
- **Schema-Driven**: Uses Pydantic models for type-safe graph generation
- **Fallback Support**: Falls back to static graphs if LLM fails
- **UNO-MCP Compatible**: Follows the exact same pattern as UNO's LLM integration

## 📋 Prerequisites

1. **Gemini API Key**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Python Dependencies**: Install required packages
3. **Environment Configuration**: Set up .env file

## 🔧 Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Add your Gemini API key to `.env`:

```env
GEMINI_API_KEY="your_gemini_api_key_here"
```

### 3. Test Integration

```bash
python test_gemini_integration.py
```

## 💡 Usage

### Option 1: Environment Variables (Recommended)

```bash
# Enable LLM graph generation
python configure_llm.py enable "Test vacation request app creation"

# Run QA automation with Gemini
python client.py

# Disable LLM (use static graph)
python configure_llm.py disable
```

### Option 2: Direct Code Usage

```python
from client import QAClient
import asyncio

client = QAClient()

# Use Gemini LLM for graph generation
result = await client.run_qa_test(
    use_llm=True,
    test_objective="Test e-commerce product catalog creation workflow"
)
```

### Option 3: Direct LLM Application

```python
from core.llm_application import QALLMApplication
from core.context import QAContext

# Create LLM application
context = QAContext("test")
llm_app = QALLMApplication("gemini-1.5-pro", context)

# Generate custom QA graph
qa_graph = llm_app.generate_qa_graph(
    test_objective="Test inventory management app creation",
    selenium_methods=selenium_methods,
    application_type="Inventory Management App"
)
```

## 🎯 Test Objectives Examples

The LLM can generate different workflows based on your test objective:

```python
# E-commerce Testing
"Test e-commerce product catalog creation and management workflow"

# HR Application Testing  
"Test employee vacation request application creation and approval workflow"

# Inventory Management
"Test inventory management system creation with stock tracking workflow"

# Customer Support
"Test customer support ticket system creation and resolution workflow"

# Financial Application
"Test expense tracking application creation and reporting workflow"
```

## 📊 Configuration Options

### Environment Variables

```env
# LLM Configuration
USE_LLM_GRAPH="true"                    # Enable/disable LLM graph generation
QA_TEST_OBJECTIVE="Your test objective"  # Default test objective
GEMINI_MODEL="gemini-1.5-pro"          # Gemini model to use
GEMINI_API_KEY="your_api_key"          # Gemini API key

# QA Configuration
QA_PLATFORM_URL="https://your-platform.com"
QA_USERNAME="your_username"
QA_PASSWORD="your_password"
```

### Configuration Commands

```bash
# Check current status
python configure_llm.py status

# Enable LLM with custom objective
python configure_llm.py enable "Test your custom workflow"

# Disable LLM (use static graph)
python configure_llm.py disable
```

## 🔍 How It Works

### 1. Schema Generation (UNO Pattern)
```python
# Get Pydantic schema for LLM
schema = QAGraph.model_json_schema()
```

### 2. Prompt Building
```python
# Build context-aware prompt
system_prompt = template.format(
    test_objective=test_objective,
    selenium_functions=selenium_methods,
    schema=schema
)
```

### 3. LLM Generation
```python
# Generate with Gemini (like UNO's Bedrock)
response = gemini.generate_content(
    system_prompt,
    generation_config=genai.types.GenerationConfig(
        response_mime_type="application/json",
        response_schema=schema
    )
)
```

### 4. Validation & Execution
```python
# Validate and create typed object
qa_graph = QAGraph.model_validate_json(response.text)

# Execute the generated workflow
result = await workflow.execute_workflow(start_node_id)
```

## 🧪 Testing

### Run All Tests
```bash
python test_gemini_integration.py
```

### Test Individual Components
```bash
# Test API key configuration
python -c "from test_gemini_integration import test_gemini_api_key; test_gemini_api_key()"

# Test direct LLM integration
python -c "from test_gemini_integration import test_gemini_llm_direct; test_gemini_llm_direct()"

# Test QA graph generation
python -c "from test_gemini_integration import test_qa_graph_generation; test_qa_graph_generation()"
```

## 📁 File Structure

```
qa-agent/QA-Agent-internal/
├── core/
│   ├── llm_application.py      # Gemini LLM integration (like UNO)
│   ├── graph.py               # Enhanced with LLM support
│   └── workflow.py            # Updated for LLM graphs
├── models/
│   └── qa_models.py           # Pydantic models for LLM
├── prompts/
│   └── qa_graph_generation.txt # LLM prompt template
├── test_gemini_integration.py  # Integration tests
├── configure_llm.py           # Configuration utility
├── client.py                  # Updated with LLM support
└── requirements.txt           # Added Gemini dependencies
```

## 🔧 Troubleshooting

### Common Issues

1. **API Key Not Found**
   ```
   ValueError: GEMINI_API_KEY environment variable not set
   ```
   **Solution**: Add your API key to `.env` file

2. **Import Errors**
   ```
   ModuleNotFoundError: No module named 'google.generativeai'
   ```
   **Solution**: Install dependencies: `pip install -r requirements.txt`

3. **LLM Generation Fails**
   - Falls back to static graph automatically
   - Check API key and internet connection
   - Verify Gemini API quota

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🎉 Benefits

### Dynamic Workflows
- **Adaptive**: Different workflows for different app types
- **Intelligent**: LLM understands test requirements
- **Flexible**: Easy to modify test objectives

### UNO-MCP Compatibility
- **Same Pattern**: Follows UNO's LLM integration exactly
- **Type Safety**: Full Pydantic validation
- **Robust**: Fallback to static graphs

### Future Ready
- **Extensible**: Easy to add other LLM providers
- **Scalable**: Can generate complex multi-phase workflows
- **Maintainable**: Clean separation of concerns

## 📚 References

- [UNO-MCP LLM Integration](../uno-mcp/app/llm_application.py)
- [Google Gemini API](https://ai.google.dev/docs)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

🚀 **Ready to generate dynamic QA workflows with Gemini!**