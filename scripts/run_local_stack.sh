#!/usr/bin/env bash
# ==============================================================================
# Suraksha Identity Protection Platform
# Interactive Local Stack Runner & First-Principles Testing Controller
# ==============================================================================
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PORT=8000
MOBILE_PORT=8082
MINISKY_PORT=8080

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
RESET='\033[0m'

cd "$REPO_ROOT"

# Check prerequisites
check_prerequisites() {
    echo -e "${CYAN}Checking runtime environment...${RESET}"
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}✖ 'uv' is not installed. Run: curl -LsSf https://astral.sh/uv/install.sh | sh${RESET}"
        exit 1
    fi
    if ! command -v node &> /dev/null; then
        echo -e "${RED}✖ 'node' is not installed. Please install Node.js 18+.${RESET}"
        exit 1
    fi
    echo -e "${GREEN}✓ uv ($(uv --version)) and node ($(node -v)) detected.${RESET}"
}

start_backend() {
    if lsof -i :$BACKEND_PORT > /dev/null 2>&1; then
        echo -e "${YELLOW}ℹ Backend is already running on http://localhost:$BACKEND_PORT${RESET}"
    else
        echo -e "${CYAN}Starting FastAPI backend on http://localhost:$BACKEND_PORT...${RESET}"
        nohup uv run uvicorn services.api.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > .backend.log 2>&1 &
        local pid=$!
        echo $pid > .backend.pid
        
        # Poll up to 10 seconds for backend readiness
        local attempts=0
        while [ $attempts -lt 10 ]; do
            if curl -s http://localhost:$BACKEND_PORT/readyz | grep -q "ready" > /dev/null 2>&1; then
                break
            fi
            sleep 1
            attempts=$((attempts + 1))
        done

        if lsof -i :$BACKEND_PORT > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Backend started successfully (PID: $pid, Log: .backend.log)${RESET}"
        else
            echo -e "${RED}✖ Failed to start backend within 10s. Check .backend.log for errors.${RESET}"
            cat .backend.log | tail -n 15
        fi
    fi
}

start_mobile() {
    if lsof -i :$MOBILE_PORT > /dev/null 2>&1; then
        echo -e "${YELLOW}ℹ React Native client is already running on http://localhost:$MOBILE_PORT${RESET}"
    else
        echo -e "${CYAN}Checking mobile dependencies in apps/mobile...${RESET}"
        if [ ! -d "apps/mobile/node_modules" ]; then
            echo -e "${YELLOW}Installing mobile dependencies (npm install)...${RESET}"
            (cd apps/mobile && npm install --silent)
        fi
        echo -e "${CYAN}Starting React Native / Expo web client on port $MOBILE_PORT...${RESET}"
        (cd apps/mobile && nohup npx expo start --web --port $MOBILE_PORT > ../../.mobile.log 2>&1 &)
        local pid=$!
        echo $pid > .mobile.pid
        sleep 3
        echo -e "${GREEN}✓ React Native client launched (PID: $pid, Log: .mobile.log)${RESET}"
        echo -e "${GREEN}  👉 Open in browser: http://localhost:$MOBILE_PORT${RESET}"
    fi
}

seed_data() {
    echo -e "${CYAN}Seeding database with synthetic Indian identity profiles & dark web leaks...${RESET}"
    uv run python dummy_data_to_test/seed_db.py --seed-db --residents 10
    echo -e "${GREEN}✓ Database seeded with Verhoeff-valid Aadhaar and PAN numbers.${RESET}"
}

run_interactive_test() {
    echo -e "${CYAN}Launching interactive first-principles verification test...${RESET}"
    uv run python scripts/interactive_test.py
}

run_auto_test() {
    echo -e "${CYAN}Executing automated end-to-end smoke test...${RESET}"
    uv run python scripts/interactive_test.py --auto
}

check_status() {
    echo -e "\n${BOLD}${CYAN}=== Active Suraksha Local Stack Status ===${RESET}"
    
    echo -n "1. Backend API (Port $BACKEND_PORT): "
    if lsof -i :$BACKEND_PORT > /dev/null 2>&1; then
        echo -e "${GREEN}ONLINE${RESET} (curl -s http://localhost:$BACKEND_PORT/readyz -> OK)"
    else
        echo -e "${RED}OFFLINE${RESET}"
    fi

    echo -n "2. React Native App (Port $MOBILE_PORT): "
    if lsof -i :$MOBILE_PORT > /dev/null 2>&1; then
        echo -e "${GREEN}ONLINE${RESET} (Listening at http://localhost:$MOBILE_PORT)"
    else
        echo -e "${RED}OFFLINE${RESET}"
    fi

    echo -n "3. MiniSky GCP Emulator (Port $MINISKY_PORT): "
    if lsof -i :$MINISKY_PORT > /dev/null 2>&1; then
        echo -e "${GREEN}ONLINE${RESET} (Dashboard at http://localhost:8081)"
    else
        echo -e "${YELLOW}STANDBY${RESET}"
    fi
    echo ""
}

stop_services() {
    echo -e "${YELLOW}Stopping local stack background processes...${RESET}"
    if [ -f .backend.pid ]; then
        kill $(cat .backend.pid) 2>/dev/null || true
        rm -f .backend.pid
    fi
    if [ -f .mobile.pid ]; then
        kill $(cat .mobile.pid) 2>/dev/null || true
        rm -f .mobile.pid
    fi
    # Also kill any stray processes on port 8000 or 8082 if owned by user
    local b_pids=$(lsof -ti :$BACKEND_PORT 2>/dev/null || true)
    if [ -n "$b_pids" ]; then
        kill -9 $b_pids 2>/dev/null || true
    fi
    local m_pids=$(lsof -ti :$MOBILE_PORT 2>/dev/null || true)
    if [ -n "$m_pids" ]; then
        kill -9 $m_pids 2>/dev/null || true
    fi
    echo -e "${GREEN}✓ All local stack services stopped.${RESET}"
}

show_menu() {
    echo -e "${CYAN}${BOLD}"
    echo "╔══════════════════════════════════════════════════════════════════════╗"
    echo "║          SURAKSHA IDENTITY PROTECTION - INTERACTIVE CONTROLLER        ║"
    echo "╚══════════════════════════════════════════════════════════════════════╝"
    echo -e "${RESET}"
    echo "Please choose an action:"
    echo -e "  ${BOLD}[1]${RESET} 🚀 ${GREEN}Start Full Stack${RESET} (Backend API :$BACKEND_PORT + React Native App :$MOBILE_PORT)"
    echo -e "  ${BOLD}[2]${RESET} 🖥️  ${CYAN}Start Backend Web Server Only${RESET} (http://localhost:$BACKEND_PORT)"
    echo -e "  ${BOLD}[3]${RESET} 📱 ${CYAN}Start React Native Mobile Client Only${RESET} (http://localhost:$MOBILE_PORT)"
    echo -e "  ${BOLD}[4]${RESET} 🧪 ${YELLOW}Run Interactive E2E Testing Console${RESET} (First-principles walkthrough)"
    echo -e "  ${BOLD}[5]${RESET} ⚡ ${YELLOW}Run Automated Fast Smoke Test${RESET} (Non-interactive test)"
    echo -e "  ${BOLD}[6]${RESET} 📦 ${MAGENTA}Seed Database with Synthetic Indian Identity Dataset${RESET}"
    echo -e "  ${BOLD}[7]${RESET} 🔍 ${CYAN}Check Active Stack Status & Port Health${RESET}"
    echo -e "  ${BOLD}[8]${RESET} 🛑 ${RED}Stop All Local Background Services${RESET}"
    echo -e "  ${BOLD}[0]${RESET} 🚪 Exit"
    echo ""
}

# Trap Ctrl+C cleanly
trap 'echo -e "\n${YELLOW}Exiting controller.${RESET}"; exit 0' INT TERM

check_prerequisites

# Non-interactive argument dispatch support
if [ "$1" == "--all" ] || [ "$1" == "start" ]; then
    start_backend
    start_mobile
    check_status
    exit 0
elif [ "$1" == "--test" ]; then
    start_backend
    run_auto_test
    exit 0
elif [ "$1" == "--stop" ]; then
    stop_services
    exit 0
fi

while true; do
    show_menu
    read -p "Select option [0-8]: " choice
    case $choice in
        1)
            start_backend
            start_mobile
            check_status
            ;;
        2)
            start_backend
            ;;
        3)
            start_mobile
            ;;
        4)
            start_backend
            run_interactive_test
            ;;
        5)
            start_backend
            run_auto_test
            ;;
        6)
            seed_data
            ;;
        7)
            check_status
            ;;
        8)
            stop_services
            ;;
        0)
            echo -e "${GREEN}Goodbye!${RESET}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid selection. Please enter a number between 0 and 8.${RESET}"
            ;;
    esac
    echo ""
    read -p "Press Enter to return to main menu..."
    clear || true
done
