# 🎯 TinyCode Command Reference Card
## Print & Keep Handy! 📄

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                            🚀 TINYCODER COMMAND CARD                         ║
║                              Super-User Edition                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## 🎮 **LAUNCH COMMANDS**
```bash
python tiny_code.py          # Interactive CLI mode
python tiny_code_rag.py      # RAG-enhanced mode
python api_server.py         # API server mode
```

## 🔧 **MODE COMMANDS**
```
/mode chat      # 💬 Safe Q&A (read-only)
/mode plan      # 📋 Planning & design
/mode code      # 💻 Full coding mode
/mode help      # ❓ Mode information
```

## 📁 **FILE OPERATIONS**
```
read FILE       # 📖 Read & analyze file
cat FILE        # 📄 Display file contents
ls [DIR]        # 📂 List directory
find PATTERN    # 🔍 Search files
tree            # 🌳 Show file tree
write FILE      # ✏️ Create/edit file
```

## 🧠 **RAG COMMANDS** (RAG Mode Only)
```
add_doc FILE    # 📚 Add to knowledge base
search TERM     # 🔍 Search knowledge
query QUESTION  # ❓ Ask questions
summarize FILE  # 📝 Summarize document
```

## 💻 **SYSTEM COMMANDS**
```
help            # ❓ Show all commands
status          # 📊 System status
config          # ⚙️ Show configuration
models          # 🤖 List available models
exit            # 🚪 Quit application
```

## 🎯 **POWER PROMPTS**

### **Code Generation**
```
"Create a Python class for [PURPOSE] with [FEATURES]"
"Write a REST API endpoint for [OPERATION]"
"Generate a React component for [UI_ELEMENT]"
"Build a database schema for [DOMAIN]"
```

### **Code Analysis**
```
"Review this code for security issues"
"Analyze performance bottlenecks"
"Check for best practices compliance"
"Find potential bugs and fixes"
```

### **Documentation**
```
"Generate API documentation for [MODULE]"
"Create README for this project"
"Write unit tests for [FUNCTION]"
"Add inline documentation to this code"
```

### **Optimization**
```
"Optimize this code for performance"
"Refactor for better maintainability"
"Add error handling to this function"
"Implement caching strategy"
```

## ⚡ **ADVANCED WORKFLOWS**

### **🔄 Iterative Development**
```
1. /mode plan → "Design [FEATURE] architecture"
2. /mode code → "Implement [COMPONENT]"
3. "Add tests for [COMPONENT]"
4. "Optimize and document [COMPONENT]"
```

### **🐛 Debugging Flow**
```
1. read buggy_file.py
2. "Analyze this code for bugs"
3. "Fix identified issues"
4. "Add tests to prevent regression"
```

### **📚 RAG-Enhanced Development**
```
1. add_doc project_docs/
2. search "authentication patterns"
3. "Implement OAuth2 based on our docs"
4. "Add rate limiting to auth endpoints"
```

## 🚨 **SAFETY CHECKLIST**
```
✅ Start in /mode chat for exploration
✅ Use /mode plan before major changes
✅ Review code before execution
✅ Keep backups of important files
✅ Use version control (git)
❌ Never execute code blindly
❌ Don't ignore safety confirmations
❌ Don't modify system files without backup
```

## 🛠️ **TROUBLESHOOTING**

### **Ollama Issues**
```bash
curl http://localhost:11434/api/tags  # Test connection
ollama serve                          # Start service
ollama list                          # Check models
```

### **RAG Problems**
```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
ls -la data/index/                   # Check index
```

### **Performance Issues**
```bash
htop                                 # Check system resources
export OLLAMA_NUM_PARALLEL=1        # Optimize Ollama
python scripts/verify_offline_models.py  # Full check
```

## 🎨 **CUSTOMIZATION**

### **Environment Variables**
```bash
export OLLAMA_MODEL=tinyllama:latest
export OLLAMA_HOST=localhost
export SAFETY_LEVEL=standard
export RAG_INDEX_PATH=./data/index
```

### **Config File** (~/.tinycoder/config.yaml)
```yaml
model:
  temperature: 0.7
  max_tokens: 2048
safety:
  level: "standard"
  require_confirmation: true
```

## 💡 **PRO TIPS**

### **Efficiency Hacks**
```
• Use descriptive prompts for better results
• Chain related requests in same session
• Save successful prompts as templates
• Use /mode plan before complex tasks
• Keep context with "based on our previous work"
```

### **Performance Boosters**
```
• Lower temperature (0.1) for faster responses
• Reduce max_tokens for quicker generation
• Use smaller RAG chunk sizes (256)
• Clear model cache when memory is low
```

## 🎯 **QUICK EXAMPLES**

### **Create a Web API**
```
/mode plan
"Design a REST API for task management"

/mode code
"Implement the planned task API with FastAPI"
"Add authentication middleware"
"Write comprehensive tests"
```

### **Debug & Fix Code**
```
read broken_script.py
"Find and fix all bugs in this code"
"Add proper error handling"
"Write unit tests to prevent these bugs"
```

### **Document a Project**
```
add_doc src/
"Generate comprehensive README.md"
"Create API documentation"
"Write deployment guide"
```

## 🏆 **MASTERY LEVELS**

### **Beginner** (First Week)
```
□ Launch TinyCode successfully
□ Switch between modes confidently
□ Use basic file operations
□ Generate simple code snippets
□ Understand safety features
```

### **Intermediate** (Second Week)
```
□ Use advanced prompting techniques
□ Implement complex workflows
□ Customize configuration
□ Use RAG system effectively
□ Debug code efficiently
```

### **Expert** (Third Week+)
```
□ Optimize performance settings
□ Create custom templates
□ Integrate with development workflow
□ Troubleshoot complex issues
□ Train others on TinyCode
```

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  🎉 CONGRATULATIONS! You're ready to become a TinyCode Super-User! 🎉        ║
║                                                                              ║
║  💡 Print this card and keep it visible while coding                         ║
║  🚀 Practice these commands daily for maximum efficiency                     ║
║  📚 Refer to TINYCODER_SUPERUSER_GUIDE.md for detailed explanations         ║
║                                                                              ║
║                        Happy Coding! 🚀👨‍💻👩‍💻                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
```