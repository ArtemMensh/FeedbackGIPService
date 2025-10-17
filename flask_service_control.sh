#!/bin/bash

#!/usr/bin/env bash
set -euo pipefail

APP_NAME="flask_service"           # Название вашего приложения (можно изменить)
APP_DIR="/home/projects/FeedbackGIPService"        # Путь к вашему Flask приложению
APP_SCRIPT="main.py"                # Имя файла вашего Flask приложения

VENV_DIR="$APP_DIR/.venv"
PYTHON="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"

LOG_FILE="$APP_DIR/flask_service.log"
PID_FILE="$APP_DIR/flask_service.pid"
REQ_FILE="$APP_DIR/requirements.txt"
REQ_HASH_FILE="$VENV_DIR/.req.sha256"

ensure_venv() {
  if [[ ! -x "$PYTHON" ]]; then
    echo "[init] creating venv at $VENV_DIR" | tee -a "$LOG_FILE"
    python3 -m venv "$VENV_DIR"
    "$PIP" install --upgrade pip setuptools wheel --disable-pip-version-check
  fi
}

install_deps_if_needed() {
  [[ -f "$REQ_FILE" ]] || { echo "[deps] no requirements.txt — skip" | tee -a "$LOG_FILE"; return 0; }
  local new_hash old_hash=""
  new_hash="$(sha256sum "$REQ_FILE" | awk '{print $1}')"
  [[ -f "$REQ_HASH_FILE" ]] && old_hash="$(cat "$REQ_HASH_FILE")"
  if [[ "$new_hash" != "$old_hash" ]]; then
    echo "[deps] installing from $REQ_FILE" | tee -a "$LOG_FILE"
    "$PIP" install --no-cache-dir -r "$REQ_FILE" --disable-pip-version-check
    echo "$new_hash" > "$REQ_HASH_FILE"
    echo "[deps] up to date" | tee -a "$LOG_FILE"
  fi
}

# Функция для запуска сервиса
start_service() {
     if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "$APP_NAME is already running." | tee -a "$LOG_FILE"
        return 0
     fi
     cd "$APP_DIR"
     ensure_venv
     install_deps_if_needed
     echo "Starting $APP_NAME..." | tee -a "$LOG_FILE"
     nohup "$PYTHON" "$APP_SCRIPT" >> "$LOG_FILE" 2>&1 &
     echo $! > "$PID_FILE"
     echo "$APP_NAME started with PID $(cat "$PID_FILE")." | tee -a "$LOG_FILE"
}

# Функция для остановки сервиса
stop_service() {
    if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "Stopping $APP_NAME..." | tee -a "$LOG_FILE"
    kill "$(cat "$PID_FILE")" || true
    rm -f "$PID_FILE"
    echo "$APP_NAME stopped." | tee -a "$LOG_FILE"
  else
    echo "$APP_NAME is not running." | tee -a "$LOG_FILE"
  fi
}

# Функция для проверки статуса сервиса
status_service() {
    if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "$APP_NAME is running with PID $(cat "$PID_FILE")." | tee -a "$LOG_FILE"
  else
    echo "$APP_NAME is not running." | tee -a "$LOG_FILE"
  fi
}

# Функция для перезапуска сервиса
restart_service() {
    echo "Restarting $APP_NAME..." | tee -a "$LOG_FILE"
    stop_service
    start_service
}

# Логика команд
case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        status_service
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
