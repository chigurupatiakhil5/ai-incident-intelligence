from typing import Optional

THRESHOLDS = {
    "cpu_critical": 90.0,
    "cpu_warning": 75.0,
    "memory_critical": 85.0,
    "memory_warning": 70.0,
}

def detect_anomaly(server_name: str, cpu_percent: float, memory_percent: float) -> Optional[dict]:
    severity = None
    reasons = []

    if cpu_percent >= THRESHOLDS["cpu_critical"]:
        severity = "critical"
        reasons.append(f"CPU at {cpu_percent}% (threshold: {THRESHOLDS['cpu_critical']}%)")
    elif cpu_percent >= THRESHOLDS["cpu_warning"]:
        severity = severity or "warning"
        reasons.append(f"CPU at {cpu_percent}% (threshold: {THRESHOLDS['cpu_warning']}%)")

    if memory_percent >= THRESHOLDS["memory_critical"]:
        severity = "critical"
        reasons.append(f"Memory at {memory_percent}% (threshold: {THRESHOLDS['memory_critical']}%)")
    elif memory_percent >= THRESHOLDS["memory_warning"]:
        severity = severity or "warning"
        reasons.append(f"Memory at {memory_percent}% (threshold: {THRESHOLDS['memory_warning']}%)")

    if severity is None:
        return None

    return {
        "server_name": server_name,
        "severity": severity,
        "description": " | ".join(reasons),
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent,
    }