#!/usr/bin/env python3
"""
Internal Network Deployment Script for Athena Web Interface
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import json
import time

def check_requirements():
    """Check system requirements"""
    print("🔍 Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    # Check Node.js for frontend
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Node.js not found - required for frontend build")
            return False
        print(f"✅ Node.js {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ Node.js not found")
        return False
    
    # Check npm
    try:
        subprocess.run(['npm', '--version'], capture_output=True, text=True, check=True)
        print("✅ npm available")
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("❌ npm not found")
        return False
    
    print("✅ All requirements satisfied")
    return True

def setup_environment():
    """Setup deployment environment"""
    print("\n📁 Setting up environment...")
    
    # Create necessary directories
    directories = [
        'data',
        'logs',
        'backups',
        'data/batches',
        'data/rules',
        'data/metrics',
        'data/feedback'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Check .env file
    env_file = Path('.env')
    if not env_file.exists():
        print("⚠️  .env file not found")
        create_env = input("Create basic .env file? (y/n): ").lower() == 'y'
        if create_env:
            env_content = """# Athena Internal Deployment Configuration
ATHENA_WEB_HOST=0.0.0.0
ATHENA_WEB_PORT=8000
ATHENA_WEB_DEBUG=False
ATHENA_WEB_ENVIRONMENT=production

# OpenAI Configuration (if available)
# OPENAI_API_KEY=your-api-key-here

# Logging
ATHENA_WEB_LOG_LEVEL=INFO
ATHENA_WEB_LOG_FILE=logs/web.log
"""
            with open(env_file, 'w') as f:
                f.write(env_content)
            print("✅ Created basic .env file")
    else:
        print("✅ .env file exists")

def install_dependencies():
    """Install Python and Node.js dependencies"""
    print("\n📦 Installing dependencies...")
    
    # Install Python dependencies
    print("Installing Python dependencies...")
    try:
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], check=True)
        print("✅ Python dependencies installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install Python dependencies")
        return False
    
    # Install Node.js dependencies and build frontend
    frontend_dir = Path('frontend')
    if frontend_dir.exists():
        print("Installing Node.js dependencies...")
        try:
            subprocess.run(['npm', 'install'], cwd=frontend_dir, check=True)
            print("✅ Node.js dependencies installed")
            
            print("Building frontend...")
            subprocess.run(['npm', 'run', 'build'], cwd=frontend_dir, check=True)
            print("✅ Frontend built successfully")
            
            # Copy built frontend to web static directory
            web_static = Path('web/static')
            if web_static.exists():
                shutil.rmtree(web_static)
            
            dist_dir = frontend_dir / 'dist'
            if dist_dir.exists():
                shutil.copytree(dist_dir, web_static)
                print("✅ Frontend deployed to web/static")
            
        except subprocess.CalledProcessError:
            print("❌ Failed to build frontend")
            return False
    else:
        print("⚠️  Frontend directory not found")
    
    return True

def validate_deployment():
    """Validate deployment configuration"""
    print("\n🔍 Validating deployment...")
    
    # Test import of main modules
    try:
        from web.main import app
        print("✅ Web application imports successfully")
    except ImportError as e:
        print(f"❌ Failed to import web application: {e}")
        return False
    
    # Test Athena core
    try:
       from src.iterative_refinement_system import IterativeRefinementSystem
       print("✅ Athena core system imports successfully")
    except ImportError as e:
       print(f"❌ Failed to import Athena core: {e}")
       return False
   
   # Check data directory structure
    data_dir = Path('data')
    required_subdirs = ['batches', 'rules', 'metrics', 'feedback']
    for subdir in required_subdirs:
        if not (data_dir / subdir).exists():
           print(f"❌ Missing required directory: data/{subdir}")
           return False
    print("✅ Data directory structure valid")
   
    # Check configuration
    from web.config import settings, validate_internal_deployment
    validate_internal_deployment()
   
    return True

def create_service_files():
   """Create systemd service files for internal deployment"""
   print("\n🔧 Creating service files...")
   
   # Create systemd service file
   service_content = f"""[Unit]
Description=Athena Web Interface
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'athena')}
WorkingDirectory={os.getcwd()}
Environment=PATH={os.getcwd()}/venv/bin
ExecStart={sys.executable} -m uvicorn web.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""
   
   service_file = Path('athena-web.service')
   with open(service_file, 'w') as f:
       f.write(service_content)
   
   print(f"✅ Created service file: {service_file}")
   print("\nTo install as system service:")
   print(f"  sudo cp {service_file} /etc/systemd/system/")
   print("  sudo systemctl daemon-reload")
   print("  sudo systemctl enable athena-web")
   print("  sudo systemctl start athena-web")
   
   # Create startup script
   startup_script = Path('start_athena.sh')
   startup_content = f"""#!/bin/bash
# Athena Internal Deployment Startup Script

cd {os.getcwd()}
source venv/bin/activate 2>/dev/null || echo "Virtual environment not found"

echo "Starting Athena Web Interface..."
echo "Access at: http://$(hostname -I | awk '{{print $1}}'):8000"
echo "API Documentation: http://$(hostname -I | awk '{{print $1}}'):8000/api/docs"
echo ""

# Start the web server
python -m uvicorn web.main:app --host 0.0.0.0 --port 8000 --workers 4
"""
   
   with open(startup_script, 'w') as f:
       f.write(startup_content)
   
   startup_script.chmod(0o755)
   print(f"✅ Created startup script: {startup_script}")

def run_tests():
   """Run basic system tests"""
   print("\n🧪 Running basic tests...")
   
   try:
       # Test web server startup
       print("Testing web server startup...")
       process = subprocess.Popen([
           sys.executable, '-m', 'uvicorn', 'web.main:app', 
           '--host', '127.0.0.1', '--port', '8001'
       ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
       
       # Wait a bit for startup
       time.sleep(3)
       
       # Test if server is responding
       import requests
       try:
           response = requests.get('http://127.0.0.1:8001/api/health', timeout=5)
           if response.status_code == 200:
               print("✅ Web server responding to health checks")
           else:
               print(f"⚠️  Web server responding with status {response.status_code}")
       except requests.exceptions.RequestException:
           print("⚠️  Web server not responding (may need authentication)")
       
       # Clean up test server
       process.terminate()
       process.wait(timeout=5)
       
   except Exception as e:
       print(f"⚠️  Test failed: {e}")
   
   print("✅ Basic tests completed")

def display_deployment_info():
   """Display deployment information"""
   print("\n" + "="*60)
   print("🎉 ATHENA WEB INTERFACE DEPLOYMENT COMPLETE")
   print("="*60)
   
   # Get network interfaces
   import socket
   hostname = socket.gethostname()
   try:
       local_ip = socket.gethostbyname(hostname)
   except:
       local_ip = "localhost"
   
   print(f"\n🌐 Access Information:")
   print(f"   • Web Interface: http://{local_ip}:8000")
   print(f"   • API Documentation: http://{local_ip}:8000/api/docs")
   print(f"   • Health Check: http://{local_ip}:8000/api/health")
   
   print(f"\n🚀 Startup Options:")
   print(f"   • Manual: ./start_athena.sh")
   print(f"   • Direct: python -m uvicorn web.main:app --host 0.0.0.0 --port 8000")
   print(f"   • Service: sudo systemctl start athena-web")
   
   print(f"\n📁 Important Directories:")
   print(f"   • Data: {Path('data').absolute()}")
   print(f"   • Logs: {Path('logs').absolute()}")
   print(f"   • Backups: {Path('backups').absolute()}")
   
   print(f"\n🔧 Configuration:")
   print(f"   • Environment file: .env")
   print(f"   • Web config: web/config.py")
   print(f"   • Athena config: src/utils/config.py")
   
   print(f"\n⚠️  Security Notes (Internal Network):")
   print(f"   • Authentication is simplified for internal use")
   print(f"   • HTTPS not required on trusted internal network")
   print(f"   • Full API documentation exposed for development")
   print(f"   • Detailed error messages enabled for debugging")
   
   print(f"\n📖 Next Steps:")
   print(f"   1. Review configuration in .env file")
   print(f"   2. Add OpenAI API key for AI features (optional)")
   print(f"   3. Start the service: ./start_athena.sh")
   print(f"   4. Access web interface and create users")
   print(f"   5. Configure system settings via web interface")
   
   print("\n" + "="*60)

def main():
   """Main deployment function"""
   print("🏢 ATHENA INTERNAL NETWORK DEPLOYMENT")
   print("=====================================\n")
   
   try:
       # Check requirements
       if not check_requirements():
           sys.exit(1)
       
       # Setup environment
       setup_environment()
       
       # Install dependencies
       if not install_dependencies():
           sys.exit(1)
       
       # Validate deployment
       if not validate_deployment():
           sys.exit(1)
       
       # Create service files
       create_service_files()
       
       # Run tests
       run_tests()
       
       # Display information
       display_deployment_info()
       
   except KeyboardInterrupt:
       print("\n❌ Deployment cancelled by user")
       sys.exit(1)
   except Exception as e:
       print(f"\n❌ Deployment failed: {e}")
       sys.exit(1)

if __name__ == "__main__":
   main()