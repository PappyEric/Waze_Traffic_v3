"""
Windows Service wrapper for the Waze Traffic Ingest Service.
=============================================================

Usage (run from elevated/admin command prompt):
    Install:   python install_service.py install
    Start:     python install_service.py start
    Stop:      python install_service.py stop
    Remove:    python install_service.py remove
    Debug:     python install_service.py debug

The service runs under the same Windows account that installs it,
which must have SQL Server access via Windows Authentication.
"""

import sys
import os
import time
import servicemanager
import win32event
import win32service
import win32serviceutil

# Add the parent directory to sys.path so we can import waze_ingest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class WazeTrafficIngestService(win32serviceutil.ServiceFramework):
    """Windows Service that runs the Waze traffic ingest loop."""

    _svc_name_ = "WazeTrafficIngest"
    _svc_display_name_ = "Waze Traffic Ingest Service"
    _svc_description_ = (
        "Fetches real-time traffic data from the Waze Partner Hub API "
        "every 30 seconds and loads it into the ArcSDE MSSQL database "
        "for use as a dynamic GIS layer in 911 CAD."
    )

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.running = True

    def SvcStop(self):
        """Called when the service is asked to stop."""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.running = False

    def SvcDoRun(self):
        """Called when the service starts."""
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ""),
        )

        # Import the ingest module
        try:
            import waze_ingest
        except ImportError as e:
            servicemanager.LogErrorMsg(
                f"WazeTrafficIngest: Failed to import waze_ingest: {e}"
            )
            return

        # Main service loop
        while self.running:
            try:
                waze_ingest.run_ingest_cycle()
            except Exception as e:
                servicemanager.LogErrorMsg(
                    f"WazeTrafficIngest: Ingest cycle error: {e}"
                )

            # Wait for stop signal or poll interval
            result = win32event.WaitForSingleObject(
                self.hWaitStop, waze_ingest.POLL_INTERVAL * 1000
            )
            if result == win32event.WAIT_OBJECT_0:
                break

        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STOPPED,
            (self._svc_name_, ""),
        )


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Called by the Windows Service Control Manager
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(WazeTrafficIngestService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Called from the command line (install, start, stop, etc.)
        win32serviceutil.HandleCommandLine(WazeTrafficIngestService)
