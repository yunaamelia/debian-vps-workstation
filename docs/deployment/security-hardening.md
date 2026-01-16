# Security Hardening

This guide covers the security measures applied by the configurator.

## SSH Hardening
*   Disables root login.
*   Disables password authentication (keys only).
*   Changes default port (configurable).

## Firewall (UFW)
*   Enables UFW.
*   Denies incoming by default.
*   Allows outgoing.
*   Allows configured SSH port.

## Fail2Ban
*   Installs and configures Fail2Ban for SSH protection.

## Auto-Updates
*   Configures `unattended-upgrades` for security patches.
