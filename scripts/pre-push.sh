#!/bin/bash
# Pre-push script to check linting, formatting, and tests before pushing to remote
# Usage: ./scripts/pre-push.sh

set -e  # Exit on any error

echo "🚀 Running pre-push checks..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}➤${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

# Ensure we're in the project root
if [ ! -f "pyproject.toml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    print_error "Poetry is not installed. Please install Poetry first."
    exit 1
fi

echo "🔍 Pre-push Quality Checks"
echo "=========================="
echo ""

# 1. Backend Linting
print_status "Running Ruff linting checks..."
if poetry run ruff check backend/ tests/; then
    print_success "Ruff linting passed"
else
    print_error "Ruff linting failed. Fix linting errors before pushing."
    echo ""
    echo "💡 Tip: Run 'poetry run ruff check --fix backend/ tests/' to auto-fix many issues"
    exit 1
fi
echo ""

# 2. Code Formatting
print_status "Checking Black code formatting..."
if poetry run black --check backend/ tests/; then
    print_success "Black formatting check passed"
else
    print_error "Black formatting check failed. Code needs formatting."
    echo ""
    echo "💡 Tip: Run 'poetry run black backend/ tests/' to format your code"
    exit 1
fi
echo ""

# 3. Type Checking
print_status "Running MyPy type checking..."
if poetry run mypy backend/; then
    print_success "MyPy type checking passed"
else
    print_error "MyPy type checking failed. Fix type errors before pushing."
    echo ""
    echo "💡 Tip: Add type annotations or # type: ignore comments for untyped code"
    exit 1
fi
echo ""

# 4. Backend Tests
print_status "Running backend tests..."
if poetry run pytest backend/tests/ -v --tb=short; then
    print_success "Backend tests passed"
else
    print_error "Backend tests failed. Fix failing tests before pushing."
    exit 1
fi
echo ""

# 5. Integration Tests (optional - skip if not available)
if [ -f "tests/test_api.py" ]; then
    print_status "Running integration tests..."
    if poetry run pytest tests/ -v --tb=short; then
        print_success "Integration tests passed"
    else
        print_warning "Integration tests failed (may require running backend server)"
        echo "   You can skip this by running the backend server in another terminal:"
        echo "   cd backend && poetry run uvicorn app.main:app --reload"
    fi
    echo ""
fi

# 6. Frontend Tests (if frontend exists and has package.json)
if [ -f "frontend/package.json" ]; then
    print_status "Running frontend tests..."
    cd frontend
    if npm test -- --watchAll=false --passWithNoTests; then
        print_success "Frontend tests passed"
    else
        print_error "Frontend tests failed. Fix failing frontend tests before pushing."
        cd ..
        exit 1
    fi
    cd ..
    echo ""
fi

# 7. Frontend Build Test (if frontend exists)
if [ -f "frontend/package.json" ]; then
    print_status "Testing frontend build..."
    cd frontend
    if npm run build; then
        print_success "Frontend build successful"
    else
        print_error "Frontend build failed. Fix build errors before pushing."
        cd ..
        exit 1
    fi
    cd ..
    echo ""
fi

# All checks passed!
echo "🎉 All pre-push checks passed!"
echo ""
echo "✅ Ruff linting: PASSED"
echo "✅ Black formatting: PASSED"
echo "✅ MyPy type checking: PASSED"
echo "✅ Backend tests: PASSED"
if [ -f "tests/test_api.py" ]; then
    echo "✅ Integration tests: PASSED"
fi
if [ -f "frontend/package.json" ]; then
    echo "✅ Frontend tests: PASSED"
    echo "✅ Frontend build: PASSED"
fi
echo ""
echo "🚀 Your code is ready to push to the remote repository!"
echo ""
echo "Next steps:"
echo "  git add ."
echo "  git commit -m 'Your commit message'"
echo "  git push"