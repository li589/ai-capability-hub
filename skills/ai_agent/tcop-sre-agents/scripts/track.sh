#!/bin/bash

set -o pipefail

BEACON_URL="https://otheve.beacon.qq.com/analytics/v2_upload"
SDK_ID="js"
SDK_VERSION="4.3.4-web"
APP_VERSION="1.0.0"
PLATFORM_ID="3"
TIMEOUT_SECONDS=3

APP_KEY="${1:-}"
SKILL_NAME="${2:-}"
EVENT_NAME="${3:-}"
CUSTOM_DATA="${4:-}"
USER_ID="${5:-${SKILL_TRACKER_USER_ID:-}}"

if [ -z "$APP_KEY" ] || [ -z "$SKILL_NAME" ] || [ -z "$EVENT_NAME" ]; then
    echo "Usage: bash scripts/track.sh <app_key> <skill_name> <event_name> [json_data]" >&2
    exit 0
fi

if [ "$APP_KEY" = "YOUR_APP_KEY" ] || [ "$APP_KEY" = "your_app_key" ] || [ "$APP_KEY" = "YOUR-APP-KEY" ]; then
    echo "[skill-tracker] WARNING: app_key is not configured (got '$APP_KEY'). Skipping event '$EVENT_NAME'." >&2
    echo "[skill-tracker] Please provide a valid Beacon Appkey. Get one at https://trackmate.woa.com/" >&2
    exit 0
fi

replace_symbol() {
    local value="$1"
    value="${value//|/%7C}"
    value="${value//&/%26}"
    value="${value//=/%3D}"
    value="${value//+/%2B}"
    echo "$value"
}

generate_a2() {
    local raw_hostname=""
    local raw_username=""
    local device_id=""

    raw_hostname=$(hostname 2>/dev/null || echo "unknown-host")
    raw_username=$(whoami 2>/dev/null || echo "unknown-user")

    if [ -z "$device_id" ] && [ -f /etc/machine-id ]; then
        device_id=$(cat /etc/machine-id 2>/dev/null | tr -d '[:space:]')
    fi
    if [ -z "$device_id" ] && [ -f /var/lib/dbus/machine-id ]; then
        device_id=$(cat /var/lib/dbus/machine-id 2>/dev/null | tr -d '[:space:]')
    fi
    if [ -z "$device_id" ] && command -v reg.exe &>/dev/null; then
        device_id=$(reg.exe query "HKLM\\SOFTWARE\\Microsoft\\Cryptography" /v MachineGuid 2>/dev/null \
            | grep -i "MachineGuid" | awk '{print $NF}' | tr -d '[:space:]')
    fi
    if [ -z "$device_id" ] && command -v ioreg &>/dev/null; then
        device_id=$(ioreg -rd1 -c IOPlatformExpertDevice 2>/dev/null \
            | grep IOPlatformUUID | sed 's/.*= "//;s/"//' | tr -d '[:space:]')
    fi

    local _uname_s=""
    _uname_s=$(uname -s 2>/dev/null || echo "")
    case "$_uname_s" in
        MINGW*|MSYS*|CYGWIN*) _is_windows=1 ;;
        *) _is_windows=0 ;;
    esac
    if [ -z "$device_id" ] && [ "$_is_windows" -eq 0 ]; then
        local raw_mac=""
        if command -v ifconfig &>/dev/null; then
            raw_mac=$(ifconfig 2>/dev/null | grep -oE '([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}' | head -1)
        elif command -v ip &>/dev/null; then
            raw_mac=$(ip link 2>/dev/null | grep -oE '([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}' | head -1)
        elif command -v getmac &>/dev/null; then
            raw_mac=$(getmac /FO CSV /NH 2>/dev/null | head -1 | cut -d',' -f1 | tr -d '"' | tr '-' ':')
        fi
        if [ -z "$raw_mac" ] && [ -d /sys/class/net ]; then
            for iface in /sys/class/net/*/address; do
                local addr=""
                addr=$(cat "$iface" 2>/dev/null | tr -d '[:space:]')
                if [ -n "$addr" ] && [ "$addr" != "00:00:00:00:00:00" ]; then
                    raw_mac="$addr"
                    break
                fi
            done
        fi
        [ -n "$raw_mac" ] && device_id=$(echo "$raw_mac" | tr '[:upper:]' '[:lower:]')
    fi

    if [ -z "$device_id" ]; then
        local did_dir="$HOME/.skill-tracker"
        local did_file="$did_dir/device-id"
        if [ -f "$did_file" ]; then
            device_id=$(cat "$did_file" 2>/dev/null | tr -d '[:space:]')
        fi
        if [ -z "$device_id" ]; then
            local new_did=""
            if command -v uuidgen &>/dev/null; then
                new_did=$(uuidgen 2>/dev/null | tr '[:upper:]' '[:lower:]')
            elif command -v python3 &>/dev/null; then
                new_did=$(python3 -c "import uuid; print(uuid.uuid4())" 2>/dev/null)
            elif [ -f /proc/sys/kernel/random/uuid ]; then
                new_did=$(cat /proc/sys/kernel/random/uuid 2>/dev/null)
            fi
            if [ -n "$new_did" ]; then
                mkdir -p "$did_dir" 2>/dev/null && echo "$new_did" > "$did_file" 2>/dev/null
                device_id="$new_did"
            fi
        fi
    fi

    [ -z "$device_id" ] && device_id="no-device-id"

    local fingerprint="${raw_hostname}:${raw_username}:${device_id}"

    local a2=""
    if command -v md5sum &>/dev/null; then
        a2=$(echo -n "$fingerprint" | md5sum | cut -c1-32)
    elif command -v md5 &>/dev/null; then
        a2=$(echo -n "$fingerprint" | md5 -q)
    elif command -v openssl &>/dev/null; then
        a2=$(echo -n "$fingerprint" | openssl md5 | sed 's/.*= //')
    elif command -v python3 &>/dev/null; then
        a2=$(echo -n "$fingerprint" | python3 -c "import hashlib,sys; print(hashlib.md5(sys.stdin.buffer.read()).hexdigest())" 2>/dev/null)
    else
        a2=$(echo -n "$fingerprint" | cksum | awk '{print $1}')
        a2=$(printf '%032s' "$a2" | tr ' ' '0')
    fi
    echo "$a2"
}

generate_a2_v2() {
    local h u sid fp
    h=$(hostname 2>/dev/null || echo "unknown-host")
    u=$(whoami 2>/dev/null || echo "unknown-user")
    sid=""

    if [ -z "$sid" ] && [ -f /etc/machine-id ]; then
        sid=$(cat /etc/machine-id 2>/dev/null | tr -d '[:space:]')
    fi
    if [ -z "$sid" ] && [ -f /var/lib/dbus/machine-id ]; then
        sid=$(cat /var/lib/dbus/machine-id 2>/dev/null | tr -d '[:space:]')
    fi
    if [ -z "$sid" ] && command -v reg.exe &>/dev/null; then
        sid=$(reg.exe query "HKLM\\SOFTWARE\\Microsoft\\Cryptography" /v MachineGuid 2>/dev/null \
            | grep -i "MachineGuid" | awk '{print $NF}' | tr -d '[:space:]')
    fi
    if [ -z "$sid" ] && command -v ioreg &>/dev/null; then
        sid=$(ioreg -rd1 -c IOPlatformExpertDevice 2>/dev/null \
            | grep IOPlatformUUID | sed 's/.*= "//;s/"//' | tr -d '[:space:]')
    fi
    if [ -z "$sid" ]; then
        local did_dir="$HOME/.skill-tracker"
        local did_file="$did_dir/device-id"
        if [ -f "$did_file" ]; then
            sid=$(cat "$did_file" 2>/dev/null | tr -d '[:space:]')
        fi
        if [ -z "$sid" ]; then
            local new_did=""
            if command -v uuidgen &>/dev/null; then
                new_did=$(uuidgen 2>/dev/null | tr '[:upper:]' '[:lower:]')
            elif command -v python3 &>/dev/null; then
                new_did=$(python3 -c "import uuid; print(uuid.uuid4())" 2>/dev/null)
            elif [ -f /proc/sys/kernel/random/uuid ]; then
                new_did=$(cat /proc/sys/kernel/random/uuid 2>/dev/null)
            fi
            if [ -n "$new_did" ]; then
                mkdir -p "$did_dir" 2>/dev/null && echo "$new_did" > "$did_file" 2>/dev/null
                sid="$new_did"
            fi
        fi
    fi
    [ -z "$sid" ] && sid="no-device-id"

    fp="${h}:${u}:${sid}"
    if command -v md5sum &>/dev/null; then
        echo -n "$fp" | md5sum | cut -c1-32
    elif command -v md5 &>/dev/null; then
        echo -n "$fp" | md5 -q
    elif command -v openssl &>/dev/null; then
        echo -n "$fp" | openssl md5 | sed 's/.*= //'
    elif command -v python3 &>/dev/null; then
        echo -n "$fp" | python3 -c "import hashlib,sys; print(hashlib.md5(sys.stdin.buffer.read()).hexdigest())" 2>/dev/null
    else
        local ck
        ck=$(echo -n "$fp" | cksum | awk '{print $1}')
        printf '%032s' "$ck" | tr ' ' '0'
    fi
}

detect_platform() {
    local platform="unknown"

    if [ -n "${CLAUDE_CODE_ENTRYPOINT:-}" ] || [ -n "${CLAUDE_SKILL_DIR:-}" ]; then
        platform="claude-code"
    elif [ -n "${CODEBUDDY_PROJECT_DIR:-}" ] || [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
        platform="codebuddy"
    elif [ -n "${CODEBUDDY_ENV:-}" ] || [ -n "${CODEBUDDY_VERSION:-}" ]; then
        platform="codebuddy"
    elif [ -n "${OPENCLAW_SHELL:-}" ] || [ -n "${OPENCLAW_ENV:-}" ] || [ -n "${OPENCLAW_VERSION:-}" ]; then
        platform="openclaw"
    elif [ -n "${BOXAI_ENV:-}" ] || [ -n "${BOXAI_VERSION:-}" ]; then
        platform="boxai"
    fi

    if [ "$platform" = "unknown" ]; then
        local parent_cmd=""
        parent_cmd=$(ps -o comm= -p $PPID 2>/dev/null || echo "")
        if echo "$parent_cmd" | grep -qi "claude"; then
            platform="claude-code"
        elif echo "$parent_cmd" | grep -qi "codebuddy"; then
            platform="codebuddy"
        elif echo "$parent_cmd" | grep -qi "openclaw"; then
            platform="openclaw"
        elif echo "$parent_cmd" | grep -qi "boxai"; then
            platform="boxai"
        fi
    fi

    if [ "$platform" = "unknown" ]; then
        if [ -d ".claude" ]; then
            platform="claude-code"
        fi
    fi

    if [ "$platform" = "unknown" ]; then
        if [ -n "${VSCODE_PID:-}" ] || [ -n "${TERM_PROGRAM:-}" ]; then
            platform="ide-${TERM_PROGRAM:-vscode}"
        fi
    fi

    echo "$platform"
}

detect_runtime() {
    local override="${SKILL_TRACKER_RUNTIME:-}"
    case "$override" in
        terminal|cloud-sandbox) echo "$override"; return ;;
    esac

    local sysname=""
    sysname=$(uname -s 2>/dev/null || echo "")
    case "$sysname" in
        Darwin|MINGW*|MSYS*|CYGWIN*) echo "terminal"; return ;;
    esac

    if [ -n "${ANTHROPIC_SANDBOX:-}" ] \
        || [ -n "${CODE_INTERPRETER:-}" ] \
        || [ -n "${GITHUB_ACTIONS:-}" ] \
        || [ -n "${GITLAB_CI:-}" ] \
        || [ -n "${JENKINS_URL:-}" ] \
        || [ -n "${CIRCLECI:-}" ] \
        || [ -n "${BUILDKITE:-}" ] \
        || [ -n "${CODEBUILD_BUILD_ID:-}" ] \
        || [ -n "${RUNNER_OS:-}" ] \
        || [ -n "${CODESPACE_NAME:-}" ]; then
        echo "cloud-sandbox"
        return
    fi

    local h u
    h=$(hostname 2>/dev/null | tr '[:upper:]' '[:lower:]')
    u=$(whoami 2>/dev/null | tr '[:upper:]' '[:lower:]')
    case "$u" in
        sandbox|runner|vscode|codespace) echo "cloud-sandbox"; return ;;
    esac
    case "$h" in
        runner[-_]*|sandbox*|codespaces[-_]*|ip-[0-9]*) echo "cloud-sandbox"; return ;;
    esac
    if [ ${#h} -eq 12 ] && echo "$h" | grep -qE '^[a-f0-9]{12}$'; then
        echo "cloud-sandbox"
        return
    fi

    echo "terminal"
}

collect_platform_context() {
    local platform="$1"
    local extra=""

    local os_info=""
    os_info=$(uname -s 2>/dev/null || echo "unknown")
    extra="\"skill_os\":\"$(replace_symbol "$os_info")\""

    local arch=""
    arch=$(uname -m 2>/dev/null || echo "unknown")
    extra="$extra,\"arch\":\"$(replace_symbol "$arch")\""

    if [ "$platform" = "codebuddy" ]; then
        local project_dir="${CODEBUDDY_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-$(pwd)}}"
        extra="$extra,\"project_dir\":\"$(replace_symbol "$(basename "$project_dir")")\""

        local project_type="unknown"
        if [ -f "$project_dir/package.json" ]; then project_type="nodejs"
        elif [ -f "$project_dir/go.mod" ]; then project_type="go"
        elif [ -f "$project_dir/requirements.txt" ] || [ -f "$project_dir/pyproject.toml" ]; then project_type="python"
        elif [ -f "$project_dir/Cargo.toml" ]; then project_type="rust"
        elif [ -f "$project_dir/pom.xml" ] || [ -f "$project_dir/build.gradle" ]; then project_type="java"
        elif [ -f "$project_dir/CMakeLists.txt" ] || [ -f "$project_dir/Makefile" ]; then project_type="cpp"
        fi
        extra="$extra,\"project_type\":\"$project_type\""

        local file_count="0"
        file_count=$(find "$project_dir" -maxdepth 2 -type f ! -path '*/.git/*' 2>/dev/null | wc -l | tr -d ' ')
        extra="$extra,\"file_count\":\"$file_count\""

        if [ -f "$project_dir/.codebuddy/settings.json" ]; then
            extra="$extra,\"hooks_active\":\"true\""
        else
            extra="$extra,\"hooks_active\":\"false\""
        fi
    fi

    if [ "$platform" = "claude-code" ]; then
        local project_dir="${CLAUDE_SKILL_DIR:-$(pwd)}"
        extra="$extra,\"project_dir\":\"$(replace_symbol "$(basename "$project_dir")")\""

        local project_type="unknown"
        if [ -f "$project_dir/package.json" ]; then project_type="nodejs"
        elif [ -f "$project_dir/go.mod" ]; then project_type="go"
        elif [ -f "$project_dir/requirements.txt" ] || [ -f "$project_dir/pyproject.toml" ]; then project_type="python"
        elif [ -f "$project_dir/Cargo.toml" ]; then project_type="rust"
        elif [ -f "$project_dir/pom.xml" ] || [ -f "$project_dir/build.gradle" ]; then project_type="java"
        elif [ -f "$project_dir/CMakeLists.txt" ] || [ -f "$project_dir/Makefile" ]; then project_type="cpp"
        fi
        extra="$extra,\"project_type\":\"$project_type\""

        if [ -f "$project_dir/.claude/settings.json" ] || [ -f "$project_dir/SKILL.md" ]; then
            extra="$extra,\"hooks_active\":\"true\""
        else
            extra="$extra,\"hooks_active\":\"false\""
        fi
    fi

    echo "$extra"
}

collect_skill_user() {
    local user="${SKILL_TRACKER_USER:-}"
    if [ -z "$user" ]; then
        user=$(whoami 2>/dev/null || echo "unknown")
    fi
    echo "$user"
}

collect_skill_version() {
    local version="${SKILL_VERSION:-}"

    if [ -z "$version" ] && [ -f "$SKILL_DIR/pyproject.toml" ]; then
        version=$(grep -E '^version\s*=' "$SKILL_DIR/pyproject.toml" 2>/dev/null \
            | head -1 | sed 's/.*=\s*["'"'"']\(.*\)["'"'"'].*/\1/')
    fi

    if [ -z "$version" ] && [ -f "$SKILL_DIR/package.json" ]; then
        version=$(grep -o '"version"[[:space:]]*:[[:space:]]*"[^"]*"' "$SKILL_DIR/package.json" 2>/dev/null \
            | head -1 | sed 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
    fi

    if [ -z "$version" ] && [ -f "$SKILL_DIR/VERSION" ]; then
        version=$(cat "$SKILL_DIR/VERSION" 2>/dev/null | tr -d '[:space:]')
    fi

    echo "$version"
}

if [ -z "${SKILL_DIR:-}" ]; then
    SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

build_map_value() {
    local skill_name="$1"
    local platform="$2"
    local platform_context="$3"
    local custom_data="$4"
    local runtime="$5"

    local map_value=""
    map_value="\"skill_name\":\"$(replace_symbol "$skill_name")\""
    map_value="$map_value,\"skill_platform\":\"$(replace_symbol "$platform")\""
    map_value="$map_value,\"skill_runtime\":\"$(replace_symbol "$runtime")\""

    local skill_user=""
    skill_user=$(collect_skill_user)
    map_value="$map_value,\"skill_user\":\"$(replace_symbol "$skill_user")\""

    local skill_version=""
    skill_version=$(collect_skill_version)
    if [ -n "$skill_version" ]; then
        map_value="$map_value,\"skill_version\":\"$(replace_symbol "$skill_version")\""
    fi

    if [ -n "$platform_context" ]; then
        map_value="$map_value,$platform_context"
    fi

    if [ -n "$custom_data" ]; then
        local stripped=""
        stripped=$(echo "$custom_data" | sed 's/^[[:space:]]*{//;s/}[[:space:]]*$//')
        if [ -n "$stripped" ]; then
            map_value="$map_value,$stripped"
        fi
    fi

    echo "{$map_value}"
}

main() {
    local a2=""
    a2=$(generate_a2)

    local a2_v2=""
    a2_v2=$(generate_a2_v2)

    local platform=""
    platform=$(detect_platform)

    local runtime=""
    runtime=$(detect_runtime)

    local platform_context=""
    platform_context=$(collect_platform_context "$platform")

    local event_time=""
    if date +%s%3N &>/dev/null 2>&1; then
        event_time=$(date +%s%3N 2>/dev/null)
        if echo "$event_time" | grep -q "N"; then
            event_time="$(date +%s)000"
        fi
    else
        event_time="$(date +%s)000"
    fi

    local map_value=""
    map_value=$(build_map_value "$SKILL_NAME" "$platform" "$platform_context" "$CUSTOM_DATA" "$runtime")

    local common_fields=""
    if [ -n "$USER_ID" ]; then
        common_fields="\"A1\": \"$(replace_symbol "$USER_ID")\", \"A2\": \"${a2}\", \"A2_v2\": \"${a2_v2}\""
    else
        common_fields="\"A2\": \"${a2}\", \"A2_v2\": \"${a2_v2}\""
    fi

    local body=""
    body=$(cat <<EOF
{
    "appVersion": "${APP_VERSION}",
    "sdkId": "${SDK_ID}",
    "sdkVersion": "${SDK_VERSION}",
    "mainAppKey": "$(replace_symbol "$APP_KEY")",
    "platformId": ${PLATFORM_ID},
    "common": {
        ${common_fields}
    },
    "events": [
        {
            "eventCode": "$(replace_symbol "$EVENT_NAME")",
            "eventTime": "${event_time}",
            "mapValue": ${map_value}
        }
    ]
}
EOF
)

    curl -s -o /dev/null \
        --max-time "$TIMEOUT_SECONDS" \
        -X POST "$BEACON_URL" \
        -H "Content-Type: application/json;charset=UTF-8" \
        -d "$body" 2>/dev/null || true

    exit 0
}

main
