"""
Build all three quantum computing notebooks using nbformat.
Run: python3 build_qc_notebooks.py
"""
import nbformat as nbf
from pathlib import Path

OUT = Path(__file__).parent

def md(src): return nbf.v4.new_markdown_cell(src)
def code(src): return nbf.v4.new_code_cell(src)

# ═══════════════════════════════════════════════════════════════════════════════
# NOTEBOOK 1: DEUTSCH & DEUTSCH-JOZSA
# ═══════════════════════════════════════════════════════════════════════════════

nb1 = nbf.v4.new_notebook()
nb1.cells = [

md("""# Deutsch & Deutsch-Jozsa Algorithm
### Quantum advantage with a single query

**Course:** UCL Quantum Computing · **Prerequisites:** qubits, Hadamard, phase kickback

---

## The Problem: Constant or Balanced?

You are given a black-box function $f:\\{0,1\\}^n \\to \\{0,1\\}$ — an **oracle** you can query.
The function is promised to be either:
- **Constant**: $f(x) = 0$ for all $x$, or $f(x) = 1$ for all $x$.
- **Balanced**: exactly half the inputs map to 0 and half to 1.

**Goal**: determine which case you are in, using as few queries as possible.

**Classical cost**: in the worst case you must query $2^{n-1}+1$ inputs — more than half.
**Quantum cost**: **one query**, always. This is the first proven quantum speedup over classical computation.
"""),

md("""## The Oracle Model

The quantum oracle is a unitary $U_f$ acting on an input register and an ancilla qubit:

$$U_f |x\\rangle |y\\rangle = |x\\rangle |y \\oplus f(x)\\rangle$$

where $\\oplus$ is XOR. The oracle encodes $f(x)$ into the ancilla without disturbing the input.
If we set the ancilla to $|-\\rangle = \\frac{1}{\\sqrt{2}}(|0\\rangle - |1\\rangle)$, something special happens — **phase kickback**:

$$U_f |x\\rangle |-\\rangle = (-1)^{f(x)} |x\\rangle |-\\rangle$$

The $(-1)^{f(x)}$ phase is "kicked back" onto the input register. The ancilla is unchanged.
This is the central trick: the oracle writes its answer as a **phase**, not a bit-flip.
"""),

md("""## Deutsch's Algorithm (n = 1)

**Circuit:**

$$|0\\rangle|1\\rangle \\xrightarrow{H \\otimes H} \\frac{1}{2}(|0\\rangle+|1\\rangle)(|0\\rangle-|1\\rangle) \\xrightarrow{U_f} \\frac{(-1)^{f(0)}}{2}\\bigl(|0\\rangle + (-1)^{f(0)\\oplus f(1)}|1\\rangle\\bigr)(|0\\rangle-|1\\rangle) \\xrightarrow{H\\otimes I} \\cdots$$

After the final Hadamard on qubit 0:
- **Constant** ($f(0) = f(1)$): $(-1)^{f(0)} \\oplus (-1)^{f(1)} = $ same phase → qubit 0 is $|0\\rangle$
- **Balanced** ($f(0) \\neq f(1)$): opposite phases → qubit 0 is $|1\\rangle$

**One query determines everything via interference.**
"""),

code("""from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams.update({'figure.dpi': 120, 'font.size': 11})

simulator = AerSimulator()
print("Qiskit + Aer ready ✓")
"""),

code("""# ── Oracle builder ─────────────────────────────────────────────────
def deutsch_oracle(oracle_type):
    \"\"\"
    Returns a 2-qubit circuit implementing the Deutsch oracle.
    Qubit 0 = input, qubit 1 = ancilla.
    oracle_type: 'constant_0' | 'constant_1' | 'balanced_id' | 'balanced_not'
    \"\"\"
    qc = QuantumCircuit(2, name=f"Oracle ({oracle_type})")
    if oracle_type == 'constant_0':
        pass                          # f(x) = 0: do nothing
    elif oracle_type == 'constant_1':
        qc.x(1)                       # f(x) = 1: flip ancilla
    elif oracle_type == 'balanced_id':
        qc.cx(0, 1)                   # f(x) = x: CNOT
    elif oracle_type == 'balanced_not':
        qc.cx(0, 1)                   # f(x) = NOT x: CNOT + X
        qc.x(1)
    return qc

# ── Deutsch circuit builder ────────────────────────────────────────
def deutsch_circuit(oracle_type):
    qc = QuantumCircuit(2, 1)

    # Initialise ancilla to |1⟩
    qc.x(1)
    qc.barrier()

    # Apply H to both qubits  →  |+⟩|−⟩
    qc.h([0, 1])
    qc.barrier()

    # Apply oracle  →  phase kickback writes f into phase
    oracle = deutsch_oracle(oracle_type)
    qc.compose(oracle, inplace=True)
    qc.barrier()

    # Apply H to input qubit  →  interference reveals constant/balanced
    qc.h(0)
    qc.barrier()

    # Measure input qubit
    qc.measure(0, 0)
    return qc

# Draw all four oracles
for otype in ['constant_0', 'constant_1', 'balanced_id', 'balanced_not']:
    qc = deutsch_circuit(otype)
    print(f"\\n─── Oracle: {otype} ───")
    print(qc.draw('text'))
"""),

code("""# ── Run all four oracles ──────────────────────────────────────────
fig, axes = plt.subplots(1, 4, figsize=(14, 3.5))
oracle_types = ['constant_0', 'constant_1', 'balanced_id', 'balanced_not']

for ax, otype in zip(axes, oracle_types):
    qc = deutsch_circuit(otype)
    t_qc = transpile(qc, simulator)
    result = simulator.run(t_qc, shots=1024).result()
    counts = result.get_counts()

    is_constant = 'constant' in otype
    ax.bar(list(counts.keys()), list(counts.values()),
           color='#111' if not is_constant else '#666', width=0.4)
    ax.set_title(f"{otype}\\n→ {'CONSTANT' if is_constant else 'BALANCED'}", fontsize=9)
    ax.set_xlabel("Measurement")
    ax.set_ylabel("Counts")
    ax.set_ylim(0, 1100)
    ax.axhline(1024, color='red', lw=0.5, ls='--', alpha=0.4)

plt.suptitle("Deutsch Algorithm: 0 = constant, 1 = balanced", fontsize=12, y=1.02)
plt.tight_layout()
plt.savefig('deutsch_results.png', dpi=120, bbox_inches='tight')
plt.show()
print("\\nInterpretation:")
print("  Measure |0⟩ → function is CONSTANT")
print("  Measure |1⟩ → function is BALANCED")
print("  Always deterministic in 1 query.")
"""),

md("""## Deutsch-Jozsa Algorithm (n qubits)

The generalisation to $n$ input qubits is direct. The circuit is:

$$|0\\rangle^{\\otimes n}|1\\rangle \\xrightarrow{H^{\\otimes(n+1)}} \\frac{1}{\\sqrt{2^n}}\\sum_{x=0}^{2^n-1}|x\\rangle |-\\rangle \\xrightarrow{U_f} \\frac{1}{\\sqrt{2^n}}\\sum_x (-1)^{f(x)}|x\\rangle |-\\rangle \\xrightarrow{H^{\\otimes n}} \\cdots$$

After the final layer of Hadamards, the amplitude of the all-zeros state $|0\\rangle^{\\otimes n}$ is:

$$\\alpha_{0\\ldots 0} = \\frac{1}{2^n}\\sum_{x=0}^{2^n-1}(-1)^{f(x)}$$

- **Constant**: all terms have the same sign → $|\\alpha_{0\\ldots0}|^2 = 1$. We measure $|0\\rangle^{\\otimes n}$ with certainty.
- **Balanced**: half are $+1$, half are $-1$ → they cancel completely, $\\alpha_{0\\ldots 0} = 0$. We **never** measure all zeros.

One query, no probability of error. Classical randomised algorithms need $O(1)$ queries with bounded error, but Deutsch-Jozsa is deterministic.
"""),

code("""# ── Deutsch-Jozsa circuit for n input qubits ────────────────────────
def dj_oracle(oracle_type, n):
    \"\"\"
    oracle_type: 'constant_0' | 'constant_1' | 'balanced'
    n: number of input qubits  (ancilla is qubit n)
    \"\"\"
    qc = QuantumCircuit(n + 1, name=f"DJ Oracle ({oracle_type}, n={n})")

    if oracle_type == 'constant_0':
        pass                                    # f = 0 everywhere
    elif oracle_type == 'constant_1':
        qc.x(n)                                 # f = 1 everywhere
    elif oracle_type == 'balanced':
        # XOR of all input bits → exactly balanced
        for i in range(n):
            qc.cx(i, n)
    return qc

def dj_circuit(oracle_type, n=3):
    qc = QuantumCircuit(n + 1, n)

    # |0...0⟩|1⟩
    qc.x(n)
    qc.barrier()

    # H on all qubits
    qc.h(range(n + 1))
    qc.barrier()

    # Oracle
    qc.compose(dj_oracle(oracle_type, n), inplace=True)
    qc.barrier()

    # H on input register
    qc.h(range(n))
    qc.barrier()

    # Measure input qubits
    qc.measure(range(n), range(n))
    return qc

# Show 3-qubit circuit
print("Deutsch-Jozsa (n=3, balanced oracle):")
print(dj_circuit('balanced', n=3).draw('text'))
"""),

code("""# ── Run DJ for n = 3 ─────────────────────────────────────────────
n = 3
fig, axes = plt.subplots(1, 3, figsize=(12, 3.5))

for ax, otype in zip(axes, ['constant_0', 'constant_1', 'balanced']):
    qc = dj_circuit(otype, n=n)
    t_qc = transpile(qc, simulator)
    result = simulator.run(t_qc, shots=1024).result()
    counts = result.get_counts()
    label = "CONSTANT" if 'constant' in otype else "BALANCED"

    ax.bar(list(counts.keys()), list(counts.values()),
           color='#111' if 'balanced' in otype else '#888', width=0.6)
    ax.set_title(f"Oracle: {otype}\\n→ {label}", fontsize=9)
    ax.set_xlabel("Measurement outcome")
    ax.set_ylabel("Counts")
    ax.set_ylim(0, 1100)

plt.suptitle("Deutsch-Jozsa (n=3): constant → |000⟩, balanced → never |000⟩", fontsize=11, y=1.02)
plt.tight_layout()
plt.savefig('dj_results.png', dpi=120, bbox_inches='tight')
plt.show()
print("\\nConstant: always measure |000⟩")
print("Balanced: never measure |000⟩  (all amplitudes cancel)")
"""),

code("""# ── DJ scales to any n — show that it still uses one query ───────────
print("Query count comparison:\\n")
print(f"{'n (input bits)':>18} | {'Classical (worst)':>18} | {'Quantum':>8}")
print("-" * 52)
for n in [1, 2, 3, 4, 5, 8, 10, 20]:
    classical = 2**(n-1) + 1
    print(f"{n:>18} | {classical:>18,} | {'1':>8}")
"""),

md("""## Key Takeaways

1. **Phase kickback** is the core quantum trick: set the ancilla to $|-\\rangle$, and the oracle writes $f(x)$ as a phase on the input.
2. **Interference** does the computation: the final Hadamard layer adds/cancels amplitudes to give a deterministic answer.
3. **Exponential separation** in query complexity: classical needs $O(2^n)$ queries; quantum needs exactly 1.
4. **Limitation**: Deutsch-Jozsa is artificial. Real-world problems are not promised to be exactly constant or balanced. Bernstein-Vazirani (next step) and Simon's problem give more practical separations.
5. The same phase kickback idea appears in **Grover** (next notebook) and **Shor** (following notebook).
"""),
]

# ═══════════════════════════════════════════════════════════════════════════════
# NOTEBOOK 2: GROVER'S ALGORITHM
# ═══════════════════════════════════════════════════════════════════════════════

nb2 = nbf.v4.new_notebook()
nb2.cells = [

md("""# Grover's Search Algorithm
### $O(\\sqrt{N})$ quantum search over $N$ unstructured items

**Course:** UCL Quantum Computing · **Prerequisites:** Hadamard, phase kickback, Deutsch-Jozsa

---

## The Search Problem

Given an unstructured database of $N = 2^n$ items, find the one marked item.
There is no structure to exploit — you can only query "is this item the target?".

| | Queries needed |
|---|---|
| Classical (deterministic) | $N$ worst case |
| Classical (randomised) | $N/2$ on average |
| **Grover's algorithm** | $\\approx \\frac{\\pi}{4}\\sqrt{N}$ — provably optimal for quantum |

For $N = 2^{20} \\approx 10^6$: classical needs 500,000 queries; Grover needs ~800.
For $N = 2^{40}$: classical needs $10^{12}$; Grover needs ~1 million.
This is a **quadratic speedup** — significant but not exponential like Shor's.
"""),

md("""## The Core Idea: Amplitude Amplification

Start with a uniform superposition over all $N$ states. The target state $|\\omega\\rangle$ has amplitude $1/\\sqrt{N}$ — tiny.

Grover's algorithm **amplifies** the target amplitude while suppressing all others, using two operations repeated $k \\approx \\frac{\\pi}{4}\\sqrt{N}$ times:

1. **Oracle** $U_\\omega$: flips the sign (phase) of the target state only.
   $U_\\omega|x\\rangle = -|x\\rangle$ if $x = \\omega$, else $|x\\rangle$.

2. **Diffusion** $D$ (Grover diffusion / inversion about average):
   $D = 2|s\\rangle\\langle s| - I$ where $|s\\rangle = H^{\\otimes n}|0\\rangle^{\\otimes n}$ is the uniform superposition.
   This reflects all amplitudes about their average — boosting whatever the oracle boosted.

**Geometric picture**: the state lives in the 2D space spanned by $|\\omega\\rangle$ and $|\\omega^\\perp\\rangle$.
Each oracle + diffusion step rotates the state vector by $2\\theta$ toward $|\\omega\\rangle$,
where $\\sin\\theta = 1/\\sqrt{N}$. After $k$ steps, the angle from $|\\omega\\rangle$ is $\\frac{\\pi}{2} - (2k+1)\\theta$.
Optimal: stop when $(2k+1)\\theta \\approx \\pi/2$, giving $k \\approx \\frac{\\pi}{4\\theta} \\approx \\frac{\\pi}{4}\\sqrt{N}$.
"""),

code("""from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram
from qiskit.quantum_info import Statevector
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

matplotlib.rcParams.update({'figure.dpi': 120, 'font.size': 11})
simulator = AerSimulator()
print("Ready ✓")
"""),

code("""# ── Phase Oracle ────────────────────────────────────────────────────
def phase_oracle(n, target):
    \"\"\"
    Marks target state |target⟩ with a phase flip: |target⟩ → −|target⟩
    target: integer (0 to 2^n - 1) or binary string like '101'
    \"\"\"
    qc = QuantumCircuit(n, name=f"Oracle |{target}⟩")

    if isinstance(target, int):
        target = format(target, f'0{n}b')

    # Flip qubits where target bit is '0'
    for i, bit in enumerate(reversed(target)):
        if bit == '0':
            qc.x(i)

    # Multi-controlled Z (= H · MCX · H on last qubit)
    qc.h(n - 1)
    qc.mcx(list(range(n - 1)), n - 1)
    qc.h(n - 1)

    # Undo the bit flips
    for i, bit in enumerate(reversed(target)):
        if bit == '0':
            qc.x(i)

    return qc

# Test: show oracle for |101⟩ on 3 qubits
oracle = phase_oracle(3, '101')
print(oracle.draw('text'))
print("\\nOracle marks state |101⟩ with a phase flip.")
"""),

code("""# ── Grover Diffusion Operator ────────────────────────────────────────
def grover_diffusion(n):
    \"\"\"
    Grover diffusion = inversion about the uniform superposition |s⟩.
    D = H^n · (2|0⟩⟨0| - I) · H^n
      = H^n · X^n · (MCZ) · X^n · H^n
    \"\"\"
    qc = QuantumCircuit(n, name="Diffusion")

    qc.h(range(n))
    qc.x(range(n))

    # Multi-controlled Z
    qc.h(n - 1)
    qc.mcx(list(range(n - 1)), n - 1)
    qc.h(n - 1)

    qc.x(range(n))
    qc.h(range(n))

    return qc

print("Diffusion operator (3 qubits):")
print(grover_diffusion(3).draw('text'))
"""),

code("""# ── Full Grover Circuit ──────────────────────────────────────────────
def grover_circuit(n, target, iterations=None):
    \"\"\"
    Full Grover search circuit.
    n: number of qubits  (searches 2^n items)
    target: binary string e.g. '101'
    iterations: number of oracle+diffusion steps (auto if None)
    \"\"\"
    N = 2 ** n
    if iterations is None:
        iterations = max(1, int(np.round(np.pi / 4 * np.sqrt(N))))

    qc = QuantumCircuit(n, n)

    # ① Uniform superposition
    qc.h(range(n))
    qc.barrier()

    # ② Grover iterations
    oracle = phase_oracle(n, target)
    diffusion = grover_diffusion(n)

    for step in range(iterations):
        qc.compose(oracle, inplace=True)
        qc.compose(diffusion, inplace=True)
        qc.barrier()

    # ③ Measure
    qc.measure(range(n), range(n))
    return qc

# Build and show circuit for n=3, target=|101⟩, 2 iterations
qc = grover_circuit(3, '101', iterations=2)
print(f"Grover circuit: n=3, target=|101⟩, iterations=2")
print(f"Total gates (without barriers): {qc.size()}")
print(qc.draw('text'))
"""),

code("""# ── Run Grover search and visualise ─────────────────────────────────
n, target = 3, '101'
N = 2 ** n
opt_iters = max(1, int(np.round(np.pi / 4 * np.sqrt(N))))

qc = grover_circuit(n, target, iterations=opt_iters)
t_qc = transpile(qc, simulator)
result = simulator.run(t_qc, shots=2048).result()
counts = result.get_counts()

# Sort for clean plot
all_states = [format(i, f'0{n}b') for i in range(N)]
values = [counts.get(s, 0) for s in all_states]
colors = ['#000' if s == target else '#ccc' for s in all_states]

fig, ax = plt.subplots(figsize=(9, 4))
bars = ax.bar(all_states, values, color=colors)
ax.set_xlabel("State")
ax.set_ylabel("Counts (2048 shots)")
ax.set_title(f"Grover's Algorithm: n={n} qubits, searching for |{target}⟩\\n"
             f"Optimal iterations = {opt_iters}, N = {N} states")
ax.axhline(2048/N, color='gray', ls='--', lw=1, label=f'Uniform = {2048//N}')
ax.legend()

# Annotate target
target_idx = all_states.index(target)
ax.annotate(f'|{target}⟩\\n← TARGET', xy=(target_idx, values[target_idx]),
            xytext=(target_idx + 0.5, values[target_idx] - 100),
            fontsize=9, ha='left')

plt.tight_layout()
plt.savefig('grover_results.png', dpi=120, bbox_inches='tight')
plt.show()

print(f"\\nTarget |{target}⟩ measured {counts.get(target, 0)} / 2048 times")
print(f"Success probability: {counts.get(target, 0) / 2048:.1%}")
print(f"Expected (classical random): {1/N:.1%}")
print(f"Speedup: ~{(N/2) / opt_iters:.0f}×  (avg classical / Grover iterations)")
"""),

code("""# ── Show how probability evolves with iterations ────────────────────
n, target = 3, '101'
N = 2 ** n
max_iters = 10

probs = []
for k in range(1, max_iters + 1):
    qc = grover_circuit(n, target, iterations=k)
    t_qc = transpile(qc, simulator)
    result = simulator.run(t_qc, shots=4096).result()
    counts = result.get_counts()
    probs.append(counts.get(target, 0) / 4096)

# Theoretical curve: P(k) = sin²((2k+1)·arcsin(1/√N))
theta = np.arcsin(1 / np.sqrt(N))
k_range = np.linspace(0.5, max_iters, 200)
theory = np.sin((2 * k_range + 1) * theta) ** 2

fig, ax = plt.subplots(figsize=(9, 4))
ax.plot(range(1, max_iters + 1), probs, 'o-', color='#000', ms=7, label='Simulated')
ax.plot(k_range, theory, '--', color='#888', lw=1.5, label='Theory: $\\sin^2((2k+1)\\\\theta)$')
ax.axvline(int(np.pi / 4 * np.sqrt(N)), color='red', lw=1, ls=':', label=f'Optimal k={int(np.pi/4*np.sqrt(N))}')
ax.set_xlabel("Number of Grover iterations k")
ax.set_ylabel("P(measuring target)")
ax.set_title(f"Grover's Algorithm: Success Probability vs. Iterations (n={n}, N={N})")
ax.set_ylim(0, 1.05)
ax.legend()
plt.tight_layout()
plt.savefig('grover_iterations.png', dpi=120, bbox_inches='tight')
plt.show()

print("\\nKey insight: overshot iterations REDUCE probability — Grover is not monotone.")
print("Apply too many times and the state rotates past |ω⟩ back toward |ω⊥⟩.")
print(f"The sinusoidal behaviour confirms the geometric (rotation) picture.")
"""),

code("""# ── Scaling: how many iterations vs N? ─────────────────────────────
print(f"{'n qubits':>10} | {'N = 2^n':>10} | {'Classical avg':>14} | {'Grover iters':>13} | {'Speedup':>8}")
print("-" * 62)
for n in [2, 3, 4, 5, 6, 8, 10, 16, 20, 30]:
    N = 2 ** n
    classical = N // 2
    grover = max(1, int(np.pi / 4 * np.sqrt(N)))
    speedup = classical / grover
    print(f"{n:>10} | {N:>10,} | {classical:>14,} | {grover:>13,} | {speedup:>7.0f}×")
"""),

md("""## Key Takeaways

1. **Oracle + Diffusion** is the Grover iteration. Each step rotates the state by $2\\theta$ in the $\\{|\\omega\\rangle, |\\omega^\\perp\\rangle\\}$ plane.
2. **Optimal iterations**: $k^* \\approx \\frac{\\pi}{4}\\sqrt{N}$. Too few → low probability; too many → wraps past the target.
3. **Quadratic speedup**: $O(N) \\to O(\\sqrt{N})$. Provably optimal — no quantum algorithm can search faster.
4. **Generalisation**: works for $M$ marked items with $O(\\sqrt{N/M})$ iterations.
5. **Impact**: Grover weakens (but does not break) symmetric cryptography. AES-256 has $2^{256}$ keys; Grover reduces this to $2^{128}$ effective security. Solution: double the key length.
6. **Amplitude amplification** is the general version: any algorithm with success probability $p$ can be boosted to near-certainty in $O(1/\\sqrt{p})$ applications.
"""),
]

# ═══════════════════════════════════════════════════════════════════════════════
# NOTEBOOK 3: SHOR'S ALGORITHM
# ═══════════════════════════════════════════════════════════════════════════════

nb3 = nbf.v4.new_notebook()
nb3.cells = [

md("""# Shor's Algorithm
### Factoring integers in polynomial time with a quantum computer

**Course:** UCL Quantum Computing · **Prerequisites:** QFT, phase estimation, modular arithmetic

---

## Why Factoring Matters

Integer factorisation is the mathematical backbone of RSA encryption, Diffie-Hellman, and elliptic curve cryptography — together securing essentially all encrypted internet traffic. The best classical algorithm (General Number Field Sieve) factors an $n$-bit number in:

$$\\text{Classical: } \\exp\\!\\left(O\\!\\left(n^{1/3}(\\log n)^{2/3}\\right)\\right) \\quad \\text{(sub-exponential, super-polynomial)}$$

**Shor's algorithm (1994)** factors in:

$$\\text{Quantum: } O(n^3) \\quad \\text{(polynomial!)}$$

This is an **exponential speedup** — the most powerful quantum advantage known for a practical problem.
"""),

md("""## Reduction: Factoring → Period Finding

Shor's insight: factoring reduces to finding the **period** of a modular function. Given $N$ to factor:

1. Choose a random $a$ with $\\gcd(a, N) = 1$ (coprime). If $\\gcd(a, N) > 1$, we found a factor trivially.
2. Consider $f(x) = a^x \\bmod N$. This function is **periodic** with some period $r$:
   $f(x+r) = f(x)$ because $a^r \\equiv 1 \\pmod{N}$.
3. If $r$ is even and $a^{r/2} \\not\\equiv -1 \\pmod{N}$, then:
   $a^r - 1 \\equiv 0 \\pmod{N}$
   $(a^{r/2} - 1)(a^{r/2} + 1) \\equiv 0 \\pmod{N}$
   The factors of $N$ divide these two terms:
   $$p = \\gcd(a^{r/2} - 1,\\, N), \\qquad q = \\gcd(a^{r/2} + 1,\\, N)$$

4. **Period finding is done quantumly** using the Quantum Fourier Transform — the classical step is just GCD.

**Example: $N = 15, a = 7$**
$7^1=7,\\; 7^2=4,\\; 7^3=13,\\; 7^4=1 \\pmod{15}$ → period $r = 4$
$\\gcd(7^2-1, 15) = \\gcd(48, 15) = 3$ ✓
$\\gcd(7^2+1, 15) = \\gcd(50, 15) = 5$ ✓
"""),

md("""## The Quantum Fourier Transform

The QFT is the quantum analogue of the discrete Fourier transform. On $n$ qubits it maps:

$$\\text{QFT}|j\\rangle = \\frac{1}{\\sqrt{2^n}}\\sum_{k=0}^{2^n-1} e^{2\\pi i jk/2^n}|k\\rangle$$

The circuit uses $n$ Hadamard gates and $O(n^2)$ controlled phase rotations:

$$R_k = \\begin{pmatrix}1 & 0 \\\\ 0 & e^{2\\pi i/2^k}\\end{pmatrix}$$

Applied to qubit $j$: apply $H$, then controlled-$R_2, R_3, \\ldots, R_{n-j}$ from higher qubits, then swap to reverse bit order.
Total circuit depth: $O(n^2)$ gates vs. classical FFT's $O(n \\cdot 2^n)$.
"""),

code("""from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Statevector
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from math import gcd, pi
from fractions import Fraction

matplotlib.rcParams.update({'figure.dpi': 120, 'font.size': 11})
simulator = AerSimulator()
print("Ready ✓")
"""),

code("""# ── Quantum Fourier Transform ────────────────────────────────────────
def qft(n):
    \"\"\"
    QFT on n qubits.
    Produces the circuit WITHOUT the final swap (swap added separately).
    \"\"\"
    qc = QuantumCircuit(n, name="QFT")

    for j in range(n):
        qc.h(j)
        for k in range(j + 1, n):
            angle = 2 * pi / 2 ** (k - j + 1)
            qc.cp(angle, k, j)      # controlled phase rotation

    # Bit reversal: swap pairs to match DFT ordering
    for i in range(n // 2):
        qc.swap(i, n - i - 1)

    return qc

def inverse_qft(n):
    \"\"\"Inverse QFT = QFT†\"\"\"
    return qft(n).inverse()

# Display the 4-qubit QFT circuit
print("4-qubit QFT circuit:")
print(qft(4).draw('text'))
"""),

code("""# ── Verify QFT: transform a basis state ─────────────────────────────
# QFT|j⟩ should produce phases exp(2πi·j·k/N) on each basis state |k⟩
n = 4
N = 2**n

# Build circuit: prepare |5⟩ = |0101⟩, then apply QFT
qc_verify = QuantumCircuit(n)
for i, bit in enumerate(reversed(format(5, f'0{n}b'))):
    if bit == '1':
        qc_verify.x(i)
qc_verify.compose(qft(n), inplace=True)

sv = Statevector(qc_verify)
probs = np.abs(sv.data) ** 2
phases = np.angle(sv.data)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 3.5))

ax1.bar(range(N), probs, color='#333')
ax1.set_title(f"QFT|5⟩: probability distribution (uniform = 1/{N})")
ax1.set_xlabel("Basis state")
ax1.set_ylabel("Probability")
ax1.axhline(1/N, color='red', ls='--', lw=1, label=f"1/{N} = {1/N:.4f}")
ax1.legend()

ax2.bar(range(N), phases / pi, color='#666')
ax2.set_title("QFT|5⟩: phases in units of π")
ax2.set_xlabel("Basis state")
ax2.set_ylabel("Phase / π")
ax2.set_ylim(-1.1, 1.1)

plt.suptitle("QFT of |5⟩: uniform amplitudes with linearly increasing phases", y=1.02)
plt.tight_layout()
plt.savefig('qft_demo.png', dpi=120, bbox_inches='tight')
plt.show()

print("\\nQFT of any basis state |j⟩:")
print("  All amplitudes are equal: |amplitude|² = 1/N (uniform distribution)")
print("  Phases rotate at frequency j: φ_k = 2π·j·k/N")
"""),

code("""# ── Quantum Phase Estimation ─────────────────────────────────────────
# QPE estimates the phase φ in U|ψ⟩ = e^{2πiφ}|ψ⟩
# This is the subroutine Shor's uses to find the period.

def qpe_circuit(eigenphase, n_count=4):
    \"\"\"
    Simplified QPE: demonstrate phase estimation for a single-qubit unitary
    U = phase gate with eigenphase φ.
    n_count: number of counting qubits.
    \"\"\"
    qc = QuantumCircuit(n_count + 1, n_count)

    # Prepare eigenstate |1⟩ of U (phase gate fixes |1⟩)
    qc.x(n_count)

    # Superposition on counting qubits
    qc.h(range(n_count))

    # Apply controlled-U^(2^j) for each counting qubit
    for j in range(n_count):
        repetitions = 2 ** j
        angle = 2 * pi * eigenphase * repetitions
        qc.cp(angle, j, n_count)   # controlled phase = controlled-U^(2^j)

    # Inverse QFT on counting register
    qc.compose(inverse_qft(n_count), range(n_count), inplace=True)

    # Measure
    qc.measure(range(n_count), range(n_count))
    return qc

# Test: estimate phase φ = 1/4 → should measure |0100⟩ (= 4 in decimal, 4/16 = 1/4) ✓
phi = 1/4
n_count = 4
qc_qpe = qpe_circuit(phi, n_count)

t_qc = transpile(qc_qpe, simulator)
result = simulator.run(t_qc, shots=2048).result()
counts = result.get_counts()

print(f"QPE for phase φ = {phi}")
print(f"Expected measurement: {int(phi * 2**n_count)} = |{format(int(phi * 2**n_count), f'0{n_count}b')}⟩")
print(f"Measured: {counts}")
print(f"\\nEstimated phase: {max(counts, key=counts.get)} / 2^{n_count} = {int(max(counts, key=counts.get), 2)/2**n_count}")
"""),

md("""## Shor's Algorithm for N = 15

We now implement the full algorithm for $N=15$, $a=7$.

**Circuit structure:**
1. $n_{\\text{count}}$ counting qubits in superposition $\\to$ will hold the period information
2. 4 work qubits initialised to $|1\\rangle$ (the state that gets multiplied)
3. Apply controlled-$U^{2^j}$ for each counting qubit, where $U|y\\rangle = |ay \\bmod 15\\rangle$
4. Apply inverse QFT to counting register
5. Measure counting register — outcomes cluster at multiples of $2^{n_{\\text{count}}}/r$
6. Extract $r$ using continued fractions, then compute GCD for the factors

The controlled modular multiplication $U|y\\rangle = |7y \\bmod 15\\rangle$ is implemented with SWAP gates — the 4-qubit cyclic permutation $1 \\to 7 \\to 4 \\to 13 \\to 1$ can be decomposed into SWAPs and X gates.
"""),

code("""# ── Controlled modular multiplication for N = 15 ─────────────────────
def c_amod15(a, power):
    \"\"\"
    Controlled-U^power where U|y⟩ = |a·y mod 15⟩ on 4 work qubits.
    Implements the cycle 1 → a → a² → ... (mod 15) using SWAP/X decomposition.
    Only supports a coprime to 15: {2, 4, 7, 8, 11, 13}.
    \"\"\"
    if a not in [2, 4, 7, 8, 11, 13]:
        raise ValueError(f"a={a} must be coprime to 15. Choose from {{2,4,7,8,11,13}}.")

    U = QuantumCircuit(4)
    for _ in range(power):
        # SWAP decomposition of the cyclic permutation induced by ×a mod 15
        if a in [2, 13]:
            U.swap(0, 1); U.swap(1, 2); U.swap(2, 3)
        if a in [7, 8]:
            U.swap(2, 3); U.swap(1, 2); U.swap(0, 1)
        if a in [4, 11]:
            U.swap(1, 3); U.swap(0, 2)
        if a in [7, 11, 13]:
            for q in range(4):
                U.x(q)

    gate = U.to_gate()
    gate.name = f"{a}^{power} mod 15"
    return gate.control()          # make it a controlled gate

# Verify: 7^1 mod 15 = 7, 7^2 = 4, 7^3 = 13, 7^4 = 1 → period r = 4
a = 7
print(f"Verifying a={a} mod 15 cycle:")
val = 1
for k in range(1, 6):
    val = (val * a) % 15
    print(f"  {a}^{k} mod 15 = {val}")
print(f"  Period r = 4  (7^4 mod 15 = 1) ✓")
"""),

code("""# ── Full Shor's Circuit for N = 15 ──────────────────────────────────
def shors_circuit(a, N=15, n_count=8):
    \"\"\"
    Build Shor's period-finding circuit for N=15.
    a: base (coprime to 15)
    n_count: counting qubits (more → sharper peaks, easier phase readout)
    \"\"\"
    n_work = 4          # work register: 4 qubits to represent 0-15
    qc = QuantumCircuit(n_count + n_work, n_count)

    # ① Initialise work register to |1⟩ = |0001⟩
    qc.x(n_count)       # qubit n_count is the LSB of the work register

    # ② Uniform superposition on counting register
    qc.h(range(n_count))
    qc.barrier()

    # ③ Controlled-U^(2^j) for j = 0, 1, ..., n_count-1
    for j in range(n_count):
        qc.append(
            c_amod15(a, 2**j),
            [j] + list(range(n_count, n_count + n_work))
        )
    qc.barrier()

    # ④ Inverse QFT on counting register → transforms phases to measurable state
    qc.compose(inverse_qft(n_count), range(n_count), inplace=True)
    qc.barrier()

    # ⑤ Measure counting register
    qc.measure(range(n_count), range(n_count))
    return qc

a = 7
qc_shor = shors_circuit(a, N=15, n_count=8)
print(f"Shor's circuit for N=15, a={a}:")
print(f"  Total qubits: {qc_shor.num_qubits}")
print(f"  Total classical bits: {qc_shor.num_clbits}")
print(f"  Circuit depth: {qc_shor.depth()}")
print(f"  Gate count: {qc_shor.size()}")
"""),

code("""# ── Run the circuit ─────────────────────────────────────────────────
a, n_count = 7, 8
N_val = 15
qc_shor = shors_circuit(a, N=N_val, n_count=n_count)

t_qc = transpile(qc_shor, simulator)
result = simulator.run(t_qc, shots=2048).result()
counts = result.get_counts()

# Plot histogram — expect peaks at 0, 64, 128, 192  (= 0, 256/4, 256/2, 3·256/4)
fig, ax = plt.subplots(figsize=(12, 4))
sorted_counts = dict(sorted(counts.items(), key=lambda x: int(x[0], 2)))
states = [int(k, 2) for k in sorted_counts.keys()]
vals = list(sorted_counts.values())
ax.bar(states, vals, color='#111', width=2)
ax.set_xlabel("Measurement outcome (decimal)")
ax.set_ylabel("Counts")
ax.set_title(f"Shor's Algorithm: N=15, a={a}, n_count={n_count} qubits\\n"
             f"Expected peaks at 0, {2**n_count//4}, {2**n_count//2}, {3*2**n_count//4}  (multiples of 2^n/r, r=4)")
for x in [0, 2**n_count//4, 2**n_count//2, 3*2**n_count//4]:
    ax.axvline(x, color='red', lw=1, ls='--', alpha=0.6)
plt.tight_layout()
plt.savefig('shors_histogram.png', dpi=120, bbox_inches='tight')
plt.show()

# Show top outcomes
top = sorted(counts.items(), key=lambda x: -x[1])[:8]
print("\\nTop measurement outcomes:")
print(f"{'Binary':>12} {'Decimal':>8} {'Phase = k/256':>16} {'Fraction':>12} {'Counts':>8}")
print("-" * 62)
for bits, cnt in top:
    dec = int(bits, 2)
    phase = dec / 2**n_count
    frac = Fraction(phase).limit_denominator(N_val)
    print(f"{bits:>12} {dec:>8} {phase:>16.4f} {str(frac):>12} {cnt:>8}")
"""),

code("""# ── Classical post-processing: extract period → factors ──────────────
print(f"Extracting period r from measurement outcomes for N=15, a={a}")
print("=" * 60)

a = 7
N_val = 15
n_count = 8

# Get the most frequent non-zero measurement
top = sorted(
    [(int(k, 2), v) for k, v in counts.items() if int(k, 2) != 0],
    key=lambda x: -x[1]
)

found_factors = set()
for dec, cnt in top[:6]:
    phase = dec / 2**n_count
    # Continued fraction approximation to get r
    frac = Fraction(phase).limit_denominator(N_val)
    r = frac.denominator

    print(f"\\nOutcome {dec:3d} → phase = {dec}/{2**n_count} ≈ {phase:.4f} → fraction {frac} → r = {r}")

    if r % 2 != 0:
        print(f"  r={r} is odd — skip")
        continue

    # Try to extract factors
    guess1 = gcd(a**(r//2) - 1, N_val)
    guess2 = gcd(a**(r//2) + 1, N_val)
    print(f"  gcd({a}^{r//2} - 1, {N_val}) = gcd({a**(r//2)-1}, {N_val}) = {guess1}")
    print(f"  gcd({a}^{r//2} + 1, {N_val}) = gcd({a**(r//2)+1}, {N_val}) = {guess2}")

    for g in [guess1, guess2]:
        if 1 < g < N_val:
            found_factors.add(g)

print("\\n" + "=" * 60)
if found_factors:
    factors = sorted(found_factors)
    print(f"\\n✓ Factors of {N_val}: {factors[0]} × {N_val // factors[0]} = {N_val}")
    assert factors[0] * (N_val // factors[0]) == N_val
else:
    print("No factors found in top outcomes — re-run with more shots or different a")
"""),

code("""# ── Summary: classical vs quantum scaling ───────────────────────────
print("Factoring complexity comparison")
print("=" * 65)
print(f"{'Bits n':>8} | {'RSA key size':>14} | {'Classical GNFS':>22} | {'Shor O(n³)':>12}")
print("-" * 65)

for n in [128, 256, 512, 1024, 2048, 4096]:
    # Classical GNFS: rough order-of-magnitude (ignoring constants)
    gnfs_exp = (64/9)**(1/3) * n**(1/3) * (np.log2(n))**(2/3)
    gnfs = f"~2^{gnfs_exp:.0f}"
    shor = f"~{n**3:,.0f} gates"
    rsa = f"RSA-{n}"
    print(f"{n:>8} | {rsa:>14} | {gnfs:>22} | {shor:>12}")

print("\\nWith physical quantum computers of ~4,000 logical qubits,")
print("Shor's algorithm would break RSA-2048 in hours.")
print("Current quantum computers (2024): ~1000 noisy physical qubits,")
print("~100-200 logical qubits — not yet a threat, but approaching rapidly.")
"""),

md("""## Key Takeaways

1. **Period finding is the key**: Shor reduces factoring to finding the period $r$ of $f(x) = a^x \\bmod N$. The quantum computer does only this step; everything else is classical number theory.

2. **QFT is the engine**: The inverse QFT at the end of the circuit maps the periodic phase pattern in the counting register into sharp peaks at multiples of $2^{n_{\\text{count}}}/r$. Measuring these peaks reveals $r$.

3. **Continued fractions extract $r$**: The measurement outcome is a rational multiple of $2^{n_{\\text{count}}}$ close to $k/r$. Continued fractions convert this to the exact fraction $k/r$ in lowest terms, giving $r$ as the denominator.

4. **Exponential speedup**: $O(e^{n^{1/3}})$ classical → $O(n^3)$ quantum. For 2048-bit RSA keys, this is the difference between $10^{50}$ operations and $10^{10}$ operations.

5. **The quantum advantage is structural**: Shor's algorithm exploits the exponential state space of quantum registers to perform modular exponentiation over all $2^{n_{\\text{count}}}$ inputs simultaneously, then uses interference (via QFT) to extract the globally periodic structure.

6. **Real hardware requirements**: Factoring RSA-2048 requires ~4,000 **logical** qubits (error-corrected). With current physical error rates (~0.1%), this needs ~4 million physical qubits. IBM Q plans to reach this scale in the early 2030s.
"""),
]

# ── Save all three notebooks ─────────────────────────────────────────────────

for fname, nb in [
    ("qc_03_deutsch_jozsa.ipynb", nb1),
    ("qc_04_grover.ipynb",        nb2),
    ("qc_05_shor.ipynb",          nb3),
]:
    path = OUT / fname
    with open(path, "w") as f:
        nbf.write(nb, f)
    print(f"Written: {path}")

print("\nAll three notebooks created. Run nbconvert to execute and export to HTML.")
