#!/usr/bin/env python3
"""Production API server for TinyCode with rate limiting and monitoring"""

import os
import sys
import time
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge, generate_latest

from tiny_code.rag_enhanced_agent import RAGEnhancedTinyCodeAgent
from tiny_code.mode_manager import ModeManager, OperationMode
from tiny_code.rate_limiter import RateLimiter, RateLimitExceeded, LimitType
from tiny_code.safety_config import SafetyConfigManager
from rich.console import Console

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('tinyllama_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('tinyllama_request_duration_seconds', 'Request duration', ['endpoint'])
ACTIVE_CONNECTIONS = Gauge('tinyllama_active_connections', 'Active connections')
PLAN_OPERATIONS = Counter('tinyllama_plan_operations_total', 'Plan operations', ['operation', 'status'])
RAG_OPERATIONS = Counter('tinyllama_rag_operations_total', 'RAG operations', ['operation'])

# Initialize Flask app
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
CORS(app, origins=os.getenv('ALLOWED_ORIGINS', '*').split(','))

# Global components
agent = None
mode_manager = None
rate_limiter = None
console = Console()

def init_app():
    """Initialize application components"""
    global agent, mode_manager, rate_limiter

    try:
        logger.info("Initializing TinyCode API server...")

        # Initialize agent
        agent = RAGEnhancedTinyCodeAgent()
        logger.info("RAG-enhanced agent initialized")

        # Initialize mode manager
        mode_manager = ModeManager(initial_mode=OperationMode.CHAT)
        logger.info("Mode manager initialized")

        # Initialize rate limiter
        redis_url = os.getenv('REDIS_URL')
        if redis_url:
            from tiny_code.rate_limiter import RedisRateLimiter
            rate_limiter = RedisRateLimiter(redis_url)
            logger.info("Redis rate limiter initialized")
        else:
            rate_limiter = RateLimiter()
            logger.info("Memory rate limiter initialized")

        logger.info("TinyCode API server initialization complete")

    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

def get_client_id():
    """Extract client ID from request"""
    # Check API key first
    api_key = request.headers.get('X-API-Key')
    if api_key:
        return api_key[:8]  # Use first 8 chars as client ID

    # Fall back to IP address
    return request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)

def require_api_key(f):
    """Decorator to require API key authentication"""
    def wrapper(*args, **kwargs):
        if os.getenv('API_KEY_REQUIRED', 'false').lower() == 'true':
            api_key = request.headers.get('X-API-Key')
            if not api_key:
                return jsonify({'error': 'API key required'}), 401

            # Validate API key (implement your validation logic)
            valid_keys = os.getenv('VALID_API_KEYS', '').split(',')
            if valid_keys and api_key not in valid_keys:
                return jsonify({'error': 'Invalid API key'}), 401

        return f(*args, **kwargs)
    return wrapper

@app.before_request
def before_request():
    """Before request handler"""
    g.start_time = time.time()
    g.request_id = str(uuid.uuid4())[:8]
    ACTIVE_CONNECTIONS.inc()

    # Log request
    logger.info(f"Request {g.request_id}: {request.method} {request.path} from {get_client_id()}")

@app.after_request
def after_request(response):
    """After request handler"""
    ACTIVE_CONNECTIONS.dec()

    # Record metrics
    duration = time.time() - g.start_time
    REQUEST_DURATION.labels(endpoint=request.endpoint or 'unknown').observe(duration)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.endpoint or 'unknown',
        status=response.status_code
    ).inc()

    # Add headers
    response.headers['X-Request-ID'] = g.request_id
    response.headers['X-Response-Time'] = f"{duration:.3f}s"

    # Log response
    logger.info(f"Response {g.request_id}: {response.status_code} in {duration:.3f}s")

    return response

# Health check endpoints
@app.route('/health')
def health():
    """Basic health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/ready')
def ready():
    """Readiness check with dependency validation"""
    checks = {}

    # Check agent
    try:
        checks['agent'] = agent is not None
    except Exception:
        checks['agent'] = False

    # Check mode manager
    try:
        checks['mode_manager'] = mode_manager is not None
        checks['current_mode'] = mode_manager.get_current_mode().value if mode_manager else None
    except Exception:
        checks['mode_manager'] = False

    # Check rate limiter
    try:
        checks['rate_limiter'] = rate_limiter is not None
    except Exception:
        checks['rate_limiter'] = False

    all_ready = all(checks.values())
    status_code = 200 if all_ready else 503

    return jsonify({
        'ready': all_ready,
        'checks': checks,
        'timestamp': datetime.now().isoformat()
    }), status_code

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}

# API Endpoints
@app.route('/api/v1/mode', methods=['GET'])
@require_api_key
def get_mode():
    """Get current operation mode"""
    try:
        if not rate_limiter.check_limit(get_client_id(), LimitType.API_GENERAL):
            return jsonify({'error': 'Rate limit exceeded'}), 429

        return jsonify({
            'mode': mode_manager.get_current_mode().value,
            'status': mode_manager.get_mode_status()
        })

    except Exception as e:
        logger.error(f"Error getting mode: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/mode', methods=['POST'])
@require_api_key
def set_mode():
    """Set operation mode"""
    try:
        if not rate_limiter.check_limit(get_client_id(), LimitType.API_GENERAL):
            return jsonify({'error': 'Rate limit exceeded'}), 429

        data = request.get_json()
        if not data or 'mode' not in data:
            return jsonify({'error': 'Mode is required'}), 400

        mode_str = data['mode']
        try:
            mode = OperationMode(mode_str)
        except ValueError:
            return jsonify({'error': f'Invalid mode: {mode_str}'}), 400

        success = mode_manager.set_mode(mode)
        return jsonify({
            'success': success,
            'mode': mode_manager.get_current_mode().value
        })

    except Exception as e:
        logger.error(f"Error setting mode: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/plans', methods=['POST'])
@require_api_key
def create_plan():
    """Create execution plan"""
    try:
        client_id = get_client_id()
        if not rate_limiter.check_limit(client_id, LimitType.PLAN_GENERATION):
            wait_time = rate_limiter.get_wait_time(client_id, LimitType.PLAN_GENERATION)
            return jsonify({
                'error': 'Rate limit exceeded',
                'retry_after': wait_time
            }), 429

        data = request.get_json()
        if not data or 'request' not in data:
            return jsonify({'error': 'Request is required'}), 400

        # Generate plan
        plan = agent.plan_generator.generate_plan(
            data['request'],
            title=data.get('title')
        )

        PLAN_OPERATIONS.labels(operation='create', status='success').inc()

        return jsonify({
            'plan_id': plan.id,
            'title': plan.title,
            'status': plan.status.value,
            'actions': len(plan.actions),
            'risk_assessment': plan.risk_assessment,
            'estimated_duration': plan.estimated_total_duration
        })

    except Exception as e:
        PLAN_OPERATIONS.labels(operation='create', status='error').inc()
        logger.error(f"Error creating plan: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/plans/<plan_id>', methods=['GET'])
@require_api_key
def get_plan(plan_id):
    """Get plan details"""
    try:
        if not rate_limiter.check_limit(get_client_id(), LimitType.API_GENERAL):
            return jsonify({'error': 'Rate limit exceeded'}), 429

        plan = agent.plan_generator.get_plan(plan_id)
        if not plan:
            return jsonify({'error': 'Plan not found'}), 404

        return jsonify({
            'id': plan.id,
            'title': plan.title,
            'description': plan.description,
            'status': plan.status.value,
            'created_at': plan.created_at.isoformat(),
            'updated_at': plan.updated_at.isoformat(),
            'actions': [
                {
                    'id': action.id,
                    'type': action.action_type.value,
                    'description': action.description,
                    'target_path': action.target_path,
                    'risk_level': action.risk_level
                }
                for action in plan.actions
            ],
            'risk_assessment': plan.risk_assessment,
            'estimated_duration': plan.estimated_total_duration
        })

    except Exception as e:
        logger.error(f"Error getting plan: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/rag/search', methods=['POST'])
@require_api_key
def rag_search():
    """Search RAG knowledge base"""
    try:
        client_id = get_client_id()
        if not rate_limiter.check_limit(client_id, LimitType.RAG_SEARCH):
            return jsonify({'error': 'Rate limit exceeded'}), 429

        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400

        # Perform RAG search
        results = agent.rag_search(
            data['query'],
            knowledge_base=data.get('knowledge_base', 'general'),
            top_k=data.get('top_k', 5)
        )

        RAG_OPERATIONS.labels(operation='search').inc()

        return jsonify({
            'results': [
                {
                    'content': result.get('content', ''),
                    'score': result.get('score', 0.0),
                    'metadata': result.get('metadata', {})
                }
                for result in results
            ],
            'query': data['query'],
            'knowledge_base': data.get('knowledge_base', 'general')
        })

    except Exception as e:
        logger.error(f"Error in RAG search: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/stats', methods=['GET'])
@require_api_key
def get_stats():
    """Get API statistics"""
    try:
        if not rate_limiter.check_limit(get_client_id(), LimitType.API_GENERAL):
            return jsonify({'error': 'Rate limit exceeded'}), 429

        return jsonify({
            'rate_limiting': rate_limiter.get_stats(),
            'system': {
                'mode': mode_manager.get_current_mode().value,
                'uptime': time.time() - app.start_time if hasattr(app, 'start_time') else 0
            }
        })

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(RateLimitExceeded)
def handle_rate_limit_exceeded(e):
    """Handle rate limit exceeded errors"""
    return jsonify({'error': str(e)}), 429

@app.errorhandler(404)
def handle_not_found(e):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def handle_internal_error(e):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {e}")
    return jsonify({'error': 'Internal server error'}), 500

def create_app():
    """Application factory"""
    init_app()
    app.start_time = time.time()
    return app

if __name__ == '__main__':
    # Development server
    app = create_app()

    # Configure for development
    app.config['DEBUG'] = os.getenv('DEBUG', 'false').lower() == 'true'
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))

    logger.info(f"Starting TinyCode API server on {host}:{port}")
    app.run(host=host, port=port, debug=app.config['DEBUG'])