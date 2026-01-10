# XRDP Performance Configuration - Quick Reference

**Module**: Desktop (`configurator/modules/desktop.py`)
**Config File**: `config/default.yaml`

## Configuration Options

All configuration options are under the `desktop.xrdp` section in `config/default.yaml`.

### Available Settings

```yaml
desktop:
  xrdp:
    max_bpp: 24 # Color depth
    bitmap_cache: true # Enable client-side bitmap caching
    security_layer: "tls" # Security protocol
    tcp_nodelay: true # Disable Nagle's algorithm
```

---

## Option Details

### `max_bpp` (Color Depth)

**Type**: Integer
**Default**: `24`
**Valid Values**: `8`, `15`, `16`, `24`, `32`

Controls the color depth (bits per pixel) for the remote desktop session.

| Value | Description        | Use Case                           |
| ----- | ------------------ | ---------------------------------- |
| `8`   | 256 colors         | Very slow connections (< 256 kbps) |
| `15`  | 32,768 colors      | Slow connections (< 512 kbps)      |
| `16`  | 65,536 colors      | Low bandwidth (< 1 Mbps)           |
| `24`  | 16.7M colors       | **Recommended** - Good balance     |
| `32`  | True color + alpha | LAN only (> 100 Mbps)              |

**Performance Impact**:

- Lower values = Less bandwidth, faster over slow connections
- Higher values = Better image quality, more bandwidth

**Recommendation**:

- **Remote/WAN**: Use `24` (default)
- **LAN**: Use `32` for best quality
- **Mobile/Slow**: Use `16`

---

### `bitmap_cache` (Client-Side Caching)

**Type**: Boolean
**Default**: `true`
**Valid Values**: `true`, `false`

Enables bitmap caching on the RDP client side. This stores frequently used images (icons, backgrounds) in client memory to avoid retransmission.

**Performance Impact**:

- **Enabled**: 30-50% less bandwidth usage, faster screen updates
- **Disabled**: More bandwidth, slower performance

**Recommendation**: **Always enable** (`true`) unless troubleshooting graphics issues.

---

### `security_layer` (Security Protocol)

**Type**: String
**Default**: `"tls"`
**Valid Values**: `"tls"`, `"rdp"`, `"negotiate"`

Controls the encryption layer for the RDP connection.

| Value       | Description         | Security | Performance |
| ----------- | ------------------- | -------- | ----------- |
| `tls`       | TLS 1.2+ encryption | High     | Best        |
| `rdp`       | RDP native security | Medium   | Good        |
| `negotiate` | Auto-negotiate      | Variable | Variable    |

**Performance Impact**:

- `tls`: Lower CPU overhead than RDP security
- `rdp`: Slightly higher CPU overhead
- `negotiate`: Let client choose (may be slower)

**Recommendation**: Use `"tls"` (default) for best security and performance.

---

### `tcp_nodelay` (Nagle's Algorithm)

**Type**: Boolean
**Default**: `true`
**Valid Values**: `true`, `false`

Disables Nagle's algorithm, which batches small packets to reduce network overhead.

**Performance Impact**:

- **Enabled** (`true`): Lower latency, more responsive mouse/keyboard
- **Disabled** (`false`): Higher latency, but less network overhead

**Recommendation**: **Always enable** (`true`) for interactive sessions. Only disable for bulk data transfers.

---

## Configuration Examples

### Example 1: Default (Balanced)

```yaml
desktop:
  xrdp:
    max_bpp: 24
    bitmap_cache: true
    security_layer: "tls"
    tcp_nodelay: true
```

**Use Case**: General purpose, remote work over the internet.

---

### Example 2: High Quality (LAN)

```yaml
desktop:
  xrdp:
    max_bpp: 32 # Full color
    bitmap_cache: true
    security_layer: "tls"
    tcp_nodelay: true
```

**Use Case**: Local network with >100 Mbps bandwidth.

---

### Example 3: Low Bandwidth (Mobile)

```yaml
desktop:
  xrdp:
    max_bpp: 16 # Lower color depth
    bitmap_cache: true # Still cache
    security_layer: "tls"
    tcp_nodelay: true # Still responsive
```

**Use Case**: Mobile hotspot, slow VPN, or congested network.

---

### Example 4: Maximum Performance (Development/Testing)

```yaml
desktop:
  xrdp:
    max_bpp: 24
    bitmap_cache: true
    security_layer: "rdp" # Slightly less secure but faster
    tcp_nodelay: true
```

**Use Case**: Development environment, local testing only.

---

## Testing Configuration Changes

After modifying `config/default.yaml`, run:

```bash
# Re-run the desktop module
sudo python3 -m configurator --module desktop --force

# Or full reconfiguration
sudo python3 -m configurator --config config/default.yaml --force
```

---

## Troubleshooting

### Problem: Slow/Laggy Remote Desktop

**Solution**: Lower `max_bpp`:

```yaml
desktop:
  xrdp:
    max_bpp: 16 # Try 16 instead of 24
```

---

### Problem: Poor Image Quality

**Solution**: Increase `max_bpp` (if bandwidth allows):

```yaml
desktop:
  xrdp:
    max_bpp: 32 # Requires good connection
```

---

### Problem: High Bandwidth Usage

**Solution**: Ensure caching is enabled:

```yaml
desktop:
  xrdp:
    bitmap_cache: true # Should always be true
```

---

### Problem: Connection Fails with TLS

**Solution**: Fall back to RDP security:

```yaml
desktop:
  xrdp:
    security_layer: "rdp" # Less secure but more compatible
```

---

## Verifying Current Settings

Check the generated configuration:

```bash
# Check xrdp.ini
cat /etc/xrdp/xrdp.ini | grep -E "max_bpp|bitmap_cache|security_layer|tcp_nodelay"

# Check sesman.ini
cat /etc/xrdp/sesman.ini | grep -E "IdleTimeLimit|KillDisconnected"

# Check user session
cat ~/.xsession | grep -E "NO_AT_BRIDGE|XCURSOR_THEME"
```

---

## Performance Benchmarking

Test your configuration:

1. **Connection Time**: Time from RDP connect to desktop visible

   - **Target**: < 5 seconds

2. **Mouse Latency**: Move mouse and observe lag

   - **Target**: < 50ms (feels instant)

3. **Typing Latency**: Type in terminal and observe lag

   - **Target**: < 100ms (no noticeable delay)

4. **Screen Refresh**: Drag window and observe smoothness
   - **Target**: 30+ FPS (smooth)

---

## Advanced Tuning

For even better performance, combine XRDP optimizations with:

1. **XFCE Compositor**: Disable in Settings → Window Manager Tweaks
2. **Polkit Rules**: Prevent authentication popups (done automatically)
3. **Kernel Tuning**: Increase network buffer sizes (Phase 6)
4. **Client Settings**: Use "LAN" preset in RDP client

See the full guide: `docs/XRDP-XFCE-ZSH-GUIDE.md`

---

## Getting Help

**Issues**: https://github.com/noviasari42/debian-vps-workstation/issues
**Docs**: `docs/XRDP-XFCE-ZSH-GUIDE.md`
**Implementation**: `docs/implementation/PHASE1-XRDP-OPTIMIZATION.md`

---

**Last Updated**: January 10, 2026
**Version**: 1.0.0 (Phase 1)
