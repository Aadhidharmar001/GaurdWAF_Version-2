import json
import os
import re
from typing import Any, Dict

from openai import OpenAI
from sqlalchemy.orm import Session

from app.audit.logger import log_audit_event
from app.config import settings
from app.hitl.queue_manager import create_hitl_request
from app.models import ToolCallRequest
from app.proxy.interceptor import evaluate_tool_call_request
from app.proxy.sequence_guard import record_sequence_state
from app.rules_engine.loader import load_policy_from_yaml


def parse_prompt_intent(prompt: str) -> Dict[str, Any]:
    """
    Intelligent Tool Intent Parser that converts natural language prompts
    into structured tool call requests for GuardWAF evaluation.
    """
    prompt_lower = prompt.lower()

    # 1. SQL Injection / Query execution
    if any(
        kw in prompt_lower
        for kw in [
            "drop table",
            "select",
            "delete from",
            "insert into",
            "execute_query",
            "query",
            "sql",
        ]
    ):
        query_str = "DROP TABLE Users;" if "drop table" in prompt_lower else prompt
        if not ("select" in prompt_lower or "drop" in prompt_lower or "delete" in prompt_lower):
            query_str = f"SELECT * FROM logs WHERE details LIKE '%{prompt}%'"
        return {"tool": "execute_query", "parameters": {"query": query_str}}

    # 2. Bulk Delete Records
    if "delete" in prompt_lower or "remove" in prompt_lower or "wipe" in prompt_lower or "bulk" in prompt_lower:
        numbers = re.findall(r"\d+", prompt)
        count = int(numbers[0]) if numbers else 500
        return {
            "tool": "delete_records",
            "parameters": {"record_count": count, "customer_id": "cust-999"},
        }

    # 3. Verify Recipient
    if "verify" in prompt_lower or "check recipient" in prompt_lower:
        email_match = re.search(r"[\w\.-]+@[\w\.-]+", prompt)
        recipient = email_match.group(0) if email_match else "alice@aivar.com"
        return {"tool": "verify_recipient", "parameters": {"recipient": recipient}}

    # 4. Send Email (Default for email prompts)
    email_match = re.search(r"[\w\.-]+@[\w\.-]+", prompt)
    recipient = email_match.group(0) if email_match else "alice@aivar.com"
    return {
        "tool": "send_email",
        "parameters": {
            "recipient": recipient,
            "subject": "System Status Update",
            "body": f"Automated notification for prompt: {prompt}",
        },
    }


def run_agent_prompt(
    user_prompt: str,
    agent_id: str = "demo-agent-01",
    session_id: str = "demo-session-01",
    db: Session = None,
) -> Dict[str, Any]:
    api_key = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
    base_url = settings.OPENAI_BASE_URL or os.environ.get("OPENAI_BASE_URL", "https://api.x.ai/v1")

    provider_label = "xAI Grok" if "x.ai" in base_url else "OpenAI"
    model_name = settings.OPENAI_MODEL or ("grok-2" if "x.ai" in base_url else "gpt-4o-mini")

    tool_intent = parse_prompt_intent(user_prompt)

    # Attempt real LLM reasoning if valid API key is provided
    if api_key:
        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            system_instruction = (
                "You are an AI Agent with access to tools: verify_recipient, send_email, delete_records, execute_query. "
                "Respond in JSON format with keys: 'tool' and 'parameters'."
            )
            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
            )
            content = completion.choices[0].message.content
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                parsed_llm = json.loads(json_match.group(0))
                if "tool" in parsed_llm and "parameters" in parsed_llm:
                    tool_intent = parsed_llm
            provider_label = f"{provider_label} ({model_name})"
        except Exception:
            provider_label = f"{provider_label} (Agent Core Engine)"
    else:
        provider_label = "Agent Intent Core Engine"

    # Evaluate tool call against GuardWAF Proxy Interceptor
    waf_response = None
    if db is not None:
        policy = load_policy_from_yaml(settings.RULES_PATH)
        req = ToolCallRequest(
            agent_id=agent_id,
            session_id=session_id,
            tool=tool_intent["tool"],
            parameters=tool_intent["parameters"],
        )
        eval_res = evaluate_tool_call_request(req, policy, db)

        status = eval_res.status
        outcome = eval_res.outcome
        matched_rule = eval_res.matched_rule
        hitl_entry = None

        if status == "allowed":
            record_sequence_state(session_id, req.tool, db)
            log_audit_event(
                db,
                agent_id,
                session_id,
                req.tool,
                req.parameters,
                outcome,
                matched_rule,
                "allowed",
            )
            waf_status = "ALLOWED"
        elif status == "blocked":
            log_audit_event(
                db,
                agent_id,
                session_id,
                req.tool,
                req.parameters,
                outcome,
                matched_rule,
                "blocked",
            )
            waf_status = "BLOCKED"
        elif status == "pending_hitl":
            hitl_entry = create_hitl_request(
                db,
                agent_id,
                session_id,
                req.tool,
                req.parameters,
                matched_rule=matched_rule,
            )
            log_audit_event(
                db,
                agent_id,
                session_id,
                req.tool,
                req.parameters,
                f"Paused for HITL approval (ID: {hitl_entry.id})",
                matched_rule,
                "pending_hitl",
            )
            waf_status = "PENDING_HITL"
        else:
            waf_status = status.upper()

        waf_response = {
            "disposition": waf_status,
            "outcome": outcome,
            "matched_rule": matched_rule,
            "fraud_score": getattr(hitl_entry, "fraud_score", None) if status == "pending_hitl" else None,
            "confidence_score": getattr(hitl_entry, "confidence_score", None) if status == "pending_hitl" else None,
            "risk_level": getattr(hitl_entry, "risk_level", None) if status == "pending_hitl" else None,
        }

    disposition_str = waf_response["disposition"] if waf_response else "EVALUATED"
    outcome_str = waf_response["outcome"] if waf_response else "Clear"

    formatted_response = (
        f"🤖 Agent Reasoning Engine: {provider_label}\n"
        f"🛠️ Tool Call Emitted: {tool_intent['tool']}({json.dumps(tool_intent['parameters'])})\n"
        f"🛡️ GuardWAF Interception Result: [{disposition_str}]\n"
        f"📋 Security Policy Evaluation: {outcome_str}"
    )

    return {
        "agent_id": agent_id,
        "session_id": session_id,
        "provider": provider_label,
        "prompt": user_prompt,
        "tool_call": tool_intent,
        "waf_evaluation": waf_response,
        "response": formatted_response,
    }
