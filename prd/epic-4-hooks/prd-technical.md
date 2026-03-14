# Epic 4: Hook System Expansion - Technical Specification

**Document:** prd-technical.md
**Version:** 1.0
**Date:** 2026-03-14

---

## Table of Contents

1. Hook Dispatch Architecture
2. Hook Interface & Base Classes
3. Security Tier Classifier
4. Hook Implementations (6 hooks)
5. Survival Architecture v3.0 Template
6. Performance & Reliability
7. Testing & Verification

---

## 1. Hook Dispatch Architecture

### 1.1 Session Lifecycle Model

Hooks execute at 4 distinct lifecycle points:

```
┌─────────────────────────────────────────────────────────────┐
│                      Session Lifecycle                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. SessionStart Hook(s)                                     │
│     ├─ Load PipelineState                                   │
│     ├─ Validate SKILL.md versions                           │
│     ├─ Check iCloud sync                                    │
│     └─ Initialize session state                             │
│                                                               │
│  2. Tool Execution Loop (per tool)                          │
│     ├─ Pre-tool-use Hook(s)                                 │
│     │  ├─ enforce-doc-read (check if doc read)             │
│     │  └─ security-tier-check (classify command)           │
│     │                                                        │
│     ├─ [Tool Execution]                                     │
│     │                                                        │
│     └─ Post-tool-use Hook(s)                                │
│        ├─ validate-output-schema (check output)             │
│        └─ update-pipeline-state (log state + event)         │
│                                                               │
│  3. SessionEnd Hook(s)                                      │
│     ├─ Finalize AuditEvent log                              │
│     ├─ Generate HandoffDocument                             │
│     └─ Upload to iCloud                                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Hook Execution Sequencing

**SessionStart Phase:**
```python
for hook in config.session_start_hooks:
    try:
        result = await hook.execute(context)
        if result.status == 'block':
            raise SessionInitError(result.message)
    except Exception as e:
        raise SessionInitError(f"Hook {hook.name} failed: {e}")
```

**Pre-tool-use Phase:**
```python
for hook in config.pre_tool_hooks:
    result = await hook.execute(context)
    if result.status == 'block':
        if user_override_confirmed(result.message):
            log_override_decision(result)
            continue  # Skip remaining pre-hooks
        else:
            raise ToolBlockedError(result.message)
    elif result.status == 'ask':
        # Already handled by hook implementation
        pass
```

**Post-tool-use Phase:**
```python
for hook in config.post_tool_hooks:
    try:
        result = await hook.execute(context)
        if result.status == 'block':
            log_warning(f"Post-hook blocked: {result.message}")
            # Don't raise; tool already executed
    except Exception as e:
        log_error(f"Post-hook error: {e}")
```

**SessionEnd Phase:**
```python
for hook in config.session_end_hooks:
    try:
        result = await hook.execute(context)
        # Log any errors but don't raise
    except Exception as e:
        log_error(f"SessionEnd hook failed: {e}")
```

---

## 2. Hook Interface & Base Classes

### 2.1 HookResult Data Structure

```python
from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class HookResult:
    """Result of hook execution."""
    status: str  # 'allow' | 'block' | 'ask' | 'error'
    message: str  # Human-readable reason
    context: dict[str, Any]  # Hook-specific data
    tier: Optional[int] = None  # For security-tier-check
    errors: Optional[list[str]] = None  # For validate-output-schema
```

### 2.2 HookContext Data Structure

```python
from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class HookContext:
    """Context passed to all hooks."""
    session_id: str
    session_state: 'PipelineState'  # From Epic 2
    tool_name: str  # Name of tool being executed
    command: Optional[str] = None  # Bash command (for bash hooks)
    skill_config: dict[str, Any] = None  # Parsed SKILL.md
    audit_log: list['AuditEvent'] = None  # Recent audit events
    doc_read_tracker: dict[str, str] = None  # {skill_name: ISO8601_read_time}
    security_config: dict[str, Any] = None  # Tier overrides
```

### 2.3 Hook Abstract Base Class

```python
from abc import ABC, abstractmethod
from typing import Optional

class Hook(ABC):
    """Abstract base class for all hooks."""

    def __init__(self, name: str, hook_type: str):
        self.name = name
        self.hook_type = hook_type  # 'session_start' | 'pre_tool' | 'post_tool' | 'session_end'

    @abstractmethod
    async def execute(self, context: HookContext) -> HookResult:
        """
        Execute hook logic.

        Args:
            context: HookContext with session state, tool info, etc.

        Returns:
            HookResult with status, message, context dict.
        """
        pass

    @abstractmethod
    def validate_config(self, skill_config: dict) -> bool:
        """
        Validate hook configuration in SKILL.md.
        Return True if valid, False otherwise.
        """
        pass
```

### 2.4 Hook Registry

```python
class HookRegistry:
    """Registry of available hooks."""

    _hooks = {}

    @classmethod
    def register(cls, hook: Hook):
        """Register a hook by name."""
        cls._hooks[hook.name] = hook

    @classmethod
    def get_hooks_for_type(cls, hook_type: str) -> list[Hook]:
        """Get all hooks of specified type."""
        return [h for h in cls._hooks.values() if h.hook_type == hook_type]

    @classmethod
    def get_hook(cls, name: str) -> Optional[Hook]:
        """Get hook by name."""
        return cls._hooks.get(name)
```

### 2.5 Hook Locations

```
hooks/
├── __init__.py
├── base.py              # Hook, HookResult, HookContext base classes
├── registry.py          # HookRegistry
├── session_start/
│   ├── __init__.py
│   └── session_start_hook.py        # SessionStart (loads state)
├── pre_tool_use/
│   ├── __init__.py
│   ├── enforce_doc_read.py          # Pre-tool: doc read verification
│   └── security_tier_check.py       # Pre-tool: bash command classification
├── post_tool_use/
│   ├── __init__.py
│   ├── validate_output_schema.py    # Post-tool: output schema validation
│   └── update_pipeline_state.py     # Post-tool: state + audit logging
└── session_end/
    ├── __init__.py
    └── save_session_summary.py      # SessionEnd: handoff generation
```

---

## 3. Security Tier Classifier

### 3.1 Tier Definitions (10-Tier Model)

```python
SECURITY_TIERS = {
    1: {
        'name': 'Safe reads',
        'risk': 'None',
        'verdict': 'allow',
        'commands': ['cat', 'ls', 'grep', 'head', 'tail', 'less', 'find', 'stat'],
        'description': 'Read-only file operations'
    },
    2: {
        'name': 'Environment',
        'risk': 'Low',
        'verdict': 'allow',
        'commands': ['echo', 'pwd', 'env', 'date', 'whoami', 'hostname', 'uname'],
        'description': 'Environment introspection'
    },
    3: {
        'name': 'Package queries',
        'risk': 'Low',
        'verdict': 'allow',
        'commands': ['pip', 'npm', 'brew', 'gem', 'apt', 'yum'],
        'command_flags': ['-list', 'list', 'ls', 'search', 'info', 'show'],
        'description': 'Package manager queries (read-only)'
    },
    4: {
        'name': 'Write/create',
        'risk': 'Moderate',
        'verdict': 'allow+log',
        'commands': ['touch', 'mkdir', 'cp', 'mv', 'rm', 'sed', 'awk', 'ed'],
        'description': 'File creation/modification'
    },
    5: {
        'name': 'Publish',
        'risk': 'Moderate',
        'verdict': 'allow+log',
        'commands': ['git', 'npm', 'aws', 'gcloud', 'azure'],
        'command_flags': ['push', 'publish', 'deploy', 'upload', 'cp', 'sync'],
        'description': 'Code/artifact publishing'
    },
    6: {
        'name': 'Docker ops',
        'risk': 'High',
        'verdict': 'block+ask',
        'commands': ['docker', 'podman', 'buildah'],
        'description': 'Container operations (can leak secrets, escalate)'
    },
    7: {
        'name': 'Permissions',
        'risk': 'High',
        'verdict': 'block+ask',
        'commands': ['chmod', 'chown', 'sudo', 'su', 'usermod', 'setfacl'],
        'description': 'Permission/privilege changes'
    },
    8: {
        'name': 'Process kill',
        'risk': 'Very high',
        'verdict': 'block',
        'commands': ['kill', 'killall', 'pkill', 'pkill9'],
        'description': 'Process termination'
    },
    9: {
        'name': 'System files',
        'risk': 'Critical',
        'verdict': 'block',
        'regex': [r'rm.*/(etc|usr/bin|sys|proc|lib)', r'dd.*if=/dev/'],
        'description': 'System file deletion'
    },
    10: {
        'name': 'Destructive',
        'risk': 'Catastrophic',
        'verdict': 'block',
        'regex': [r'rm -rf /', r'dd.*if=/dev/zero.*of=/dev/'],
        'description': 'System-wide destruction'
    }
}
```

### 3.2 Command Classifier Implementation

```python
import re
from typing import Optional

class CommandClassifier:
    """Classify bash commands by security tier."""

    def __init__(self, tier_config: dict = None):
        self.tier_config = tier_config or SECURITY_TIERS
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        self.patterns = {}
        for tier, config in self.tier_config.items():
            if 'regex' in config:
                self.patterns[tier] = [
                    re.compile(pattern) for pattern in config['regex']
                ]

    def classify(self, command: str) -> dict:
        """
        Classify a bash command.

        Args:
            command: Full bash command string (e.g., 'rm -rf /etc/shadow')

        Returns:
            {
                'tier': int (1-10),
                'category': str,
                'verdict': str ('allow', 'allow+log', 'block+ask', 'block'),
                'reason': str,
                'matched_pattern': str (optional)
            }
        """
        # Parse command: extract binary + flags
        parts = command.split()
        if not parts:
            return {'tier': 1, 'category': 'empty', 'verdict': 'allow', 'reason': 'Empty command'}

        binary = parts[0].split('/')[-1]  # Handle /usr/bin/rm → rm
        flags = parts[1:] if len(parts) > 1 else []

        # Check tiers 10-1 (highest risk first)
        for tier in sorted(self.tier_config.keys(), reverse=True):
            config = self.tier_config[tier]

            # Check regex patterns (high precision)
            if tier in self.patterns:
                for pattern in self.patterns[tier]:
                    if pattern.search(command):
                        return {
                            'tier': tier,
                            'category': config['name'],
                            'verdict': config['verdict'],
                            'reason': config['description'],
                            'matched_pattern': pattern.pattern
                        }

            # Check command list
            if 'commands' in config and binary in config['commands']:
                # For tier 3, 5: check flags to narrow classification
                if tier in [3, 5]:
                    if any(flag in flags for flag in config.get('command_flags', [])):
                        return {
                            'tier': tier,
                            'category': config['name'],
                            'verdict': config['verdict'],
                            'reason': config['description']
                        }
                else:
                    return {
                        'tier': tier,
                        'category': config['name'],
                        'verdict': config['verdict'],
                        'reason': config['description']
                    }

        # Default: tier 1 (safe read)
        return {
            'tier': 1,
            'category': 'unknown',
            'verdict': 'allow',
            'reason': 'Unknown command; treated as safe read'
        }
```

---

## 4. Hook Implementations (6 Hooks)

### 4.1 Hook 1: SessionStart

**File:** `hooks/session_start/session_start_hook.py`

```python
import asyncio
from datetime import datetime, timezone
from hooks.base import Hook, HookContext, HookResult

class SessionStartHook(Hook):
    """Initialize session state at startup."""

    def __init__(self):
        super().__init__('SessionStart', 'session_start')

    async def execute(self, context: HookContext) -> HookResult:
        """
        Execute SessionStart logic:
        1. Load PipelineState from iCloud
        2. Validate SKILL.md versions
        3. Check iCloud sync status
        4. Initialize doc_read_tracker
        """
        try:
            # Load PipelineState from iCloud
            pipeline_state = await self._load_pipeline_state()
            context.session_state = pipeline_state

            # Validate SKILL.md versions
            validation_errors = await self._validate_skill_versions()
            if validation_errors:
                for error in validation_errors:
                    self._log_error(error)

            # Check iCloud sync status
            sync_status = await self._check_icloud_sync()
            if not sync_status['synced']:
                self._log_warning(f"iCloud sync stale: {sync_status['lag_minutes']} min")

            # Initialize doc_read_tracker
            if not hasattr(context, 'doc_read_tracker'):
                context.doc_read_tracker = {}

            # Log session start
            self._log_audit_event(context, 'session_start', 'success')

            return HookResult(
                status='allow',
                message='Session initialized',
                context={
                    'sync_status': sync_status,
                    'validation_errors': validation_errors
                }
            )

        except Exception as e:
            return HookResult(
                status='block',
                message=f'Session initialization failed: {str(e)}',
                context={'error': str(e)}
            )

    async def _load_pipeline_state(self):
        """Load PipelineState from iCloud (or local fallback)."""
        # Implementation: Load from iCloud API or local cache
        # Retry logic: exponential backoff, max 3 retries
        # Fallback to local disk if iCloud unavailable
        pass

    async def _validate_skill_versions(self):
        """Validate all SKILL.md files are >= v2.2."""
        errors = []
        # Scan skills/ directory
        # Parse SKILL.md versions
        # Return list of errors (empty if all valid)
        return errors

    async def _check_icloud_sync(self):
        """Check iCloud sync status."""
        # Query last sync timestamp
        # Return: {synced: bool, lag_minutes: int}
        pass

    def validate_config(self, skill_config: dict) -> bool:
        """No skill-level config for SessionStart."""
        return True
```

### 4.2 Hook 2: enforce-doc-read

**File:** `hooks/pre_tool_use/enforce_doc_read.py`

```python
from hooks.base import Hook, HookContext, HookResult

class EnforceDocReadHook(Hook):
    """Block tool execution until SKILL.md is read."""

    def __init__(self):
        super().__init__('enforce-doc-read', 'pre_tool_use')

    async def execute(self, context: HookContext) -> HookResult:
        """
        Check if current skill's SKILL.md has been read this session.
        If not: block + return formatted SKILL.md content.
        If yes: allow.
        """
        # Check if hook is enabled for this skill
        if not self.validate_config(context.skill_config):
            return HookResult(status='allow', message='Hook disabled', context={})

        skill_name = context.tool_name

        # Check doc_read_tracker
        if skill_name in context.doc_read_tracker:
            # Already read this session
            return HookResult(
                status='allow',
                message=f'SKILL.md for {skill_name} already read',
                context={'read_at': context.doc_read_tracker[skill_name]}
            )

        # Not read; block and display SKILL.md
        skill_md = await self._load_skill_md(skill_name)
        formatted_md = self._format_skill_md(skill_md)

        return HookResult(
            status='block',
            message=f'SKILL.md not read. Please review:\n\n{formatted_md}',
            context={'skill_name': skill_name}
        )

    async def _load_skill_md(self, skill_name: str) -> str:
        """Load SKILL.md for skill."""
        # Implementation: read skills/{skill_name}/SKILL.md
        pass

    def _format_skill_md(self, md: str) -> str:
        """Format SKILL.md for terminal display."""
        # Truncate if >1000 lines
        # Format with markdown rendering
        # Add "I've read this" instruction
        pass

    def validate_config(self, skill_config: dict) -> bool:
        """Check if enforce-doc-read is enabled for this skill."""
        return skill_config.get('enforce-doc-read', False)
```

### 4.3 Hook 3: validate-output-schema

**File:** `hooks/post_tool_use/validate_output_schema.py`

```python
import json
from jsonschema import validate, ValidationError
from hooks.base import Hook, HookContext, HookResult

class ValidateOutputSchemaHook(Hook):
    """Validate tool output against declared schema."""

    def __init__(self):
        super().__init__('validate-output-schema', 'post_tool_use')

    async def execute(self, context: HookContext) -> HookResult:
        """
        Validate tool output against output-schema in SKILL.md.
        """
        if not self.validate_config(context.skill_config):
            return HookResult(status='allow', message='No schema declared', context={})

        schema = context.skill_config.get('output-schema')
        output = context.session_state.last_tool_output  # Assuming this field exists

        # Parse output based on output-format
        try:
            output_format = context.skill_config.get('output-format', 'json')
            if output_format == 'json':
                parsed_output = json.loads(output)
            elif output_format == 'yaml':
                import yaml
                parsed_output = yaml.safe_load(output)
            else:
                parsed_output = output  # Plain text
        except Exception as e:
            return HookResult(
                status='block',
                message=f'Failed to parse output as {output_format}: {str(e)}',
                context={'error': str(e)}
            )

        # Validate against schema
        try:
            validate(instance=parsed_output, schema=schema)
            return HookResult(
                status='allow',
                message='Output schema valid',
                context={'valid': True}
            )
        except ValidationError as e:
            errors = [str(e.message)]
            enforce = context.skill_config.get('enforce-schema', True)

            return HookResult(
                status='block' if enforce else 'allow',
                message=f'Schema validation failed: {errors[0]}' if enforce else f'Schema warning: {errors[0]}',
                context={'errors': errors, 'enforced': enforce}
            )

    def validate_config(self, skill_config: dict) -> bool:
        """Check if output-schema is declared."""
        return 'output-schema' in skill_config
```

### 4.4 Hook 4: security-tier-check

**File:** `hooks/pre_tool_use/security_tier_check.py`

```python
from hooks.base import Hook, HookContext, HookResult
from security_classifier import CommandClassifier

class SecurityTierCheckHook(Hook):
    """Classify bash commands by security tier."""

    def __init__(self):
        super().__init__('security-tier-check', 'pre_tool_use')
        self.classifier = CommandClassifier()

    async def execute(self, context: HookContext) -> HookResult:
        """
        Classify bash command and decide: allow, allow+log, block+ask, or block.
        """
        if not context.command:
            return HookResult(status='allow', message='No bash command', context={})

        # Classify command
        classification = self.classifier.classify(context.command)
        tier = classification['tier']
        verdict = classification['verdict']

        # Log to audit trail
        self._log_audit_event(
            context,
            event_type='security_tier_check',
            tier=tier,
            command=context.command,
            verdict=verdict
        )

        # Decision logic based on tier
        if verdict == 'allow':
            return HookResult(
                status='allow',
                message=f'Tier {tier}: {classification["category"]}',
                context=classification
            )
        elif verdict == 'allow+log':
            return HookResult(
                status='allow',
                message=f'Tier {tier}: {classification["category"]} (logged)',
                context=classification
            )
        elif verdict == 'block+ask':
            return HookResult(
                status='ask',
                message=f'Tier {tier}: {classification["category"]}. Override? (yes/no)',
                context=classification
            )
        else:  # block
            return HookResult(
                status='block',
                message=f'Tier {tier}: {classification["category"]} (blocked unconditionally)',
                context=classification
            )

    def validate_config(self, skill_config: dict) -> bool:
        """security-tier-check always runs."""
        return True
```

### 4.5 Hook 5: update-pipeline-state

**File:** `hooks/post_tool_use/update_pipeline_state.py`

```python
from datetime import datetime, timezone
from hooks.base import Hook, HookContext, HookResult

class UpdatePipelineStateHook(Hook):
    """Update PipelineState and log AuditEvent."""

    def __init__(self):
        super().__init__('update-pipeline-state', 'post_tool_use')

    async def execute(self, context: HookContext) -> HookResult:
        """
        Update PipelineState after tool execution and log AuditEvent.
        """
        try:
            # Update PipelineState
            context.session_state.last_tool_executed = context.tool_name
            context.session_state.tool_execution_count += 1
            context.session_state.stage_completion_timestamp = datetime.now(timezone.utc).isoformat()
            context.session_state.last_execution_status = 'success'  # Assuming tool succeeded

            # Create AuditEvent
            audit_event = self._create_audit_event(context)
            await self._persist_audit_event(context, audit_event)

            # Persist PipelineState to memory + iCloud
            await self._persist_pipeline_state(context)

            return HookResult(
                status='allow',
                message='PipelineState updated',
                context={
                    'audit_event_id': audit_event.id,
                    'state_timestamp': context.session_state.stage_completion_timestamp
                }
            )

        except Exception as e:
            return HookResult(
                status='allow',  # Don't block post-tool-use
                message=f'Warning: failed to update state: {str(e)}',
                context={'error': str(e)}
            )

    def _create_audit_event(self, context: HookContext):
        """Create AuditEvent entry."""
        # Implementation: instantiate AuditEvent model from Epic 2
        # Fields: timestamp, event_type, actor, action, resource, result, context
        pass

    async def _persist_audit_event(self, context: HookContext, event):
        """Persist AuditEvent to log."""
        # Implementation: append to session log
        pass

    async def _persist_pipeline_state(self, context: HookContext):
        """Persist PipelineState to iCloud."""
        # Implementation: iCloud sync with retry logic
        pass

    def validate_config(self, skill_config: dict) -> bool:
        """update-pipeline-state always runs."""
        return True
```

### 4.6 Hook 6: save-session-summary

**File:** `hooks/session_end/save_session_summary.py`

```python
from hooks.base import Hook, HookContext, HookResult

class SaveSessionSummaryHook(Hook):
    """Generate and save session handoff document."""

    def __init__(self):
        super().__init__('save-session-summary', 'session_end')

    async def execute(self, context: HookContext) -> HookResult:
        """
        Generate HandoffDocument from AuditEvents and PipelineState.
        Save to sessions/{session_id}/handoff.md.
        """
        try:
            # Generate HandoffDocument
            handoff = await self._generate_handoff(context)

            # Write to disk
            handoff_path = f'sessions/{context.session_id}/handoff.md'
            await self._write_handoff(handoff_path, handoff)

            # Compress + upload to iCloud
            await self._upload_to_icloud(context.session_id)

            return HookResult(
                status='allow',
                message=f'Session summary saved to {handoff_path}',
                context={'path': handoff_path}
            )

        except Exception as e:
            return HookResult(
                status='allow',  # Don't block session end
                message=f'Warning: failed to save session summary: {str(e)}',
                context={'error': str(e)}
            )

    async def _generate_handoff(self, context: HookContext) -> str:
        """Generate HandoffDocument content."""
        # Implementation: build markdown with:
        # - Session metadata (ID, start/end time)
        # - Tool execution summary
        # - Security events (tier 6+ commands)
        # - Audit trail (30 most recent events)
        # - Recommendations
        pass

    async def _write_handoff(self, path: str, content: str):
        """Write HandoffDocument to disk."""
        # Implementation: create directory if needed, write markdown
        pass

    async def _upload_to_icloud(self, session_id: str):
        """Compress + upload to iCloud with retry logic."""
        # Implementation: tar.gz, upload, handle conflicts
        pass

    def validate_config(self, skill_config: dict) -> bool:
        """save-session-summary always runs."""
        return True
```

---

## 5. Survival Architecture v3.0 Template

### 5.1 v3.0 Template Structure

**File:** `templates/skill-template-v3.0.md`

```markdown
# Skill: [Skill Name]

**Author:** [Name]
**Version:** 1.0
**Created:** [Date]
**Last Modified:** [Date]

## Overview

[Brief description of what this skill does]

## Survival Architecture

### Metadata
- **survival-architecture-version:** 3.0
- **skill-id:** [unique identifier]
- **dependencies:** [list of skill dependencies]

### Hook Declarations

This skill activates the following hooks during execution:

```yaml
hooks-declared:
  - enforce-doc-read
  - security-tier-check
  - validate-output-schema
```

**Hook Behavior:**
- `enforce-doc-read`: User must acknowledge reading this SKILL.md before first tool execution
- `security-tier-check`: Bash commands classified before execution; tier 6+ blocked
- `validate-output-schema`: Output validated against declared schema

### Context Budget

Token allocation per stage:

```yaml
context-budget:
  stage-1:
    max-tokens: 4000
    timeout-seconds: 30
  stage-2:
    max-tokens: 8000
    timeout-seconds: 60
```

### Security Tier

Bash commands in this skill classified as:

```yaml
security-tier: 4  # Write/create operations
```

**Justification:** This skill creates temporary files and directories during execution.

### Output Schema

Expected output format for final stage:

```yaml
output-schema:
  type: object
  required: [status, result, metadata]
  properties:
    status:
      type: string
      enum: [success, warning, failure]
    result:
      type: object
      properties:
        data:
          type: array
        count:
          type: integer
    metadata:
      type: object
      properties:
        execution-time:
          type: number
        timestamp:
          type: string
          format: date-time

enforce-schema: true  # Blocking validation
```

## Stages

### Stage 1: Initialize
[Stage details]

### Stage 2: Execute
[Stage details]

### Stage 3: Finalize
[Stage details]

## References

- [ADR-009: Survival Architecture v3.0](../adr/adr-009.md)
- [Hook System Documentation](../docs/hooks.md)
```

### 5.2 v2.2 → v3.0 Upgrade Script

**File:** `scripts/upgrade-skill-v2-to-v3.py`

```python
#!/usr/bin/env python3
"""Upgrade SKILL.md from v2.2 to v3.0."""

import sys
import yaml
from pathlib import Path

def upgrade_skill_md(skill_path: Path) -> tuple[str, list[str]]:
    """
    Upgrade SKILL.md from v2.2 to v3.0.

    Returns: (upgraded_content, required_reviews)
    """
    with open(skill_path) as f:
        content = f.read()

    # Parse existing SKILL.md
    metadata = parse_metadata(content)

    # Generate v3.0 sections
    v3_sections = {
        'survival-architecture-version': '3.0',
        'hooks-declared': ['enforce-doc-read', 'security-tier-check'],
        'context-budget': generate_context_budget(skill_path),
        'security-tier': '3',  # Default; requires review
        'output-schema': {},  # Empty; requires review
    }

    # Insert v3.0 sections
    upgraded = insert_v3_sections(content, v3_sections)

    # List required reviews
    reviews = [
        'security-tier: Classify bash commands (1-10)',
        'output-schema: Define expected output structure',
        'hooks-declared: Verify applicable hooks',
    ]

    return upgraded, reviews

def parse_metadata(content: str) -> dict:
    """Extract metadata from SKILL.md."""
    # Implementation: parse YAML frontmatter or sections
    pass

def generate_context_budget(skill_path: Path) -> dict:
    """Generate reasonable defaults for context budget."""
    # Implementation: estimate based on skill complexity
    pass

def insert_v3_sections(content: str, sections: dict) -> str:
    """Insert v3.0 sections into SKILL.md."""
    # Implementation: add sections while preserving existing content
    pass

if __name__ == '__main__':
    skill_dir = Path('skills')

    for skill_path in skill_dir.glob('*/SKILL.md'):
        upgraded, reviews = upgrade_skill_md(skill_path)

        # Backup original
        backup_path = skill_path.with_suffix('.md.v2.2.bak')
        backup_path.write_text(skill_path.read_text())

        # Write upgraded
        skill_path.write_text(upgraded)

        print(f"\n✓ Upgraded {skill_path.parent.name}")
        print(f"  Required reviews:")
        for review in reviews:
            print(f"    - {review}")
```

---

## 6. Performance & Reliability

### 6.1 Hook Latency Budget

| Hook | Latency Target | Notes |
|------|---|---|
| SessionStart | <500ms | Load + validation |
| enforce-doc-read | <100ms | Dict lookup |
| security-tier-check | <200ms | Regex + tier lookup (cached) |
| validate-output-schema | <300ms | JSON validation |
| update-pipeline-state | <150ms | State update + I/O |
| save-session-summary | <1s | Handoff generation + upload |

**Combined Budget:** <2.5s for full session lifecycle

### 6.2 Caching Strategy

```python
class HookCache:
    """Cache expensive operations."""

    # Regex patterns compiled once at startup
    _security_patterns = None

    # SKILL.md parsed files cached
    _skill_configs = {}

    # iCloud sync status cached (TTL 5 min)
    _sync_status_cache = {}
    _sync_status_ttl = 300

    @classmethod
    def get_compiled_patterns(cls):
        if cls._security_patterns is None:
            cls._security_patterns = CommandClassifier()._compile_patterns()
        return cls._security_patterns
```

### 6.3 Error Handling & Logging

```python
class HookLogger:
    """Unified logging for all hooks."""

    @staticmethod
    def log_hook_execution(hook_name: str, context: HookContext, result: HookResult):
        """Log hook execution result."""
        # Structured logging: timestamp, hook, status, context
        pass

    @staticmethod
    def log_security_decision(command: str, tier: int, verdict: str):
        """Log security-tier-check decision."""
        # Structured: command hash, tier, verdict, timestamp
        pass

    @staticmethod
    def log_schema_violation(skill_name: str, errors: list):
        """Log schema validation failures."""
        # Structured: skill, errors, timestamp
        pass
```

---

## 7. Testing & Verification

### 7.1 Test Structure (see prd-tests.md)

```
tests/
├── conftest.py              # Fixtures, mocks
├── test_enforce_doc_read.py
├── test_security_tier.py
├── test_validate_schema.py
├── test_update_state.py
├── test_session_hooks.py
├── fixtures/
│   ├── security_tiers.json  # 30+ command examples
│   ├── skill_configs.yaml   # SKILL.md fixtures
│   └── audit_events.json    # Sample AuditEvents
```

### 7.2 Integration Test Scenario

```python
@pytest.mark.asyncio
async def test_full_session_lifecycle():
    """Test complete session: start → tool → end."""

    # 1. SessionStart
    session = await SessionStartHook().execute(context)
    assert session.status == 'allow'

    # 2. Pre-tool hooks
    doc_read = await EnforceDocReadHook().execute(context)
    assert doc_read.status == 'block'  # Not read yet

    # Mock user confirms read
    context.doc_read_tracker[skill_name] = datetime.now().isoformat()

    doc_read = await EnforceDocReadHook().execute(context)
    assert doc_read.status == 'allow'  # Now allowed

    # 3. Security tier check
    context.command = 'ls -la /tmp'
    tier_check = await SecurityTierCheckHook().execute(context)
    assert tier_check.status == 'allow'
    assert tier_check.context['tier'] == 1

    # 4. Post-tool hooks (after tool execution)
    schema_validation = await ValidateOutputSchemaHook().execute(context)
    assert schema_validation.status == 'allow'

    state_update = await UpdatePipelineStateHook().execute(context)
    assert state_update.status == 'allow'

    # 5. SessionEnd
    session_end = await SaveSessionSummaryHook().execute(context)
    assert session_end.status == 'allow'
```

---

**Document Owner:** AI Architect Engineering Team
**Last Updated:** 2026-03-14
**Version:** 1.0
