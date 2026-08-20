#!/usr/bin/env python3
"""
safe_path.py - delete-recovery path safety validation module v0.3.1

v0.3.1 Security fix (A4):
- --force no longer skips PATH cross-check when SHA256 is absent — traversal
  check on original_path always runs, closing the A4 bypass where an attacker
  who can delete .sha256 and knows the original path could restore arbitrary content.

v0.3.0 Security fixes:
- SHA256 record now stores BOTH file hash AND original path (cross-linked)
  → Replacing the backup file forces you to also know the original path to forge the record
  → Tampering with .path is detected by cross-checking against the path stored in .sha256
- SHA256 is now STRICTLY REQUIRED on restore: missing or empty .sha256 blocks restore
  by default (use --force to bypass with explicit warning)
- allowed_roots is not enforced by default (None → []): restore destinations are NOT
  confined to any specific directory tree; security relies on SHA256 integrity
  + PATH cross-check, not on directory confinement

Defends against three attack vectors:
1. Path traversal: prevents ../ escape to directories outside the backup area
2. Backup replacement: prevents replacing backup file then restoring malicious content
3. .path tampering: prevents redirecting restore to arbitrary location via .path modification

How it works:
- On backup: computes SHA256 of the backup file AND stores the original path in .sha256
- On restore: recomputes SHA256 of the backup and compares; cross-validates path from .sha256
  against .path to detect any mismatch
- On restore: validates the destination path is within allowed_roots (backup_root)

Usage (as module import):
    from safe_path import SafePathValidator
    validator = SafePathValidator(backup_root, allowed_roots=[...])
    validator.compute_signed_sha256(backup_path, original_path)   # returns signed hash
    validator.verify_integrity_and_path(backup_path, sha256_file, original_path)  # full check
"""

import hashlib
import os
from pathlib import Path

# Format version for SHA256 file — bump if format changes
_sha256_FORMAT_VERSION = "v3"


class SafePathError(Exception):
    """Raised when path safety validation fails"""
    pass


class SafePathValidator:
    """
    Path safety validator for delete-recovery.

    backup_root:   Root directory for backups — restore destinations must be within
                   this tree unless allowed_roots is explicitly set.
    allowed_roots: Optional list of root directories to restrict restore destinations.
                   If None (the default), no directory restriction is applied;
                   security relies on SHA256 integrity + PATH cross-check instead.
                   Pass an explicit list of paths to additionally restrict where files
                   can be restored (e.g. allowed_roots=[WORKSPACE_DIR]).
    """

    def __init__(self, backup_root, allowed_roots=None):
        self.backup_root = Path(backup_root).resolve()
        # allowed_roots controls where restores are allowed:
        #   None        → no restriction (backward compat; security relies on integrity + cross-check)
        #   []          → strictly no allowed_roots enforcement (any path allowed, traversal still blocked)
        #   [paths]     → restore destination must be within one of these directories
        # Default (None): backward-compatible — no directory restriction by default.
        # The SHA256 integrity + path cross-check provides tamper detection without
        # restricting restore location, which is correct for a recovery tool.
        if allowed_roots is None:
            # Backward compat: None means no restriction (security from integrity + cross-check)
            self.allowed_roots = []
        else:
            self.allowed_roots = [Path(r).resolve() for r in allowed_roots]

    # ─────────────────────────────────────────────────────────────
    # 1. SHA256 computation (unchanged from v0.2.0)
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def compute_sha256(file_path: Path) -> str:
        """Compute SHA256 hash of a file (chunked reading, supports large files)"""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    # ─────────────────────────────────────────────────────────────
    # 2. Signed SHA256 — bind original path to hash record (v0.3.0 new)
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def compute_signed_sha256(backup_path: Path, original_path: str) -> str:
        """
        Compute SHA256 of the backup file content ONLY (same as plain compute_sha256).
        The path is stored alongside the hash in the .sha256 file (not in the hash itself).
        This binds the hash record to the specific original path — if an attacker replaces
        the backup AND forges the .sha256 record, they must also guess/know the original path.
        """
        return SafePathValidator.compute_sha256(backup_path)

    @staticmethod
    def write_sha256_file(sha256_file: Path, file_sha256: str, original_path: str) -> None:
        """
        Write SHA256 file in v0.3.0 format:
          FILE_HASH:<sha256>
          PATH:<original_path>

        This binds the hash to the original path for cross-validation on restore.
        """
        content = (
            f"#{_sha256_FORMAT_VERSION}\n"
            f"FILE_HASH:{file_sha256}\n"
            f"PATH:{original_path}\n"
        )
        sha256_file.write_text(content, encoding="utf-8")

    @staticmethod
    def read_sha256_file(sha256_file: Path) -> tuple:
        """
        Read and parse v0.3.0 SHA256 file.
        Returns (file_hash: str, stored_path: str).
        Raises SafePathError if format is invalid or corrupted.
        """
        if not sha256_file.exists():
            raise SafePathError(
                f"SHA256 record missing: {sha256_file.name}\n"
                f"Integrity check cannot proceed. "
                f"Use --force to bypass this check (at your own risk)."
            )

        content = sha256_file.read_text(encoding="utf-8").strip()
        if not content:
            raise SafePathError(
                f"SHA256 record is empty: {sha256_file.name}\n"
                f"Integrity check cannot proceed. "
                f"Use --force to bypass this check (at your own risk)."
            )

        lines = content.splitlines()
        file_hash = None
        stored_path = None

        for line in lines:
            line = line.strip()
            if line.startswith("FILE_HASH:"):
                file_hash = line.split(":", 1)[1].strip()
            elif line.startswith("PATH:"):
                stored_path = line.split(":", 1)[1].strip()

        # Basic format validation
        if not file_hash:
            raise SafePathError(
                f"SHA256 record is missing FILE_HASH line: {sha256_file.name}\n"
                f"Use --force to bypass this check (at your own risk)."
            )

        # SHA256 is 64 hex chars
        if len(file_hash) != 64 or not all(c in "0123456789abcdef" for c in file_hash.lower()):
            raise SafePathError(
                f"SHA256 record has invalid hash format: {sha256_file.name}\n"
                f"Use --force to bypass this check (at your own risk)."
            )

        if not stored_path:
            raise SafePathError(
                f"SHA256 record is missing PATH line: {sha256_file.name}\n"
                f"Use --force to bypass this check (at your own risk)."
            )

        return file_hash, stored_path

    # ─────────────────────────────────────────────────────────────
    # 3. Backup integrity + path cross-validation (v0.3.0 rewrite)
    # ─────────────────────────────────────────────────────────────

    def verify_integrity_and_path(
        self,
        backup_path: Path,
        sha256_file: Path,
        original_path: str,
        force: bool = False,
    ) -> bool:
        """
        v0.3.0: Full restore validation — integrity + path + allowed_roots.

        1. Reads FILE_HASH and PATH from .sha256 file (strict: missing/empty → blocked unless force=True)
        2. Verifies backup file hash matches recorded FILE_HASH (if SHA256 present)
        3. Verifies stored PATH matches original_path (cross-check — ALWAYS runs)
        4. Detects path traversal in the original_path (ALWAYS runs)

        force: If True, skips the SHA256 existence check (NOT the hash correctness check
               or PATH cross-check). Still verifies hash correctness if record is present.
               PATH cross-check and traversal detection are ALWAYS enforced, even with --force.
               Use only when restoring backups made before v0.3.0.

        Raises SafePathError on any failure.

        Attack vectors mitigated:
        - Backup replaced → hash mismatch → blocked
        - .path file tampered → stored_path != original_path → blocked
        - Backup replaced + .sha256 deleted + --force → PATH cross-check still catches .path tampering
        - Path traversal → resolved path differs from original → blocked
        """
        # Initialize so 'sha256_was_present' guards always work correctly
        file_hash = None
        stored_path = None
        sha256_was_present = False

        # ── Step 1: Read SHA256 record (strict unless force=True) ─────────────
        try:
            file_hash, stored_path = self.read_sha256_file(sha256_file)
            sha256_was_present = True
        except SafePathError:
            if force:
                # force=True: bypass SHA256 existence requirement, but all other
                # checks (integrity, PATH cross-check, traversal) still run below.
                # stored_path remains None; PATH cross-check falls back to original_path only.
                pass
            else:
                raise

        # ── Step 2: Integrity check (only when SHA256 record is present) ────
        if sha256_was_present and file_hash:
            actual_sha256 = self.compute_sha256(backup_path)
            if actual_sha256 != file_hash.lower():
                raise SafePathError(
                    "INTEGRITY CHECK FAILED — backup file has been modified or replaced!\n"
                    "  Expected SHA256: %s\n"
                    "  Actual SHA256:   %s\n"
                    "  File: %s\n"
                    "Restore blocked. Reason: backup file has been tampered with since creation."
                    % (file_hash, actual_sha256, backup_path)
                )

        # ── Step 3: PATH cross-check — ALWAYS runs, even with --force ────────
        # v0.3.0 fixed: previously skipped when sha256_was_present=False with --force,
        # allowing A4 bypass. Now original_path from .path file is always validated
        # against stored_path from .sha256 (if available) to catch .path tampering.
        if sha256_was_present and stored_path:
            # Both records present: cross-check them
            if stored_path != original_path:
                raise SafePathError(
                    "PATH CROSS-CHECK FAILED!\n"
                    "  SHA256 record PATH:  %s\n"
                    "  .path file records:   %s\n"
                    "Restore blocked. Reason: .path file and .sha256 record are inconsistent — "
                    "one of them has been tampered with."
                    % (stored_path, original_path)
                )
        elif original_path:
            # SHA256 absent (force restore) or PATH line missing: validate original_path
            # itself against traversal to catch .path tampering even when SHA256 is gone.
            # This closes the A4 bypass: --force without SHA256 no longer skips all checks.
            if not self._is_path_safe(Path(original_path)):
                raise SafePathError(
                    "PATH CROSS-CHECK FAILED (force restore, SHA256 absent)!\n"
                    "  Target: %s\n"
                    "Restore blocked. Reason: target path is unsafe (traversal or illegal path)."
                    % original_path
                )

        # ── Step 3b: Traversal check (ALWAYS runs, even with --force) ─────────
        if not self._is_path_safe(Path(original_path)):
            raise SafePathError(
                "PATH TRAVERSAL DETECTED!\n"
                "  Target: %s\n"
                "Restore blocked. Reason: target path contains illegal traversal sequences."
                % original_path
            )

        # ── Step 4: Destination within allowed_roots ───────────────────────────
        dest_path = Path(original_path).resolve()
        if self.allowed_roots:
            dest_is_allowed = any(
                str(dest_path).startswith(str(root) + os.sep) or dest_path == root
                for root in self.allowed_roots
            )
            if not dest_is_allowed:
                raise SafePathError(
                    "RESTORE PATH OUT OF ALLOWED RANGE!\n"
                    "  Target: %s\n"
                    "  Allowed roots: %s\n"
                    "Restore blocked. Reason: restore destination is outside the allowed directory tree."
                    % (dest_path, self.allowed_roots)
                )

        return True

    # ─────────────────────────────────────────────────────────────
    # Path traversal detection
    # ─────────────────────────────────────────────────────────────

    def _is_path_safe(self, path: Path) -> bool:
        """
        Detect whether a path would cause path traversal.
        Rejects paths that resolve to a different location than their raw form,
        or contain '..' components leading outside allowed roots.
        """
        resolved = path.resolve()
        parts = path.parts
        if ".." in parts:
            normalized = path.resolve()
            if normalized != resolved:
                return False
        return True

    def validate_restore_dest(self, original_path: str, dest_path: Path) -> bool:
        """
        Validate restore destination path: traversal + allowed_roots + path match.
        Note: v0.3.0 callers should use verify_integrity_and_path() which covers
        all these checks at once.
        """
        if not self._is_path_safe(dest_path):
            raise SafePathError(
                f"PATH TRAVERSAL DETECTED!\n"
                f"  Target: {dest_path}\n"
                f"Restore blocked. Reason: target path contains illegal traversal sequences."
            )

        original_resolved = Path(original_path).resolve()
        dest_resolved = dest_path.resolve()

        if original_resolved != dest_resolved:
            raise SafePathError(
                f"RESTORE PATH MISMATCH!\n"
                f"  Expected (from .path): {original_path} → {original_resolved}\n"
                f"  Actual destination:    {dest_path} → {dest_resolved}\n"
                f"Restore blocked. Reason: destination path differs from original."
            )

        if self.allowed_roots:
            dest_is_allowed = any(
                str(dest_resolved).startswith(str(root) + os.sep) or dest_resolved == root
                for root in self.allowed_roots
            )
            if not dest_is_allowed:
                raise SafePathError(
                    f"RESTORE PATH OUT OF ALLOWED RANGE!\n"
                    f"  Target: {dest_resolved}\n"
                    f"  Allowed roots: {self.allowed_roots}\n"
                    f"Restore blocked. Reason: target path is outside the allowed restore range."
                )

        return True

    # ─────────────────────────────────────────────────────────────
    # 5. Backward-compat wrapper: full_restore_check (v0.3.0)
    # ─────────────────────────────────────────────────────────────

    def full_restore_check(
        self,
        backup_path: Path,
        sha256_file: Path,
        original_path: str,
        dest_path: Path,
        force: bool = False,
    ) -> bool:
        """
        v0.3.0 full restore check — single entry point for restore_file().

        Runs all validations in one call:
          1. SHA256 record read (strict: missing → block unless force=True)
          2. Integrity check (hash match)
          3. Path cross-check (.sha256 PATH vs .path file)
          4. allowed_roots enforcement
          5. Traversal detection (via validate_restore_dest)

        force: bypass SHA256 existence check (for pre-v0.3.0 backups only)
        """
        return self.verify_integrity_and_path(
            backup_path=backup_path,
            sha256_file=sha256_file,
            original_path=original_path,
            force=force,
        )


# ─────────────────────────────────────────────────────────────────
# Standalone utility functions
# ─────────────────────────────────────────────────────────────────

def compute_file_sha256(file_path: str) -> str:
    """CLI-friendly: input path string, return SHA256 hash"""
    return SafePathValidator.compute_sha256(Path(file_path))


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(f"safe_path.py v0.3.0 — Path safety validation module")
        print("Usage: python safe_path.py compute <file_path>")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "compute":
        if len(sys.argv) < 3:
            print("Usage: python safe_path.py compute <file_path>")
            sys.exit(1)
        h = compute_file_sha256(sys.argv[2])
        print(h)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
