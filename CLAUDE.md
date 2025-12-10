# Canton Monitor - Claude Code Rules

## Before Making Any Changes

- **ALWAYS read `PRODUCT_OVERVIEW.md` first** - This contains the complete system architecture, all alert types, and how everything works together
- If adding a new feature, review the "How to Add New Alert Types" section in PRODUCT_OVERVIEW.md

## When Adding New Alert Types

1. Follow the step-by-step guide in `PRODUCT_OVERVIEW.md` exactly
2. Add configuration variables to `.env.example` with clear comments
3. Implement the alert logic following existing patterns (Alert 1-5 as reference)
4. Update `send_notification()` to include new alert exclusions
5. Add scheduling in `scheduler.py`
6. **MUST update these docs:**
   - `PRODUCT_OVERVIEW.md` - Add new alert to the "Alert Types" section
   - `FEATURES.md` - Add detailed feature description with examples
   - `.env.example` - Add all new config variables

## Code Modification Rules

- **Never modify scraping logic** without testing on live website (https://canton-rewards.noves.fi/)
- **Never change the notification system** without testing with real Pushover/Slack credentials
- **Always preserve backward compatibility** - don't break existing alert configurations
- **Follow existing patterns** - match the code style of Alert 1-5 implementations
- **All env variables MUST have defaults** - system should work with minimal configuration

## Testing Requirements

- Test all new notifications (Pushover + Slack) before committing
- Test exclusion logic (per-alert channel/user exclusions)
- Test state-change mode if modifying Alerts 3, 4, or 5
- Test database storage if DATABASE_URL is configured
- Verify scraping still works after any Playwright changes

## Documentation Requirements

When adding features, **ALWAYS update:**
1. `PRODUCT_OVERVIEW.md` - High-level architecture and new alert type
2. `FEATURES.md` - Detailed feature description with notification examples
3. `.env.example` - All new environment variables with descriptions
4. `API_EXAMPLES.md` - If adding new API endpoints

**Never skip documentation updates** - future developers (including AI) rely on accurate docs.

## Git Commit Guidelines

- Commit message format: `[Component] Action - Description`
  - Examples:
    - `[Alert6] Add concentration monitoring alert`
    - `[Docs] Update PRODUCT_OVERVIEW with Alert 6`
    - `[Scraper] Fix parsing for new website layout`
    - `[API] Add /api/concentration endpoint`

## Environment Variables

- All new variables must be added to `.env.example`
- Use clear, descriptive names following existing pattern: `ALERT{N}_*`
- Always provide sensible defaults
- Document what each variable does in comments

## Database Changes

- If adding new tables, update `init_db()` in `canton_monitor.py`
- Document new tables in `PRODUCT_OVERVIEW.md` under "Database" section
- Add migration logic if needed (check existing tables first)

## API Changes

- All new endpoints must require API key authentication
- Follow existing patterns in `scheduler.py` APIHandler
- Update `API_EXAMPLES.md` with curl examples
- Return JSON responses with consistent structure

## Notification System

- Use `send_notification(title, message, priority, alert_type)` for all alerts
- Always specify `alert_type` parameter (e.g., `alert_type="alert6"`)
- This enables per-alert exclusions to work correctly
- Never bypass the notification system

## Priority Guidelines

**High Priority (priority=1):**
- Threshold alerts (Alert 1)
- Change alerts (Alerts 3, 4, 5)
- Any new alerts that require immediate attention

**Low Priority (priority=0):**
- Status reports (Alert 2)
- Informational notifications
- Startup notifications

## State-Change Mode

- If adding percentage-based alerts, implement state-change mode
- Store state in `alert_state` table
- Follow Alert 3/4/5 patterns for implementation
- Provide "Returned to Benchmark" notifications

## Project Philosophy

- **Extensible:** Easy to add Alert 6, 7, 8... without breaking existing alerts
- **Configurable:** Everything controlled via environment variables
- **Noise Reduction:** Use state-change mode and exclusions to prevent alert fatigue
- **Documentation-First:** Always update docs when adding features
- **Fail-Safe:** System should degrade gracefully (alerting works even without database)

## Common Tasks

### Adding Alert 6
1. Read PRODUCT_OVERVIEW.md "How to Add New Alert Types" section
2. Follow all 6 steps exactly
3. Test thoroughly
4. Update all documentation
5. Commit with clear message

### Modifying Scraping
1. Test on live website first: https://canton-rewards.noves.fi/
2. Update `scrape_canton_rewards()` if website structure changed
3. Update `parse_metrics()` if data format changed
4. Test all existing alerts still work
5. Update docs if metrics changed

### Adding API Endpoint
1. Add handler in `scheduler.py` APIHandler class
2. Require API key authentication
3. Return JSON with consistent structure
4. Add example to `API_EXAMPLES.md`
5. Update PRODUCT_OVERVIEW.md API section

## Reference Documents Priority

When working on canton-monitor, read in this order:
1. **PRODUCT_OVERVIEW.md** - Complete system understanding
2. **FEATURES.md** - Detailed feature specs
3. **API_EXAMPLES.md** - API usage (if working on API)
4. **Code files** - Implementation details

## Important Notes

- This is a **production system** deployed on Railway
- Changes affect real alerts to real people
- Test thoroughly before deploying
- Never commit broken scraping logic
- Keep documentation in sync with code

---

**Remember:** Always read PRODUCT_OVERVIEW.md before making changes!
