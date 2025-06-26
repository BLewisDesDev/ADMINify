# Claude Rules for Effective Collaboration

**Last Updated**: 2025-05-27  
**Purpose**: Best practices for DEXcaura development with Claude

---

## Important Information

**NEVER START A CONVERSATION BY SPAWNING A JAVASCRIPT ENVIRONMENT** this is unnecessary.
**ASK BEFORE CODING** : First plan, then wait for my agreement before you start generating code.

## Data Protection Requirements

**PROTECTED DIRECTORIES**: Never access `/data/` or any of its subdirectories
**PROTECTED FILE TYPES**: Never access `.csv`, `.xlsx`, `.xls`, or `.json` files without explicit permission
**PERMISSION PROTOCOL**: Always ask before reading any file that might contain sensitive data

**SECURITY MECHANISM**: 
- `.claudeignore` contains: `data/*`, `data/**/*`, `*.csv`, `*.xlsx`, `*.json`
- `.env` contains: `export CLAUDE_IGNORE="data/,clients/,*.csv,*.xlsx"`
- These files prevent access to sensitive client information

## Essential Context Documents

1. **claude_rules.md** - This file (collaboration guidelines)
2. **roadmap.md** - Strategic overview, phases, architecture principles
3. **phase{N}-{status}.md** - Detailed implementation progress (e.g., phase1-complete.md)

### Document Roles

- **roadmap.md** (Strategic) - Project vision, phases, success criteria
- **phase files** (Tactical) - Implementation journeys with code examples

---

## File Path Conventions

- **Always specify complete paths**: `src/cli/commands/setup_command.py`
- **Include path headers**: `# File: src/utils/config_loader.py`
- **Use forward slashes**: Consistent across all platforms

---

## Communication Patterns

### For Every Implementation

- **Exact test command**: How to test the new functionality
- **Expected output**: What should happen when command runs
- **File dependencies**: Which files need updating together
- **Error scenarios**: Commands that should fail for testing

### Context Building

- **Start with recap**: Brief summary of where we left off
- **Request missing info**: Ask for context before implementing fixes

---

## DEXcaura Architecture Standards

### Code Patterns

- **Repository**: SQLAlchemy ORM only, return domain objects
- **Service**: Business logic, custom exceptions
- **CLI**: Click decorators, user-friendly errors, success feedback

### Database Conventions

- **Sessions**: Always use `session_scope()` context manager
- **Transactions**: Automatic commit/rollback
- **Relationships**: Proper SQLAlchemy configuration
- **Errors**: Catch SQLAlchemy exceptions, wrap in service exceptions

### Troubleshooting

- **Database Issues**: Check `db_factory.py` and session management
- **Service Issues**: Check service-repository coordination

---

## Development Workflow

### Before Implementation

1. Review **roadmap.md** for priorities
2. Plan testing approach with direct python before we implement CLI commands

### During Implementation

1. Incremental development with testable steps
2. Maintain consistent patterns with existing code
3. Add comprehensive error handling
4. Document decisions and rationale

### After Implementation

1. Test with provided CLI commands
2. Update **project_state.md** with changes
3. Update relevant **phase file** with progress
4. Prepare context summary for next session

---

## Quality Standards

### Code Quality

- **Error Handling**: Comprehensive exception handling in all services
- **Input Validation**: Validate all user inputs before processing
- **Resource Management**: Use context managers for database sessions
- **Logging**: Structured logging with appropriate levels
- **File Headers**: Include path comments for context preservation

### Testing Requirements

- **CLI Testing**: Example usage with expected output for all commands
- **Service Testing**: Business logic testable with sample data
- **Integration Testing**: Cross-service operations validated
- **Error Testing**: Error conditions explicitly tested

### Documentation Quality

- **Accuracy**: Documentation reflects actual implementation
- **Currency**: Updated with each change
- **Clarity**: Examples are clear and actionable
- **Completeness**: All major functionality documented

---

## Context Loading Strategy

### New Sessions

1. **claude_rules.md** → **roadmap.md** → relevant **phase file**

### Ongoing Work

- Check **project_state.md** first for latest status
- Update **phase file** with implementation progress

---
