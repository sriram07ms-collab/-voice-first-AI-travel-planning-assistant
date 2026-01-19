"""
Wikivoyage scraper for city guides and travel tips.
Extracts sections from Wikivoyage pages and prepares them for RAG.
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import logging
import re
from urllib.parse import quote, urljoin

logger = logging.getLogger(__name__)

WIKIVOYAGE_BASE_URL = "https://en.wikivoyage.org/wiki/"


def _clean_text(text: str) -> str:
    """
    Clean extracted text from HTML.
    
    Args:
        text: Raw text from HTML
    
    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove references like [1], [2]
    text = re.sub(r'\[\d+\]', '', text)
    # Remove edit links
    text = re.sub(r'\[edit\]', '', text)
    # Strip
    text = text.strip()
    return text


def _extract_section_content(soup: BeautifulSoup, section_id: str) -> str:
    """
    Extract content from a specific section.
    
    Args:
        soup: BeautifulSoup object
        section_id: Section ID or heading text
    
    Returns:
        Section content as text
    """
    # Try to find by ID first
    section = soup.find(id=section_id)
    
    if not section:
        # Try to find by heading text
        headings = soup.find_all(['h2', 'h3', 'h4'])
        for heading in headings:
            if section_id.lower() in heading.get_text().lower():
                section = heading
                break
    
    if not section:
        return ""
    
    # Get all content until next heading
    content_parts = []
    current = section.next_sibling
    
    while current:
        if current.name in ['h2', 'h3', 'h4']:
            break
        
        if current.name == 'p':
            text = _clean_text(current.get_text())
            if text:
                content_parts.append(text)
        
        current = current.next_sibling
    
    return "\n\n".join(content_parts)


def scrape_city_page(city: str) -> Dict[str, str]:
    """
    Scrape Wikivoyage page for a city.
    
    Args:
        city: City name
    
    Returns:
        Dictionary mapping section names to content
    """
    try:
        # Build URL
        city_encoded = city.replace(' ', '_')
        url = urljoin(WIKIVOYAGE_BASE_URL, city_encoded)
        
        logger.info(f"Scraping Wikivoyage page: {url}")
        
        # Make request
        headers = {
            "User-Agent": "Voice-First-Travel-Assistant/1.0 (Educational Project)"
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract sections
        sections = {}
        
        # Common sections to extract
        section_names = [
            "Understand",
            "Get in",
            "Get around",
            "See",
            "Do",
            "Buy",
            "Eat",
            "Drink",
            "Sleep",
            "Stay safe",
            "Cope",
            "Go next"
        ]
        
        for section_name in section_names:
            content = _extract_section_content(soup, section_name)
            if content:
                sections[section_name] = content
                logger.debug(f"Extracted {section_name} section ({len(content)} chars)")
        
        # Also extract introduction (first paragraph)
        intro = soup.find('div', class_='mw-parser-output')
        if intro:
            first_p = intro.find('p')
            if first_p:
                intro_text = _clean_text(first_p.get_text())
                if intro_text:
                    sections["Introduction"] = intro_text
        
        logger.info(f"Extracted {len(sections)} sections from {city} page")
        return sections
    
    except requests.RequestException as e:
        logger.error(f"Error scraping Wikivoyage page: {e}")
        raise Exception(f"Failed to scrape Wikivoyage page for {city}: {e}")
    except Exception as e:
        logger.error(f"Error parsing Wikivoyage page: {e}", exc_info=True)
        raise


def chunk_text(text: str, max_tokens: int = 500, overlap: int = 50) -> List[str]:
    """
    Chunk text into smaller pieces for RAG.
    Uses approximate token counting (1 token ≈ 4 characters).
    
    Args:
        text: Text to chunk
        max_tokens: Maximum tokens per chunk
        overlap: Number of tokens to overlap between chunks
    
    Returns:
        List of text chunks
    """
    # Approximate: 1 token ≈ 4 characters
    max_chars = max_tokens * 4
    overlap_chars = overlap * 4
    
    # Split by paragraphs first
    paragraphs = text.split('\n\n')
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for paragraph in paragraphs:
        para_length = len(paragraph)
        
        if current_length + para_length > max_chars and current_chunk:
            # Save current chunk
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append(chunk_text)
            
            # Start new chunk with overlap
            if overlap_chars > 0 and len(current_chunk) > 0:
                # Keep last part for overlap
                overlap_text = '\n\n'.join(current_chunk[-1:])
                current_chunk = [overlap_text]
                current_length = len(overlap_text)
            else:
                current_chunk = []
                current_length = 0
        
        current_chunk.append(paragraph)
        current_length += para_length + 2  # +2 for '\n\n'
    
    # Add remaining chunk
    if current_chunk:
        chunk_text = '\n\n'.join(current_chunk)
        chunks.append(chunk_text)
    
    return chunks


def extract_sections(html: str) -> Dict[str, str]:
    """
    Extract sections from HTML content.
    
    Args:
        html: HTML content
    
    Returns:
        Dictionary mapping section names to content
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    sections = {}
    section_names = [
        "Understand", "Get in", "Get around", "See", "Do",
        "Buy", "Eat", "Drink", "Sleep", "Stay safe", "Cope", "Go next"
    ]
    
    for section_name in section_names:
        content = _extract_section_content(soup, section_name)
        if content:
            sections[section_name] = content
    
    return sections


def get_city_url(city: str) -> str:
    """
    Get Wikivoyage URL for a city.
    
    Args:
        city: City name
    
    Returns:
        Full URL to city page
    """
    city_encoded = city.replace(' ', '_')
    return urljoin(WIKIVOYAGE_BASE_URL, city_encoded)
