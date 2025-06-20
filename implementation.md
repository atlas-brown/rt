# Models of Supported Command Invocations

## Commands

### cut

#### Flag `-f` with Optional `-d`

**Pattern:** `cut (-d <delimiter>)? -f <field_list>`

**Field List Syntax:**
```
<field_list> ::= [0-9]+ | [0-9]+-[0-9]+ | [0-9]+- | <field_list>,<field_list>
```

The default delimiter is tab.

<!-- let n be the minimum number of fields in the <field_list>, for example, if the <field_list> is "1-3,5-10,15-", then n = 1. -->

**Line-based Type:** 
For all $a \not\subseteq$ `[^<delimiter>]*`: $a \rightarrow$ field-select($a$ & `(.*<delimiter>.*)`, `<delimiter>`, `<field_list>`) | $a$ & `[^<delimiter>]*`

**Type Constraints:**
The type constraint is based on the "no meaningless command" heuristic. There is another implicit type constraint that could be $a \not\subseteq$ `[^<delimiter>]*(<delimiter>[^<delimiter>]*){1, n-2}` if $n \geq 3$, where $n$ is the minimum number of fields in the `<field_list>`. For example, if the `<field_list>` is "1-3,5-10,15-", then $n = 1$. This constraint exists because `cut` requires enough fields to be selected.

This implicit type constraint is not checked because the type checker can report this by checking if the inferred output is a subset of $\epsilon$ (using the "no empty output" heuristic).

**Implementation Approaches:**

There are three ways to construct the model:

1. **Precise Construction:** Use the precise construction of translate-match (to be introduced later).

2. **FST Model for field-select (Current Choice):** Use the FST model for field-select directly. This is simple but cannot handle the whole stream case:

   - If the `<field_list>` has an upper bound, expand it to a list of fields $x_1, x_2, \ldots, x_n$ where $x_1 < x_2 < \cdots < x_n$.
   - If `<field_list>` has no upper bound (e.g., "10-"), find the smallest number $x_n$ such that any field greater than or equal to $x_n$ is selected. Rewrite the `<field_list>` as $x_1, x_2, \ldots, x_n\text{-}$ where $x_1 < x_2 < \cdots < x_n$.
   
   **FST Construction:**
   - Create an FST with $x_n + 1$ states, mapping $1 \ldots x_n + 1$ to corresponding states.
   - For each $i \in 1 \ldots x_n$:
     - State $i$ has a transition to state $i+1$ that accepts the delimiter. If $i+1$ is not selected, this transition outputs $\epsilon$; otherwise, it outputs the delimiter.
     - State $i$ has a transition to itself that accepts any character except the delimiter. If $i$ is selected, this transition outputs the accepted character; otherwise, it outputs $\epsilon$.
   - State $x_n + 1$ has a transition to itself that accepts any character. If $x_n + 1$ is not selected, this transition outputs nothing; otherwise, it outputs the accepted character.
   - State 1 is the initial state.
   - Every state is a final state.

3. **Pure FST Model:** Use a pure FST to model directly. Keep the above FST construction, translate `[^<delimiter>]*` to a DFA, and compute the products of:
   - The negation of the DFA with the above FST
   - The DFA with an FST representing identity translation
   
   Then obtain 2 FSTs and construct a new FST by creating a new initial state and adding two epsilon transitions to the initial states of the 2 previous FSTs respectively. This creates a non-deterministic but functional FST because these 2 sub-FSTs have disjoint domains.

**Whole Stream Reasoning:**

- For approach 2: There is no way to handle the whole stream case precisely. We need to transform the input into line-based representation and then compute the line-based output.

- For approaches 1 and 3: Since we have a line-based functional FST, we can easily transform it into a whole-stream-based functional FST. For each non-final state, there is no transition from it that accepts "\n". For each final state, we add a transition from it to the initial state that accepts "\n" and outputs "\n".

#### Flag `-c`

**Pattern:** `cut -c <field_list>`

The `<field_list>` has the same format as `-f`.

**Line-based Type:** 
For all $a$: $a \rightarrow$ field-select($a$, "", `<field_list>`)

Again, there is an implicit type constraint that could be $a \not\subseteq$ `.{0, n-1}`, where $n$ is the minimum number of fields in the `<field_list>`. However, we don't check this because the type checker can report this by checking if the inferred output is a subset of $\epsilon$ (using the "no empty output" heuristic).

**Implementation Approaches:**

There are two ways to construct the model:

1. **Precise Construction:** Use the precise construction of translate-match (to be introduced later).

2. **FST Model for field-select:**

   - If the `<field_list>` has an upper bound, expand it to a list of fields $x_1, x_2, \ldots, x_n$ where $x_1 < x_2 < \cdots < x_n$.
   - If `<field_list>` has no upper bound, find the smallest number $x_n$ such that any field greater than or equal to $x_n$ is selected. Rewrite the `<field_list>` as $x_1, x_2, \ldots, x_n\text{-}$ where $x_1 < x_2 < \cdots < x_n$.

   **FST Construction:**
   - Create an FST with $x_n + 2$ states, mapping $0 \ldots x_n + 1$ to corresponding states.
   - For each $i \in 0 \ldots x_n$:
     - State $i$ has a transition to state $i+1$ that accepts any character. If $i+1$ is not selected, this transition outputs $\epsilon$; otherwise, it outputs the accepted character.
   - State $x_n + 1$ has a transition to itself that accepts any character. If $x_n+1$ is not selected, this transition outputs $\epsilon$; otherwise, it outputs the accepted character.
   - State 0 is the initial state.
   - Every state is a final state.

**Whole Stream Reasoning:**

Following the method described for flag `-f`, we can transform a line-based functional FST into a whole-stream-based functional FST.

#### Flag `-b`

Same as `-c`.