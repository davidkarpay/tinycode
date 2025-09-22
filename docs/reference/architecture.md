# TinyCode System Architecture

This document provides a comprehensive overview of TinyCode's architecture, including system design, component interactions, and technical implementation details.

## Table of Contents

- [System Overview](#system-overview)
- [Core Architecture](#core-architecture)
- [Component Details](#component-details)
- [Data Flow](#data-flow)
- [Security Architecture](#security-architecture)
- [Deployment Architecture](#deployment-architecture)
- [Scalability Considerations](#scalability-considerations)
- [Technology Stack](#technology-stack)

## System Overview

TinyCode is a local-first AI coding assistant designed for 100% offline operation. The system combines multiple AI techniques with robust safety mechanisms to provide intelligent code assistance without external dependencies.

### Design Principles

1. **Local-First**: All processing happens locally, no external API calls
2. **Safety-First**: Multiple layers of protection against harmful operations
3. **Modular Design**: Loosely coupled components for flexibility
4. **Plan-Based Execution**: Explicit approval process for modifications
5. **Audit Trail**: Complete logging of all operations
6. **Resource Efficiency**: Optimized for local resource constraints

## Core Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            TinyCode Enhanced System                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │    CLI      │  │    API      │  │    RAG      │  │   Plugin    │       │
│  │ Interface   │  │   Server    │  │   Enhanced  │  │   System    │       │
│  │ Enhanced    │  │             │  │   Agent     │  │             │       │
│  └─────┬───────┘  └─────┬───────┘  └─────┬───────┘  └─────┬───────┘       │
│        │                │                │                │               │
│        └────────────────┼────────────────┼────────────────┘               │
│                         │                │                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    Core Agent System                                   │ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │ │
│  │  │    Mode     │  │    Plan     │  │   Safety    │  │   Command   │  │ │
│  │  │  Manager    │  │ Generator/  │  │   System    │  │  Registry   │  │ │
│  │  │             │  │  Executor   │  │             │  │  (40+ cmds) │  │ │
│  │  └─────┬───────┘  └─────┬───────┘  └─────┬───────┘  └─────┬───────┘  │ │
│  │        │                │                │                │          │ │
│  │        └────────────────┼────────────────┼────────────────┘          │ │
│  │                         │                │                           │ │
│  └─────────────────────────┼────────────────┼───────────────────────────┘ │
│                            │                │                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    Enhanced Capabilities Layer                         │ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │ │
│  │  │    Git      │  │   System    │  │    Error    │  │    CLI      │  │ │
│  │  │Integration  │  │Integration  │  │  Handling   │  │Enhancements │  │ │
│  │  │             │  │             │  │             │  │             │  │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                    │ │
│  │  │  Advanced   │  │    Self     │  │   Plugin    │                    │ │
│  │  │    File     │  │ Awareness   │  │   Manager   │                    │ │
│  │  │ Operations  │  │             │  │             │                    │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                    │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                       │                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                       Foundation Layer                                 │ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │ │
│  │  │   Ollama    │  │    RAG      │  │   Storage   │  │   Plugin    │  │ │
│  │  │   Client    │  │   System    │  │   Layer     │  │   Loader    │  │ │
│  │  │             │  │             │  │             │  │             │  │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Interface Layer

#### CLI Interface (`tiny_code/cli.py`)
- **Purpose**: Interactive command-line interface with enhanced capabilities
- **Features**: Rich formatting, intelligent auto-completion, command history, usage analytics
- **Components**:
  - Command parser and dispatcher (40+ commands)
  - Mode-aware prompt system
  - Output formatting with Rich library
  - Session management with SQLite-based analytics
  - Plugin command integration
  - Error context management

#### API Server (`api_server.py`)
- **Purpose**: REST API for programmatic access
- **Features**: Rate limiting, authentication, metrics
- **Endpoints**:
  - `/complete` - Code completion
  - `/fix` - Bug fixing
  - `/explain` - Code explanation
  - `/refactor` - Code refactoring
  - `/health` - Health check
  - `/metrics` - Prometheus metrics

#### RAG Enhanced Agent (`tiny_code/rag_enhanced_agent.py`)
- **Purpose**: Document-aware coding assistance
- **Features**: Context search, knowledge integration
- **Capabilities**:
  - Document ingestion and indexing
  - Semantic search across knowledge base
  - Context-aware code generation

### 2. Core Agent System

#### Mode Manager (`tiny_code/mode_manager.py`)
- **Purpose**: Controls operation modes and transitions
- **Modes**:
  - **Chat Mode**: Safe exploration, read-only
  - **Propose Mode**: Plan generation and review
  - **Execute Mode**: Approved plan execution
- **Features**:
  - Mode transition validation
  - Permission enforcement
  - State persistence

#### Plan System
- **Plan Generator** (`tiny_code/plan_generator.py`)
  - Creates detailed execution plans
  - Risk assessment and categorization
  - Step-by-step breakdown

- **Plan Validator** (`tiny_code/plan_validator.py`)
  - Pre-execution validation
  - Dangerous pattern detection
  - Dependency verification

- **Plan Executor** (`tiny_code/plan_executor.py`)
  - Safe plan execution
  - Checkpoint management
  - Rollback capabilities

#### Safety System
- **Safety Config** (`tiny_code/safety_config.py`)
  - Four-tier safety levels
  - Configurable restrictions
  - Policy enforcement

- **Audit Logger** (`tiny_code/audit_logger.py`)
  - Hash-chain integrity logging
  - Tamper detection
  - Complete operation history

- **Resource Monitor** (`tiny_code/resource_monitor.py`)
  - System resource tracking
  - File handle management
  - Performance monitoring

### 3. Enhanced Capabilities Framework

#### Advanced File Operations (`tiny_code/tools.py`)
- **Purpose**: Sophisticated file manipulation and analysis
- **Features**:
  - Glob pattern matching with metadata
  - Advanced grep functionality with filtering
  - Multi-file editing operations
  - Directory analysis and visualization
  - File comparison and diffing

#### Git Integration (`tiny_code/git_operations.py`)
- **Purpose**: Comprehensive git workflow automation
- **Features**:
  - Repository analysis and statistics
  - Branch management and visualization
  - Automated workflow operations
  - Commit history analysis
  - Remote repository management

#### System Integration (`tiny_code/system_integration.py`)
- **Purpose**: System monitoring and management
- **Features**:
  - Process monitoring and control
  - Environment variable management
  - Network connection analysis
  - Resource usage tracking
  - System information gathering

#### Error Handling System (`tiny_code/error_handling.py`)
- **Purpose**: Robust error recovery and analytics
- **Features**:
  - Automatic error categorization
  - Recovery strategy execution
  - Error pattern analysis
  - Historical error tracking
  - User-friendly error reporting

#### CLI Enhancements (`tiny_code/cli_enhancements.py`)
- **Purpose**: Advanced CLI user experience
- **Features**:
  - Intelligent command completion
  - SQLite-based usage analytics
  - Command history management
  - Context-aware suggestions
  - Performance metrics

#### Plugin System (`tiny_code/plugin_system.py`)
- **Purpose**: Modular architecture for extensibility
- **Features**:
  - Dynamic plugin loading and management
  - Hot-reload capabilities for development
  - Dependency management
  - Safety integration
  - Command registration system

#### Self-Awareness System (`tiny_code/self_awareness.py`)
- **Purpose**: Dynamic capability discovery and introspection
- **Features**:
  - Real-time command inventory
  - Feature availability checking
  - Capability self-reporting
  - Dynamic help generation

### 4. Command Registry System (`tiny_code/command_registry.py`)
- **Purpose**: Centralized command management and categorization
- **Features**:
  - Safety level categorization (NONE → CRITICAL)
  - Mode-based command filtering
  - Permission enforcement
  - Command metadata management
  - 40+ registered commands across categories
  - Resource limit enforcement

### 5. Foundation Layer

#### Ollama Client (`tiny_code/ollama_client.py`)
- **Purpose**: Interface to local LLM service
- **Features**:
  - Connection management
  - Request/response handling
  - Error recovery
  - Model management

#### Plugin System Foundation (`plugins/`)
- **Purpose**: Modular extension architecture
- **Components**:
  - Plugin discovery and loading mechanism
  - Safety integration for plugin commands
  - Hot-reload support for development
  - Dependency management system
- **Built-in Plugins**:
  - Utilities Plugin: Text processing, hashing, encoding
  - Code Formatter Plugin: Multi-language formatting
  - Web Scraper Plugin: Content extraction and analysis

#### RAG System (`rag/`)
- **Embeddings** (`rag/embeddings/local_embedder.py`)
  - Local sentence transformer models
  - Vector generation for documents and queries
  - Caching for performance

- **Vector Store** (`rag/vectorstore/faiss_store.py`)
  - FAISS-based similarity search
  - Index management and optimization
  - Metadata filtering

- **Retrieval** (`rag/retrieval/hybrid_retriever.py`)
  - Hybrid dense/sparse search
  - Result ranking and fusion
  - Context extraction

#### Storage Layer
- **File System**: Local file operations with safety checks
- **SQLite Database**: Audit logs, plan history, metadata
- **FAISS Indexes**: Vector storage for RAG
- **Backup System**: Automatic backup management

## Data Flow

### 1. Request Processing Flow

```
User Input → CLI/API → Mode Manager → Command Registry
                  ↓
         Mode Validation → Safety Check → Command Execution
                  ↓
         Plan Generation → Validation → Approval → Execution
                  ↓
         Audit Logging → Result Return → User Response
```

### 2. RAG-Enhanced Flow

```
User Query → Query Processing → Vector Search → Context Retrieval
                  ↓
         Context + Query → LLM Processing → Response Generation
                  ↓
         Safety Validation → Audit Logging → User Response
```

### 3. Plan Execution Flow

```
Plan Request → Risk Assessment → Step Generation → Validation
                  ↓
         User Approval → Backup Creation → Step Execution
                  ↓
         Progress Tracking → Error Handling → Completion/Rollback
```

## Security Architecture

### 1. Defense in Depth

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layers                          │
├─────────────────────────────────────────────────────────────┤
│ Layer 1: Mode Separation (Capability Isolation)            │
│ Layer 2: Plan Review (Explicit Approval)                   │
│ Layer 3: Validation (Pattern Detection)                    │
│ Layer 4: Sandboxing (Path Restrictions)                    │
│ Layer 5: Monitoring (Resource Limits)                      │
│ Layer 6: Audit Trail (Complete Logging)                    │
└─────────────────────────────────────────────────────────────┘
```

### 2. Safety Mechanisms

#### Path Traversal Protection
```python
BLOCKED_PATHS = [
    "/etc", "/usr", "/bin", "/sbin",
    "/System", "/Windows",
    "../", "/..", "~/"
]
```

#### Dangerous Pattern Detection
```python
DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"DROP\s+TABLE",
    r"eval\s*\(",
    r"exec\s*\(",
    r"__import__"
]
```

#### Resource Limits
```python
RESOURCE_LIMITS = {
    "max_file_size": 10_000_000,     # 10MB
    "max_memory": 2_000_000_000,     # 2GB
    "max_cpu_time": 300,             # 5 minutes
    "max_open_files": 100
}
```

### 3. Audit System

#### Hash Chain Integrity
```python
# Each log entry includes hash of previous entry
current_hash = sha256(
    previous_hash +
    json.dumps(current_entry, sort_keys=True)
)
```

#### Audit Record Structure
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "action": "file_modify",
  "mode": "EXECUTE",
  "user": "current_user",
  "details": {...},
  "risk_level": "MEDIUM",
  "hash": "sha256:...",
  "previous_hash": "sha256:..."
}
```

## Deployment Architecture

### 1. Single Node Deployment

```
┌─────────────────────────────────────────┐
│              Single Host                │
├─────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐       │
│  │  TinyCode   │  │   Ollama    │       │
│  │  Process    │  │   Service   │       │
│  │             │  │             │       │
│  └─────────────┘  └─────────────┘       │
│                                         │
│  ┌─────────────────────────────────────┐ │
│  │         Local Storage               │ │
│  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐  │ │
│  │  │Data │ │Logs │ │Index│ │Back │  │ │
│  │  │     │ │     │ │     │ │ ups │  │ │
│  │  └─────┘ └─────┘ └─────┘ └─────┘  │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### 2. Containerized Deployment

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Host                              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  TinyCode   │  │    Redis    │  │    Nginx    │          │
│  │ Container   │  │ Container   │  │ Container   │          │
│  │             │  │             │  │             │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐                          │
│  │ Prometheus  │  │  Grafana    │                          │
│  │ Container   │  │ Container   │                          │
│  │             │  │             │                          │
│  └─────────────┘  └─────────────┘                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 Docker Volumes                          │ │
│  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐      │ │
│  │  │Data │ │Logs │ │Redis│ │Prom │ │Graf │ │SSL  │      │ │
│  │  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘      │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 3. Production Deployment

```
┌─────────────────────────────────────────────────────────────┐
│                   Load Balancer                            │
│                  (Nginx/HAProxy)                           │
└─────────────────────┬───────────────────────────────────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  TinyCode   │ │  TinyCode   │ │  TinyCode   │
│  Instance 1 │ │  Instance 2 │ │  Instance 3 │
└─────────────┘ └─────────────┘ └─────────────┘
         │            │            │
         └────────────┼────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                 Shared Services                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │    Redis    │  │ Prometheus  │  │   Grafana   │          │
│  │   Cluster   │  │   Server    │  │  Dashboard  │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Persistent Storage                         │ │
│  │        (NFS/Ceph/Cloud Storage)                        │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Scalability Considerations

### 1. Vertical Scaling

- **CPU**: Multi-core support for parallel operations
- **Memory**: Increased capacity for larger models and datasets
- **Storage**: SSD for better I/O performance
- **GPU**: Optional GPU acceleration for model inference

### 2. Horizontal Scaling

- **Stateless Design**: API instances can be replicated
- **Shared Storage**: Common data access across instances
- **Load Balancing**: Request distribution
- **Redis Clustering**: Distributed rate limiting state

### 3. Performance Optimization

#### Model Optimization
- Model quantization for reduced memory usage
- Caching frequently used responses
- Batch processing for multiple requests
- Lazy loading of large models

#### Data Optimization
- FAISS index optimization
- Efficient vector storage
- Incremental indexing
- Query result caching

#### Resource Optimization
- Connection pooling
- Memory management
- Disk I/O optimization
- Network optimization

## Technology Stack

### Core Technologies
- **Python 3.8+**: Primary programming language
- **Ollama**: Local LLM inference server
- **TinyLlama**: Primary language model
- **SQLite**: Local database for persistence
- **FAISS**: Vector similarity search

### Interface Technologies
- **Rich**: CLI formatting and styling
- **Click**: Command-line interface framework
- **Flask**: Web API framework
- **Prometheus**: Metrics collection

### Data Processing
- **sentence-transformers**: Text embeddings
- **pandas**: Data manipulation
- **numpy**: Numerical computing
- **chromadb**: Alternative vector database

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **Nginx**: Reverse proxy and load balancing
- **Redis**: Caching and rate limiting

### Monitoring
- **Prometheus**: Metrics collection
- **Grafana**: Visualization and dashboards
- **AlertManager**: Alert routing and management

### Development
- **pytest**: Testing framework
- **black**: Code formatting
- **mypy**: Type checking
- **pre-commit**: Git hooks

## Design Patterns

### 1. Command Pattern
- Commands encapsulate operations
- Undo/redo capabilities through plan system
- Queuing and logging of operations

### 2. Strategy Pattern
- Multiple safety levels with different strategies
- Pluggable retrieval algorithms
- Configurable validation approaches

### 3. Observer Pattern
- Event-driven audit logging
- Resource monitoring callbacks
- Progress tracking notifications

### 4. Factory Pattern
- Plan generation based on task type
- Model client creation
- Component initialization

## See Also

- [Configuration Reference](configuration.md) - Detailed configuration options
- [Troubleshooting Guide](troubleshooting.md) - Common issues and solutions
- [Production Deployment](../deployment/production.md) - Enterprise setup
- [Docker Guide](../deployment/docker.md) - Container deployment