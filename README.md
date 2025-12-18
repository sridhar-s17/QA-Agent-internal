# QA Agent - Automated Testing Framework

## Overview
QA Agent is an automated testing framework built with the same architecture as UNO-MCP, designed to automate the complete app creation process validation.

## Architecture
- **Graph-based workflow** with nodes (agents) and edges (flow control)
- **MCP tools integration** wrapping Selenium automation functions
- **Phase-based execution** (9 phases covering 14 automation steps)
- **LLM integration** for intelligent decision making
- **Screenshot capture** and test result storage

## Phases
1. **AUTHENTICATION & SETUP** (Discovery) - Steps 1-2
2. **REQUIREMENTS GATHERING** (Discovery) - Step 3
3. **DISCOVERY DOCUMENT VALIDATION** (Discovery) - Step 4
4. **WIREFRAMES VALIDATION** (Wireframe) - Steps 5-6
5. **DESIGN DOCUMENT VALIDATION** (Specification) - Steps 7-8
6. **BUILD PROCESS** (Build) - Steps 9-10
7. **TEST PLAN VALIDATION** (Test) - Step 11
8. **PREVIEW APP** (Test) - Steps 12-13
9. **FINAL CONFIRMATION** (Deploy) - Step 14

## Key Features
- **No S3 uploads** - Local storage only
- **Document screenshot capture** when opened
- **Test results** stored with tab session + timestamp
- **Error handling** with automatic retry
- **Processing wait** intelligence
- **Validation screen** detection

## Quick Start

### 1. Setup Virtual Environment (Windows)
```bash
# Run the setup script
setup_venv.bat

# Or manually:
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

### 2. Setup Virtual Environment (Linux/Mac)
```bash
# Make script executable and run
chmod +x setup_venv.sh
./setup_venv.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run QA Tests
```bash
# Windows - Easy way
activate_and_run.bat

# Linux/Mac - Easy way
chmod +x activate_and_run.sh
./activate_and_run.sh

# Or manually activate and run
# Windows: venv\Scripts\activate.bat
# Linux/Mac: source venv/bin/activate
python run_qa.py
```

## Project Structure
```
qa-agent/
├── config/           # Configuration files
│   ├── models.json   # LLM model configuration
│   └── profiles.yaml # QA agent profiles and test config
├── core/            # Core workflow engine
│   ├── context.py   # QA session context management
│   ├── graph.py     # Graph-based workflow definition
│   └── workflow.py  # Workflow orchestration engine
├── agents/          # QA-specific agents
│   └── authentication_agent.py  # Phase 1 agent
├── selenium/        # Selenium automation functions
│   └── automation_core.py  # Selenium wrapper
├── tools/           # Utilities and tools
│   └── graph_visualizer.py  # Graph analysis and visualization
├── results/         # Test results and screenshots (auto-created)
├── venv/            # Virtual environment (auto-created)
├── setup_venv.bat   # Windows setup script
├── setup_venv.sh    # Linux/Mac setup script
├── activate_and_run.bat  # Windows run script
├── activate_and_run.sh   # Linux/Mac run script
├── client.py        # Direct client (no FastAPI)
├── run_qa.py        # Simple test runner
└── qa_workflow_graph.json  # Generated graph definition
```