"""Performance monitor - tracks slow frames without modifying game behavior.

This is a passive monitor that just measures time. It doesn't wrap or
modify any processors - just records timestamps and logs slow frames.
"""

import time
from pathlib import Path
from collections import deque


class PerfMonitor:
    """Passive performance monitor - measures but doesn't modify."""
    
    SLOW_FRAME_MS = 100      # 100ms = 10fps
    VERY_SLOW_FRAME_MS = 500  # 500ms = 2fps
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.log_path = Path("perf_log.txt")
        
        self._frame_start = 0.0
        self._marks = {}  # name -> start time
        self._durations = {}  # name -> duration in ms
        
        self._frame_times = deque(maxlen=60)
        self._slow_count = 0
        self._total_frames = 0
        
        if self.enabled:
            with open(self.log_path, 'w') as f:
                f.write(f"=== Perf Log - {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
    
    def frame_start(self):
        """Call at very start of frame."""
        if not self.enabled:
            return
        self._frame_start = time.perf_counter()
        self._durations.clear()
    
    def mark(self, name: str):
        """Mark the start of a section."""
        if not self.enabled:
            return
        self._marks[name] = time.perf_counter()
    
    def measure(self, name: str):
        """Measure time since mark() was called with this name."""
        if not self.enabled:
            return
        if name in self._marks:
            self._durations[name] = (time.perf_counter() - self._marks[name]) * 1000
    
    def frame_end(self):
        """Call at very end of frame. Logs if slow."""
        if not self.enabled:
            return
        
        frame_ms = (time.perf_counter() - self._frame_start) * 1000
        self._frame_times.append(frame_ms)
        self._total_frames += 1
        
        if frame_ms >= self.SLOW_FRAME_MS:
            self._slow_count += 1
            self._log_slow(frame_ms)
    
    def _log_slow(self, frame_ms: float):
        """Log a slow frame."""
        severity = "VERY_SLOW" if frame_ms >= self.VERY_SLOW_FRAME_MS else "SLOW"
        fps = 1000 / frame_ms if frame_ms > 0 else 0
        
        # Sort sections by duration
        sorted_sections = sorted(self._durations.items(), key=lambda x: -x[1])
        
        with open(self.log_path, 'a') as f:
            f.write(f"[{severity}] Frame {self._total_frames}: {frame_ms:.0f}ms ({fps:.1f}fps)\n")
            for name, ms in sorted_sections[:5]:
                pct = ms / frame_ms * 100 if frame_ms > 0 else 0
                f.write(f"  {name}: {ms:.0f}ms ({pct:.0f}%)\n")
            f.write("\n")
        
        # Console output
        top = sorted_sections[0][0] if sorted_sections else "?"
        print(f"[{severity}] {frame_ms:.0f}ms - {top}")


# Global instance - disabled to prevent console spam
perf = PerfMonitor(enabled=False)
