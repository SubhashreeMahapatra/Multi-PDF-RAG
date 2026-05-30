#!/bin/bash
# ========================================
# Multi-PDF RAG Chat - Quick Setup Script
# ========================================

set -e
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 Setting up Multi-PDF RAG Chat System...${NC}\n"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Install Python 3.11+${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python found: $(python3 --version)${NC}"

# Check Node
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found. Install Node.js 18+${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Node found: $(node --version)${NC}"

# Backend setup
echo -e "\n${YELLOW}📦 Setting up backend...${NC}"
cd backend

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt --quiet

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Created .env from example. Please add your OPENAI_API_KEY!${NC}"
fi

cd ..

# Frontend setup
echo -e "\n${YELLOW}📦 Setting up frontend...${NC}"
cd frontend
npm install --silent
cd ..

echo -e "\n${GREEN}✅ Setup complete!${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Edit backend/.env and add your OPENAI_API_KEY"
echo "2. Start backend:  cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "3. Start frontend: cd frontend && npm run dev"
echo "4. Visit: http://localhost:5173"
echo ""
echo -e "${GREEN}📚 Docs: http://localhost:8000/docs${NC}"
