Automated Remediation Expert System

This project implements a rule-based expert system for IT Operations.
It reads infrastructure events from a CSV file, applies remediation rules using Experta / Experta3, and outputs a simplified CSV containing only the recommended actions.

🚀 Features

Rule-based inference engine (expert system)

Uses service metrics (CPU, Disk, Errors, Latency, Traffic)

Automatically chooses remediation actions

Clean output CSV (only actions + reasons)

Easy to modify or add new rules

📦 Requirements
Recommended (works best):

Python 3.8 or 3.9

Install experta:

pip install experta

If using Python 3.10–3.12:

Install experta3:

pip install experta3

🧠 How It Works

Each event becomes a Fact

Experta rules check for conditions such as:

High CPU under high traffic → Scale out

Too many restarts → Escalate to on-call

High error rate → Rollback deployment

Disk almost full → Clear logs

The first matching rule generates the remediation action

📤 Example Output
event_id,service_name,status,recommended_action,reason,severity
12,auth-service,CRITICAL,SCALE_OUT,"High CPU under high traffic",HIGH
27,payment-api,OK,NO_ACTION,"Service healthy",INFO

🛠 Editing Rules

Rules are located inside RemediationEngine and follow this pattern:

@Rule(EventFact(cpu_percent=MATCH.cpu), TEST(lambda cpu: cpu > 90))
def high_cpu(self):
    # define action here

📄 License

This project is licensed under the MIT License.
