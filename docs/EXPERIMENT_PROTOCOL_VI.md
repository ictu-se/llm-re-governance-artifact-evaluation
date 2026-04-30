# Protocol thuc nghiem moi: RE for LLM-Based Software Systems

## Muc tieu

Tao mot thuc nghiem moi, khong dung lai bat ky du lieu/kich ban/ket qua nao cua bai use-case recovery cu. Thuc nghiem nay danh gia kha nang cua LLM local trong viec tao artifact requirements engineering cho cac he thong phan mem co LLM la thanh phan chinh.

## Khac voi bai cu

- Bai cu: khoi phuc user-goal use case tu source code evidence cua 16 repository.
- Bai moi: tao capability requirement, validation scenarios, traceability links va runtime governance cho LLM-based systems tu stakeholder intent va system context.
- Khong dung lai `use_case_ground_truth_v1.csv`, `subfunction_ground_truth_v1.csv`, code paths, API paths, model-family results, error taxonomy, hay bat ky bang/so lieu nao cua bai cu.

## Don vi task

Ban mo rong hien co 32 task, phu 16 loai he thong LLM-based: academic advising, HR policy, code review, customer support, clinical information, legal information, financial education, procurement, data analysis, security operations, teaching feedback, research literature, DevOps incident, privacy compliance, IT ticket triage, and meeting summarization.

Moi task gom:

- `system_type`: loai he thong LLM-based.
- `stakeholder_intent`: intent tu stakeholder.
- `context`: boi canh nghiep vu va rang buoc.
- `available_evidence`: nguon bang chung cho phep dung.
- `disallowed_behavior`: hanh vi khong chap nhan.
- `gold`: artifact chuan do nguoi thiet ke tao, gom:
  - capability requirement;
  - source constraints;
  - failure behavior;
  - validation scenarios;
  - traceability links;
  - runtime monitoring signals.

## Dau ra model

Model phai tra ve JSON:

```json
{
  "capability_requirement": "...",
  "source_constraints": ["..."],
  "failure_behavior": ["..."],
  "validation_scenarios": ["..."],
  "traceability_links": ["..."],
  "runtime_signals": ["..."]
}
```

## Metric pilot

1. `parse_ok`: output co parse duoc JSON khong.
2. `slot_coverage`: ty le 6 slot co non-empty value.
3. `gold_keyword_recall`: ty le keyword bat buoc trong gold duoc nhac toi.
4. `risk_control_recall`: ty le control lien quan refusal/escalation/privacy/citation duoc nhac toi.
5. `traceability_signal_recall`: ty le artifact trace/runtime signal duoc nhac toi.

## Model pilot

Chay nhanh 3 model local:

- `llama3.2:3b`
- `qwen2.5:3b`
- `qwen2.5-coder:3b`

Sau pilot, final-analysis package da mo rong sang 15 completed model runs, including Qwen2.5, Qwen2.5-Coder, Qwen3 8B/14B, Llama, Granite-Code, CodeGemma, and StarCoder2. `qwen3:4b` khong nam trong released final package.

## Cach dung ket qua trong bai

Ket qua pilot chi nen duoc trinh bay nhu feasibility/pilot evaluation cho framework, khong phai leaderboard. Neu muon thanh bai empirical manh, can mo rong:

- 240 tasks;
- 20 system types;
- 7 model families;
- deterministic automated rubric plus independent human review workflow;
- ablation prompt with/without traceability schema.
