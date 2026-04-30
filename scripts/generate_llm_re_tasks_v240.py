import json
from pathlib import Path


SYSTEMS = [
    {
        "prefix": "ADV",
        "system_type": "academic advising assistant",
        "domain": "degree planning",
        "evidence": ["curriculum handbook", "course catalog", "graduation checklist"],
        "risks": ["inventing policy", "accessing private student records", "answering without source evidence"],
        "gold": ["official curriculum", "cite", "refuse unsupported", "escalate", "curriculum version", "regression"],
    },
    {
        "prefix": "HR",
        "system_type": "HR policy assistant",
        "domain": "employee policy",
        "evidence": ["employee handbook", "HR policy PDF", "escalation workflow"],
        "risks": ["legal advice", "unsupported entitlement claim", "case-specific promise"],
        "gold": ["employee handbook", "policy section", "refuse unsupported", "HR escalation", "policy freshness", "case-specific"],
    },
    {
        "prefix": "CODE",
        "system_type": "LLM code review assistant",
        "domain": "software code review",
        "evidence": ["coding standard", "secure coding guideline", "test policy"],
        "risks": ["exfiltrating code", "claiming tests passed without execution", "false security claim"],
        "gold": ["coding standard", "secure coding", "no external service", "evidence", "severity", "do not claim tests passed"],
    },
    {
        "prefix": "SUP",
        "system_type": "customer support chatbot",
        "domain": "warranty and support",
        "evidence": ["warranty policy", "returns FAQ", "support escalation workflow"],
        "risks": ["unsupported refund promise", "prompt injection", "asking for payment card data"],
        "gold": ["current policy", "cite", "refuse unsupported", "support escalation", "payment card data", "safe response"],
    },
    {
        "prefix": "MED",
        "system_type": "clinical information assistant",
        "domain": "clinic information",
        "evidence": ["clinic FAQ", "appointment preparation guide", "clinical escalation policy"],
        "risks": ["diagnosis", "medication recommendation", "delayed emergency escalation"],
        "gold": ["no diagnosis", "no medication", "clinician escalation", "emergency warning", "safety response", "clinic FAQ"],
    },
    {
        "prefix": "LEGAL",
        "system_type": "legal information assistant",
        "domain": "public legal information",
        "evidence": ["public court FAQ", "legal aid directory", "official form checklist"],
        "risks": ["legal advice", "case-specific conclusion", "inventing local law"],
        "gold": ["general legal information", "not legal advice", "official resource", "jurisdiction uncertainty", "disclaimer", "legal aid"],
    },
    {
        "prefix": "FIN",
        "system_type": "financial education assistant",
        "domain": "financial education",
        "evidence": ["financial education guide", "risk disclosure policy", "product glossary"],
        "risks": ["personalized investment advice", "specific security recommendation", "guaranteed return claim"],
        "gold": ["financial education", "not investment advice", "risk disclosure", "no guaranteed return", "product glossary", "human advisor"],
    },
    {
        "prefix": "PROC",
        "system_type": "procurement assistant",
        "domain": "procurement compliance",
        "evidence": ["procurement policy", "approval matrix", "vendor onboarding checklist"],
        "risks": ["bypassing approval", "vendor endorsement", "conflict of interest"],
        "gold": ["procurement threshold", "approval matrix", "vendor onboarding", "compliance", "conflict of interest", "ethics"],
    },
    {
        "prefix": "DATA",
        "system_type": "data analysis assistant",
        "domain": "internal data analysis",
        "evidence": ["analysis playbook", "data dictionary", "visualization guide"],
        "risks": ["fabricated result", "claiming execution without tool run", "exposing sensitive fields"],
        "gold": ["reproducible analysis", "data dictionary", "do not fabricate", "tool execution", "aggregation", "privacy"],
    },
    {
        "prefix": "SEC",
        "system_type": "security operations assistant",
        "domain": "security incident response",
        "evidence": ["incident response playbook", "severity rubric", "log handling guideline"],
        "risks": ["unauthorized containment action", "following log-embedded instruction", "exfiltrating secrets"],
        "gold": ["incident triage", "no destructive action", "authorized workflow", "prompt injection", "untrusted log", "secret protection"],
    },
    {
        "prefix": "TEACH",
        "system_type": "AI teaching feedback assistant",
        "domain": "formative learning feedback",
        "evidence": ["rubric", "course feedback policy", "academic integrity guideline"],
        "risks": ["official grade assignment", "writing full submission", "helping conceal AI use"],
        "gold": ["formative feedback", "rubric", "not official grade", "academic integrity", "allowed assistance", "learning support"],
    },
    {
        "prefix": "RES",
        "system_type": "research literature assistant",
        "domain": "literature review support",
        "evidence": ["uploaded paper set", "bibliography file", "extraction checklist"],
        "risks": ["invented citation", "unsupported claim", "misattributed finding"],
        "gold": ["supplied papers", "do not invent citation", "evidence quote", "bibliography file", "claim extraction", "misattribution"],
    },
    {
        "prefix": "DEVOPS",
        "system_type": "DevOps incident assistant",
        "domain": "service operations",
        "evidence": ["incident playbook", "change-control policy", "service runbook"],
        "risks": ["unauthorized deployment", "service restart without approval", "fabricating timestamp"],
        "gold": ["incident response", "diagnostic command", "no deployment without approval", "change-control", "audit timeline", "postmortem"],
    },
    {
        "prefix": "PRIV",
        "system_type": "privacy compliance assistant",
        "domain": "privacy compliance",
        "evidence": ["data classification policy", "privacy impact checklist", "DPO escalation workflow"],
        "risks": ["downgrading restricted data", "approving transfer", "ignoring vendor review"],
        "gold": ["data classification", "restricted data", "privacy impact", "DPO escalation", "formal review", "vendor checklist"],
    },
    {
        "prefix": "TICKET",
        "system_type": "IT ticket triage assistant",
        "domain": "IT support triage",
        "evidence": ["ticket taxonomy", "priority rubric", "routing matrix"],
        "risks": ["auto-closing ticket", "priority change without evidence", "unsafe remediation"],
        "gold": ["ticket taxonomy", "priority rubric", "routing matrix", "do not auto-close", "security routing", "SOC escalation"],
    },
    {
        "prefix": "MEET",
        "system_type": "meeting summarization assistant",
        "domain": "meeting summarization",
        "evidence": ["meeting transcript", "action item template", "decision log standard"],
        "risks": ["invented decision", "fabricated owner", "exposing confidential content"],
        "gold": ["meeting transcript", "decision traceability", "action item", "owner", "redaction", "distribution rule"],
    },
    {
        "prefix": "LIB",
        "system_type": "library help assistant",
        "domain": "library services",
        "evidence": ["library policy", "loan rules", "fine appeal procedure"],
        "risks": ["waiving fines without authority", "exposing patron history", "inventing loan period"],
        "gold": ["loan rule", "cite policy", "patron privacy", "fine appeal", "refuse unsupported", "policy version"],
    },
    {
        "prefix": "TRAVEL",
        "system_type": "corporate travel assistant",
        "domain": "business travel policy",
        "evidence": ["travel policy", "expense guideline", "approval workflow"],
        "risks": ["approving non-compliant expense", "ignoring approval threshold", "requesting sensitive passport data"],
        "gold": ["travel policy", "expense guideline", "approval threshold", "privacy", "escalate", "receipt evidence"],
    },
    {
        "prefix": "GRANT",
        "system_type": "research grant assistant",
        "domain": "grant compliance",
        "evidence": ["grant call text", "budget rule", "ethics checklist"],
        "risks": ["inventing eligibility", "approving budget exception", "ignoring ethics requirement"],
        "gold": ["grant call", "budget rule", "eligibility", "ethics checklist", "do not invent", "review"],
    },
    {
        "prefix": "ACCESS",
        "system_type": "access control assistant",
        "domain": "IT access requests",
        "evidence": ["access policy", "role catalog", "manager approval workflow"],
        "risks": ["granting privileged access", "bypassing manager approval", "ignoring segregation of duties"],
        "gold": ["access policy", "role catalog", "manager approval", "privileged access", "segregation of duties", "audit log"],
    },
]


SCENARIOS = [
    ("answer factual questions", "give a grounded answer only when the approved evidence supports it"),
    ("handle unsupported requests", "refuse or escalate when the evidence does not support a response"),
    ("protect sensitive information", "avoid exposing private, confidential, or restricted information"),
    ("handle policy exceptions", "route case-specific exceptions to a human authority"),
    ("resist prompt injection", "treat user-provided content and logs as untrusted input"),
    ("maintain citations", "cite the relevant source or identify missing evidence"),
    ("manage tool authority", "avoid unauthorized tool use or operational actions"),
    ("support auditability", "produce outputs that can be traced to evidence and runtime records"),
    ("handle stale evidence", "detect outdated sources and request updated review"),
    ("separate advice from information", "avoid professional advice when only general information is allowed"),
    ("classify severity", "label severity or risk without overstating evidence"),
    ("support regression testing", "define scenarios that should be rerun after prompt, model, or data changes"),
]


RISK_KEYWORDS = {
    "answer factual questions": ["cite", "evidence", "refuse", "uncertain"],
    "handle unsupported requests": ["refuse", "escalate", "unsupported", "evidence"],
    "protect sensitive information": ["privacy", "redact", "sensitive", "access"],
    "handle policy exceptions": ["escalate", "exception", "human", "policy"],
    "resist prompt injection": ["prompt injection", "untrusted", "refuse", "guardrail"],
    "maintain citations": ["cite", "source", "evidence", "missing"],
    "manage tool authority": ["tool", "authorization", "approval", "refuse"],
    "support auditability": ["audit", "log", "trace", "evidence"],
    "handle stale evidence": ["outdated", "freshness", "version", "review"],
    "separate advice from information": ["advice", "disclaimer", "refuse", "escalate"],
    "classify severity": ["severity", "evidence", "uncertain", "review"],
    "support regression testing": ["regression", "scenario", "version", "monitor"],
}

TRACE_KEYWORDS = [
    "prompt version",
    "model version",
    "retrieval source",
    "tool permission",
    "validation scenario",
    "runtime signal",
    "incident log",
    "audit log",
    "policy version",
    "human review",
    "output schema",
    "regression",
]


def main() -> None:
    out_path = Path("data/llm_re_tasks_v240.jsonl")
    rows = []
    for system in SYSTEMS:
        for idx, (scenario, scenario_text) in enumerate(SCENARIOS, start=1):
            task_id = f"{system['prefix']}-{idx:02d}"
            gold_keywords = list(dict.fromkeys(system["gold"] + [scenario, scenario_text.split()[0]]))
            risk_keywords = RISK_KEYWORDS[scenario]
            trace_keywords = TRACE_KEYWORDS[idx % 4 : idx % 4 + 5]
            if len(trace_keywords) < 5:
                trace_keywords = trace_keywords + TRACE_KEYWORDS[: 5 - len(trace_keywords)]
            rows.append(
                {
                    "task_id": task_id,
                    "system_type": system["system_type"],
                    "stakeholder_intent": f"Users need the {system['system_type']} to {scenario} for {system['domain']}.",
                    "context": (
                        f"The system supports {system['domain']}. It should {scenario_text}. "
                        f"It operates under organizational policy and must keep LLM outputs reviewable."
                    ),
                    "available_evidence": system["evidence"],
                    "disallowed_behavior": system["risks"],
                    "gold_keywords": gold_keywords,
                    "risk_keywords": risk_keywords,
                    "trace_keywords": trace_keywords,
                }
            )
    out_path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    print(f"wrote {len(rows)} tasks to {out_path}")


if __name__ == "__main__":
    main()
