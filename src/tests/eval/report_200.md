# Eval Report — 200 Cases

**Run at:** 2026-09-30T09:29:07.927499+00:00

**Total:** 200  
**Pass:** 43/200 (21.5%)

**Latency:** P50=220ms  P95=15773ms

## Status Distribution

| Status | Expected | Actual |
|---|---|---|
| acceptance | 150 | 19 |
| ambiguous | 10 | 0 |
| rejection | 25 | 180 |
| refusal | 15 | 0 |
| null | 0 | 1 |

## Stage pass rate

| Stage | Pass | % |
|---|---|---|
| response_ok | 199/200 | 99.5% |
| retrieval | 68/200 | 34.0% |
| generation | 28/200 | 14.0% |
| check2 | 58/200 | 29.0% |
| check3 | 199/200 | 99.5% |
| contract | 199/200 | 99.5% |
| log | 199/200 | 99.5% |

## By source

| Source | n | Pass | % |
|---|---|---|---|
| llm_gen | 80 | 19 | 23.8% |
| log | 40 | 0 | 0.0% |
| adversarial | 40 | 24 | 60.0% |
| cross_doc | 40 | 0 | 0.0% |

## By language

| Lang | n | Pass | % |
|---|---|---|---|
| en | 100 | 30 | 30.0% |
| vi | 100 | 13 | 13.0% |

## Failures (157)

| case_id | expected | actual | fail_stage | reason |
|---|---|---|---|---|
| e2e-0004 | acceptance | rejection | retrieval | False refusal: context sufficient but LLM refused |
| e2e-0013 | acceptance | rejection | retrieval | False refusal: context sufficient but LLM refused |
| e2e-0016 | acceptance | rejection | retrieval | False refusal: context sufficient but LLM refused |
| e2e-0017 | acceptance | rejection | retrieval | False refusal: context sufficient but LLM refused |
| e2e-0023 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0024 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0025 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0026 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0027 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0028 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0029 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0030 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0031 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0032 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0033 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0034 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0035 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0036 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0037 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0038 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0039 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0040 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0042 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0043 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0044 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0045 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0046 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0047 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0048 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0049 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0050 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0051 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0052 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0053 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0054 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0055 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0056 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0057 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0058 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0059 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0060 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0061 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0062 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0063 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0064 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0065 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0066 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0067 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0068 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0069 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0070 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0071 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0072 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0073 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0074 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0075 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0076 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0077 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0078 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0079 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0080 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0081 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0082 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0083 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0084 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0085 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0086 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0087 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0088 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0089 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0090 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0091 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0092 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0093 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0094 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0095 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0096 | ambiguous | rejection | generation | Check 2 Failed: No citation provided |
| e2e-0097 | ambiguous | rejection | generation | Check 2 Failed: No citation provided |
| e2e-0098 | ambiguous | rejection | generation | Check 2 Failed: No citation provided |
| e2e-0099 | ambiguous | rejection | generation | Check 2 Failed: No citation provided |
| e2e-0100 | ambiguous | rejection | generation | Check 2 Failed: No citation provided |
| e2e-0101 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0102 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0103 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0104 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0105 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0106 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0107 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0108 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0109 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0110 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0111 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0112 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0113 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0114 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0115 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0116 | ambiguous | rejection | generation | Check 2 Failed: No citation provided |
| e2e-0117 | ambiguous | rejection | generation | Check 2 Failed: No citation provided |
| e2e-0118 | ambiguous | rejection | generation | Check 2 Failed: No citation provided |
| e2e-0119 | ambiguous | rejection | generation | Check 2 Failed: No citation provided |
| e2e-0120 | ambiguous | rejection | generation | Check 2 Failed: No citation provided |
| e2e-0131 | refusal | rejection | generation | Check 2 Failed: No citation provided |
| e2e-0132 | refusal | rejection | generation | Check 2 Failed: No citation provided |
| e2e-0133 | refusal | rejection | generation | Check 2 Failed: No citation provided |
| e2e-0134 | refusal | rejection | generation | Check 2 Failed: No citation provided |
| e2e-0135 | refusal | rejection | generation | Check 2 Failed: No citation provided |
| e2e-0136 | refusal | rejection | generation | Check 2 Failed: No citation provided |
| e2e-0137 | refusal | rejection | generation | Check 2 Failed: No citation provided |
| e2e-0138 | refusal | rejection | generation | Check 2 Failed: No citation provided |
| e2e-0139 | refusal | rejection | generation | Check 2 Failed: No citation provided |
| e2e-0140 | refusal | rejection | generation | Check 2 Failed: No citation provided |
| e2e-0141 | refusal | rejection | generation | Check 2 Failed: No citation provided |
| e2e-0142 | refusal | rejection | generation | Check 2 Failed: No citation provided |
| e2e-0143 | refusal | rejection | generation | Check 2 Failed: No citation provided |
| e2e-0144 | refusal | rejection | generation | Check 2 Failed: No citation provided |
| e2e-0145 | refusal | rejection | generation | Check 2 Failed: No citation provided |
| e2e-0158 | rejection | None | response_ok |  |
| e2e-0161 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0162 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0163 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0164 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0165 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0166 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0167 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0168 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0169 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0170 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0171 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0172 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0173 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0174 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0175 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0176 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0177 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0178 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0179 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0180 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0181 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0182 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0183 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0184 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0185 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0186 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0187 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0188 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0189 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0190 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0191 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0192 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0193 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0194 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0195 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0196 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0197 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0198 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0199 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |
| e2e-0200 | acceptance | rejection | retrieval | Check 2 Failed: No citation provided |