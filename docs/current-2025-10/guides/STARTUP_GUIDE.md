# 🚀 OmicsOracle Startup Guide

Welcome to OmicsOracle! This guide explains how to start the application using our unified, intelligent startup system.

## 🎯 One Script to Rule Them All

We've consolidated all startup functionality into a single, smart script: `start.sh`

This universal launcher can handle:
- ✅ Backend-only mode
- ✅ Frontend-only mode
- ✅ Full-stack mode (both backend and frontend)
- ✅ Development mode with hot reload
- ✅ Automatic port detection and conflict resolution
- ✅ Smart environment setup

## 🚀 Quick Start

### Start Everything (Recommended)
```bash
./start.sh
```
This starts both the backend API server (port 8000) and the futuristic frontend interface (port 8001).

### Backend Only
```bash
./start.sh --backend-only
```
Perfect for API development, testing, or when using external frontends.

### Frontend Only
```bash
./start.sh --frontend-only
```
Great for frontend development when the backend is already running elsewhere.

### Development Mode
```bash
./start.sh --dev
```
Enables hot reload, build tools, and enhanced development features.

## 📋 All Available Options

```bash
Usage: ./start.sh [options]

Options:
  --backend-only         Start only the backend server
  --frontend-only        Start only the frontend interface
  --dev                  Enable development mode (hot reload, build tools)
  --backend-port PORT    Backend port (default: 8000)
  --frontend-port PORT   Frontend port (default: 8001)
  --help, -h            Show help message

Examples:
  ./start.sh                     # Start both backend and frontend
  ./start.sh --backend-only      # Start only backend
  ./start.sh --frontend-only     # Start only frontend
  ./start.sh --dev               # Full-stack with development tools
  ./start.sh --backend-port 9000 --frontend-port 9001  # Custom ports
```

## 🌐 Access Points

After starting, you can access:

### Backend (API Server)
- **Main API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Alternative Docs**: http://localhost:8000/redoc

### Frontend (Futuristic Interface)
- **Main Interface**: http://localhost:8001
- **Enhanced Search**: http://localhost:8001/api/v2/search/enhanced
- **WebSocket**: ws://localhost:8001/ws/{client_id}

## 🔧 Advanced Features

### Automatic Mode Detection
The script is smart enough to detect what you want based on how you call it:

```bash
# These all start backend-only mode:
./start.sh --backend-only
./start.sh --backend
./start.sh --api

# These all start frontend-only mode:
./start.sh --frontend-only
./start.sh --frontend
./start.sh --ui
```

### Environment Setup
The script automatically:
- ✅ Detects and activates virtual environments (`venv/`)
- ✅ Loads environment variables from `.env.local`
- ✅ Sets up the Python path
- ✅ Checks for required dependencies
- ✅ Manages port conflicts

### Background Process Management
- Services run in the background with proper logging
- Press `Ctrl+C` to stop all services cleanly
- Automatic cleanup on exit
- Process monitoring and health checks

## 🛠️ Prerequisites

Before running, ensure you have:

1. **Python 3.8+** installed
2. **Virtual environment** set up (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Dependencies** installed:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-web.txt
   pip install -r requirements-dev.txt
   ```
4. **Node.js and npm** (for frontend development):
   ```bash
   cd interfaces/futuristic_enhanced
   npm install
   ```

## 🐛 Troubleshooting

### Port Already in Use
The script automatically detects and handles port conflicts:
```bash
[WARN] Backend port 8000 is already in use
[OK] Backend appears to be already running
```

### Backend Not Starting
Check the logs:
```bash
tail -f backend.log
```

### Frontend Build Issues
Enable development mode for detailed build output:
```bash
./start.sh --dev
```

### Virtual Environment Issues
Make sure your virtual environment is properly set up:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 📁 File Locations

- **Main Script**: `/start.sh` (root directory)
- **Frontend Dev Script**: `/interfaces/futuristic_enhanced/start_enhanced.sh` (implementation detail)
- **Logs**: `backend.log`, `server.log`
- **Environment**: `.env.local`, `.env.development`

## 🎯 Why One Script?

We consolidated from 10+ startup scripts to this single, intelligent launcher because:

- ✅ **Eliminates confusion** - no more guessing which script to use
- ✅ **Reduces maintenance** - one script to maintain and update
- ✅ **Better UX** - consistent interface and options
- ✅ **Smart defaults** - works out of the box for most use cases
- ✅ **Expert friendly** - full control with command-line options

## 📞 Support

If you encounter issues:

1. Check this guide first
2. Run `./start.sh --help` for quick reference
3. Check the log files (`backend.log`, `server.log`)
4. Ensure all prerequisites are met
5. Open an issue on GitHub with error details

---

**Happy coding!** 🧬✨
