"""Cross-platform environment variable loader for packaged apps"""

import os
import platform
import subprocess
import logging

logger = logging.getLogger(__name__)

def load_user_environment():
    """Load user environment variables from shell/system"""
    system = platform.system()
    
    try:
        if system in ['Darwin', 'Linux']:
            _load_unix_environment()
        elif system == 'Windows':
            _load_windows_environment()
        
        # Setup npm environment after loading shell environment
        _setup_npm_environment()
        
        logger.info("User environment variables loaded successfully")
    except Exception as e:
        logger.warning(f"Failed to load user environment: {e}")

def _load_unix_environment():
    """Load Unix/macOS environment variables"""
    shells = ['zsh', 'bash']
    
    for shell in shells:
        try:
            # Try to source common profile files and get environment
            cmd = f'{shell} -c "source ~/.zshrc ~/.bashrc ~/.profile 2>/dev/null; env"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                _parse_env_output(result.stdout)
                logger.info(f"Loaded environment from {shell}")
                return
        except Exception as e:
            logger.debug(f"Failed to load from {shell}: {e}")
            continue

def _load_windows_environment():
    """Load Windows environment variables"""
    try:
        # Get environment variables from PowerShell
        cmd = ['powershell', '-Command', 'Get-ChildItem Env: | ForEach-Object { "$($_.Name)=$($_.Value)" }']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            _parse_env_output(result.stdout)
            logger.info("Loaded environment from PowerShell")
    except Exception as e:
        logger.debug(f"Failed to load Windows environment: {e}")

def _parse_env_output(output):
    """Parse environment variable output and update os.environ"""
    for line in output.strip().split('\n'):
        if '=' in line and line.strip():
            try:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Only update if not already set or if it's a PATH-like variable
                if key not in os.environ or key.upper() in ['PATH', 'NODE_PATH', 'PYTHONPATH']:
                    os.environ[key] = value
            except ValueError:
                continue

def _setup_npm_environment():
    """Setup npm/node environment variables dynamically"""
    system = platform.system()
    
    # Try npm command first
    try:
        result = subprocess.run(['npm', 'config', 'get', 'prefix'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            npm_prefix = result.stdout.strip()
            _set_npm_paths(npm_prefix, system)
            logger.info(f"npm environment setup via npm command: prefix={npm_prefix}")
            return
    except Exception as e:
        logger.debug(f"npm command failed: {e}")
    
    # Fallback: try common npm installation paths
    common_paths = []
    if system == 'Windows':
        common_paths = [
            'C:\\Program Files\\nodejs',
            os.path.expanduser('~\\AppData\\Roaming\\npm'),
            os.path.expanduser('~\\AppData\\Local\\Programs\\Microsoft VS Code\\resources\\app\\extensions\\node_modules'),
            'C:\\Program Files (x86)\\nodejs',
            # Windows nvm paths
            os.path.expanduser('~\\AppData\\Roaming\\nvm\\*'),
        ]
    else:
        common_paths = [
            '/opt/homebrew',  # Homebrew on Apple Silicon
            '/usr/local',     # Homebrew on Intel Mac / standard Unix
            '/usr',           # System installation
            os.path.expanduser('~/.nvm/versions/node/*/'),  # nvm
        ]
    
    for path in common_paths:
        if '*' in path:
            # Handle nvm glob pattern
            import glob
            nvm_paths = glob.glob(path)
            if nvm_paths:
                # Sort by version number if possible, otherwise alphabetically
                try:
                    # Try to sort by version number
                    nvm_paths.sort(key=lambda x: [int(i) for i in x.split('/')[-1].replace('v', '').split('.') if i.isdigit()])
                except:
                    # Fallback to alphabetical sort
                    nvm_paths.sort()
                path = nvm_paths[-1]  # Use latest version
        
        if os.path.exists(path):
            # Check for valid Node.js installation
            valid_installation = False
            
            if system == 'Windows':
                # Windows: check for node.exe or npm.cmd
                if (os.path.exists(f"{path}\\node.exe") or 
                    os.path.exists(f"{path}\\npm.cmd") or
                    os.path.exists(f"{path}\\node_modules")):
                    valid_installation = True
            else:
                # Unix: check for node binary or lib/node_modules
                if (os.path.exists(f"{path}/bin/node") or 
                    os.path.exists(f"{path}/lib/node_modules")):
                    valid_installation = True
            
            if valid_installation:
                _set_npm_paths(path, system)
                logger.info(f"npm environment setup via fallback: prefix={path}")
                return
    
    logger.warning("Could not setup npm environment - no valid paths found")

def _set_npm_paths(npm_prefix, system):
    """Set npm-related environment variables"""
    if system == 'Windows':
        os.environ['NODE_PATH'] = f"{npm_prefix}\\node_modules"
        os.environ['npm_config_cache'] = os.path.expanduser('~\\AppData\\Roaming\\npm-cache')
        bin_path = f"{npm_prefix}\\bin"
    else:
        os.environ['NODE_PATH'] = f"{npm_prefix}/lib/node_modules"
        os.environ['npm_config_cache'] = os.path.expanduser('~/.npm')
        bin_path = f"{npm_prefix}/bin"
    
    os.environ['npm_config_prefix'] = npm_prefix
    
    # PATH에 npm/node 경로 추가 (가장 중요!)
    current_path = os.environ.get('PATH', '')
    if bin_path not in current_path:
        path_separator = ';' if system == 'Windows' else ':'
        os.environ['PATH'] = f"{bin_path}{path_separator}{current_path}"
        logger.info(f"Added to PATH: {bin_path}")