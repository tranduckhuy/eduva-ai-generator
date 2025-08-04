import os
from typing import Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.utils.logger import logger

class SimpleDocumentProcessor:
    """Production-ready document processor optimized"""
    
    def __init__(self):
        self.max_chars = int(os.getenv('MAX_CONTENT_CHARS', '50000'))  # ~14k tokens
        self.chunk_size = int(os.getenv('CHUNK_SIZE', '2000'))
        self.chunk_overlap = int(os.getenv('CHUNK_OVERLAP', '200'))
        self.max_chunks_to_process = int(os.getenv('MAX_CHUNKS_TO_PROCESS', '50'))
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " "]
        )
    
    async def process_content(self, content: str, topic: str) -> str:
        try:
            content_length = len(content)
            logger.info(f"Processing {content_length} chars for topic: {topic}")
            
            if content_length <= self.max_chars:
                logger.info("Content within limits - no processing needed")
                return content
            
            # Extract most relevant content
            processed = await self._extract_relevant_content(content, topic)
            reduction = (1 - len(processed) / content_length) * 100
            
            logger.info(f"Optimized: {content_length} → {len(processed)} chars ({reduction:.1f}% reduction)")
            return processed
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            return content[:self.max_chars]  # Fallback
    
    async def _extract_relevant_content(self, content: str, topic: str) -> str:
        """Extract most relevant chunks based on topic"""
        try:
            chunks = self.text_splitter.split_text(content)
            
            if len(chunks) > self.max_chunks_to_process:
                chunks = chunks[:self.max_chunks_to_process]
            
            # Score chunks by relevance
            topic_keywords = set(topic.lower().split())
            scored_chunks = []
            
            for i, chunk in enumerate(chunks):
                score = self._score_chunk(chunk, topic_keywords)
                scored_chunks.append((score, i, chunk))
            
            # Sort by score (highest first)
            scored_chunks.sort(key=lambda x: -x[0])
            
            # Select chunks that fit within limit
            selected = []
            total_length = 0
            
            for score, index, chunk in scored_chunks:
                if total_length + len(chunk) <= self.max_chars:
                    selected.append((index, chunk))
                    total_length += len(chunk)
                else:
                    break
            
            # Sort by original order
            selected.sort(key=lambda x: x[0])
            
            result = "\n\n".join(chunk for _, chunk in selected)
            logger.info(f"Selected {len(selected)} most relevant chunks")
            
            return result
            
        except Exception as e:
            logger.error(f"Content extraction failed: {e}")
            return content[:self.max_chars]
    
    def _score_chunk(self, chunk: str, topic_keywords: set) -> float:
        """Score chunk relevance to topic"""
        chunk_words = set(chunk.lower().split())
        score = 0.0
        
        # Topic keyword matches (highest priority)
        matches = len(topic_keywords.intersection(chunk_words))
        score += matches * 15
        
        # Educational terms
        edu_terms = {
            'định nghĩa', 'khái niệm', 'ví dụ', 'phương pháp', 'công thức',
            'definition', 'concept', 'example', 'method', 'formula'
        }
        edu_matches = len(edu_terms.intersection(chunk_words))
        score += edu_matches * 8
        
        # Structure indicators
        if any(indicator in chunk for indicator in ['###', '##', '1.', '2.', '•']):
            score += 5
        
        # Length preference (500-3000 chars is ideal)
        chunk_len = len(chunk)
        if 500 <= chunk_len <= 3000:
            score += 3
        elif chunk_len < 200:
            score *= 0.3  # Penalty for very short chunks
        
        return score
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for Vietnamese/English content"""
        words = len(text.split())
        # More accurate for mixed Vietnamese/English
        return int(max(words * 1.2, len(text) / 3.5))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processor configuration stats"""
        return {
            "max_chars": self.max_chars,
            "max_tokens_estimate": self.estimate_tokens("x" * self.max_chars),
            "chunk_size": self.chunk_size,
            "max_chunks": self.max_chunks_to_process,
            "concurrent_users_supported": 16,
            "optimized_for": "Gemini Free Tier"
        }
