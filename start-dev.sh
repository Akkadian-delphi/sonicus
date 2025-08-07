#!/bin/bash

# Sonicus Development Startup Script
# Starts both backend (FastAPI) and frontend (React) servers

echo "🌿 Starting Sonicus Development Environment"
echo "=========================================="

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the Sonicus project root directory"
    echo "Expected structure: /path/to/Sonicus/{backend,frontend}"
    exit 1
fi

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

echo "🔍 Checking ports..."

# Check backend port (18100)
if check_port 18100; then
    echo "✅ Backend port 18100 is already in use (backend may already be running)"
else
    echo "🚀 Starting FastAPI backend on port 18100..."
    cd backend
    python -m uvicorn run:app --host 127.0.0.1 --port 18100 --reload &
    BACKEND_PID=$!
    cd ..
    sleep 3
    echo "✅ Backend started with PID $BACKEND_PID"
fi

# Check frontend port (3000)  
if check_port 3000; then
    echo "✅ Frontend port 3000 is already in use (frontend may already be running)"
else
    echo "🌐 Starting React frontend on port 3000..."
    cd frontend
    npm start &
    FRONTEND_PID=$!
    cd ..
    echo "✅ Frontend started with PID $FRONTEND_PID"
fi

echo ""
echo "🎉 Sonicus Development Environment is ready!"
echo "=========================================="
echo "🔧 Backend API:  http://localhost:18100"
echo "🔧 API Docs:     http://localhost:18100/docs"
echo "🌐 Frontend App: http://localhost:3000"
echo ""
echo "📝 Test Credentials:"
echo "   Email:    test.user@example.com"
echo "   Password: testpassword123"
echo ""
echo "⏹️  To stop both servers, press Ctrl+C"
echo "🐛 To debug, check terminal output above"

# Wait for interrupt signal
trap 'echo "🛑 Stopping servers..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit' INT

# Keep script running
wait
