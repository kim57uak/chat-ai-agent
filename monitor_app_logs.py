#!/usr/bin/env python3
"""
Monitor MyGenie.app logs from Launchpad
Real-time log monitoring for packaged application
"""

import subprocess
import sys
from datetime import datetime

def monitor_logs(app_name="MyGenie", follow=True):
    """
    Monitor application logs using macOS log system
    
    Args:
        app_name: Application name to filter
        follow: Follow logs in real-time
    """
    print(f"🔍 Monitoring logs for {app_name}...")
    print(f"⏰ Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    
    try:
        # macOS unified logging system
        cmd = [
            "log", "stream",
            "--predicate", f'process == "{app_name}"',
            "--style", "compact",
            "--color", "auto"
        ]
        
        if not follow:
            cmd = [
                "log", "show",
                "--predicate", f'process == "{app_name}"',
                "--last", "1h",
                "--style", "compact"
            ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        for line in process.stdout:
            print(line.rstrip())
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitoring stopped")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor MyGenie app logs")
    parser.add_argument("--app", default="MyGenie", help="App name to monitor")
    parser.add_argument("--history", action="store_true", help="Show last 1 hour logs only")
    
    args = parser.parse_args()
    
    monitor_logs(args.app, follow=not args.history)
