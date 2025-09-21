# 🚀 TinyCode Super-User Guide
## From Zero to Hero in 5 Minutes

```
╭─────────────────────────────────────────────────────────────╮
│                    🎯 TINYCODER MASTERY                     │
│                  The Ultimate Day-1 Guide                   │
╰─────────────────────────────────────────────────────────────╯
```

---

## 📋 **QUICK START CHECKLIST**

```
□ Ollama installed and running
□ TinyLlama model downloaded (ollama pull tinyllama:latest)
□ Python dependencies installed (pip install -r requirements.txt)
□ RAG system initialized
□ Verification passed (python scripts/verify_offline_models.py)
```

---

## 🎮 **LAUNCHING TINYCODER**

### **CLI Mode (Interactive)**
```bash
python tiny_code.py
```
```
╭──────────────────────────────────────────────────────────────────────╮
│ Welcome to Tiny Code!                                                │
│ Your AI coding assistant powered by TinyLlama                        │
│ Type 'help' for commands, '/mode help' for mode info, 'exit' to quit │
╰──────────────────────────────────────────────────────────────────────╯
```

### **RAG Mode (Enhanced)**
```bash
python tiny_code_rag.py
```
```
╭─────────────────────────────────────────────────────────────╮
│ Tiny Code RAG                                               │
│ AI Coding Assistant with Retrieval-Augmented Generation     │
│ Enhanced with genetics knowledge and document summarization │
│ Type 'help' for commands, 'exit' to quit                    │
╰─────────────────────────────────────────────────────────────╯
```

### **API Server (Production)**
```bash
python api_server.py
# Access at: http://localhost:8000
```

---

## 🔧 **OPERATING MODES**

### **🎯 Mode Switching Commands**
```
/mode chat      # Safe Q&A mode (no file modifications)
/mode plan      # Planning and review mode
/mode code      # Full coding mode with file access
/mode help      # Show all available modes
```

### **📊 Mode Comparison**
```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│    MODE     │   SAFETY    │ FILE ACCESS │  USE CASE   │
├─────────────┼─────────────┼─────────────┼─────────────┤
│ 💬 CHAT     │ ✅ Safest   │ ❌ Read-only │ Learning    │
│ 📋 PLAN     │ ⚠️ Medium   │ 📖 Read-only │ Design      │
│ 💻 CODE     │ ⚠️ Full     │ ✅ Full R/W  │ Development │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

---

## 💻 **ESSENTIAL COMMANDS**

### **🔍 Discovery Commands**
```bash
# Get help
help
/help

# Check system status
status
/status

# View current configuration
config
/config

# List available models
models
```

### **📁 File Operations**
```bash
# Read files
read filename.py
cat config.json

# List directory contents
ls
ls src/

# Find files
find *.py
find "class MyClass"

# Show file tree
tree
```

### **🧠 RAG Commands (RAG Mode Only)**
```bash
# Add documents to knowledge base
add_doc path/to/document.pdf
add_doc https://example.com/api-docs

# Search knowledge base
search "machine learning algorithms"
query "how to implement neural networks"

# Summarize documents
summarize document.md
```

---

## 🎯 **PRO PROMPTING TECHNIQUES**

### **🔥 Power Patterns**

#### **1. Context-Rich Requests**
```
❌ Bad:  "Write a function"
✅ Good: "Write a Python function to validate email addresses using regex,
         with error handling and type hints. Include docstring and tests."
```

#### **2. Iterative Refinement**
```
Step 1: "Create a basic REST API for user management"
Step 2: "Add authentication middleware"
Step 3: "Add input validation and error handling"
Step 4: "Add rate limiting and logging"
```

#### **3. Architecture Planning**
```
"Plan a microservices architecture for an e-commerce platform.
 Consider: user service, product catalog, order processing,
 payment gateway integration, and deployment strategy."
```

### **📋 Template Prompts**

#### **Code Generation**
```
"Create a [LANGUAGE] [COMPONENT_TYPE] that:
- [PRIMARY_FUNCTION]
- Follows [DESIGN_PATTERN] pattern
- Includes [FEATURES_LIST]
- Has comprehensive error handling
- Is production-ready with tests"
```

#### **Code Review**
```
"Review this [LANGUAGE] code for:
- Security vulnerabilities
- Performance issues
- Code maintainability
- Best practices compliance
- Suggest specific improvements"
```

#### **Documentation**
```
"Generate comprehensive documentation for [CODE_COMPONENT]:
- API reference with examples
- Installation guide
- Usage examples
- Troubleshooting section
- Performance considerations"
```

---

## ⚡ **ADVANCED WORKFLOWS**

### **🔄 RAG-Enhanced Development**
```
1. Load project documentation: add_doc README.md
2. Add API specs: add_doc api-spec.yaml
3. Query for context: search "authentication flow"
4. Generate code: "Implement OAuth2 flow based on our API spec"
5. Iterate: "Add rate limiting to the auth endpoint"
```

### **🏗️ Full-Stack Project Creation**
```
/mode plan
"Design a todo app with React frontend and Node.js backend"

/mode code
"Implement the backend API we planned"
"Create the React components"
"Add database integration"
"Write comprehensive tests"
```

### **🐛 Debugging Workflow**
```
1. read buggy_file.py
2. "Analyze this code for potential bugs"
3. "Fix the identified issues"
4. "Add unit tests to prevent regression"
5. "Optimize for better performance"
```

---

## 🎨 **CUSTOMIZATION & CONFIGURATION**

### **⚙️ Environment Variables**
```bash
# Model Selection
export OLLAMA_MODEL=tinyllama:latest
export OLLAMA_HOST=localhost
export OLLAMA_PORT=11434

# RAG Configuration
export RAG_INDEX_PATH=./data/index
export EMBEDDING_MODEL=all-MiniLM-L6-v2

# Safety Settings
export SAFETY_LEVEL=standard
export CONFIRMATION_REQUIRED=true
```

### **📝 Custom Templates**
Create `.tinycoder/templates/` directory:
```
templates/
├── python_class.template
├── react_component.template
├── api_endpoint.template
└── test_suite.template
```

### **🔧 Configuration File**
`.tinycoder/config.yaml`:
```yaml
model:
  name: "tinyllama:latest"
  temperature: 0.7
  max_tokens: 2048

safety:
  level: "standard"
  require_confirmation: true

rag:
  index_path: "./data/index"
  chunk_size: 512
  similarity_threshold: 0.75
```

---

## 🚨 **SAFETY & BEST PRACTICES**

### **🛡️ Safety Guidelines**
```
✅ DO:
- Start in /mode chat for experimentation
- Use /mode plan before major changes
- Review generated code before execution
- Keep backups of important files
- Use version control (git)

❌ DON'T:
- Execute generated code blindly
- Ignore safety confirmations
- Modify system files without backup
- Share sensitive information in prompts
```

### **🔒 Security Checklist**
```
□ API keys in environment variables (not code)
□ Input validation on all generated endpoints
□ Authentication implemented properly
□ No hardcoded secrets in generated code
□ Generated SQL uses parameterized queries
□ File permissions set correctly
```

---

## 🎯 **PRO TIPS & SHORTCUTS**

### **⚡ Efficiency Hacks**

#### **Batch Operations**
```bash
# Process multiple files
for file in *.py; do
  echo "Reviewing $file" | python tiny_code.py
done
```

#### **Prompt Chaining**
```
Session 1: "Create data models for user management"
Session 2: "Now create API endpoints for these models"
Session 3: "Add authentication to protect these endpoints"
```

#### **Context Preservation**
```
# Use descriptive variable names
user_service_code = """[previous code]"""

# Reference previous work
"Extend the UserService we created earlier with email verification"
```

### **🔥 Power User Commands**

#### **Quick File Analysis**
```bash
# Analyze entire project
find . -name "*.py" -exec echo "File: {}" \; -exec python tiny_code.py -c "analyze this file" \;
```

#### **Automated Code Review**
```bash
# Review changed files
git diff --name-only | xargs python tiny_code.py -c "review for security issues"
```

#### **Documentation Generation**
```bash
# Generate docs for all modules
find . -name "*.py" -exec python tiny_code.py -c "generate docs for this module" \;
```

---

## 🐛 **TROUBLESHOOTING GUIDE**

### **Common Issues & Solutions**

#### **🔴 Ollama Connection Failed**
```bash
# Check service status
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve

# Verify model availability
ollama list
```

#### **🔴 RAG System Not Working**
```bash
# Verify embedding model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Check index directory
ls -la data/index/

# Rebuild index
rm -rf data/index && python tiny_code_rag.py
```

#### **🔴 Performance Issues**
```bash
# Check system resources
htop
nvidia-smi  # If using GPU

# Optimize model parameters
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_MAX_LOADED_MODELS=1
```

### **🆘 Emergency Recovery**
```bash
# Reset configuration
rm -rf ~/.tinycoder/
python tiny_code.py --reset

# Restore from backup
cp backup/config.yaml ~/.tinycoder/config.yaml

# Verify installation
python scripts/verify_offline_models.py
```

---

## 📈 **PERFORMANCE OPTIMIZATION**

### **⚡ Speed Boosters**
```yaml
# Optimized config for speed
model:
  temperature: 0.1      # Faster, more deterministic
  max_tokens: 1024      # Shorter responses

rag:
  chunk_size: 256       # Smaller chunks
  max_results: 5        # Fewer search results
```

### **🧠 Memory Management**
```bash
# Monitor memory usage
ps aux | grep python

# Clear model cache
ollama stop && ollama serve

# Optimize Python memory
export PYTHONHASHSEED=0
export MALLOC_ARENA_MAX=2
```

---

## 🎓 **LEARNING PATH**

### **📚 Beginner (Week 1)**
```
Day 1: Basic commands and chat mode
Day 2: File operations and code generation
Day 3: Mode switching and safety features
Day 4: Simple debugging workflows
Day 5: Configuration and customization
Day 6: RAG system basics
Day 7: Project: Build a simple script
```

### **🚀 Intermediate (Week 2)**
```
Day 1-2: Advanced prompting techniques
Day 3-4: Complex project workflows
Day 5-6: API server and production deployment
Day 7: Project: Full-stack application
```

### **🏆 Expert (Week 3+)**
```
- Custom model integration
- Advanced RAG workflows
- Performance optimization
- Security hardening
- Team collaboration workflows
```

---

## 🎯 **QUICK REFERENCE CARD**

```
╭─────────────────────────────────────────────────────────────╮
│                    🎮 ESSENTIAL HOTKEYS                     │
├─────────────────────────────────────────────────────────────┤
│ help          │ Show all commands                           │
│ /mode X       │ Switch to mode X (chat/plan/code)          │
│ status        │ Show system status                          │
│ read FILE     │ Read and analyze file                       │
│ ls            │ List directory contents                     │
│ search TERM   │ Search knowledge base (RAG mode)           │
│ add_doc FILE  │ Add document to knowledge base              │
│ exit          │ Quit TinyCode                               │
├─────────────────────────────────────────────────────────────┤
│                   🔧 POWER PROMPTS                          │
├─────────────────────────────────────────────────────────────┤
│ "Create a..."        │ Generate new code/components         │
│ "Analyze this..."    │ Code review and analysis             │
│ "Fix the bug in..."  │ Debugging assistance                 │
│ "Optimize..."        │ Performance improvements             │
│ "Add tests for..."   │ Generate test suites                 │
│ "Document..."        │ Generate documentation               │
│ "Refactor..."        │ Code refactoring                     │
╰─────────────────────────────────────────────────────────────╯
```

---

## 🎉 **CONGRATULATIONS!**

```
╭─────────────────────────────────────────────────────────────╮
│  🏆 You're now a TinyCode Super-User! 🏆                    │
│                                                             │
│  ✅ Master all modes and commands                           │
│  ✅ Use advanced prompting techniques                       │
│  ✅ Optimize for peak performance                           │
│  ✅ Follow security best practices                          │
│  ✅ Troubleshoot like a pro                                 │
│                                                             │
│           Happy Coding! 🚀👨‍💻👩‍💻                              │
╰─────────────────────────────────────────────────────────────╯
```

---

**💡 Pro Tip**: Print this guide and keep it handy during your first week. You'll be amazed at how quickly you become a TinyCode expert!

**🔗 Quick Links**:
- 📖 Full Documentation: `PRODUCTION_DEPLOYMENT.md`
- 🛠️ Setup Guide: `OFFLINE_SETUP_GUIDE.md`
- 🔍 Verification: `python scripts/verify_offline_models.py`
- 🚀 Quick Start: `python tiny_code.py`