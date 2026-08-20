#!/bin/sh

# SkillHub cloud-sandbox compatibility path for free, local-only preflight.
# This script intentionally supports only doctor and structure-manifest creation.
# Paid requests, plan application, HTML generation, and updates remain on the
# Python 3.10+ runtime so payment state cannot be weakened by a shell fallback.

LC_ALL=C
export LC_ALL
umask 077

emit_error() {
    code=$1
    message=$2
    exit_code=${3:-2}
    printf '{"status":"error","code":"%s","message":"%s","data":{"uploaded":false,"model_calls":0,"source_files_changed":false}}\n' \
        "$code" "$message"
    exit "$exit_code"
}

require_value() {
    option=$1
    count=$2
    if [ "$count" -lt 2 ]; then
        emit_error "SKILLHUB_COMPAT_ARGUMENT_INVALID" "Missing value for $option."
    fi
}

detect_stat_mode() {
    probe=$1
    if stat -c %s "$probe" >/dev/null 2>&1; then
        printf '%s' "gnu"
        return 0
    fi
    if stat -f %z "$probe" >/dev/null 2>&1; then
        printf '%s' "bsd"
        return 0
    fi
    return 1
}

detect_hash_mode() {
    if command -v sha256sum >/dev/null 2>&1; then
        printf '%s' "sha256sum"
        return 0
    fi
    if command -v shasum >/dev/null 2>&1; then
        printf '%s' "shasum"
        return 0
    fi
    if command -v openssl >/dev/null 2>&1; then
        printf '%s' "openssl"
        return 0
    fi
    return 1
}

hash_file() {
    mode=$1
    path=$2
    case "$mode" in
        sha256sum)
            sha256sum "$path" | awk '{print $1}'
            ;;
        shasum)
            shasum -a 256 "$path" | awk '{print $1}'
            ;;
        openssl)
            openssl dgst -sha256 "$path" | awk '{print $NF}'
            ;;
        *)
            return 1
            ;;
    esac
}

python_3_10_available() {
    if command -v python3 >/dev/null 2>&1 &&
        python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
        return 0
    fi
    if command -v python >/dev/null 2>&1 &&
        python -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

resolve_directory() {
    path=$1
    if [ ! -d "$path" ] || [ -L "$path" ]; then
        return 1
    fi
    (
        CDPATH=
        cd "$path" 2>/dev/null || exit 1
        pwd -P
    )
}

subcommand=${1:-}
if [ -z "$subcommand" ]; then
    emit_error "SKILLHUB_COMPAT_ARGUMENT_INVALID" "A subcommand is required."
fi
shift

source_path=
workspace_path=
output_path=
confirmed=false

while [ "$#" -gt 0 ]; do
    case "$1" in
        --source)
            require_value "$1" "$#"
            source_path=$2
            shift 2
            ;;
        --workspace)
            require_value "$1" "$#"
            workspace_path=$2
            shift 2
            ;;
        --output)
            require_value "$1" "$#"
            output_path=$2
            shift 2
            ;;
        --confirm-structure-only)
            confirmed=true
            shift
            ;;
        --json)
            shift
            ;;
        *)
            emit_error "SKILLHUB_COMPAT_ARGUMENT_INVALID" "Unsupported argument."
            ;;
    esac
done

for required_command in find awk stat mktemp tr rm; do
    if ! command -v "$required_command" >/dev/null 2>&1; then
        emit_error "SKILLHUB_COMPAT_RUNTIME_INCOMPLETE" "The free precheck runtime is incomplete."
    fi
done

if [ -z "$source_path" ]; then
    emit_error "SKILLHUB_SOURCE_REQUIRED" "An explicit source directory is required."
fi
source_abs=$(resolve_directory "$source_path") ||
    emit_error "SKILLHUB_SOURCE_INVALID" "The source must be a readable, non-symlink directory."
if [ "$source_abs" = "/" ]; then
    emit_error "SKILLHUB_SOURCE_TOO_BROAD" "The filesystem root cannot be used as the source."
fi
if [ ! -r "$source_abs" ] || [ ! -x "$source_abs" ]; then
    emit_error "SKILLHUB_SOURCE_NOT_READABLE" "The source directory is not readable."
fi

stat_mode=$(detect_stat_mode "$source_abs") ||
    emit_error "SKILLHUB_METADATA_STAT_UNAVAILABLE" "A metadata-only file-size probe is unavailable."
hash_mode=$(detect_hash_mode) ||
    emit_error "SKILLHUB_SHA256_UNAVAILABLE" "A supported SHA-256 command is unavailable."

if [ "$subcommand" = "doctor" ]; then
    if [ -z "$workspace_path" ]; then
        emit_error "SKILLHUB_WORKSPACE_REQUIRED" "An explicit workspace directory is required."
    fi
    workspace_abs=$(resolve_directory "$workspace_path") ||
        emit_error "SKILLHUB_WORKSPACE_INVALID" "The workspace must be an existing, non-symlink directory."
    if [ ! -w "$workspace_abs" ] || [ ! -x "$workspace_abs" ]; then
        emit_error "SKILLHUB_WORKSPACE_NOT_WRITABLE" "The workspace directory is not writable."
    fi
    case "$workspace_abs/" in
        "$source_abs/"*)
            emit_error "SKILLHUB_WORKSPACE_INSIDE_SOURCE" "The workspace must be separate from the fact source."
            ;;
    esac
    if python_3_10_available; then
        python_available=true
    else
        python_available=false
    fi
    printf '{"status":"ok","code":"SKILLHUB_FREE_PRECHECK_OK","message":"The SkillHub free precheck path is ready; no source content was uploaded or changed.","data":{"full_local_build_requires_python":true,"model_calls":0,"python_available":%s,"runtime_path":"posix-shell-free-precheck","source_files_changed":false,"structure_manifest_supported":true,"uploaded":false}}\n' \
        "$python_available"
    exit 0
fi

if [ "$subcommand" != "manifest" ]; then
    emit_error "SKILLHUB_COMPAT_SUBCOMMAND_UNSUPPORTED" "Only doctor and manifest are supported by the no-Python compatibility path."
fi
if [ "$confirmed" != "true" ]; then
    printf '{"status":"needs_user_input","code":"STRUCTURE_MANIFEST_CONFIRMATION_REQUIRED","message":"Confirm structure-only local analysis before creating the upload candidate.","data":{"model_calls":0,"uploaded":false,"source_files_changed":false}}\n'
    exit 3
fi
if [ -z "$output_path" ]; then
    emit_error "STRUCTURE_MANIFEST_OUTPUT_REQUIRED" "An explicit manifest output path is required."
fi

case "$output_path" in
    */*)
        output_parent=${output_path%/*}
        if [ -z "$output_parent" ]; then
            output_parent=/
        fi
        ;;
    *)
        output_parent=.
        ;;
esac
output_parent_abs=$(resolve_directory "$output_parent") ||
    emit_error "STRUCTURE_MANIFEST_OUTPUT_PARENT_INVALID" "The manifest output parent must already exist."
if [ ! -w "$output_parent_abs" ] || [ ! -x "$output_parent_abs" ]; then
    emit_error "STRUCTURE_MANIFEST_OUTPUT_PARENT_NOT_WRITABLE" "The manifest output parent is not writable."
fi
case "$output_parent_abs/" in
    "$source_abs/"*)
        emit_error "STRUCTURE_MANIFEST_OUTPUT_INSIDE_SOURCE" "The manifest must be written outside the fact source."
        ;;
esac

records_path=$(mktemp "${TMPDIR:-/tmp}/skillhub-compat-records.XXXXXX") ||
    emit_error "SKILLHUB_COMPAT_TEMPFILE_FAILED" "Unable to create a temporary aggregate record."
body_path=$(mktemp "${TMPDIR:-/tmp}/skillhub-compat-body.XXXXXX") || {
    rm -f "$records_path"
    emit_error "SKILLHUB_COMPAT_TEMPFILE_FAILED" "Unable to create a temporary manifest body."
}
trap 'rm -f "$records_path" "$body_path"' 0 1 2 3 15

if ! find "$source_abs" \
    \( -type l -exec sh -c '
        for path do
            printf "%s\n" "L"
        done
    ' sh {} + \) -o \
    \( -type d ! -path "$source_abs" \
        \( -name .ai-workbench -o -name .git -o -name .obsidian -o \
           -name .trash -o -name .Trash -o -name __pycache__ -o \
           -name AI-Dashboard -o -name AI-Knowledge \) -prune \) -o \
    \( -type d -exec sh -c '
        source_root=$1
        shift
        for path do
            if [ "$path" = "$source_root" ]; then
                continue
            fi
            relative=${path#"$source_root"/}
            depth=1
            remainder=$relative
            while [ "${remainder#*/}" != "$remainder" ]; do
                depth=$((depth + 1))
                remainder=${remainder#*/}
            done
            printf "D|%s\n" "$depth"
        done
    ' sh "$source_abs" {} + \) -o \
    \( -type f -exec sh -c '
        source_root=$1
        stat_mode=$2
        shift 2
        for path do
            relative=${path#"$source_root"/}
            depth=0
            remainder=$relative
            while [ "${remainder#*/}" != "$remainder" ]; do
                depth=$((depth + 1))
                remainder=${remainder#*/}
            done
            if [ "$stat_mode" = "gnu" ]; then
                size=$(stat -c %s "$path" 2>/dev/null) || continue
            else
                size=$(stat -f %z "$path" 2>/dev/null) || continue
            fi
            name=${path##*/}
            extension=
            case "$name" in
                .*)
                    without_dot=${name#.}
                    case "$without_dot" in
                        *.*) extension=${without_dot##*.} ;;
                    esac
                    ;;
                *.*)
                    extension=${name##*.}
                    ;;
            esac
            extension=$(printf "%s" "$extension" | tr "[:upper:]" "[:lower:]")
            case "$extension" in
                md) category=markdown ;;
                doc|docx|odt|pdf|rtf|txt) category=document ;;
                csv|ods|xls|xlsx) category=spreadsheet ;;
                gif|jpeg|jpg|png|svg|webp) category=image ;;
                c|cpp|css|go|html|java|js|json|py|rs|ts|yaml|yml) category=code ;;
                *) category=other ;;
            esac
            printf "F|%s|%s|%s\n" "$depth" "$size" "$category"
        done
    ' sh "$source_abs" "$stat_mode" {} + \) \
    >"$records_path" 2>/dev/null; then
    emit_error "STRUCTURE_MANIFEST_SCAN_FAILED" "The metadata-only source scan failed."
fi

if [ -d "$source_abs/.obsidian" ]; then
    obsidian=true
else
    obsidian=false
fi

if ! awk -F '|' -v obsidian="$obsidian" '
    BEGIN {
        directories = 0
        files = 0
        symlinks = 0
        total_bytes = 0
        max_depth = 0
    }
    $1 == "L" {
        symlinks += 1
    }
    $1 == "D" {
        directories += 1
        depth = $2 + 0
        if (depth > max_depth) max_depth = depth
    }
    $1 == "F" {
        files += 1
        depth = $2 + 0
        size = $3 + 0
        category[$4] += 1
        total_bytes += size
        if (depth > max_depth) max_depth = depth
        if (depth < 3) depth_bucket[depth ""] += 1
        else depth_bucket["3-plus"] += 1
        if (size == 0) size_bucket["empty"] += 1
        else if (size < 65536) size_bucket["small"] += 1
        else if (size < 1048576) size_bucket["medium"] += 1
        else size_bucket["large"] += 1
    }
    END {
        depth_json = "{"
        separator = ""
        split("0 1 2 3-plus", depth_keys, " ")
        for (i = 1; i <= 4; i += 1) {
            key = depth_keys[i]
            if (depth_bucket[key] > 0) {
                depth_json = depth_json separator "\"" key "\":" depth_bucket[key]
                separator = ","
            }
        }
        depth_json = depth_json "}"

        category_json = "{"
        separator = ""
        split("code document image markdown other spreadsheet", category_keys, " ")
        for (i = 1; i <= 6; i += 1) {
            key = category_keys[i]
            if (category[key] > 0) {
                category_json = category_json separator "\"" key "\":" category[key]
                separator = ","
            }
        }
        category_json = category_json "}"

        size_json = "{"
        separator = ""
        split("empty large medium small", size_keys, " ")
        for (i = 1; i <= 4; i += 1) {
            key = size_keys[i]
            if (size_bucket[key] > 0) {
                size_json = size_json separator "\"" key "\":" size_bucket[key]
                separator = ","
            }
        }
        size_json = size_json "}"

        if (max_depth < 3) max_depth_bucket = max_depth ""
        else max_depth_bucket = "3-plus"
        if (total_bytes < 1048576) total_bucket = "under-1mb"
        else if (total_bytes < 10485760) total_bucket = "1mb-to-10mb"
        else if (total_bytes < 104857600) total_bucket = "10mb-to-100mb"
        else total_bucket = "over-100mb"

        printf "%s", \
            "{\"consent_scope\":\"aggregate-structure-only\"," \
            "\"counts\":{\"directories\":" directories ",\"files\":" files "}," \
            "\"depth_buckets\":" depth_json "," \
            "\"features\":{\"max_depth_bucket\":\"" max_depth_bucket "\"," \
                "\"obsidian_detected\":" obsidian "," \
                "\"symlinks_skipped\":" symlinks "," \
                "\"total_size_bucket\":\"" total_bucket "\"}," \
            "\"file_categories\":" category_json "," \
            "\"file_size_buckets\":" size_json "," \
            "\"privacy_mode\":\"structure-only\"," \
            "\"schema_version\":1}"
    }
' "$records_path" >"$body_path"; then
    emit_error "STRUCTURE_MANIFEST_AGGREGATION_FAILED" "The aggregate structure manifest could not be generated."
fi
if [ ! -s "$body_path" ]; then
    emit_error "STRUCTURE_MANIFEST_AGGREGATION_EMPTY" "The aggregate structure manifest is empty."
fi

digest=$(hash_file "$hash_mode" "$body_path") ||
    emit_error "STRUCTURE_MANIFEST_DIGEST_FAILED" "Unable to compute the structure manifest digest."
case "$digest" in
    ""|*[!0-9a-f]*)
        emit_error "STRUCTURE_MANIFEST_DIGEST_INVALID" "The SHA-256 command returned an invalid digest."
        ;;
esac

manifest_json=$(awk -v digest="$digest" '
    {
        sub(/,"privacy_mode"/, ",\"manifest_digest\":\"" digest "\",\"privacy_mode\"")
        printf "%s", $0
    }
' "$body_path")
printf '%s\n' "$manifest_json" >"$output_path" ||
    emit_error "STRUCTURE_MANIFEST_WRITE_FAILED" "Unable to write the local structure manifest."

counts_json=$(awk '
    match($0, /"counts":\{[^}]*\}/) {
        value = substr($0, RSTART, RLENGTH)
        sub(/^"counts":/, "", value)
        print value
    }
' "$output_path")
printf '{"status":"ok","code":"STRUCTURE_MANIFEST_READY","message":"A local aggregate-only manifest was created through the SkillHub no-Python compatibility path; it has not been uploaded.","data":{"counts":%s,"manifest_digest":"%s","model_calls":0,"privacy_mode":"structure-only","runtime_path":"posix-shell-free-precheck","source_files_changed":false,"uploaded":false}}\n' \
    "$counts_json" "$digest"
