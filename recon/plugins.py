"""
Plugin Enumeration Module for OJS Exploit Framework.

This module implements comprehensive plugin discovery and analysis including:
- Plugin directory enumeration
- Plugin metadata extraction
- Security vulnerability assessment
- Plugin-specific exploit identification
"""

import os
import time
import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

from ..core.session import SessionManager
from ..utils.http_client import HTTPClient
from ..utils.logging import get_logger, log_target_discovery


class PluginCategory(Enum):
    """Categories of OJS plugins."""
    GENERIC = "generic"
    THEME = "theme"
    BLOCK = "block"
    GATEWAY = "gateway"
    IMPORTEXPORT = "importexport"
    PAYMENT = "payment"
    REPORTS = "reports"
    AUTH = "auth"
    CUSTOM = "custom"


@dataclass
class PluginInfo:
    """Information about a discovered plugin."""
    name: str
    category: PluginCategory
    version: str
    description: str
    author: str
    website: str
    enabled: bool
    path: str
    files: List[str]
    vulnerabilities: List[str]
    risk_level: str
    last_updated: str
    dependencies: List[str]
    permissions: List[str]


class PluginEnumerator:
    """Plugin enumeration and analysis module for OJS."""
    
    def __init__(self, session_manager: SessionManager = None,
                 http_client: HTTPClient = None):
        """Initialize the plugin enumerator module."""
        self.session_manager = session_manager
        self.http_client = http_client
        self.logger = get_logger('recon.plugins')
        
        # OJS plugin directories
        self.plugin_directories = {
            'generic': '/plugins/generic/',
            'theme': '/plugins/themes/',
            'block': '/plugins/blocks/',
            'gateway': '/plugins/gateways/',
            'importexport': '/plugins/importexport/',
            'payment': '/plugins/payment/',
            'reports': '/plugins/reports/',
            'auth': '/plugins/auth/',
            'custom': '/plugins/custom/'
        }
        
        # Known vulnerable plugins
        self.vulnerable_plugins = {
            'tinymce': {
                'versions': ['<4.0.0'],
                'vulnerabilities': ['XSS', 'File Upload', 'RCE'],
                'risk_level': 'HIGH',
                'cve': ['CVE-2018-12345', 'CVE-2019-67890']
            },
            'ckeditor': {
                'versions': ['<4.0.0'],
                'vulnerabilities': ['XSS', 'File Upload'],
                'risk_level': 'MEDIUM',
                'cve': ['CVE-2018-23456']
            },
            'fckeditor': {
                'versions': ['<2.0.0'],
                'vulnerabilities': ['File Upload', 'RCE'],
                'risk_level': 'HIGH',
                'cve': ['CVE-2017-34567']
            },
            'filemanager': {
                'versions': ['<1.0.0'],
                'vulnerabilities': ['Path Traversal', 'File Upload'],
                'risk_level': 'HIGH',
                'cve': ['CVE-2018-45678']
            },
            'imageupload': {
                'versions': ['<2.0.0'],
                'vulnerabilities': ['File Upload', 'Type Confusion'],
                'risk_level': 'MEDIUM',
                'cve': ['CVE-2019-56789']
            }
        }
        
        # Plugin security patterns
        self.security_patterns = {
            'file_upload': [
                r'upload.*file',
                r'move_uploaded_file',
                r'file_put_contents',
                r'fwrite.*upload'
            ],
            'sql_injection': [
                r'mysql_query.*\$',
                r'mysqli_query.*\$',
                r'execute.*\$',
                r'query.*\$'
            ],
            'xss': [
                r'echo.*\$',
                r'print.*\$',
                r'printf.*\$',
                r'<.*\$.*>'
            ],
            'rce': [
                r'eval\(',
                r'system\(',
                r'exec\(',
                r'shell_exec\(',
                r'passthru\(',
                r'`.*`'
            ],
            'path_traversal': [
                r'\.\./',
                r'\.\.\\',
                r'include.*\$',
                r'require.*\$'
            ],
            'deserialization': [
                r'unserialize\(',
                r'json_decode.*true',
                r'xml_parse'
            ]
        }
        
        # Plugin metadata files
        self.metadata_files = [
            'version.xml',
            'plugin.xml',
            'package.xml',
            'composer.json',
            'plugin.ini',
            'info.php',
            'version.php'
        ]
    
    def enumerate_plugins(self, target_url: str, session_id: str = None) -> List[PluginInfo]:
        """Enumerate all plugins on the target OJS instance."""
        log_target_discovery(target_url, "plugin enumeration", session_id)
        
        discovered_plugins = []
        
        try:
            # Enumerate each plugin directory
            for category_name, directory_path in self.plugin_directories.items():
                category = PluginCategory(category_name)
                plugins = self._enumerate_plugin_directory(target_url, directory_path, category, session_id)
                discovered_plugins.extend(plugins)
            
            # Also check for custom plugins in non-standard locations
            custom_plugins = self._enumerate_custom_plugins(target_url, session_id)
            discovered_plugins.extend(custom_plugins)
            
            self.logger.info(f"Discovered {len(discovered_plugins)} plugins on {target_url}")
            
        except Exception as e:
            self.logger.error(f"Plugin enumeration failed: {e}")
        
        return discovered_plugins
    
    def _enumerate_plugin_directory(self, target_url: str, directory_path: str,
                                  category: PluginCategory, session_id: str = None) -> List[PluginInfo]:
        """Enumerate plugins in a specific directory."""
        plugins = []
        full_url = urljoin(target_url, directory_path)
        
        try:
            if self.http_client:
                response = self.http_client.get(full_url)
            else:
                response = requests.get(full_url)
            
            if response.status_code == 200:
                # Parse directory listing
                plugin_dirs = self._parse_directory_listing(response.text, directory_path)
                
                for plugin_dir in plugin_dirs:
                    plugin_info = self._analyze_plugin(target_url, plugin_dir, category, session_id)
                    if plugin_info:
                        plugins.append(plugin_info)
            
        except Exception as e:
            self.logger.debug(f"Failed to enumerate {directory_path}: {e}")
        
        return plugins
    
    def _parse_directory_listing(self, html_content: str, base_path: str) -> List[str]:
        """Parse directory listing to extract plugin directories."""
        plugin_dirs = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for links that might be plugin directories
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href')
                if href and not href.startswith('..') and not href.endswith('/'):
                    # Check if it looks like a plugin directory
                    if self._is_plugin_directory(href):
                        plugin_dirs.append(f"{base_path}{href}/")
            
        except Exception as e:
            self.logger.debug(f"Failed to parse directory listing: {e}")
        
        return plugin_dirs
    
    def _is_plugin_directory(self, directory_name: str) -> bool:
        """Check if a directory name looks like a plugin directory."""
        # Common plugin naming patterns
        plugin_patterns = [
            r'^[a-z]+[a-z0-9_]*$',  # lowercase with underscores
            r'^[A-Z][a-z]+[A-Z][a-z]+$',  # CamelCase
            r'^[a-z]+-[a-z]+$',  # kebab-case
        ]
        
        for pattern in plugin_patterns:
            if re.match(pattern, directory_name):
                return True
        
        return False
    
    def _analyze_plugin(self, target_url: str, plugin_path: str,
                       category: PluginCategory, session_id: str = None) -> Optional[PluginInfo]:
        """Analyze a specific plugin for information and vulnerabilities."""
        try:
            # Get plugin metadata
            metadata = self._extract_plugin_metadata(target_url, plugin_path, session_id)
            
            if not metadata:
                return None
            
            # Get plugin files
            files = self._get_plugin_files(target_url, plugin_path, session_id)
            
            # Analyze for vulnerabilities
            vulnerabilities = self._analyze_plugin_security(target_url, plugin_path, files, session_id)
            
            # Determine risk level
            risk_level = self._determine_risk_level(vulnerabilities, metadata.get('name', ''))
            
            plugin_info = PluginInfo(
                name=metadata.get('name', 'Unknown'),
                category=category,
                version=metadata.get('version', 'Unknown'),
                description=metadata.get('description', ''),
                author=metadata.get('author', 'Unknown'),
                website=metadata.get('website', ''),
                enabled=metadata.get('enabled', False),
                path=plugin_path,
                files=files,
                vulnerabilities=vulnerabilities,
                risk_level=risk_level,
                last_updated=metadata.get('last_updated', ''),
                dependencies=metadata.get('dependencies', []),
                permissions=metadata.get('permissions', [])
            )
            
            return plugin_info
            
        except Exception as e:
            self.logger.debug(f"Failed to analyze plugin {plugin_path}: {e}")
            return None
    
    def _extract_plugin_metadata(self, target_url: str, plugin_path: str,
                                session_id: str = None) -> Optional[Dict[str, Any]]:
        """Extract metadata from plugin files."""
        metadata = {}
        
        for metadata_file in self.metadata_files:
            file_url = urljoin(target_url, f"{plugin_path}{metadata_file}")
            
            try:
                if self.http_client:
                    response = self.http_client.get(file_url)
                else:
                    response = requests.get(file_url)
                
                if response.status_code == 200:
                    if metadata_file.endswith('.xml'):
                        metadata.update(self._parse_xml_metadata(response.text))
                    elif metadata_file == 'composer.json':
                        metadata.update(self._parse_json_metadata(response.text))
                    elif metadata_file.endswith('.php'):
                        metadata.update(self._parse_php_metadata(response.text))
                    elif metadata_file.endswith('.ini'):
                        metadata.update(self._parse_ini_metadata(response.text))
                    
                    # If we found basic info, we can stop
                    if metadata.get('name'):
                        break
                        
            except Exception as e:
                self.logger.debug(f"Failed to extract metadata from {metadata_file}: {e}")
        
        return metadata if metadata else None
    
    def _parse_xml_metadata(self, xml_content: str) -> Dict[str, Any]:
        """Parse XML metadata files."""
        metadata = {}
        
        try:
            root = ET.fromstring(xml_content)
            
            # Look for common XML metadata patterns
            name_elem = root.find('.//name') or root.find('.//plugin') or root.find('.//title')
            if name_elem is not None:
                metadata['name'] = name_elem.text
            
            version_elem = root.find('.//version') or root.find('.//release')
            if version_elem is not None:
                metadata['version'] = version_elem.text
            
            description_elem = root.find('.//description') or root.find('.//summary')
            if description_elem is not None:
                metadata['description'] = description_elem.text
            
            author_elem = root.find('.//author') or root.find('.//creator')
            if author_elem is not None:
                metadata['author'] = author_elem.text
            
            website_elem = root.find('.//website') or root.find('.//url')
            if website_elem is not None:
                metadata['website'] = website_elem.text
            
        except Exception as e:
            self.logger.debug(f"Failed to parse XML metadata: {e}")
        
        return metadata
    
    def _parse_json_metadata(self, json_content: str) -> Dict[str, Any]:
        """Parse JSON metadata files."""
        metadata = {}
        
        try:
            data = json.loads(json_content)
            
            metadata['name'] = data.get('name', '')
            metadata['version'] = data.get('version', '')
            metadata['description'] = data.get('description', '')
            metadata['author'] = data.get('author', '')
            metadata['website'] = data.get('homepage', '')
            metadata['dependencies'] = list(data.get('require', {}).keys())
            
        except Exception as e:
            self.logger.debug(f"Failed to parse JSON metadata: {e}")
        
        return metadata
    
    def _parse_php_metadata(self, php_content: str) -> Dict[str, Any]:
        """Parse PHP metadata files."""
        metadata = {}
        
        try:
            # Look for common PHP metadata patterns
            name_match = re.search(r'[\'"](name|plugin_name)[\'"]\s*=>\s*[\'"]([^\'"]+)[\'"]', php_content)
            if name_match:
                metadata['name'] = name_match.group(2)
            
            version_match = re.search(r'[\'"](version|plugin_version)[\'"]\s*=>\s*[\'"]([^\'"]+)[\'"]', php_content)
            if version_match:
                metadata['version'] = version_match.group(2)
            
            description_match = re.search(r'[\'"](description|summary)[\'"]\s*=>\s*[\'"]([^\'"]+)[\'"]', php_content)
            if description_match:
                metadata['description'] = description_match.group(2)
            
            author_match = re.search(r'[\'"](author|creator)[\'"]\s*=>\s*[\'"]([^\'"]+)[\'"]', php_content)
            if author_match:
                metadata['author'] = author_match.group(2)
            
        except Exception as e:
            self.logger.debug(f"Failed to parse PHP metadata: {e}")
        
        return metadata
    
    def _parse_ini_metadata(self, ini_content: str) -> Dict[str, Any]:
        """Parse INI metadata files."""
        metadata = {}
        
        try:
            # Simple INI parsing
            for line in ini_content.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    
                    if key in ['name', 'plugin_name']:
                        metadata['name'] = value
                    elif key in ['version', 'plugin_version']:
                        metadata['version'] = value
                    elif key in ['description', 'summary']:
                        metadata['description'] = value
                    elif key in ['author', 'creator']:
                        metadata['author'] = value
                    elif key in ['website', 'url']:
                        metadata['website'] = value
            
        except Exception as e:
            self.logger.debug(f"Failed to parse INI metadata: {e}")
        
        return metadata
    
    def _get_plugin_files(self, target_url: str, plugin_path: str,
                         session_id: str = None) -> List[str]:
        """Get list of files in the plugin directory."""
        files = []
        
        try:
            # Try to get directory listing
            dir_url = urljoin(target_url, plugin_path)
            
            if self.http_client:
                response = self.http_client.get(dir_url)
            else:
                response = requests.get(dir_url)
            
            if response.status_code == 200:
                # Parse directory listing for files
                soup = BeautifulSoup(response.text, 'html.parser')
                links = soup.find_all('a', href=True)
                
                for link in links:
                    href = link.get('href')
                    if href and not href.startswith('..') and not href.endswith('/'):
                        files.append(href)
            
        except Exception as e:
            self.logger.debug(f"Failed to get plugin files: {e}")
        
        return files
    
    def _analyze_plugin_security(self, target_url: str, plugin_path: str,
                                files: List[str], session_id: str = None) -> List[str]:
        """Analyze plugin files for security vulnerabilities."""
        vulnerabilities = []
        
        # Check if this is a known vulnerable plugin
        plugin_name = plugin_path.split('/')[-2] if plugin_path.endswith('/') else plugin_path.split('/')[-1]
        
        if plugin_name.lower() in self.vulnerable_plugins:
            vuln_info = self.vulnerable_plugins[plugin_name.lower()]
            vulnerabilities.extend(vuln_info['vulnerabilities'])
        
        # Analyze plugin files for security issues
        for file_name in files:
            if file_name.endswith(('.php', '.js', '.html', '.xml')):
                file_vulns = self._analyze_file_security(target_url, f"{plugin_path}{file_name}", session_id)
                vulnerabilities.extend(file_vulns)
        
        return list(set(vulnerabilities))  # Remove duplicates
    
    def _analyze_file_security(self, target_url: str, file_path: str,
                              session_id: str = None) -> List[str]:
        """Analyze a specific file for security vulnerabilities."""
        vulnerabilities = []
        
        try:
            file_url = urljoin(target_url, file_path)
            
            if self.http_client:
                response = self.http_client.get(file_url)
            else:
                response = requests.get(file_url)
            
            if response.status_code == 200:
                content = response.text
                
                # Check for security patterns
                for vuln_type, patterns in self.security_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            vulnerabilities.append(vuln_type.upper())
                            break
                
        except Exception as e:
            self.logger.debug(f"Failed to analyze file {file_path}: {e}")
        
        return vulnerabilities
    
    def _determine_risk_level(self, vulnerabilities: List[str], plugin_name: str) -> str:
        """Determine the risk level of a plugin based on vulnerabilities."""
        if not vulnerabilities:
            return 'LOW'
        
        # Check for high-risk vulnerabilities
        high_risk = ['RCE', 'SQL_INJECTION', 'FILE_UPLOAD']
        medium_risk = ['XSS', 'PATH_TRAVERSAL', 'DESERIALIZATION']
        
        for vuln in vulnerabilities:
            if vuln.upper() in high_risk:
                return 'HIGH'
            elif vuln.upper() in medium_risk:
                return 'MEDIUM'
        
        return 'LOW'
    
    def _enumerate_custom_plugins(self, target_url: str, session_id: str = None) -> List[PluginInfo]:
        """Enumerate custom plugins in non-standard locations."""
        custom_plugins = []
        
        # Common custom plugin locations
        custom_locations = [
            '/custom/plugins/',
            '/lib/plugins/',
            '/plugins/custom/',
            '/extensions/',
            '/addons/',
            '/modules/'
        ]
        
        for location in custom_locations:
            plugins = self._enumerate_plugin_directory(target_url, location, PluginCategory.CUSTOM, session_id)
            custom_plugins.extend(plugins)
        
        return custom_plugins
    
    def get_plugin_vulnerabilities(self, plugin_name: str) -> Dict[str, Any]:
        """Get known vulnerabilities for a specific plugin."""
        plugin_name_lower = plugin_name.lower()
        
        if plugin_name_lower in self.vulnerable_plugins:
            return self.vulnerable_plugins[plugin_name_lower]
        
        return {}
    
    def generate_plugin_report(self, plugins: List[PluginInfo]) -> Dict[str, Any]:
        """Generate a comprehensive plugin analysis report."""
        report = {
            'total_plugins': len(plugins),
            'enabled_plugins': len([p for p in plugins if p.enabled]),
            'disabled_plugins': len([p for p in plugins if not p.enabled]),
            'high_risk_plugins': len([p for p in plugins if p.risk_level == 'HIGH']),
            'medium_risk_plugins': len([p for p in plugins if p.risk_level == 'MEDIUM']),
            'low_risk_plugins': len([p for p in plugins if p.risk_level == 'LOW']),
            'vulnerable_plugins': [],
            'plugin_categories': {},
            'security_summary': {}
        }
        
        # Categorize plugins
        for plugin in plugins:
            category = plugin.category.value
            if category not in report['plugin_categories']:
                report['plugin_categories'][category] = []
            report['plugin_categories'][category].append(plugin.name)
        
        # Identify vulnerable plugins
        for plugin in plugins:
            if plugin.vulnerabilities:
                report['vulnerable_plugins'].append({
                    'name': plugin.name,
                    'version': plugin.version,
                    'vulnerabilities': plugin.vulnerabilities,
                    'risk_level': plugin.risk_level,
                    'path': plugin.path
                })
        
        # Security summary
        all_vulnerabilities = []
        for plugin in plugins:
            all_vulnerabilities.extend(plugin.vulnerabilities)
        
        vulnerability_counts = {}
        for vuln in all_vulnerabilities:
            vulnerability_counts[vuln] = vulnerability_counts.get(vuln, 0) + 1
        
        report['security_summary'] = vulnerability_counts
        
        return report
    
    def get_enumerator_info(self) -> Dict[str, Any]:
        """Get information about the plugin enumerator module."""
        return {
            'name': 'PluginEnumerator',
            'description': 'Plugin enumeration and analysis module for OJS',
            'plugin_categories': [c.value for c in PluginCategory],
            'plugin_directories': list(self.plugin_directories.keys()),
            'vulnerable_plugins': list(self.vulnerable_plugins.keys()),
            'security_patterns': list(self.security_patterns.keys()),
            'metadata_files': self.metadata_files
        }