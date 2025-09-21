#!/usr/bin/env python3
"""
TinyCode Offline Model Verification Script

Verifies that all required models are available for offline operation:
- Ollama models (tinyllama:latest)
- Embedding models (all-MiniLM-L6-v2)
- FAISS vector operations
- Model functionality tests
"""

import os
import sys
import json
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional

try:
    import ollama
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    import time
except ImportError as e:
    print(f"❌ Missing required package: {e}")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)

console = Console()

class ModelVerifier:
    def __init__(self):
        self.ollama_host = os.getenv('OLLAMA_HOST', 'localhost')
        self.ollama_port = os.getenv('OLLAMA_PORT', '11434')
        self.ollama_url = f"http://{self.ollama_host}:{self.ollama_port}"
        self.required_models = {
            'ollama': ['tinyllama:latest'],
            'embeddings': ['all-MiniLM-L6-v2']
        }
        self.results = {}

    def check_ollama_service(self) -> bool:
        """Check if Ollama service is running"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def get_ollama_models(self) -> List[str]:
        """Get list of available Ollama models"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except Exception:
            return []

    def test_ollama_model(self, model_name: str) -> Tuple[bool, Optional[str]]:
        """Test if Ollama model responds correctly"""
        try:
            client = ollama.Client(host=self.ollama_url)
            response = client.generate(
                model=model_name,
                prompt="Hello, respond with 'OK'",
                options={'temperature': 0, 'num_predict': 5}
            )

            if response and 'response' in response:
                return True, response['response'].strip()
            return False, "No response"
        except Exception as e:
            return False, str(e)

    def check_embedding_model(self, model_name: str) -> Tuple[bool, Dict]:
        """Check if embedding model is available and functional"""
        try:
            # Load model
            model = SentenceTransformer(model_name)

            # Test encoding
            test_texts = ["Hello world", "This is a test"]
            embeddings = model.encode(test_texts)

            # Verify output
            if embeddings is not None and len(embeddings) == 2:
                return True, {
                    'dimension': embeddings.shape[1],
                    'type': str(embeddings.dtype),
                    'cache_path': model.cache_folder
                }
            return False, {'error': 'Invalid embeddings output'}
        except Exception as e:
            return False, {'error': str(e)}

    def test_faiss_operations(self) -> Tuple[bool, Dict]:
        """Test FAISS vector operations"""
        try:
            # Create test embeddings
            dimension = 384  # all-MiniLM-L6-v2 dimension
            test_vectors = np.random.random((100, dimension)).astype('float32')

            # Create FAISS index
            index = faiss.IndexFlatL2(dimension)
            index.add(test_vectors)

            # Test search
            query_vector = np.random.random((1, dimension)).astype('float32')
            distances, indices = index.search(query_vector, k=5)

            return True, {
                'dimension': dimension,
                'vectors_count': index.ntotal,
                'search_results': len(indices[0])
            }
        except Exception as e:
            return False, {'error': str(e)}

    def check_model_cache_sizes(self) -> Dict:
        """Check model cache directories and sizes"""
        cache_info = {}

        # HuggingFace cache
        hf_cache = Path.home() / '.cache' / 'huggingface' / 'hub'
        if hf_cache.exists():
            for model_dir in hf_cache.glob('models--*'):
                if 'sentence-transformers' in model_dir.name:
                    size = sum(f.stat().st_size for f in model_dir.rglob('*') if f.is_file())
                    cache_info[model_dir.name] = {
                        'path': str(model_dir),
                        'size_mb': round(size / (1024 * 1024), 2)
                    }

        # Ollama cache
        ollama_cache = Path.home() / '.ollama'
        if ollama_cache.exists():
            size = sum(f.stat().st_size for f in ollama_cache.rglob('*') if f.is_file())
            cache_info['ollama'] = {
                'path': str(ollama_cache),
                'size_gb': round(size / (1024 * 1024 * 1024), 2)
            }

        return cache_info

    def run_verification(self) -> Dict:
        """Run complete model verification"""
        results = {
            'ollama_service': False,
            'ollama_models': {},
            'embedding_models': {},
            'faiss_test': {},
            'cache_info': {},
            'overall_status': 'FAIL'
        }

        console.print("[bold blue]🔍 TinyCode Offline Model Verification[/bold blue]")
        console.print("=" * 60)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:

            # Check Ollama service
            task1 = progress.add_task("Checking Ollama service...", total=None)
            results['ollama_service'] = self.check_ollama_service()
            progress.update(task1, completed=True)

            if results['ollama_service']:
                # Check Ollama models
                task2 = progress.add_task("Verifying Ollama models...", total=None)
                available_models = self.get_ollama_models()

                for model in self.required_models['ollama']:
                    if model in available_models:
                        success, response = self.test_ollama_model(model)
                        results['ollama_models'][model] = {
                            'available': True,
                            'functional': success,
                            'test_response': response
                        }
                    else:
                        results['ollama_models'][model] = {
                            'available': False,
                            'functional': False,
                            'test_response': 'Model not found'
                        }
                progress.update(task2, completed=True)

            # Check embedding models
            task3 = progress.add_task("Verifying embedding models...", total=None)
            for model in self.required_models['embeddings']:
                success, info = self.check_embedding_model(model)
                results['embedding_models'][model] = {
                    'available': success,
                    'info': info
                }
            progress.update(task3, completed=True)

            # Test FAISS
            task4 = progress.add_task("Testing FAISS operations...", total=None)
            success, info = self.test_faiss_operations()
            results['faiss_test'] = {
                'functional': success,
                'info': info
            }
            progress.update(task4, completed=True)

            # Check cache info
            task5 = progress.add_task("Checking model caches...", total=None)
            results['cache_info'] = self.check_model_cache_sizes()
            progress.update(task5, completed=True)

        # Determine overall status
        ollama_ok = results['ollama_service'] and all(
            model_info.get('functional', False)
            for model_info in results['ollama_models'].values()
        )

        embeddings_ok = all(
            model_info.get('available', False)
            for model_info in results['embedding_models'].values()
        )

        faiss_ok = results['faiss_test'].get('functional', False)

        if ollama_ok and embeddings_ok and faiss_ok:
            results['overall_status'] = 'PASS'
        elif embeddings_ok and faiss_ok:
            results['overall_status'] = 'PARTIAL'

        return results

    def display_results(self, results: Dict):
        """Display verification results in a formatted table"""

        # Overall status
        status_color = "green" if results['overall_status'] == 'PASS' else \
                      "yellow" if results['overall_status'] == 'PARTIAL' else "red"

        console.print(f"\n[bold {status_color}]Overall Status: {results['overall_status']}[/bold {status_color}]")

        # Ollama Service
        table = Table(title="🚀 Ollama Service Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Details", style="green")

        service_status = "✅ Running" if results['ollama_service'] else "❌ Not Running"
        table.add_row("Ollama Service", service_status, f"{self.ollama_url}")

        console.print(table)

        # Ollama Models
        if results['ollama_models']:
            table = Table(title="🤖 Ollama Models")
            table.add_column("Model", style="cyan")
            table.add_column("Available", style="magenta")
            table.add_column("Functional", style="yellow")
            table.add_column("Test Response", style="green")

            for model, info in results['ollama_models'].items():
                available = "✅" if info.get('available') else "❌"
                functional = "✅" if info.get('functional') else "❌"
                response = info.get('test_response', 'N/A')[:50]
                table.add_row(model, available, functional, response)

            console.print(table)

        # Embedding Models
        table = Table(title="🔤 Embedding Models")
        table.add_column("Model", style="cyan")
        table.add_column("Available", style="magenta")
        table.add_column("Dimension", style="yellow")
        table.add_column("Cache Size", style="green")

        for model, info in results['embedding_models'].items():
            available = "✅" if info.get('available') else "❌"
            model_info = info.get('info', {})
            dimension = str(model_info.get('dimension', 'N/A'))

            # Find cache size
            cache_size = 'N/A'
            for cache_name, cache_info in results['cache_info'].items():
                if model.replace('/', '--').replace('-', '--') in cache_name:
                    cache_size = f"{cache_info.get('size_mb', 0)} MB"
                    break

            table.add_row(model, available, dimension, cache_size)

        console.print(table)

        # FAISS Test
        table = Table(title="🔍 FAISS Vector Operations")
        table.add_column("Test", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Details", style="green")

        faiss_status = "✅ Functional" if results['faiss_test'].get('functional') else "❌ Failed"
        faiss_info = results['faiss_test'].get('info', {})

        if 'error' in faiss_info:
            details = f"Error: {faiss_info['error']}"
        else:
            details = f"Dim: {faiss_info.get('dimension', 'N/A')}, " \
                     f"Vectors: {faiss_info.get('vectors_count', 'N/A')}, " \
                     f"Search: {faiss_info.get('search_results', 'N/A')}"

        table.add_row("Vector Operations", faiss_status, details)
        console.print(table)

        # Cache Information
        if results['cache_info']:
            table = Table(title="💾 Model Cache Information")
            table.add_column("Cache", style="cyan")
            table.add_column("Path", style="magenta")
            table.add_column("Size", style="green")

            for cache_name, cache_info in results['cache_info'].items():
                path = cache_info.get('path', 'N/A')
                if 'size_gb' in cache_info:
                    size = f"{cache_info['size_gb']} GB"
                else:
                    size = f"{cache_info.get('size_mb', 0)} MB"

                table.add_row(cache_name, path, size)

            console.print(table)

def main():
    """Main verification function"""
    verifier = ModelVerifier()

    try:
        results = verifier.run_verification()
        verifier.display_results(results)

        # Save results to file
        output_file = Path('model_verification_results.json')
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        console.print(f"\n📄 Results saved to: {output_file}")

        # Exit code based on status
        if results['overall_status'] == 'PASS':
            console.print("\n[bold green]✅ All models verified for offline operation![/bold green]")
            sys.exit(0)
        elif results['overall_status'] == 'PARTIAL':
            console.print("\n[bold yellow]⚠️ Partial verification - some components may not work offline[/bold yellow]")
            sys.exit(1)
        else:
            console.print("\n[bold red]❌ Verification failed - models not ready for offline operation[/bold red]")
            sys.exit(2)

    except KeyboardInterrupt:
        console.print("\n[bold red]❌ Verification interrupted by user[/bold red]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[bold red]❌ Verification failed with error: {e}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()