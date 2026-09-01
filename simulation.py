import sys

import httpx

BASE_URL = "http://localhost:8000"


def check_backend():
    try:
        response = httpx.get(f"{BASE_URL}/health")
        return response.status_code == 200
    except Exception:
        return False


def run_simulation():
    if not check_backend():
        print("[ERROR] GuardWAF server is not running!")
        print("Please start it first using: uvicorn app.main:app --reload")
        sys.exit(1)

    client = httpx.Client()

    print("\n" + "=" * 65)
    print("GUARDWAF ENTERPRISE SPECIFICATION COMPLIANCE SUITE (PS-5.1)")
    print("=" * 65)

    client.post(f"{BASE_URL}/admin/clear")
    print("\n[INFO] Database state cleared for fresh simulation run.\n")

    # --- Scenario 1: Normal Operations (Allowed) ---
    print("\n--- SCENARIO 1: Normal Sequence & Allowed Operations ---")
    session_1 = "session-prod-001"

    print("1. Call: verify_recipient(alice@aivar.com)")
    r1 = client.post(
        f"{BASE_URL}/proxy/tool",
        json={
            "agent_id": "support-agent",
            "session_id": session_1,
            "tool": "verify_recipient",
            "parameters": {"recipient": "alice@aivar.com"},
        },
    ).json()
    print(f"Outcome: {r1['status'].upper()} - {r1['evaluation_details']['outcome']}")

    print("2. Call: send_email(alice@aivar.com)")
    r2 = client.post(
        f"{BASE_URL}/proxy/tool",
        json={
            "agent_id": "support-agent",
            "session_id": session_1,
            "tool": "send_email",
            "parameters": {
                "recipient": "alice@aivar.com",
                "subject": "System Status",
                "body": "Normal operations.",
            },
        },
    ).json()
    print(f"Outcome: {r2['status'].upper()} - {r2['evaluation_details']['outcome']}")

    # --- Scenario 2: Sequence Rule Violation (Blocked) ---
    print("\n--- SCENARIO 2: Stateful Sequence Rule Violation (Blocked) ---")
    session_2 = "session-prod-002"
    print("Attempt: send_email without prior verify_recipient call in session-prod-002")
    r3 = client.post(
        f"{BASE_URL}/proxy/tool",
        json={
            "agent_id": "support-agent",
            "session_id": session_2,
            "tool": "send_email",
            "parameters": {"recipient": "charles@aivar.com", "subject": "Test"},
        },
    ).json()
    print(f"Outcome: {r3['status'].upper()} - {r3['evaluation_details']['outcome']}")

    # --- Scenario 3: Session-Aware Data Scope Mismatch (Blocked) ---
    print("\n--- SCENARIO 3: Session-Aware Data Scope Mismatch (Blocked) ---")
    session_3 = "session-prod-003"
    print("Attempt: Session customer_id=CUST-100 accessing customer_id=CUST-999 data")
    r4 = client.post(
        f"{BASE_URL}/proxy/tool",
        json={
            "agent_id": "analytics-agent",
            "session_id": session_3,
            "tool": "delete_records",
            "parameters": {"record_count": 10, "customer_id": "CUST-999"},
            "session_context": {"customer_id": "CUST-100"},
        },
    ).json()
    print(f"Outcome: {r4['status'].upper()} - {r4['evaluation_details']['outcome']}")

    # --- Scenario 4: Rate Limiting (Blocked) ---
    print("\n--- SCENARIO 4: Rate Limiting Enforcement (Blocked) ---")
    session_4 = "session-prod-004"
    client.post(
        f"{BASE_URL}/proxy/tool",
        json={
            "agent_id": "support-agent",
            "session_id": session_4,
            "tool": "verify_recipient",
            "parameters": {"recipient": "bob@aivar.com"},
        },
    )
    for i in range(1, 5):
        res = client.post(
            f"{BASE_URL}/proxy/tool",
            json={
                "agent_id": "support-agent",
                "session_id": session_4,
                "tool": "send_email",
                "parameters": {"recipient": "bob@aivar.com", "subject": f"Ping {i}"},
            },
        ).json()
        print(
            f"Call {i}/4 -> Outcome: {res['status'].upper()} - {res['evaluation_details']['outcome']}"
        )

    # --- Scenario 5: Parameter Blocklist SQL Injection (Blocked) ---
    print("\n--- SCENARIO 5: Parameter Blocklist & Injection (Blocked) ---")
    session_5 = "session-prod-005"
    r5 = client.post(
        f"{BASE_URL}/proxy/tool",
        json={
            "agent_id": "query-agent",
            "session_id": session_5,
            "tool": "execute_query",
            "parameters": {"query": "SELECT * FROM Users; DROP TABLE Users;"},
        },
    ).json()
    print(f"Outcome: {r5['status'].upper()} - {r5['evaluation_details']['outcome']}")

    # --- Scenario 6: Human-in-the-Loop Pause ---
    print("\n--- SCENARIO 6: Data Scope Pattern & HITL Queue (Paused) ---")
    session_6 = "session-prod-006"
    client.post(
        f"{BASE_URL}/proxy/tool",
        json={
            "agent_id": "support-agent",
            "session_id": session_6,
            "tool": "verify_recipient",
            "parameters": {"recipient": "client@external.com"},
        },
    )
    r6 = client.post(
        f"{BASE_URL}/proxy/tool",
        json={
            "agent_id": "support-agent",
            "session_id": session_6,
            "tool": "send_email",
            "parameters": {
                "recipient": "client@external.com",
                "subject": "External Quote",
            },
        },
    ).json()
    print(f"Outcome: {r6['status'].upper()} - {r6['evaluation_details']['outcome']}")

    print("\n" + "=" * 65)
    print("SIMULATION SUITE COMPLETED SUCCESSFULLY")
    print("=" * 65)


if __name__ == "__main__":
    run_simulation()
