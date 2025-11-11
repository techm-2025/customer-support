"""
Utility functions for data formatting and parsing
"""
import re
from typing import Tuple


def split_name(name: str) -> Tuple[str, str]:
    """
    Split full name into first and last name
    
    Args:
        name: Full name string
        
    Returns:
        Tuple of (first_name, last_name)
    """
    parts = name.strip().split()
    if len(parts) == 1:
        return parts[0], ""
    elif len(parts) == 2:
        return parts[0], parts[1]
    else:
        return parts[0], " ".join(parts[1:])


def format_date_of_birth(dob: str) -> str:
    """
    Format date of birth to YYYY-MM-DD format
    
    Args:
        dob: Date string in various formats (MM/DD/YYYY or YYYY-MM-DD)
        
    Returns:
        Formatted date string in YYYY-MM-DD format
    """
    if not dob:
        return ""
    
    # Handle MM/DD/YYYY format
    if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', dob):
        month, day, year = dob.split('/')
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    
    # Already in YYYY-MM-DD format
    if re.match(r'^\d{4}-\d{1,2}-\d{1,2}$', dob):
        return dob
    
    # Return as-is if format unknown
    return dob


def format_state(state: str) -> str:
    """
    Format state name to title case
    
    Args:
        state: State name string
        
    Returns:
        Title-cased state name
    """
    return state.strip().title() if state else ""


def clean_provider_name(provider_name: str) -> str:
    """
    Remove titles from provider name (Dr., MD, DO, etc.)
    
    Args:
        provider_name: Full provider name with potential titles
        
    Returns:
        Cleaned provider name
    """
    return re.sub(r'\b(Dr\.?|MD|DO)\b', '', provider_name, flags=re.IGNORECASE).strip()


def extract_pattern(text: str, patterns: list) -> str:
    """
    Extract text matching any of the provided regex patterns
    
    Args:
        text: Text to search
        patterns: List of regex patterns to try
        
    Returns:
        Matched text or empty string
    """
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return match.group(1).strip()
    return ""


def extract_copay(text: str) -> str:
    """
    Extract copay amount from text
    
    Args:
        text: Text containing copay information
        
    Returns:
        Copay amount as string
    """
    patterns = [
        r'co-?pay[:\s]*\$?([0-9,]+)',
        r'copayment[:\s]*\$?([0-9,]+)',
        r'patient\s+responsibility[:\s]*\$?([0-9,]+)'
    ]
    return extract_pattern(text, patterns)


def extract_payer(text: str) -> str:
    """
    Extract payer/insurance name from text
    
    Args:
        text: Text containing payer information
        
    Returns:
        Payer name in title case
    """
    patterns = [
        r'payer[:\s]*([^\n,;]+)',
        r'insurance[:\s]*([^\n,;]+)',
        r'plan[:\s]*([^\n,;]+)'
    ]
    result = extract_pattern(text, patterns)
    return result.title() if result else ""


def extract_member_id(text: str) -> str:
    """
    Extract member/policy ID from text
    
    Args:
        text: Text containing member ID
        
    Returns:
        Member ID in uppercase
    """
    patterns = [
        r'member\s*id[:\s]*([a-za-z0-9\-]+)',
        r'subscriber\s*id[:\s]*([a-za-z0-9\-]+)',
        r'policy\s*id[:\s]*([a-za-z0-9\-]+)',
        r'policy[:\s]*([a-za-z0-9\-]+)'
    ]
    result = extract_pattern(text, patterns)
    return result.upper() if result else ""