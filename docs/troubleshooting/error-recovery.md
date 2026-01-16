# Error Recovery

If the configurator fails during installation, it attempts to rollback changes.

## Automatic Rollback
The configurator maintains a transaction log. If an error occurs, it reverses:
*   Package installations.
*   File creations/modifications.
*   Service starts.

## Manual Recovery
If automatic rollback fails:
1.  Check logs in `logs/configurator.log`.
2.  Use the state manager to inspect the failed checkpoint.
3.  Resume from the last successful checkpoint:
    ```bash
    vps-configurator install --resume
    ```
