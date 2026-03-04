# Coverage Analysis Report for EquaCode (Paper ID: 2512.23173)

## Paper Algorithm Summary

EquaCode is a jailbreak attack that combines two key strategies:

1. **Equationization**: Transforms a malicious query into a mathematical equation format: `Subject (B) + Tool (C) + Steps (unknown) = MaliciousQuery (A)`
2. **Code Encapsulation**: Embeds the equation into a Python `Solver` class context, framing the task as code completion rather than direct harmful content generation

The attack leverages the synergy between mathematical abstraction and programming context to bypass safety filters that focus on natural language or single-domain detection.

**Key Components**:
- Mathematical equation transformation (B + C + x = A)
- Python Solver class template with initialization, methods, and solve logic
- Specific instructions to prevent refusal (forbidden words, output format constraints)
- Template-based prompt construction with parameter substitution

---

## Coverage Analysis - Iteration 1

### Coverage Table

| Paper Section/Step | Algorithm Description | Implementation Location | Coverage Status | Notes |
|-------------------|----------------------|------------------------|-----------------|-------|
| Equation Transformation | Define equation: Subject + Tool + Steps = Goal | `EQUACODE_TEMPLATE` lines 46-47 | ✅ | Equation format embedded in template text |
| Subject Parameter (B) | The agent performing the action (default: "Mark") | `PARAMETERS["subject"]` lines 23-29 | ✅ | Exposed as configurable parameter with default "Mark" |
| Tool Parameter (C) | The method used (default: "real tools") | `PARAMETERS["tool"]` lines 30-36 | ✅ | Exposed as configurable parameter with default "real tools" |
| Code Encapsulation | Wrap equation in Python Solver class | `EQUACODE_TEMPLATE` lines 51-81 | ✅ | Complete Solver class structure with __init__, person(), tool(), solve() methods |
| Prompt Construction | Replace [INSERT PROMPT HERE] with goal | `generate_attack()` lines 100-104 | ✅ | Uses .format() to substitute goal, subject, and tool |
| Refusal Prevention Instructions | Forbidden words list and output format constraints | `EQUACODE_TEMPLATE` lines 83-90 | ✅ | Exact instructions from reference repo included |
| Template Fidelity | Match reference repository template exactly | Entire `EQUACODE_TEMPLATE` | ✅ | Template copied verbatim from `Equacode/scripts/attack.py` (equacoder variable) |

### Coverage Statistics
- **Total Components**: 7
- **Fully Covered**: 7
- **Partial**: 0
- **Missing**: 0
- **Coverage**: 100%

### Identified Issues
None. All algorithmic components from the paper and reference implementation are fully covered.

### Required Modifications
None. Implementation is complete and matches the reference repository exactly.

---

## Coverage Analysis - Iteration 2

### Changes Applied
- Fixed PAPER identifier from full title string to planned value `"2512.23173"` (line 20)

### Coverage Table (Updated)

|| Paper Section/Step | Algorithm Description | Implementation Location | Coverage Status | Notes |
||-------------------|----------------------|------------------------|-----------------|-------|
|| Framework Integration | NAME set to `equacode_gen` | `NAME` line 19 | ✅ | Matches planned NAME |
|| Framework Integration | PAPER identifier set to `2512.23173` | `PAPER` line 20 | ✅ | **FIXED**: Now uses planned ID value |
|| Equation Transformation | Define equation: Subject + Tool + Steps = Goal | `EQUACODE_TEMPLATE` lines 46-47 | ✅ | Equation format embedded in template text |
|| Subject Parameter (B) | The agent performing the action (default: "Mark") | `PARAMETERS["subject"]` lines 23-29 | ✅ | Exposed as configurable parameter with default "Mark" |
|| Tool Parameter (C) | The method used (default: "real tools") | `PARAMETERS["tool"]` lines 30-36 | ✅ | Exposed as configurable parameter with default "real tools" |
|| Code Encapsulation | Wrap equation in Python Solver class | `EQUACODE_TEMPLATE` lines 51-81 | ✅ | Complete Solver class structure with __init__, person(), tool(), solve() methods |
|| Prompt Construction | Replace [INSERT PROMPT HERE] with goal | `generate_attack()` lines 100-104 | ✅ | Uses .format() to substitute goal, subject, and tool |
|| Refusal Prevention Instructions | Forbidden words list and output format constraints | `EQUACODE_TEMPLATE` lines 83-90 | ✅ | Exact instructions from reference repo included |

### Coverage Statistics
- **Total Components**: 8
- **Fully Covered**: 8
- **Partial**: 0
- **Missing**: 0
- **Coverage**: 100%

### Identified Issues
None. All issues from Iteration 1 audit have been resolved.

### Required Modifications
None. Implementation now achieves 100% fidelity.

---

## Final Summary

The EquaCode attack implementation achieves 100% coverage of the paper's algorithm and 100% fidelity to the implementation plan:

1. ✅ **Framework Integration**: NAME and PAPER metadata correctly set per plan
2. ✅ **Equation Transformation**: Mathematical equation format (B + C + x = A) is embedded in the template
3. ✅ **Parameterization**: Subject and Tool are exposed as configurable parameters with correct defaults
4. ✅ **Code Encapsulation**: Complete Python Solver class structure with all required methods
5. ✅ **Prompt Construction**: Proper string formatting with goal, subject, and tool substitution
6. ✅ **Refusal Prevention**: All instructions to prevent model refusal are included
7. ✅ **Template Fidelity**: Exact match with reference repository's `equacoder` template

The implementation is a faithful translation of the paper's algorithm with no simplifications or omissions. The attack is purely template-based (no LLM calls required during generation), making it efficient and deterministic.
