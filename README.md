Automated Remediation Expert System

This project is a rule-based expert system for IT Operations.
It reads system events from a CSV file, applies expert rules using Experta, and outputs recommended remediation actions.

Features

Rule-based decision making (expert system)

Reads events such as CPU, memory, disk, errors, traffic

Applies remediation rules (restart, scale out, clear logs, etc.)

Outputs a clean CSV with only recommended actions

Easy to modify or add rules

Requirements

Python 3.8 or 3.9 (recommended)

Or Python 3.10–3.12 with:

pip install experta3

How to Run
1. (Optional) Generate sample event data
python generate_it_ops_events.py


This creates:
it_ops_events.csv

2. Run the expert system
python remediation_experta.py


This creates:
it_ops_events_with_actions.csv

How It Works

Each event (service metrics) is turned into a Fact.
Experta rules check conditions like:

High CPU + High traffic → scale out

Critical + too many restarts → escalate

High error rate → rollback

Disk almost full → clear logs

The first matching rule produces the recommended action.

Output Example
event_id,service_name,status,recommended_action,reason,severity
12,auth-service,CRITICAL,SCALE_OUT,High CPU under high traffic,HIGH
27,payment-api,OK,NO_ACTION,Service healthy,INFO

Editing Rules

@Rule(EventFact(cpu_percent=MATCH.cpu), TEST(lambda cpu: cpu > 90))
def high_cpu(self):
    ...

def high_cpu(self):
    ...
