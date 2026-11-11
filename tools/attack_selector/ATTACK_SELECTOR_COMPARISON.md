## Attack Selector Comparison

This document summarizes results for four attack-selection policies evaluated on representative JBB queries from the JBB dataset.

- **Settings (unless otherwise noted):**
  - Up to **10 attacks per query**
  - **Attack concurrency:** 1  
  - **Query concurrency:** 4  

The selectors compared:

- **Rank Centrality** (`asr_cost`)
- **ASR Sort** (`asr_sort`)
- **Thompson Sampling** (`ts`)
- **LLM-guided Sort (GPT-4o)** (`llm_select`)

---

## Inspect Log Generation and Viewing

- Inspect is a framework for large language model evaluations created by the 
[AI Security Institute, UK. (2024). *Inspect AI: Framework for Large Language Model Evaluations*.](https://github.com/UKGovernmentBEIS/inspect_ai)

- Install (one-time):
  ```bash
  pip install inspect-ai
  # or inside this repo's virtualenv:
  uv pip install inspect-ai
  ```
- Convert selector runs to Inspect logs:
  ```bash
  python tools/attack_selector/batch_convert_selector_results.py
  # outputs to results/selector_viz/<dataset>/*.eval
  ```
- Convert attack runs (only *_comprehensive folders) grouped by victim model:
  ```bash
  python tools/attack_selector/batch_convert_attack_results.py
  # outputs to results/attack_eval_by_model/<model>/*.eval
  ```
- View in Inspect (either root works):
  ```bash
  inspect view --log-dir results/attack_eval_by_model
  # or
  inspect view --log-dir results/selector_viz
  ```
- Example Inspect view (replace with your screenshot):
  ![Inspect sample view](inspect_example_screenshot.png)

---
### Experimental Setup

#### Inputs

*   **ASR/Cost results:** Empirical cost with attack success rate (ASR) data as a helper in ranking strategies.
            
*   **Query selection:** Representative queries covering from the JBB dataset with each assign to a victim model.
    
*   **Run settings:** Up to 10 attacks per query; attack concurrency 1; query concurrency 4.

#### Selector Names and Explanations

*   **Rank Centrality** (`asr_cost`):  
    Uses a Rank-Centrality Markov chain that favors higher ASR and lower empirical token cost.
    
*   **ASR Sort** (`asr_sort`):  
    Ranks candidates by history ASR only.
    
*   **Thompson Sampling** (`ts`):  
    Samples from per-attack posteriors (empirical ASR prior with optional decay) and picks the highest draw.
    
*   **LLM-guided Sort (GPT-4o)** (`llm_select`):  
    Prompts an external LLM to rank attacks based on query context, ASR, cost, and template descriptions.


---

## JBB sample queries (mixed victims)

| Selector | Successful/Total | Success rate | Avg attempts → success (successes) | Median attempts → success (successes) | Avg total attempts (all) | Median total attempts (all) | Prompt tokens (attack/llm_sort) | Completion tokens (attack/llm_sort) | Total tokens (attack/llm_sort) | Reasoning tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Rank Centrality | 30/32 | 93.75% | 2.00 | 1 | 2.50 | 1 | 85,201 | 73,787 | 158,988 | 841 |
| ASR Sort | 30/32 | 93.75% | 1.70 | 1 | 2.22 | 1 | 80,841 | 78,682 | 159,523 | 302 |
| Thompson Sampling | 30/32 | 93.75% | 1.90 | 1 | 2.41 | 1 | 85,822 | 66,895 | 152,717 | 430 |
| LLM-guided Sort (GPT-4o) | 30/32 | 93.75% | 1.80 | 1 | 2.31 | 1 | 95,246 / 215,830 | 79,701 / 11,896 | 174,947 / 227,726 | 302 |

| Selector | @1 | @3 | @5 | @10 |
|---|---:|---:|---:|---:|
| Rank Centrality | 53.13% | 81.25% | 90.63% | 93.75% |
| ASR Sort | 62.50% | 81.25% | 93.75% | 93.75% |
| Thompson Sampling | 53.13% | 81.25% | 90.63% | 93.75% |
| LLM-guided Sort (GPT-4o) | 62.50% | 81.25% | 90.63% | 93.75% |

Regenerate the plot:

```bash
python3 tools/attack_selector/scripts/plot_success_at_k.py \
    --input results/jbb_sample_queries/selector=asr_sort__max=10/attack_selector_results.json \
            results/jbb_sample_queries/selector=asr_cost__max=10/attack_selector_results.json \
            results/jbb_sample_queries/selector=llm_select__max=10/attack_selector_results.json \
            results/jbb_sample_queries/selector=ts__prior=0.15__kmax=100__decay=1__lambda=0__dg=0__dz=0__ps=100__max=10/attack_selector_results.json \
    --label asr_sort --label rank_centrality --label llm_select --label thompson_sampling\
    --metric rate \
    --title "Success@K (rate) — JBB sample queries(Random victims)" \
    --output tools/attack_selector/ploted_results/success_at_k_rate_combined_random_victim_max10.png
```

![Success@K (rate) — Combined (max=10)](ploted_results/success_at_k_rate_combined_random_victim_max10.png)

---

## GPT-OSS-120B (fixed victim)

| Selector | Successful/Total | Success rate | Avg attempts → success (successes) | Median attempts → success (successes) | Avg total attempts (all) | Median total attempts (all) | Prompt tokens (attack/llm_sort) | Completion tokens (attack/llm_sort) | Total tokens (attack/llm_sort) | Reasoning tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Rank Centrality | 24/32 | 75.00% | 2.88 | 1 | 4.66 | 1.5 | 80,634 | 95,422 | 176,056 | 59,593 |
| ASR Sort | 22/32 | 68.75% | 2.59 | 1 | 4.91 | 3 | 95,517 | 113,792 | 209,309 | 75,583 |
| Thompson Sampling | 21/32 | 65.63% | 3.05 | 1 | 5.44 | 5 | 97,623 | 133,173 | 230,796 | 83,885 |
| LLM-guided Sort (GPT-4o) | 26/32 | 81.25% | 2.77 | 1 | 4.13 | 1 | 62,136 / 211,477 | 82,170 / 11,798 | 144,306 / 223,275 | 55,046 |

| Selector | @1 | @3 | @5 | @10 |
|---|---:|---:|---:|---:|
| Rank Centrality | 50.00% | 53.13% | 56.25% | 75.00% |
| ASR Sort | 43.75% | 53.13% | 56.25% | 68.75% |
| Thompson Sampling | 34.38% | 40.63% | 53.13% | 65.63% |
| LLM-guided Sort (GPT-4o) | 53.13% | 59.38% | 65.63% | 81.25% |

Regenerate the plot:

```bash
python3 tools/attack_selector/scripts/plot_success_at_k.py \
    --input results/jbb_sample_queries_gpt_oss/selector=asr_sort__max=10/attack_selector_results.json \
            results/jbb_sample_queries_gpt_oss/selector=asr_cost__max=10/attack_selector_results.json \
            results/jbb_sample_queries_gpt_oss/selector=llm_select__max=10/attack_selector_results.json \
            results/jbb_sample_queries_gpt_oss/selector=ts__prior=0.15__kmax=100__decay=1__lambda=0__dg=0__dz=0__ps=100__max=10/attack_selector_results.json \
    --label asr_sort --label rank_centrality --label llm_select --label thompson_sampling\
    --metric rate \
    --title "Success@K (rate) — JBB sample queries(GPT-OSS-120B)" \
    --output tools/attack_selector/ploted_results/success_at_k_rate_gpt_oss_120b_max10.png
```

![Success@K (rate) — gpt_oss_120b (max=10)](ploted_results/success_at_k_rate_gpt_oss_120b_max10.png)