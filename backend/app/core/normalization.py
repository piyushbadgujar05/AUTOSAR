import re
from typing import Optional

def normalize_version(version: Optional[str]) -> Optional[str]:
    """
    Normalize version strings to a canonical representation.
    e.g. 'v1.0' -> '1.0', 'V1.0' -> '1.0', '1' -> '1.0', '1.0.0' -> '1.0'
    Returns None if version is empty or represents an 'All' wildcard.
    """
    if not version:
        return None
    v = str(version).strip()
    if v.lower() in ["none", "all", "all versions", "*", ""]:
        return None
    
    # Strip leading 'v' or 'V' or 'ver' or 'rev'
    match = re.search(r'^(?:v|ver|revision|rev)?\.?\s*([0-9]+(?:\.[0-9]+)*)', v, re.IGNORECASE)
    if match:
        clean_v = match.group(1)
        parts = clean_v.split('.')
        if len(parts) == 1:
            return f"{parts[0]}.0"
        return clean_v
    
    return v

def normalize_project_name(project: Optional[str]) -> str:
    """
    Normalize project identifiers consistently.
    Maps variations like 'ADAS', 'adas_control_system' to 'ADAS Control System'.
    """
    if not project or str(project).strip().lower() in ["none", "all", "all projects", "*", ""]:
        return "ADAS Control System"
    p = str(project).strip()
    p_lower = p.lower().replace("-", " ").replace("_", " ")
    if "adas" in p_lower:
        return "ADAS Control System"
    return p

def extract_version_from_filename_or_text(filename: str, sample_text: str = "") -> str:
    """
    Extract canonical version (e.g. '1.0', '2.0') from filename or initial document text.
    Fallback to '1.0' if not detected.
    """
    # 1. Check filename: e.g. "Synthetic_ADAS_HLD_v1.0_Test_Document.pdf" -> "1.0"
    fn_match = re.search(r'[_\-\s]v?([0-9]+\.[0-9]+)', filename, re.IGNORECASE)
    if fn_match:
        return normalize_version(fn_match.group(1)) or "1.0"

    # 2. Check text: e.g. "Version: 1.0" or "Revision: 2.0"
    if sample_text:
        txt_match = re.search(r'(?:Version|Revision|Release)\s*[:\-]?\s*v?([0-9]+\.[0-9]+)', sample_text[:1500], re.IGNORECASE)
        if txt_match:
            return normalize_version(txt_match.group(1)) or "1.0"

    return "1.0"
