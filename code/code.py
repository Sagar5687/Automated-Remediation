from dataclasses import dataclass
from typing import Dict, List

import csv
from experta import KnowledgeEngine, Fact, Rule, MATCH, TEST


# ---------- Data models ----------

@dataclass
class Event:
    event_id: int
    service_name: str
    region: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    response_time_ms: float
    error_rate_percent: float
    status: str
    traffic_level: str
    previous_restarts: int
    is_business_hours: bool


@dataclass
class Decision:
    action: str
    reason: str
    severity: str = "INFO"


# ---------- Experta facts ----------

class EventFact(Fact):
    """Fact representing an IT ops event."""
    pass


# ---------- Remediation Expert System using experta ----------

class RemediationEngine(KnowledgeEngine):
    def __init__(self):
        super().__init__()
        # event_id -> Decision
        self.decisions: Dict[int, Decision] = {}

    def _set_decision_once(self, event_id: int, decision: Decision):
        """Ensure only the first (highest priority) rule sets a decision."""
        if event_id in self.decisions:
            return
        self.decisions[event_id] = decision

    # 1. Escalate if we've retried too many times and it's still critical
    @Rule(
        EventFact(status="CRITICAL",
                  event_id=MATCH.eid,
                  previous_restarts=MATCH.prev),
        TEST(lambda prev: prev >= 3),
        salience=100  # higher = higher priority
    )
    def escalate_after_retries(self, eid, prev):
        self._set_decision_once(
            eid,
            Decision(
                action="ESCALATE_TO_ONCALL",
                reason=f"[ESCALATE_AFTER_RETRIES] Still CRITICAL after {prev} restarts.",
                severity="CRITICAL",
            ),
        )

    # 2. Scale out under high load & high CPU
    @Rule(
        EventFact(status=MATCH.status,
                  traffic_level="HIGH",
                  cpu_percent=MATCH.cpu,
                  event_id=MATCH.eid),
        TEST(lambda status, cpu: status in ("WARNING", "CRITICAL") and cpu >= 85),
        salience=90
    )
    def scale_out_under_high_load(self, eid, status, cpu):
        self._set_decision_once(
            eid,
            Decision(
                action="SCALE_OUT",
                reason=(
                    f"[SCALE_OUT_UNDER_HIGH_LOAD] Status={status}, CPU={cpu}% "
                    f"under HIGH traffic."
                ),
                severity="HIGH",
            ),
        )

    # 3. Free disk space when nearly full
    @Rule(
        EventFact(disk_percent=MATCH.disk, event_id=MATCH.eid),
        TEST(lambda disk: disk >= 90),
        salience=80
    )
    def free_disk_space(self, eid, disk):
        self._set_decision_once(
            eid,
            Decision(
                action="CLEAR_LOGS_AND_TMP",
                reason=f"[FREE_DISK_SPACE] Disk at {disk}%.",
                severity="HIGH",
            ),
        )

    # 4. Rollback when errors are very high and status is critical
    @Rule(
        EventFact(error_rate_percent=MATCH.err,
                  status="CRITICAL",
                  event_id=MATCH.eid),
        TEST(lambda err: err >= 5.0),
        salience=70
    )
    def rollback_on_high_errors(self, eid, err):
        self._set_decision_once(
            eid,
            Decision(
                action="ROLLBACK_DEPLOYMENT",
                reason=f"[ROLLBACK_ON_HIGH_ERRORS] Error rate={err}%.",
                severity="CRITICAL",
            ),
        )

    # 5. Restart unresponsive / critical service if we haven't retried too many times
    @Rule(
        EventFact(status="CRITICAL",
                  previous_restarts=MATCH.prev,
                  event_id=MATCH.eid),
        TEST(lambda prev: prev < 3),
        salience=60
    )
    def restart_unresponsive_service(self, eid, prev):
        self._set_decision_once(
            eid,
            Decision(
                action="RESTART_SERVICE",
                reason=f"[RESTART_UNRESPONSIVE_SERVICE] CRITICAL, prev_restarts={prev}.",
                severity="CRITICAL",
            ),
        )

    # 6. Page on-call if critical outside business hours
    @Rule(
        EventFact(status="CRITICAL",
                  is_business_hours=0,
                  event_id=MATCH.eid),
        salience=50
    )
    def page_oncall_off_hours(self, eid):
        self._set_decision_once(
            eid,
            Decision(
                action="PAGE_ONCALL",
                reason="[PAGE_ONCALL_OFF_HOURS] Critical issue outside business hours.",
                severity="CRITICAL",
            ),
        )

    # 7. Investigate high latency with normal CPU
    @Rule(
        EventFact(response_time_ms=MATCH.rt,
                  cpu_percent=MATCH.cpu,
                  event_id=MATCH.eid),
        TEST(lambda rt, cpu: rt > 1000 and cpu < 70),
        salience=40
    )
    def investigate_backend_latency(self, eid, rt, cpu):
        self._set_decision_once(
            eid,
            Decision(
                action="OPEN_INVESTIGATION_TICKET",
                reason=(
                    f"[INVESTIGATE_BACKEND_LATENCY] High latency={rt}ms, "
                    f"CPU={cpu}% (likely downstream/backend issue)."
                ),
                severity="MEDIUM",
            ),
        )

    # 8. No action for OK events (low priority)
    @Rule(
        EventFact(status="OK", event_id=MATCH.eid),
        salience=1
    )
    def no_action_ok(self, eid):
        self._set_decision_once(
            eid,
            Decision(
                action="NO_ACTION",
                reason="[NO_ACTION_OK] Service healthy.",
                severity="INFO",
            ),
        )


# ---------- Automation stub (execution layer) ----------

def execute_action(event: Event, decision: Decision) -> None:
    """
    Stub for the automation layer.
    Replace prints with calls to:
      - Ansible, Terraform, AWS, Kubernetes, shell scripts, etc.
    """
    if decision.action == "NO_ACTION":
        return

    print(
        f"[EXECUTE] event_id={event.event_id} "
        f"service={event.service_name} "
        f"action={decision.action} "
        f"severity={decision.severity} "
        f"reason={decision.reason}"
    )


# ---------- CSV helpers ----------

def load_events_from_csv(path: str) -> List[Event]:
    events: List[Event] = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            events.append(
                Event(
                    event_id=int(row["event_id"]),
                    service_name=row["service_name"],
                    region=row["region"],
                    cpu_percent=float(row["cpu_percent"]),
                    memory_percent=float(row["memory_percent"]),
                    disk_percent=float(row["disk_percent"]),
                    response_time_ms=float(row["response_time_ms"]),
                    error_rate_percent=float(row["error_rate_percent"]),
                    status=row["status"],
                    traffic_level=row["traffic_level"],
                    previous_restarts=int(row["previous_restarts"]),
                    is_business_hours=bool(int(row["is_business_hours"])),
                )
            )
    return events


def save_decisions_to_csv(path: str,
                          events: List[Event],
                          decisions: Dict[int, Decision]) -> None:
    with open(path, "w", newline="") as f:
        fieldnames = [
            "event_id",
            "service_name",
            "region",
            "cpu_percent",
            "memory_percent",
            "disk_percent",
            "response_time_ms",
            "error_rate_percent",
            "status",
            "traffic_level",
            "previous_restarts",
            "is_business_hours",
            "recommended_action",
            "action_reason",
            "action_severity",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for e in events:
            d = decisions.get(
                e.event_id,
                Decision(
                    action="NO_DECISION",
                    reason="No matching rule fired.",
                    severity="INFO",
                ),
            )
            writer.writerow(
                {
                    "event_id": e.event_id,
                    "service_name": e.service_name,
                    "region": e.region,
                    "cpu_percent": e.cpu_percent,
                    "memory_percent": e.memory_percent,
                    "disk_percent": e.disk_percent,
                    "response_time_ms": e.response_time_ms,
                    "error_rate_percent": e.error_rate_percent,
                    "status": e.status,
                    "traffic_level": e.traffic_level,
                    "previous_restarts": e.previous_restarts,
                    "is_business_hours": int(e.is_business_hours),
                    "recommended_action": d.action,
                    "action_reason": d.reason,
                    "action_severity": d.severity,
                }
            )


# ---------- Main demo ----------

def main():
    input_csv = "it_ops_events.csv"
    output_csv = "it_ops_events_with_actions_experta.csv"

    print(f"Loading events from {input_csv} ...")
    events = load_events_from_csv(input_csv)

    decisions: Dict[int, Decision] = {}

    for e in events:
        engine = RemediationEngine()
        engine.reset()

        # Insert one EventFact into the expert system for this event
        engine.declare(
            EventFact(
                event_id=e.event_id,
                service_name=e.service_name,
                region=e.region,
                cpu_percent=e.cpu_percent,
                memory_percent=e.memory_percent,
                disk_percent=e.disk_percent,
                response_time_ms=e.response_time_ms,
                error_rate_percent=e.error_rate_percent,
                status=e.status,
                traffic_level=e.traffic_level,
                previous_restarts=e.previous_restarts,
                is_business_hours=int(e.is_business_hours),
            )
        )

        engine.run()

        # Read decision from engine
        decision = engine.decisions.get(
            e.event_id,
            Decision(
                action="NO_DECISION",
                reason="[DEFAULT] No rule fired.",
                severity="INFO",
            ),
        )
        decisions[e.event_id] = decision

        execute_action(e, decision)

    save_decisions_to_csv(output_csv, events, decisions)
    print(f"\nDone. Decisions saved to: {output_csv}")


if __name__ == "__main__":
    main()
