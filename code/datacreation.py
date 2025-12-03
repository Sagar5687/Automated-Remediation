import csv
import random

random.seed(42)

services = ["auth-service", "payment-api", "orders-service", "inventory-service", "search-service"]
regions = ["us-east-1", "us-west-2", "eu-central-1"]
statuses = ["OK", "WARNING", "CRITICAL"]
traffic_levels = ["LOW", "MEDIUM", "HIGH"]

rows = []
event_id = 1

for _ in range(150):
    service = random.choice(services)
    region = random.choice(regions)
    traffic = random.choice(traffic_levels)

    if traffic == "LOW":
        cpu = random.randint(5, 60)
        response_time = random.randint(80, 400)
        error_rate = round(random.uniform(0, 2), 2)
    elif traffic == "MEDIUM":
        cpu = random.randint(20, 85)
        response_time = random.randint(150, 800)
        error_rate = round(random.uniform(0, 4), 2)
    else:  # HIGH
        cpu = random.randint(40, 100)
        response_time = random.randint(300, 2000)
        error_rate = round(random.uniform(0, 8), 2)

    disk = random.randint(30, 98)
    memory = random.randint(20, 95)

    if cpu > 90 or disk > 95 or error_rate > 5 or response_time > 1200:
        status = "CRITICAL"
    elif cpu > 75 or disk > 85 or error_rate > 2.5 or response_time > 800:
        status = "WARNING"
    else:
        status = "OK"

    previous_restarts = random.randint(0, 4)
    is_business_hours = random.choice([0, 1])

    rows.append({
        "event_id": event_id,
        "service_name": service,
        "region": region,
        "cpu_percent": cpu,
        "memory_percent": memory,
        "disk_percent": disk,
        "response_time_ms": response_time,
        "error_rate_percent": error_rate,
        "status": status,
        "traffic_level": traffic,
        "previous_restarts": previous_restarts,
        "is_business_hours": is_business_hours,
    })
    event_id += 1

with open("it_ops_events.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

print("Generated it_ops_events.csv with", len(rows), "rows")
