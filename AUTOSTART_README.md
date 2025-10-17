# UK Legal Dashboard - Auto-Start Configuration

This document explains how to configure the UK Legal Dashboard to start automatically when your MacBook starts up.

## Overview

The auto-start system uses macOS's native `launchd` system to:
- Automatically start Flask backend and React frontend on MacBook startup
- Monitor services and restart them if they crash
- Manage logs for easy troubleshooting
- Provide graceful shutdown when your MacBook shuts down

## Quick Start

### Install Auto-Start

```bash
cd /Users/rezazeraat/Desktop/Data
bash install_autostart.sh
```

This will:
1. Install all Python and Node.js dependencies
2. Configure macOS LaunchAgent
3. Start the services immediately
4. Enable automatic startup on MacBook restart

### Uninstall Auto-Start

```bash
cd /Users/rezazeraat/Desktop/Data
bash uninstall_autostart.sh
```

This will:
1. Stop all running services
2. Remove the LaunchAgent configuration
3. Optionally clean up log files
4. Disable automatic startup

## Manual Control

### Start Services Manually

```bash
cd /Users/rezazeraat/Desktop/Data
bash start_service.sh
```

### Stop Services Manually

```bash
cd /Users/rezazeraat/Desktop/Data
bash stop_service.sh
```

## Architecture

### Components

1. **start_service.sh** - Main service wrapper
   - Starts Flask backend (port 5000)
   - Starts React frontend (port 5173)
   - Monitors both services and restarts on failure
   - Handles graceful shutdown

2. **stop_service.sh** - Service shutdown script
   - Stops Flask and React processes
   - Cleans up ports
   - Removes PID files

3. **com.uklegaldashboard.service.plist** - LaunchAgent configuration
   - Defines macOS launch agent
   - Configures automatic restart on failure
   - Sets up logging and environment

4. **install_autostart.sh** - Installation script
   - Checks dependencies
   - Installs required packages
   - Configures LaunchAgent
   - Starts services

5. **uninstall_autostart.sh** - Removal script
   - Unloads LaunchAgent
   - Stops services
   - Optionally removes logs

### File Locations

```
/Users/rezazeraat/Desktop/Data/
├── start_service.sh              # Service manager
├── stop_service.sh               # Service stopper
├── install_autostart.sh          # Installation script
├── uninstall_autostart.sh        # Removal script
└── com.uklegaldashboard.service.plist  # LaunchAgent config

~/Library/LaunchAgents/
└── com.uklegaldashboard.service.plist  # Installed LaunchAgent

~/Library/Logs/uk-legal-dashboard/
├── flask.log                     # Flask backend logs
├── react.log                     # React frontend logs
├── service.log                   # Service manager logs
├── launchd-out.log              # LaunchAgent stdout
└── launchd-err.log              # LaunchAgent stderr
```

## Log Files

All logs are stored in `~/Library/Logs/uk-legal-dashboard/`:

### View Real-Time Logs

```bash
# Flask backend
tail -f ~/Library/Logs/uk-legal-dashboard/flask.log

# React frontend
tail -f ~/Library/Logs/uk-legal-dashboard/react.log

# Service manager
tail -f ~/Library/Logs/uk-legal-dashboard/service.log

# LaunchAgent
tail -f ~/Library/Logs/uk-legal-dashboard/launchd-out.log

# All logs combined
tail -f ~/Library/Logs/uk-legal-dashboard/*.log
```

## Troubleshooting

### Check Service Status

```bash
# Check if LaunchAgent is loaded
launchctl list | grep uklegaldashboard

# Check if Flask is running
lsof -ti:5000

# Check if React is running
lsof -ti:5173

# View recent logs
tail -n 50 ~/Library/Logs/uk-legal-dashboard/service.log
```

### Common Issues

#### Services Not Starting

1. Check logs for errors:
   ```bash
   tail -f ~/Library/Logs/uk-legal-dashboard/*.log
   ```

2. Verify dependencies:
   ```bash
   python3 --version  # Should be Python 3.x
   node --version     # Should be Node.js
   npm --version      # Should be npm
   ```

3. Try manual start:
   ```bash
   cd /Users/rezazeraat/Desktop/Data
   bash start_service.sh
   ```

#### Port Already in Use

If ports 5000 or 5173 are already in use:

```bash
# Kill processes on Flask port
lsof -ti:5000 | xargs kill -9

# Kill processes on React port
lsof -ti:5173 | xargs kill -9

# Or use the stop script
bash /Users/rezazeraat/Desktop/Data/stop_service.sh
```

#### LaunchAgent Not Working

1. Unload and reload:
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.uklegaldashboard.service.plist
   launchctl load ~/Library/LaunchAgents/com.uklegaldashboard.service.plist
   ```

2. Check permissions:
   ```bash
   ls -la ~/Library/LaunchAgents/com.uklegaldashboard.service.plist
   # Should be: -rw-r--r-- (644)
   ```

3. Verify plist syntax:
   ```bash
   plutil -lint ~/Library/LaunchAgents/com.uklegaldashboard.service.plist
   ```

#### Services Keep Crashing

The LaunchAgent is configured to restart services automatically, but if they keep crashing:

1. Check logs for error messages
2. Verify all dependencies are installed
3. Check disk space: `df -h`
4. Try manual start to see errors in real-time

### Complete Reset

If you need to completely reset the auto-start configuration:

```bash
# 1. Uninstall
bash /Users/rezazeraat/Desktop/Data/uninstall_autostart.sh

# 2. Kill any stuck processes
lsof -ti:5000 | xargs kill -9
lsof -ti:5173 | xargs kill -9

# 3. Clear logs
rm -rf ~/Library/Logs/uk-legal-dashboard

# 4. Reinstall
bash /Users/rezazeraat/Desktop/Data/install_autostart.sh
```

## How It Works

### Startup Sequence

1. MacBook starts up
2. User logs in
3. `launchd` loads `com.uklegaldashboard.service.plist`
4. `launchd` executes `start_service.sh`
5. `start_service.sh` starts Flask backend
6. Flask initializes and loads `train.parquet`
7. `start_service.sh` starts React frontend
8. React dev server starts and connects to Flask
9. Services enter monitoring loop

### Monitoring

The `start_service.sh` script continuously monitors both services:
- Checks every 10 seconds if processes are alive
- Automatically restarts crashed services
- Logs all events to log files

### Shutdown Sequence

1. MacBook shutdown initiated
2. `launchd` sends SIGTERM to `start_service.sh`
3. `start_service.sh` catches signal and runs cleanup
4. React process terminated gracefully
5. Flask process terminated gracefully
6. Ports cleaned up
7. PID files removed

## Configuration

### LaunchAgent Settings

Edit `com.uklegaldashboard.service.plist` to customize:

- **RunAtLoad**: Start on login (currently: `true`)
- **KeepAlive**: Restart on crash (currently: `true`)
- **ThrottleInterval**: Wait time before restart (currently: 60 seconds)
- **Nice**: Process priority (currently: 0 = normal)

After editing, reload:
```bash
launchctl unload ~/Library/LaunchAgents/com.uklegaldashboard.service.plist
launchctl load ~/Library/LaunchAgents/com.uklegaldashboard.service.plist
```

### Environment Variables

To add environment variables, edit the `EnvironmentVariables` section in the plist:

```xml
<key>EnvironmentVariables</key>
<dict>
    <key>PATH</key>
    <string>/usr/local/bin:/usr/bin:/bin</string>
    <key>YOUR_VAR</key>
    <string>your_value</string>
</dict>
```

## Security Considerations

- The system runs under your user account (not root)
- Services listen on localhost only (not exposed to network)
- Groq API key is stored in `api_server.py` (consider using environment variables)
- Logs contain API responses (may include sensitive data)

## Performance

- **Memory**: ~500MB (Flask) + ~200MB (React dev server)
- **CPU**: Low when idle, moderate during generation
- **Disk**: Logs rotate at 10MB (not implemented yet - TODO)
- **Network**: Localhost only, no external traffic except Groq API

## Limitations

- Services take 30-60 seconds to fully start
- React dev server is used (not optimized for production)
- In-memory batch generation state lost on restart
- No log rotation implemented (logs grow indefinitely)
- Port conflicts require manual intervention

## Future Enhancements

Potential improvements:
- [ ] Add log rotation (keep last 10MB)
- [ ] Production React build instead of dev server
- [ ] Persistent batch generation state
- [ ] Automatic port conflict resolution
- [ ] Web-based status dashboard
- [ ] Email notifications on service failure
- [ ] Automatic daily backups of train.parquet

## Support

For issues or questions:
1. Check logs first: `tail -f ~/Library/Logs/uk-legal-dashboard/*.log`
2. Try manual start: `bash start_service.sh`
3. Complete reset: uninstall and reinstall
4. Check CLAUDE.md for project documentation

## License

Part of UK Legal Training Dataset project.
