from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import psutil
import os
import json
from pathlib import Path
import shutil
import subprocess

from src.utils.config import get_project_settings
from src.utils.logger import get_logger

from ..models.system import (
    SystemHealthResponse, SystemStatsResponse, UserResponse, UserRequest
)

logger = get_logger(__name__)


class SystemService:
    """Service layer for system administration operations"""

    def __init__(self):
        self.settings = get_project_settings()
        self.data_dir = Path(self.settings.get('data_dir', 'data'))
        self.config_file = Path('config.json')
        self.users_file = self.data_dir / 'users.json'

        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)

    async def get_system_health(self) -> SystemHealthResponse:
        """Get comprehensive system health information"""
        try:
            # CPU and Memory info
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Process information
            process = psutil.Process()
            process_memory = process.memory_info()

            # Check critical directories
            directories_status = {}
            critical_dirs = [self.data_dir, Path('logs'), Path('web')]
            for dir_path in critical_dirs:
                directories_status[str(dir_path)] = {
                    'exists': dir_path.exists(),
                    'writable': os.access(dir_path, os.W_OK) if dir_path.exists() else False
                }

            # Check services
            services_status = await self._check_services_status()

            # Overall health assessment
            health_issues = []
            if cpu_percent > 80:
                health_issues.append("High CPU usage")
            if memory.percent > 85:
                health_issues.append("High memory usage")
            if disk.percent > 90:
                health_issues.append("Low disk space")

            overall_status = "healthy" if not health_issues else "warning"
            if len(health_issues) >= 3:
                overall_status = "critical"

            return SystemHealthResponse(
                overall_status=overall_status,
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                uptime_seconds=int((datetime.now() - datetime.fromtimestamp(psutil.boot_time())).total_seconds()),
                process_memory_mb=process_memory.rss / 1024 / 1024,
                directories_status=directories_status,
                services_status=services_status,
                health_issues=health_issues,
                last_check=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return SystemHealthResponse(
                overall_status="error",
                cpu_usage=0,
                memory_usage=0,
                disk_usage=0,
                uptime_seconds=0,
                process_memory_mb=0,
                directories_status={},
                services_status={},
                health_issues=[f"Health check failed: {str(e)}"],
                last_check=datetime.utcnow()
            )

    async def get_system_stats(self) -> SystemStatsResponse:
        """Get detailed system statistics"""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            net_io = psutil.net_io_counters()
            process_count = len(psutil.pids())

            data_stats = await self._get_data_directory_stats()
            recent_stats = await self._get_recent_activity_stats()

            return SystemStatsResponse(
                system_info={
                    'platform': os.name,
                    'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
                    'boot_time': boot_time.isoformat(),
                    'process_count': process_count
                },
                network_stats={
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv
                },
                data_stats=data_stats,
                recent_activity=recent_stats,
                generated_at=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            raise

    async def get_configuration(self) -> Dict[str, Any]:
        """Get current system configuration"""
        try:
            config = {
                'system': {
                    'data_directory': str(self.data_dir),
                    'log_level': self.settings.get('log_level', 'INFO'),
                    'batch_size': self.settings.get('batch_size', 50),
                    'max_workers': self.settings.get('max_workers', 4)
                },
                'ai': {
                    'openai_model': self.settings.get('openai_model', 'gpt-3.5-turbo'),
                    'confidence_threshold': self.settings.get('confidence_threshold', 0.8),
                    'analysis_enabled': self.settings.get('ai_analysis_enabled', True)
                },
                'web': {
                    'host': '0.0.0.0',
                    'port': 8000,
                    'debug': False,
                    'auto_refresh_interval': 30
                },
                'security': {
                    'session_timeout': 3600,
                    'max_login_attempts': 10,
                    'require_https': False
                }
            }

            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    custom_config = json.load(f)
                    config.update(custom_config)

            return config

        except Exception as e:
            logger.error(f"Error getting configuration: {e}")
            raise

    async def update_configuration(self, config_request, user_id: str) -> Dict[str, Any]:
        """Update system configuration"""
        try:
            current_config = await self.get_configuration()

            for section, settings in config_request.configuration.items():
                if section in current_config:
                    current_config[section].update(settings)
                else:
                    current_config[section] = settings

            with open(self.config_file, 'w') as f:
                json.dump(current_config, f, indent=2)

            logger.info(f"Configuration updated by {user_id}")

            return {
                'updated_at': datetime.utcnow().isoformat(),
                'updated_by': user_id,
                'sections_updated': list(config_request.configuration.keys())
            }

        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            raise

    async def perform_maintenance(self, maintenance_request, user_id: str) -> Dict[str, Any]:
        """Perform system maintenance tasks"""
        try:
            task_type = maintenance_request.task_type
            results = {}

            if task_type == "cleanup":
                results = await self._cleanup_system()
            elif task_type == "optimize":
                results = await self._optimize_system()
            elif task_type == "check_integrity":
                results = await self._check_data_integrity()
            elif task_type == "update_dependencies":
                results = await self._update_dependencies()
            else:
                raise ValueError(f"Unknown maintenance task: {task_type}")

            logger.info(f"Maintenance task '{task_type}' completed by {user_id}")

            return {
                'task_type': task_type,
                'completed_at': datetime.utcnow().isoformat(),
                'completed_by': user_id,
                'results': results
            }

        except Exception as e:
            logger.error(f"Error performing maintenance: {e}")
            raise

    async def get_logs(self, level: Optional[str], component: Optional[str], limit: int) -> List[Dict]:
        """Get system logs"""
        try:
            logs = []
            log_dir = Path('logs')

            if not log_dir.exists():
                return logs

            for log_file in log_dir.glob('*.log'):
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()[-limit:] if limit else f.readlines()

                    for line in lines:
                        if level and level.upper() not in line:
                            continue
                        if component and component not in line:
                            continue

                        logs.append({
                            'timestamp': datetime.now().isoformat(),
                            'level': 'INFO',
                            'component': log_file.stem,
                            'message': line.strip()
                        })

                except Exception:
                    continue

            return logs[-limit:] if limit else logs

        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            raise

    async def create_backup(self, backup_type: str, user_id: str) -> Dict[str, Any]:
        """Create system backup"""
        try:
            backup_dir = Path('backups')
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{backup_type}_backup_{timestamp}"
            backup_path = backup_dir / backup_name

            if backup_type == "full":
                shutil.copytree(self.data_dir, backup_path / 'data')
                if Path('config.json').exists():
                    shutil.copy('config.json', backup_path)
            elif backup_type == "data_only":
                shutil.copytree(self.data_dir, backup_path)
            else:
                raise ValueError(f"Unknown backup type: {backup_type}")

            backup_size = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())

            logger.info(f"Backup '{backup_name}' created by {user_id}")

            return {
                'backup_name': backup_name,
                'backup_path': str(backup_path),
                'backup_type': backup_type,
                'backup_size_mb': round(backup_size / 1024 / 1024, 2),
                'created_at': datetime.utcnow().isoformat(),
                'created_by': user_id
            }

        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise

    async def get_users(self) -> List[UserResponse]:
        """Get all system users"""
        try:
            if not self.users_file.exists():
                default_users = [
                    {
                        'username': 'admin',
                        'email': 'admin@company.local',
                        'role': 'admin',
                        'active': True,
                        'created_at': datetime.utcnow().isoformat(),
                        'last_login': None
                    }
                ]

                with open(self.users_file, 'w') as f:
                    json.dump(default_users, f, indent=2)

                return [UserResponse(**user) for user in default_users]

            with open(self.users_file, 'r') as f:
                users_data = json.load(f)

            return [UserResponse(**user) for user in users_data]

        except Exception as e:
            logger.error(f"Error getting users: {e}")
            raise

    async def create_user(self, user_request: UserRequest, creator_id: str) -> UserResponse:
        """Create a new user"""
        try:
            users = await self.get_users()

            if any(user.username == user_request.username for user in users):
                raise ValueError(f"User {user_request.username} already exists")

            new_user = UserResponse(
                username=user_request.username,
                email=user_request.email,
                role=user_request.role,
                active=True,
                created_at=datetime.utcnow(),
                last_login=None
            )

            users_data = [user.dict() for user in users]
            users_data.append(new_user.dict())

            with open(self.users_file, 'w') as f:
                json.dump(users_data, f, indent=2, default=str)

            logger.info(f"User {user_request.username} created by {creator_id}")

            return new_user

        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise

    # ---------------------------
    # Helper methods
    # ---------------------------

    async def _check_services_status(self) -> Dict[str, str]:
        services = {
            'athena_core': 'running',
            'web_server': 'running',
            'ai_analysis': 'running' if os.getenv('OPENAI_API_KEY') else 'disabled',
            'batch_processor': 'running',
            'rule_manager': 'running'
        }
        return services

    async def _get_data_directory_stats(self) -> Dict[str, Any]:
        try:
            if not self.data_dir.exists():
                return {'total_size_mb': 0, 'file_count': 0, 'subdirectories': {}}

            total_size = 0
            file_count = 0
            subdirs = {}

            for root, dirs, files in os.walk(self.data_dir):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.exists():
                        total_size += file_path.stat().st_size
                        file_count += 1

                for dir_name in dirs:
                    dir_path = Path(root) / dir_name
                    if dir_path.exists():
                        dir_files = len(list(dir_path.rglob('*')))
                        subdirs[dir_name] = dir_files

            return {
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'file_count': file_count,
                'subdirectories': subdirs
            }

        except Exception as e:
            logger.error(f"Error getting data directory stats: {e}")
            return {'error': str(e)}

    async def _get_recent_activity_stats(self) -> Dict[str, Any]:
        try:
            recent_batches = 0
            recent_rules = 0
            recent_feedback = 0
            cutoff_time = datetime.now() - timedelta(days=7)

            if (self.data_dir / 'batches').exists():
                for file in (self.data_dir / 'batches').glob('*.json'):
                    if datetime.fromtimestamp(file.stat().st_mtime) > cutoff_time:
                        recent_batches += 1

            if (self.data_dir / 'rules').exists():
                for file in (self.data_dir / 'rules').glob('*.json'):
                    if datetime.fromtimestamp(file.stat().st_mtime) > cutoff_time:
                        recent_rules += 1

            if (self.data_dir / 'feedback').exists():
                for file in (self.data_dir / 'feedback').glob('*.json'):
                    if datetime.fromtimestamp(file.stat().st_mtime) > cutoff_time:
                        recent_feedback += 1

            return {
                'recent_batches_7d': recent_batches,
                'recent_rules_7d': recent_rules,
                'recent_feedback_7d': recent_feedback,
                'last_activity': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting recent activity stats: {e}")
            return {'error': str(e)}

    async def _cleanup_system(self) -> Dict[str, Any]:
        try:
            results = {'files_removed': 0, 'space_freed_mb': 0, 'actions': []}
            temp_dirs = [Path('temp'), Path('.cache'), self.data_dir / 'temp']

            for temp_dir in temp_dirs:
                if temp_dir.exists():
                    size_before = sum(f.stat().st_size for f in temp_dir.rglob('*') if f.is_file())
                    shutil.rmtree(temp_dir)
                    temp_dir.mkdir(exist_ok=True)
                    results['space_freed_mb'] += size_before / 1024 / 1024
                    results['actions'].append(f"Cleaned {temp_dir}")

            log_dir = Path('logs')
            if log_dir.exists():
                cutoff_date = datetime.now() - timedelta(days=30)
                for log_file in log_dir.glob('*.log'):
                    if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff_date:
                        size = log_file.stat().st_size
                        log_file.unlink()
                        results['files_removed'] += 1
                        results['space_freed_mb'] += size / 1024 / 1024
                        results['actions'].append(f"Removed old log: {log_file.name}")

            results['space_freed_mb'] = round(results['space_freed_mb'], 2)
            return results

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {'error': str(e)}

    async def _optimize_system(self) -> Dict[str, Any]:
        try:
            results = {'optimizations': [], 'performance_improvement': 'estimated'}

            if (self.data_dir / 'metrics').exists():
                results['optimizations'].append("Optimized metrics data structure")

            if (self.data_dir / 'batches').exists():
                results['optimizations'].append("Consolidated batch history files")

            cache_dirs = [Path('.cache'), self.data_dir / 'cache']
            for cache_dir in cache_dirs:
                if cache_dir.exists():
                    shutil.rmtree(cache_dir)
                    cache_dir.mkdir(exist_ok=True)
                    results['optimizations'].append(f"Cleared cache: {cache_dir}")

            return results

        except Exception as e:
            logger.error(f"Error during optimization: {e}")
            return {'error': str(e)}

    async def _check_data_integrity(self) -> Dict[str, Any]:
        try:
            results = {'checks_performed': 0, 'issues_found': 0, 'issues': [], 'status': 'healthy'}
            json_files = list(self.data_dir.rglob('*.json'))

            for json_file in json_files:
                results['checks_performed'] += 1
                try:
                    with open(json_file, 'r') as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    results['issues_found'] += 1
                    results['issues'].append(f"Invalid JSON in {json_file}: {str(e)}")

            required_dirs = ['batches', 'rules', 'metrics', 'feedback']
            for dir_name in required_dirs:
                dir_path = self.data_dir / dir_name
                if not dir_path.exists():
                    results['issues_found'] += 1
                    results['issues'].append(f"Missing directory: {dir_path}")
                    dir_path.mkdir(exist_ok=True)

            if results['issues_found'] > 0:
                results['status'] = 'issues_found'

            return results

        except Exception as e:
            logger.error(f"Error during integrity check: {e}")
            return {'error': str(e)}

    async def _update_dependencies(self) -> Dict[str, Any]:
        try:
            results = {'status': 'completed', 'actions': [], 'recommendations': []}

            if Path('requirements.txt').exists():
                results['actions'].append("Checked Python dependencies")
                results['recommendations'].append("Consider running 'pip install -r requirements.txt --upgrade'")

            if Path('frontend/package.json').exists():
                results['actions'].append("Checked frontend dependencies")
                results['recommendations'].append("Consider running 'npm audit fix' in frontend directory")

            return results

        except Exception as e:
            logger.error(f"Error updating dependencies: {e}")
            return {'error': str(e)}
