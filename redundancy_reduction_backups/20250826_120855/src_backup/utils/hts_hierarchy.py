"""
HTS Hierarchy Management and Navigation System
"""
import logging
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

class HTSHierarchy:
    """
    Manages HTS code hierarchy and provides navigation utilities
    """
    
    def __init__(self, hts_data: List[Dict]):
        """
        Initialize with HTS reference data
        
        Args:
            hts_data: List of HTS code dictionaries from JSON
        """
        self.hts_data = hts_data
        self.codes_by_level = self._organize_by_level()
        self.hierarchy_map = self._build_hierarchy_map()
        self.description_map = self._build_description_map()
        
    def _organize_by_level(self) -> Dict[int, List[Dict]]:
        """Organize HTS codes by indent level"""
        levels = defaultdict(list)
        for item in self.hts_data:
            levels[item['indent']].append(item)
        
        # Sort each level by HTS number
        for level in levels:
            levels[level].sort(key=lambda x: x['htsno'])
            
        return dict(levels)
    
    def _build_hierarchy_map(self) -> Dict[str, Dict]:
        """Build mapping of parent-child relationships"""
        hierarchy = {}
        
        for item in self.hts_data:
            hts_code = item['htsno']
            hierarchy[hts_code] = {
                'item': item,
                'children': [],
                'parent': None
            }
        
        # Build parent-child relationships
        for item in self.hts_data:
            hts_code = item['htsno']
            parent_code = self._find_parent_code(hts_code, item['indent'])
            
            if parent_code and parent_code in hierarchy:
                hierarchy[hts_code]['parent'] = parent_code
                hierarchy[parent_code]['children'].append(hts_code)
        
        return hierarchy
    
    def _build_description_map(self) -> Dict[str, str]:
        """Build mapping of HTS codes to descriptions"""
        return {item['htsno']: item['description'] for item in self.hts_data}
    
    def _find_parent_code(self, hts_code: str, indent_level: int) -> Optional[str]:
        """Find the parent HTS code for a given code"""
        if indent_level == 0:
            return None
        
        # For HTS codes, parent is typically the code with one less level of detail
        if '.' in hts_code:
            # For detailed codes like 7301.10.00.00, parent might be 7301.10.00
            parts = hts_code.split('.')
            if len(parts) > 1:
                # Try progressively shorter parent codes
                for i in range(len(parts) - 1, 0, -1):
                    potential_parent = '.'.join(parts[:i])
                    if any(item['htsno'] == potential_parent for item in self.hts_data):
                        return potential_parent
        
        # For 4-digit codes, no parent in our data structure
        return None
    
    def get_codes_by_level(self, level: int) -> List[Dict]:
        """Get all HTS codes at a specific indent level"""
        return self.codes_by_level.get(level, [])
    
    def get_children(self, hts_code: str) -> List[str]:
        """Get all child codes for a given HTS code"""
        return self.hierarchy_map.get(hts_code, {}).get('children', [])
    
    def get_parent(self, hts_code: str) -> Optional[str]:
        """Get parent code for a given HTS code"""
        return self.hierarchy_map.get(hts_code, {}).get('parent')
    
    def get_description(self, hts_code: str) -> Optional[str]:
        """Get description for a given HTS code"""
        return self.description_map.get(hts_code)
    
    def get_full_item(self, hts_code: str) -> Optional[Dict]:
        """Get complete HTS item information"""
        hierarchy_info = self.hierarchy_map.get(hts_code)
        return hierarchy_info['item'] if hierarchy_info else None
    
    def get_path_to_root(self, hts_code: str) -> List[str]:
        """Get the full hierarchical path from code to root"""
        path = [hts_code]
        current_code = hts_code
        
        while True:
            parent = self.get_parent(current_code)
            if parent is None:
                break
            path.append(parent)
            current_code = parent
        
        return list(reversed(path))  # Root first
    
    def get_classification_context(self, hts_code: str) -> Dict:
        """
        Get rich context for a specific HTS code including hierarchy
        
        Returns:
            Dictionary with code info, parents, children, and descriptions
        """
        item = self.get_full_item(hts_code)
        if not item:
            return {}
        
        path = self.get_path_to_root(hts_code)
        children = self.get_children(hts_code)
        
        context = {
            'code': hts_code,
            'description': item['description'],
            'indent_level': item['indent'],
            'hierarchy_path': [
                {
                    'code': code,
                    'description': self.get_description(code),
                    'level': self.get_full_item(code)['indent']
                }
                for code in path
            ],
            'children_codes': [
                {
                    'code': child,
                    'description': self.get_description(child)
                }
                for child in children
            ],
            'tariff_info': {
                'general': item.get('general', ''),
                'special': item.get('special', ''),
                'other': item.get('other', ''),
                'units': item.get('units', [])
            }
        }
        
        return context
    
    def find_similar_codes(self, search_terms: List[str], max_results: int = 10) -> List[Dict]:
        """
        Find HTS codes with descriptions containing search terms
        
        Args:
            search_terms: List of terms to search for
            max_results: Maximum number of results to return
            
        Returns:
            List of matching HTS codes with relevance scores
        """
        matches = []
        search_terms_lower = [term.lower() for term in search_terms]
        
        for item in self.hts_data:
            description_lower = item['description'].lower()
            
            # Calculate relevance score based on term matches
            score = 0
            for term in search_terms_lower:
                if term in description_lower:
                    # Boost score for exact word matches
                    if f" {term} " in f" {description_lower} ":
                        score += 2
                    else:
                        score += 1
            
            if score > 0:
                matches.append({
                    'code': item['htsno'],
                    'description': item['description'],
                    'relevance_score': score,
                    'indent_level': item['indent']
                })
        
        # Sort by relevance score and indent level (prefer more specific codes)
        matches.sort(key=lambda x: (-x['relevance_score'], -x['indent_level']))
        
        return matches[:max_results]
    
    def get_chapter_codes(self, chapter: str) -> List[Dict]:
        """Get all codes belonging to a specific chapter (e.g., '73')"""
        chapter_codes = []
        for item in self.hts_data:
            if item['htsno'].startswith(chapter):
                chapter_codes.append(item)
        
        return sorted(chapter_codes, key=lambda x: (x['indent'], x['htsno']))
    
    def get_statistics(self) -> Dict:
        """Get statistics about the HTS hierarchy"""
        stats = {
            'total_codes': len(self.hts_data),
            'codes_by_level': {
                level: len(codes) for level, codes in self.codes_by_level.items()
            },
            'chapters_covered': len(set(
                item['htsno'][:2] for item in self.hts_data
                if len(item['htsno']) >= 2 and item['htsno'][:2].isdigit()
            ))
        }
        
        return stats 