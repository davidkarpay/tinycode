"""Text chunking system for RAG with intelligent splitting strategies"""

import re
import tiktoken
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
import logging
from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)

class TextChunker:
    """Intelligent text chunking with multiple strategies"""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        tokenizer_name: str = "cl100k_base",
        separators: Optional[List[str]] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.get_encoding(tokenizer_name)
        except:
            # Fallback to basic word counting
            self.tokenizer = None

        # Default separators in order of preference
        self.separators = separators or [
            "\n\n\n",  # Multiple newlines
            "\n\n",    # Double newlines
            "\n",      # Single newlines
            ". ",      # Sentences
            "! ",      # Exclamations
            "? ",      # Questions
            "; ",      # Semicolons
            ", ",      # Commas
            " ",       # Spaces
            ""         # Character level (last resort)
        ]

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Approximate token count (4 chars ≈ 1 token)
            return len(text) // 4

    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        strategy: str = "recursive"
    ) -> List[Dict[str, Any]]:
        """Chunk text using specified strategy"""

        if strategy == "recursive":
            return self._recursive_chunk(text, metadata)
        elif strategy == "semantic":
            return self._semantic_chunk(text, metadata)
        elif strategy == "fixed":
            return self._fixed_chunk(text, metadata)
        elif strategy == "heading":
            return self._heading_chunk(text, metadata)
        elif strategy == "code":
            return self._code_chunk(text, metadata)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")

    def _recursive_chunk(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Recursively split text using multiple separators"""

        chunks = []

        def _split_recursive(text: str, separators: List[str]) -> List[str]:
            if not separators:
                return [text]

            separator = separators[0]
            remaining_seps = separators[1:]

            if separator == "":
                # Character-level split as last resort
                return [text[i:i+self.chunk_size] for i in range(0, len(text), self.chunk_size)]

            splits = text.split(separator)

            # If we can't split meaningfully, try next separator
            if len(splits) == 1:
                return _split_recursive(text, remaining_seps)

            # Reconstruct with separator
            good_splits = []
            for i, split in enumerate(splits):
                if i < len(splits) - 1:
                    split += separator
                good_splits.append(split)

            # Merge small chunks and split large ones
            final_splits = []
            current_chunk = ""

            for split in good_splits:
                potential_chunk = current_chunk + split

                if self.count_tokens(potential_chunk) <= self.chunk_size:
                    current_chunk = potential_chunk
                else:
                    if current_chunk:
                        final_splits.append(current_chunk)

                    # If single split is too large, recurse
                    if self.count_tokens(split) > self.chunk_size:
                        final_splits.extend(_split_recursive(split, remaining_seps))
                    else:
                        current_chunk = split

            if current_chunk:
                final_splits.append(current_chunk)

            return final_splits

        text_chunks = _split_recursive(text, self.separators)

        # Create overlapping chunks
        for i, chunk_text in enumerate(text_chunks):
            chunk_metadata = {
                "chunk_index": i,
                "total_chunks": len(text_chunks),
                "chunk_size": len(chunk_text),
                "token_count": self.count_tokens(chunk_text),
                "strategy": "recursive"
            }

            if metadata:
                chunk_metadata.update(metadata)

            # Add overlap from previous chunk
            if i > 0 and self.chunk_overlap > 0:
                prev_chunk = text_chunks[i-1]
                overlap_text = prev_chunk[-self.chunk_overlap:]
                chunk_text = overlap_text + chunk_text
                chunk_metadata["has_overlap"] = True
            else:
                chunk_metadata["has_overlap"] = False

            chunks.append({
                "content": chunk_text.strip(),
                "metadata": chunk_metadata
            })

        return chunks

    def _semantic_chunk(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Chunk text based on semantic boundaries (sentences/paragraphs)"""

        # Split into sentences first
        sentence_endings = r'[.!?]+\s+'
        sentences = re.split(sentence_endings, text)

        chunks = []
        current_chunk = ""
        chunk_index = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            potential_chunk = current_chunk + " " + sentence if current_chunk else sentence

            if self.count_tokens(potential_chunk) <= self.chunk_size:
                current_chunk = potential_chunk
            else:
                if current_chunk:
                    chunk_metadata = {
                        "chunk_index": chunk_index,
                        "chunk_size": len(current_chunk),
                        "token_count": self.count_tokens(current_chunk),
                        "strategy": "semantic"
                    }

                    if metadata:
                        chunk_metadata.update(metadata)

                    chunks.append({
                        "content": current_chunk.strip(),
                        "metadata": chunk_metadata
                    })

                    chunk_index += 1

                current_chunk = sentence

        # Add final chunk
        if current_chunk:
            chunk_metadata = {
                "chunk_index": chunk_index,
                "chunk_size": len(current_chunk),
                "token_count": self.count_tokens(current_chunk),
                "strategy": "semantic"
            }

            if metadata:
                chunk_metadata.update(metadata)

            chunks.append({
                "content": current_chunk.strip(),
                "metadata": chunk_metadata
            })

        return chunks

    def _fixed_chunk(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Split text into fixed-size chunks with overlap"""

        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]

            chunk_metadata = {
                "chunk_index": chunk_index,
                "start_pos": start,
                "end_pos": min(end, len(text)),
                "chunk_size": len(chunk_text),
                "token_count": self.count_tokens(chunk_text),
                "strategy": "fixed"
            }

            if metadata:
                chunk_metadata.update(metadata)

            chunks.append({
                "content": chunk_text.strip(),
                "metadata": chunk_metadata
            })

            start = end - self.chunk_overlap
            chunk_index += 1

            if end >= len(text):
                break

        return chunks

    def _heading_chunk(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Chunk text based on headings (Markdown/HTML style)"""

        # Detect heading patterns
        heading_patterns = [
            r'^#{1,6}\s+(.+)$',  # Markdown headings
            r'^(.+)\n[=-]+$',    # Setext-style headings
            r'<h[1-6][^>]*>(.+?)</h[1-6]>',  # HTML headings
        ]

        # Find all headings
        headings = []
        for pattern in heading_patterns:
            for match in re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE):
                headings.append({
                    "start": match.start(),
                    "end": match.end(),
                    "text": match.group(1) if match.groups() else match.group(0),
                    "level": self._get_heading_level(match.group(0))
                })

        # Sort headings by position
        headings.sort(key=lambda x: x["start"])

        if not headings:
            # No headings found, fall back to recursive chunking
            return self._recursive_chunk(text, metadata)

        chunks = []

        for i, heading in enumerate(headings):
            # Determine section content
            start_pos = heading["start"]
            if i + 1 < len(headings):
                end_pos = headings[i + 1]["start"]
            else:
                end_pos = len(text)

            section_text = text[start_pos:end_pos].strip()

            # If section is too large, sub-chunk it
            if self.count_tokens(section_text) > self.chunk_size:
                sub_chunks = self._recursive_chunk(section_text, metadata)
                for j, sub_chunk in enumerate(sub_chunks):
                    sub_chunk["metadata"].update({
                        "heading": heading["text"],
                        "heading_level": heading["level"],
                        "section_index": i,
                        "sub_chunk_index": j,
                        "strategy": "heading"
                    })
                chunks.extend(sub_chunks)
            else:
                chunk_metadata = {
                    "heading": heading["text"],
                    "heading_level": heading["level"],
                    "section_index": i,
                    "chunk_size": len(section_text),
                    "token_count": self.count_tokens(section_text),
                    "strategy": "heading"
                }

                if metadata:
                    chunk_metadata.update(metadata)

                chunks.append({
                    "content": section_text,
                    "metadata": chunk_metadata
                })

        return chunks

    def _code_chunk(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Chunk code while preserving function/class boundaries"""

        # Language-specific patterns
        patterns = {
            'python': [
                r'^(class\s+\w+.*?:)',
                r'^(def\s+\w+.*?:)',
                r'^(@\w+.*\n)',  # Decorators
            ],
            'javascript': [
                r'^(class\s+\w+.*?\{)',
                r'^(function\s+\w+.*?\{)',
                r'^(const\s+\w+\s*=\s*.*?=>)',
            ],
            'java': [
                r'^(public\s+class\s+\w+.*?\{)',
                r'^(public\s+.*?\s+\w+\s*\(.*?\)\s*\{)',
            ]
        }

        # Try to detect language from metadata
        language = None
        if metadata and 'extension' in metadata:
            ext = metadata['extension'].lower()
            if ext in ['.py']:
                language = 'python'
            elif ext in ['.js', '.ts']:
                language = 'javascript'
            elif ext in ['.java']:
                language = 'java'

        # Split by functions/classes if language detected
        if language and language in patterns:
            boundaries = []
            for pattern in patterns[language]:
                for match in re.finditer(pattern, text, re.MULTILINE):
                    boundaries.append(match.start())

            boundaries.sort()

            if boundaries:
                chunks = []
                for i, start in enumerate(boundaries):
                    if i + 1 < len(boundaries):
                        end = boundaries[i + 1]
                    else:
                        end = len(text)

                    chunk_text = text[start:end].strip()

                    if self.count_tokens(chunk_text) > self.chunk_size:
                        # Sub-chunk large functions
                        sub_chunks = self._recursive_chunk(chunk_text, metadata)
                        chunks.extend(sub_chunks)
                    else:
                        chunk_metadata = {
                            "chunk_index": i,
                            "language": language,
                            "chunk_size": len(chunk_text),
                            "token_count": self.count_tokens(chunk_text),
                            "strategy": "code"
                        }

                        if metadata:
                            chunk_metadata.update(metadata)

                        chunks.append({
                            "content": chunk_text,
                            "metadata": chunk_metadata
                        })

                return chunks

        # Fall back to recursive chunking
        return self._recursive_chunk(text, metadata)

    def _get_heading_level(self, heading_text: str) -> int:
        """Extract heading level from text"""
        if heading_text.startswith('#'):
            return len(heading_text) - len(heading_text.lstrip('#'))
        elif '<h' in heading_text.lower():
            match = re.search(r'<h([1-6])', heading_text.lower())
            return int(match.group(1)) if match else 1
        else:
            return 1

    def chunk_documents(
        self,
        documents: List[Dict[str, Any]],
        strategy: str = "adaptive"
    ) -> List[Dict[str, Any]]:
        """Chunk multiple documents with strategy selection"""

        all_chunks = []

        for doc in documents:
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})

            # Choose strategy based on document type
            if strategy == "adaptive":
                file_ext = metadata.get("extension", "").lower()

                if file_ext in ['.py', '.js', '.java', '.cpp', '.go', '.rs']:
                    chunk_strategy = "code"
                elif file_ext in ['.md', '.html', '.htm']:
                    chunk_strategy = "heading"
                elif file_ext in ['.txt', '.doc', '.docx']:
                    chunk_strategy = "semantic"
                else:
                    chunk_strategy = "recursive"
            else:
                chunk_strategy = strategy

            try:
                chunks = self.chunk_text(content, metadata, chunk_strategy)
                all_chunks.extend(chunks)
            except Exception as e:
                logger.error(f"Error chunking document {metadata.get('filename', 'unknown')}: {e}")
                # Add as single chunk if chunking fails
                all_chunks.append({
                    "content": content,
                    "metadata": {**metadata, "chunking_error": str(e)}
                })

        console.print(f"[green]Created {len(all_chunks)} chunks from {len(documents)} documents[/green]")
        return all_chunks