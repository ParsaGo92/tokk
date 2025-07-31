"""
Logging utilities for the OJS Exploit Framework.

This module provides comprehensive logging capabilities with security features,
log rotation, and multiple output formats for debugging and audit trails.
"""

import logging
import logging.handlers
import os
import sys
import time
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from contextlib import contextmanager


class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LogFormat(Enum):
    """Log format enumeration."""
    SIMPLE = "simple"
    DETAILED = "detailed"
    JSON = "json"
    CSV = "csv"


@dataclass
class LogConfig:
    """Configuration for logging setup."""
    level: LogLevel = LogLevel.INFO
    format: LogFormat = LogFormat.DETAILED
    log_file: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    console_output: bool = True
    file_output: bool = True
    security_log: bool = True
    sensitive_fields: List[str] = None
    log_requests: bool = True
    log_responses: bool = False
    log_payloads: bool = False
    log_errors: bool = True
    log_timing: bool = True


class SecurityFilter(logging.Filter):
    """Filter to remove sensitive information from logs."""
    
    def __init__(self, sensitive_fields: List[str] = None):
        super().__init__()
        self.sensitive_fields = sensitive_fields or [
            'password', 'token', 'session', 'cookie', 'authorization',
            'api_key', 'secret', 'private', 'key', 'credential'
        ]
    
    def filter(self, record):
        """Filter sensitive information from log records."""
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = self._sanitize_string(record.msg)
        
        if hasattr(record, 'args') and record.args:
            if isinstance(record.args, dict):
                record.args = self._sanitize_dict(record.args)
            elif isinstance(record.args, (list, tuple)):
                record.args = self._sanitize_list(record.args)
        
        return True
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize sensitive information in strings."""
        for field in self.sensitive_fields:
            # Replace common patterns
            patterns = [
                f'{field}=[^\\s&]+',
                f'{field}["\']\\s*:\\s*["\'][^"\']*["\']',
                f'{field}["\']\\s*:\\s*[^,}}]+',
            ]
            for pattern in patterns:
                import re
                text = re.sub(pattern, f'{field}=***', text, flags=re.IGNORECASE)
        return text
    
    def _sanitize_dict(self, data: Dict) -> Dict:
        """Sanitize sensitive information in dictionaries."""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = self._sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, (list, tuple)):
                sanitized[key] = self._sanitize_list(value)
            else:
                sanitized[key] = value
        return sanitized
    
    def _sanitize_list(self, data: List) -> List:
        """Sanitize sensitive information in lists."""
        sanitized = []
        for item in data:
            if isinstance(item, str):
                sanitized.append(self._sanitize_string(item))
            elif isinstance(item, dict):
                sanitized.append(self._sanitize_dict(item))
            elif isinstance(item, (list, tuple)):
                sanitized.append(self._sanitize_list(item))
            else:
                sanitized.append(item)
        return sanitized


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def __init__(self, include_timestamp: bool = True, include_level: bool = True):
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_level = include_level
    
    def format(self, record):
        """Format log record as JSON."""
        log_entry = {
            'message': record.getMessage(),
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        if self.include_timestamp:
            log_entry['timestamp'] = datetime.fromtimestamp(record.created).isoformat()
        
        if self.include_level:
            log_entry['level'] = record.levelname
        
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
        
        if hasattr(record, 'target_url'):
            log_entry['target_url'] = record.target_url
        
        if hasattr(record, 'payload_hash'):
            log_entry['payload_hash'] = record.payload_hash
        
        if hasattr(record, 'execution_time'):
            log_entry['execution_time'] = record.execution_time
        
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


class DetailedFormatter(logging.Formatter):
    """Detailed formatter with color support."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def __init__(self, use_colors: bool = True, include_timestamp: bool = True):
        super().__init__()
        self.use_colors = use_colors
        self.include_timestamp = include_timestamp
    
    def format(self, record):
        """Format log record with detailed information."""
        # Base format
        if self.include_timestamp:
            timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
            formatted = f"[{timestamp}] "
        else:
            formatted = ""
        
        # Add level with color
        level_name = record.levelname
        if self.use_colors and level_name in self.COLORS:
            formatted += f"{self.COLORS[level_name]}{level_name}{self.COLORS['RESET']} "
        else:
            formatted += f"{level_name} "
        
        # Add logger name
        formatted += f"[{record.name}] "
        
        # Add module and function
        formatted += f"[{record.module}.{record.funcName}:{record.lineno}] "
        
        # Add custom fields
        if hasattr(record, 'request_id'):
            formatted += f"[REQ:{record.request_id}] "
        
        if hasattr(record, 'session_id'):
            formatted += f"[SESS:{record.session_id}] "
        
        if hasattr(record, 'target_url'):
            formatted += f"[URL:{record.target_url}] "
        
        if hasattr(record, 'payload_hash'):
            formatted += f"[PAYLOAD:{record.payload_hash[:8]}...] "
        
        if hasattr(record, 'execution_time'):
            formatted += f"[TIME:{record.execution_time:.3f}s] "
        
        # Add message
        formatted += record.getMessage()
        
        # Add exception info
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted


class RequestLogger:
    """Specialized logger for HTTP requests and responses."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.request_counter = 0
        self._lock = threading.Lock()
    
    def log_request(self, method: str, url: str, headers: Dict = None, 
                   data: Any = None, session_id: str = None, 
                   request_id: str = None, execution_time: float = None):
        """Log HTTP request details."""
        with self._lock:
            self.request_counter += 1
            if not request_id:
                request_id = f"REQ_{self.request_counter:06d}"
        
        extra = {
            'request_id': request_id,
            'session_id': session_id,
            'target_url': url,
            'execution_time': execution_time
        }
        
        self.logger.info(
            f"HTTP {method} {url}",
            extra=extra
        )
        
        if headers:
            self.logger.debug(f"Headers: {headers}", extra=extra)
        
        if data:
            if isinstance(data, dict):
                self.logger.debug(f"Data: {json.dumps(data, indent=2)}", extra=extra)
            else:
                self.logger.debug(f"Data: {str(data)[:200]}...", extra=extra)
    
    def log_response(self, status_code: int, headers: Dict = None, 
                    content: str = None, request_id: str = None,
                    execution_time: float = None):
        """Log HTTP response details."""
        extra = {
            'request_id': request_id,
            'execution_time': execution_time
        }
        
        self.logger.info(
            f"Response: {status_code}",
            extra=extra
        )
        
        if headers:
            self.logger.debug(f"Response Headers: {headers}", extra=extra)
        
        if content:
            self.logger.debug(f"Response Content: {str(content)[:500]}...", extra=extra)
    
    def log_error(self, error: Exception, request_id: str = None, 
                  context: str = None):
        """Log HTTP errors."""
        extra = {'request_id': request_id}
        
        if context:
            self.logger.error(f"{context}: {str(error)}", extra=extra, exc_info=True)
        else:
            self.logger.error(f"HTTP Error: {str(error)}", extra=extra, exc_info=True)


class SecurityLogger:
    """Specialized logger for security events."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_exploit_attempt(self, exploit_type: str, target: str, 
                           payload: str = None, success: bool = False,
                           session_id: str = None):
        """Log exploit attempts."""
        extra = {
            'session_id': session_id,
            'target_url': target,
            'payload_hash': hashlib.sha256(payload.encode()).hexdigest() if payload else None
        }
        
        status = "SUCCESS" if success else "FAILED"
        self.logger.warning(
            f"EXPLOIT {status}: {exploit_type} against {target}",
            extra=extra
        )
        
        if payload:
            self.logger.debug(f"Payload: {payload[:100]}...", extra=extra)
    
    def log_waf_bypass(self, waf_type: str, bypass_method: str, 
                      success: bool = False, session_id: str = None):
        """Log WAF bypass attempts."""
        extra = {'session_id': session_id}
        
        status = "SUCCESS" if success else "FAILED"
        self.logger.warning(
            f"WAF BYPASS {status}: {waf_type} using {bypass_method}",
            extra=extra
        )
    
    def log_session_hijack(self, session_id: str, target_session: str,
                          success: bool = False):
        """Log session hijacking attempts."""
        extra = {
            'session_id': session_id,
            'target_session': target_session
        }
        
        status = "SUCCESS" if success else "FAILED"
        self.logger.warning(
            f"SESSION HIJACK {status}: {target_session}",
            extra=extra
        )
    
    def log_file_upload(self, filename: str, location: str, 
                       file_type: str = None, success: bool = False,
                       session_id: str = None):
        """Log file upload attempts."""
        extra = {
            'session_id': session_id,
            'target_url': location
        }
        
        status = "SUCCESS" if success else "FAILED"
        self.logger.warning(
            f"FILE UPLOAD {status}: {filename} ({file_type}) to {location}",
            extra=extra
        )
    
    def log_webshell_deployment(self, shell_type: str, location: str,
                               access_key: str = None, success: bool = False,
                               session_id: str = None):
        """Log web shell deployment."""
        extra = {
            'session_id': session_id,
            'target_url': location
        }
        
        status = "SUCCESS" if success else "FAILED"
        self.logger.critical(
            f"WEBSHELL DEPLOYMENT {status}: {shell_type} at {location}",
            extra=extra
        )
        
        if access_key:
            self.logger.debug(f"Access Key: {access_key[:8]}...", extra=extra)


class PerformanceLogger:
    """Specialized logger for performance monitoring."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.timers = {}
        self._lock = threading.Lock()
    
    @contextmanager
    def timer(self, operation: str, session_id: str = None):
        """Context manager for timing operations."""
        start_time = time.time()
        timer_id = f"{operation}_{start_time}"
        
        with self._lock:
            self.timers[timer_id] = {
                'operation': operation,
                'start_time': start_time,
                'session_id': session_id
            }
        
        try:
            yield timer_id
        finally:
            end_time = time.time()
            execution_time = end_time - start_time
            
            with self._lock:
                if timer_id in self.timers:
                    del self.timers[timer_id]
            
            extra = {
                'session_id': session_id,
                'execution_time': execution_time
            }
            
            self.logger.debug(
                f"Operation '{operation}' completed in {execution_time:.3f}s",
                extra=extra
            )
    
    def log_performance_metrics(self, metrics: Dict[str, float], 
                               session_id: str = None):
        """Log performance metrics."""
        extra = {'session_id': session_id}
        
        for metric, value in metrics.items():
            self.logger.info(f"Performance Metric - {metric}: {value}", extra=extra)
    
    def get_timer_stats(self) -> Dict[str, Any]:
        """Get statistics about active timers."""
        with self._lock:
            return {
                'active_timers': len(self.timers),
                'timer_details': self.timers.copy()
            }


def setup_logging(config: LogConfig = None) -> logging.Logger:
    """Set up logging with the specified configuration."""
    if config is None:
        config = LogConfig()
    
    # Create logs directory if it doesn't exist
    if config.log_file:
        log_dir = Path(config.log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('ojs_exploit_framework')
    logger.setLevel(config.level.value)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatters
    if config.format == LogFormat.JSON:
        formatter = JSONFormatter()
    elif config.format == LogFormat.DETAILED:
        formatter = DetailedFormatter(use_colors=config.console_output)
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Console handler
    if config.console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(SecurityFilter(config.sensitive_fields))
        logger.addHandler(console_handler)
    
    # File handler
    if config.file_output and config.log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            config.log_file,
            maxBytes=config.max_file_size,
            backupCount=config.backup_count
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(SecurityFilter(config.sensitive_fields))
        logger.addHandler(file_handler)
    
    # Security log handler
    if config.security_log and config.log_file:
        security_log_file = str(Path(config.log_file).with_suffix('.security.log'))
        security_handler = logging.handlers.RotatingFileHandler(
            security_log_file,
            maxBytes=config.max_file_size,
            backupCount=config.backup_count
        )
        security_handler.setFormatter(formatter)
        security_handler.addFilter(SecurityFilter(config.sensitive_fields))
        security_handler.setLevel(logging.WARNING)  # Only security events
        logger.addHandler(security_handler)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance."""
    if name:
        return logging.getLogger(f'ojs_exploit_framework.{name}')
    return logging.getLogger('ojs_exploit_framework')


def get_request_logger(logger: logging.Logger = None) -> RequestLogger:
    """Get a request logger instance."""
    if logger is None:
        logger = get_logger('requests')
    return RequestLogger(logger)


def get_security_logger(logger: logging.Logger = None) -> SecurityLogger:
    """Get a security logger instance."""
    if logger is None:
        logger = get_logger('security')
    return SecurityLogger(logger)


def get_performance_logger(logger: logging.Logger = None) -> PerformanceLogger:
    """Get a performance logger instance."""
    if logger is None:
        logger = get_logger('performance')
    return PerformanceLogger(logger)


# Convenience functions for common logging operations
def log_exploit_start(exploit_type: str, target: str, session_id: str = None):
    """Log the start of an exploit attempt."""
    logger = get_logger('exploits')
    extra = {'session_id': session_id, 'target_url': target}
    logger.info(f"Starting {exploit_type} exploit against {target}", extra=extra)


def log_exploit_success(exploit_type: str, target: str, result: str = None,
                       session_id: str = None):
    """Log successful exploit."""
    logger = get_logger('exploits')
    extra = {'session_id': session_id, 'target_url': target}
    message = f"SUCCESS: {exploit_type} exploit against {target}"
    if result:
        message += f" - {result}"
    logger.warning(message, extra=extra)


def log_exploit_failure(exploit_type: str, target: str, error: str = None,
                        session_id: str = None):
    """Log failed exploit."""
    logger = get_logger('exploits')
    extra = {'session_id': session_id, 'target_url': target}
    message = f"FAILED: {exploit_type} exploit against {target}"
    if error:
        message += f" - {error}"
    logger.error(message, extra=extra)


def log_target_discovery(target: str, service: str = None, session_id: str = None):
    """Log target discovery."""
    logger = get_logger('recon')
    extra = {'session_id': session_id, 'target_url': target}
    message = f"Discovered target: {target}"
    if service:
        message += f" ({service})"
    logger.info(message, extra=extra)


def log_vulnerability_found(vuln_type: str, target: str, details: str = None,
                          session_id: str = None):
    """Log discovered vulnerability."""
    logger = get_logger('recon')
    extra = {'session_id': session_id, 'target_url': target}
    message = f"VULNERABILITY: {vuln_type} found on {target}"
    if details:
        message += f" - {details}"
    logger.warning(message, extra=extra)