# UK Legal Dashboard - Quick Start Guide

## Install Auto-Start (One-Time Setup)

```bash
cd /Users/rezazeraat/Desktop/Data
bash install_autostart.sh
```

This will:
- Install all dependencies automatically
- Start Flask (port 5000) and React (port 5173)
- Configure auto-start on MacBook startup
- Enable automatic crash recovery

**Access the dashboard:** http://localhost:5173

## Useful Commands

```bash
# Stop services
bash stop_service.sh

# Start services manually
bash start_service.sh

# Remove auto-start
bash uninstall_autostart.sh

# View logs
tail -f ~/Library/Logs/uk-legal-dashboard/flask.log
tail -f ~/Library/Logs/uk-legal-dashboard/react.log
```

## Check Status

```bash
# Check if services are running
lsof -ti:5000  # Flask
lsof -ti:5173  # React

# Check LaunchAgent status
launchctl list | grep uklegaldashboard
```

## Troubleshooting

### Services won't start
```bash
# View errors
tail -n 50 ~/Library/Logs/uk-legal-dashboard/*.log

# Try manual start
bash start_service.sh
```

### Port conflicts
```bash
# Kill stuck processes
lsof -ti:5000 | xargs kill -9
lsof -ti:5173 | xargs kill -9
```

### Complete reset
```bash
bash uninstall_autostart.sh
rm -rf ~/Library/Logs/uk-legal-dashboard
bash install_autostart.sh
```

## How It Works

1. **On MacBook startup:** LaunchAgent automatically starts services
2. **Monitoring:** Services restart automatically if they crash
3. **On shutdown:** Services stop gracefully
4. **Logs:** All activity logged to `~/Library/Logs/uk-legal-dashboard/`

## File Locations

- Scripts: `/Users/rezazeraat/Desktop/Data/`
- LaunchAgent: `~/Library/LaunchAgents/com.uklegaldashboard.service.plist`
- Logs: `~/Library/Logs/uk-legal-dashboard/`

## What's Running

- **Flask Backend** (port 5000)
  - API endpoints for data access
  - Sample generation
  - Dataset management

- **React Frontend** (port 5173)
  - Web dashboard
  - Data visualization
  - Generation controls

## Need Help?

See `AUTOSTART_README.md` for detailed documentation.
