#!/bin/bash

echo "==============================="
echo "PYTHON VERSION"
echo "==============================="
python --version
echo ""

echo "==============================="
echo "AIROGRAM VERSION"
echo "==============================="
pip show aiogram 2>/dev/null || echo "aiogram not installed"
echo ""

echo "==============================="
echo "PYTHON-TELEGRAM-BOT VERSION"
echo "==============================="
pip show python-telegram-bot 2>/dev/null || echo "python-telegram-bot not installed"
echo ""

echo "==============================="
echo "FIND SQLITE DATABASE"
echo "==============================="
DB_FILE=$(find . -name "*.db" | head -n 1)

if [ -z "$DB_FILE" ]; then
  echo "No .db file found"
else
  echo "Database found: $DB_FILE"
  echo ""

  echo "==============================="
  echo "TABLES"
  echo "==============================="
  sqlite3 "$DB_FILE" ".tables"
  echo ""

  echo "==============================="
  echo "BOTSETTINGS SCHEMA"
  echo "==============================="
  sqlite3 "$DB_FILE" ".schema botsettings"
  echo ""

  echo "==============================="
  echo "BOTSETTINGS DATA"
  echo "==============================="
  sqlite3 "$DB_FILE" "SELECT * FROM botsettings;"
  echo ""
fi

echo "==============================="
echo "SEARCH intro_chat_id IN PROJECT"
echo "==============================="
grep -R "intro_chat_id" . 2>/dev/null

echo ""
echo "==============================="
echo "DONE"
echo "==============================="