# Models of Supported Command Invocations

## Commands

### cut

#### Flag `-f` with Optional `-d`

**Pattern:** `cut (-d <delimiter>)? -f <field_list>`

**Field List Syntax:**
```
<field_list> ::= [0-9]+ | [0-9]+-[0-9]+ | [0-9]+- | <field_list>,<field_list>
```
\<delimiter> is a single character, which should not be "\n".

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

1. **Precise translate-match Construction:** Use the precise construction of translate-match (to be introduced later).

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

### tr

#### Character Sets Related Flags `-c`/`-C`

This flag is related to character sets. In the implementation, this flag will be eliminated by preprocessing the character sets.

With the assumption that locale is `C`, we can expand the character set1 to the complement of the previous character set1.

#### Character Set Related Flag `-t`

This flag is related to character sets. In the implementation, this flag will be eliminated by preprocessing the character sets.

If there is only one character set, `-t` will be ignored.

The preprocessing order is: first complement the character set1 (if `-c` is used), then cut the character set1 if the character set1 is longer than the character set2, to ensure the length of the character set1 is not greater than the length of the character set2.

#### No Operation-Related Flags

**Pattern:** `tr (<character-sets-related-flags>) <character-set1> <character-set2>`

**Character Set Syntax:**
```
<character-set> ::= c | c-c | <POSIX-character-class> | <character-set><character-set>
```

`<character-set1>` and `<character-set2>` may contain "\n".

**Implementation Approaches:**

Use whole stream reasoning to directly model `tr`, to avoid the complexity introduced by "\n" in the character sets. If the input is line-based `r`, whose alphabet does not contain "\n", we can transform it into a whole-stream-based input `(r\n)*r(\n)?`. Note: We assume every stream is finite. We cannot handle the infinite line stream like the output of `yes`.

**FST Construction:**
- Expand character set1 and character set2 to a list of characters. If the length of expanded character set1 is greater than the length of expanded character set2, then repeat appending the last character of expanded character set2 to the end of expanded character set2 until the length of expanded character set2 is equal to the length of expanded character set1.
- Create an FST which has 1 state.
- This state has a transition to itself that accepts any character. If the character is in character set1, this transition outputs the corresponding character in character set2; otherwise, it outputs the character itself.
- The state is both the initial state and the final state.

#### Flag `-d`

**Pattern:** `tr (<character-sets-related-flags>)? -d <input-character-set>`

**Implementation Approaches:**

Again, use whole stream reasoning to directly model `tr`, to avoid the complexity introduced by "\n" in the character sets.

**FST Construction:**
- Expand the input character set to a list of characters.
- Create an FST which has 1 state.
- This state has a transition to itself that accepts any character. If the character is in the input character set, this transition outputs $\epsilon$; otherwise, it outputs itself.
- This state is both the initial state and the final state.

#### Flag `-s` with One Operand (Character Set)

**Pattern:** `tr (<character-sets-related-flags>)? -s <character-set>`

**Implementation Approaches:**

Use whole stream reasoning to directly model `tr`, to avoid the complexity introduced by "\n" in the character sets.

**FST Construction:**
- Expand the character set to a list of characters $c_1, c_2, \ldots, c_n$.
- Create an FST which has $n+1$ states: $q_0, q_1, \ldots, q_n$. For $i > 0$, $c_i$ maps to $q_i$.
- For each state $q_i$ where $i \geq 0$:
  - For each character $c_j$ in the character set, there is a transition from $q_i$ to $q_j$. If $q_i$ is $q_j$, this transition outputs $\epsilon$; otherwise, it outputs $c_j$.
  - For each character $c$ in the alphabet but not in the character set, there is a transition from $q_i$ to $q_0$ that outputs $c$.
- Every state is a final state.
- $q_0$ is the initial state.

#### Flag `-s` with Two Operands (Character Sets)

**Pattern:** `tr (<character-sets-related-flags>)? -s <character-set-1> <character-set-2>`

This is equivalent to `tr <character-sets-related-flags> <character-set-1> <character-set-2> | tr -s <character-set-2>`.

**Implementation Approaches:**

Compose the corresponding two FSTs.