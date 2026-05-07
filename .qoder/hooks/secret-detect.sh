#!/bin/bash
# Secret detection hook for Qoder CLI
# Reads JSON from stdin, exits 2 if secrets are detected

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Determine what content to scan
CONTENT=""
if [ "$TOOL_NAME" = "Edit" ]; then
    CONTENT=$(echo "$INPUT" | jq -r '.tool_input.new_string // empty')
elif [ "$TOOL_NAME" = "Write" ]; then
    CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty')
fi

[ -z "$CONTENT" ] && exit 0

# Write content to a temp file for scanning
TMPFILE=$(mktemp)
echo "$CONTENT" > "$TMPFILE"

DETECTED=0

check_pattern() {
    local name="$1"
    local pattern="$2"
    local match
    match=$(grep -oiE -- "$pattern" "$TMPFILE" | head -n 3)
    if [ -n "$match" ]; then
        DETECTED=1
        echo "Potential secret detected ($name):" >&2
        echo "$match" | sed 's/^/  /' >&2
    fi
}

# AWS
check_pattern "AWS Access Key" "AKIA[0-9A-Z]{16}"
check_pattern "AWS Secret Key" "aws_secret_access_key\s*=\s*[\"'][A-Za-z0-9/+=]{40}[\"']"

# GitHub
check_pattern "GitHub Token" "gh[pousr]_[A-Za-z0-9_]{36,}"
check_pattern "GitHub Token (legacy)" "github[_-]?token\s*[:=]\s*[\"']?[a-z0-9]{35,40}[\"']?"

# API Keys
check_pattern "API Key" "api[_-]?key\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{16,}[\"']?"
check_pattern "API Secret" "api[_-]?secret\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{16,}[\"']?"

# Private Keys
check_pattern "Private Key" "-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"

# Generic secrets
check_pattern "Secret" "secret\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{8,}[\"']?"
check_pattern "Token" "token\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{8,}[\"']?"
check_pattern "Password" "password\s*[:=]\s*[\"'][^\"'\n]{4,}[\"']"

# Slack
check_pattern "Slack Token" "xox[baprs]-[0-9]{10,13}-[0-9]{10,13}[a-zA-Z0-9-]*"

# OpenAI
check_pattern "OpenAI Key" "sk-[a-zA-Z0-9]{48}"
check_pattern "OpenAI Project Key" "sk-proj-[a-zA-Z0-9_-]{100,}"

# JWT
check_pattern "JWT" "eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*"

# Generic high-entropy strings (more lenient, only in key=value contexts)
check_pattern "High-entropy string" "[A-Za-z0-9_\-]{32,64}"

rm -f "$TMPFILE"

if [ "$DETECTED" -eq 1 ]; then
    echo "" >&2
    echo "Secret detection blocked $TOOL_NAME on $FILE" >&2
    echo "If this is a false positive, you can bypass with a different approach." >&2
    exit 2
fi

exit 0
