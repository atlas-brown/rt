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

Use whole stream reasoning to directly model `tr`, to avoid the complexity introduced by "\n" in the character sets. If the input is line-based `r`, whose alphabet does not contain "\n", we can transform it into a whole-stream-based input `(r\n)*(r(\n)?)?`. Note: We assume every stream is finite. We cannot handle the infinite line stream like the output of `yes`.

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


### grep

#### Flag `-c`

**Pattern:** `grep <any-flags> -c <pattern>`

The output type is `[0-9]+\n` (an imprecise model).

#### Pattern-Related Flag `-w`

Update pattern: `(^|[^[:alnum:]_])(<pattern>)([^[:alnum:]_]|$)`

#### Pattern-Related Flag `-x`

Update pattern: `^(<pattern>)$`

#### Pattern-Related Flag `-E`

Use the extended regular expression parser to parse the pattern.

#### Pattern-Related Flag `-i`

For each transition in the NFA/DFA of the pattern, if the transition accepts a lowercase letter, add a new transition between the two states of the previous transition that accepts the corresponding uppercase letter and vice versa.

#### Flag `-o`

**Note:** We assume `grep -vo` is meaningless.

**Note:** `grep -o` will not output empty lines, even if the pattern matches empty lines. For example, `grep -o ".*"` will not output empty lines.

**Pattern:** `grep <pattern-related-flags> -o <pattern>`

The `<pattern>`'s alphabet does not contain "\n".

**Implementation Approaches:**

Preprocess the regular expression pattern to eliminate the pattern-related flags (`-w`, `-x`) and make sure each disjunct of the expression has at most one start anchor and one end anchor. For example, the pattern `(^|[^[:alnum:]_])((^a)|(b$))([^[:alnum:]_]|$)` should be transformed to `(^a([^[:alnum:]_]|$))|(^|[^[:alnum:]_])b$`.

Start-anchor and end-anchor will be shown on the NFA's transition edges. The end anchor will be added to the input alphabet of FST.

Then eliminate `-E` and `-i` flags to get the NFA of the pattern.

**Transition Function Definition:**

The transition function of the NFA is defined as follows:
- Given a state or a set of states, a character, and a flag, it returns a set of states: `δ :: (2^Q | Q) × Σ × Bool -> 2^Q`
- If the flag is true, the start anchor will be treated as an epsilon transition; otherwise, the transition that accepts the start anchor will be ignored. We will omit this flag when it is false for simplicity.
- If the first given parameter is a state, the transition function will return the set of states that can be reached from the given state by the given character.
- If the first given parameter is a set of states, the transition function will return the set of states that can be reached from any state in the set by the given character.

`.` and character classes will not match the anchor characters.

The input can be line-based or whole-stream-based. The output is whole-stream-based.

**FST Construction (Line-based to Whole-stream-based):**

**First FST:** Used to add the end-anchor to the input.

It is a 2-state non-deterministic but functional FST:
- There is a transition from the initial state to the second state that accepts epsilon and outputs the end-anchor.
- There is a transition from the initial state to itself that accepts any character and outputs the character itself.
- The second state does not have any transition and is the final state.

**Second FST:** Suppose we have an NFA for the pattern. The state set of the NFA is $Q$. We construct a non-deterministic but functional FST which has $O(|Q|4^{|Q|})$ states. The states are represented as $(mode, q_i, s_1, s_2) \in \{\text{init}, \text{start}, \text{scan}, \text{match}\} \times Q \times 2^Q \times 2^Q$.

For any state $(mode, q_i, s_1, s_2)$, if $s_1$ contains any final states in the NFA, then $(mode, q_i, s_1, s_2)$ will not be a final state and have no transitions. For the rest of the states, they satisfy the following conditions:

**Init Mode:**
- The init state is $(\text{init}, q_0, \emptyset, \emptyset)$. This is the only state under init mode.
- For any character $c$ which is not end anchor, $(\text{init}, q_0, \emptyset, \emptyset)$ has transitions to $\{(\text{scan}, q_i, \emptyset, \delta(q_0, c, \text{true}) - q_i) \mid q_i \in \delta(q_0, c, \text{true})\}$ that accepts $c$ and outputs $c$.
- For any character $c$ which is not end anchor, another transition that accepts $c$ from this state is to $(\text{start}, q_0, \delta(q_0, c, \text{true}), \emptyset)$ with epsilon outputs.
- For the end anchor, $(\text{init}, q_0, \emptyset, \emptyset)$ has a transition that accepts the end anchor to $(\text{start}, q_0, \emptyset, \emptyset)$ with epsilon outputs.

**Start Mode:**
- All states are in the form of $(\text{start}, q_0, s_1, \emptyset)$.
- For any character $c$, if $c$ is not an end anchor, $(\text{start}, q_0, s_1, \emptyset)$ has transitions that accept $c$ to $\{(\text{scan}, q_i, \delta(s_1, c), \delta(q_0, c) - q_i) \mid q_i \in \delta(q_0, c)\}$. These transitions output the character $c$.
- For any character $c$, if $c$ is not an end anchor, $(\text{start}, q_0, s_1, \emptyset)$ also has a transition to $(\text{start}, q_0, \delta(s_1, c) \cup \delta(q_0, c), \emptyset)$ that accepts $c$ and outputs epsilon.
- If $c$ is an end anchor, $(\text{start}, q_0, s_1, \emptyset)$ has a transition to $(\text{start}, q_0, \delta(s_1, c), \emptyset)$ that accepts $c$ and outputs epsilon.

**Scan Mode:**
- For any character $c$, $(\text{scan}, q_i, s_1, s_2)$ has transitions to $\{(\text{scan}, q_j, \delta(s_1, c), \delta(q_0, c) - q_j) \mid q_j \in \delta(q_0, c)\}$.
- If $c$ is not an end anchor, these transitions output the character $c$. Otherwise, these transitions output epsilon.
- If $q_i$ is a final state in the original NFA, $(\text{scan}, q_i, s_1, s_2)$ has a transition to $(\text{match}, q_i, s_1, s_2)$ that accepts epsilon and outputs "\n".

**Match Mode:**
- For any character $c$ which is not the end anchor, $(\text{match}, q_i, s_1, s_2)$ has transitions that accept $c$ to $\{(\text{scan}, q_j, \delta(s_1, c) \cup \delta(s_2, c) \cup \delta(q_i, c), \delta(q_0, c) - q_j) \mid q_j \in \delta(q_0, c)\}$ with output the character $c$.
- For any character $c$, if $c$ is not an end anchor, $(\text{match}, q_i, s_1, s_2)$ has a transition to $(\text{start}, q_0, \delta(s_1, c) \cup \delta(s_2, c) \cup \delta(q_i, c) \cup \delta(q_0, c), \emptyset)$ that accepts $c$ and outputs epsilon.
- If $c$ is an end anchor, $(\text{match}, q_i, s_1, s_2)$ has a transition to $(\text{start}, q_0, \delta(s_1, c) \cup \delta(s_2, c) \cup \delta(q_i, c), \emptyset)$ that accepts $c$ and outputs epsilon.

**Final States:**
- For any start mode states $(\text{start}, q_i, s_1, \emptyset)$, if $s_1$ does not contain any final states in the NFA, then it will be a final state.
- For any match mode states $(\text{match}, q_i, s_1, s_2)$, if $s_1$ does not contain any final states in the NFA, then it will be a final state.
- The initial state is a final state.

The final FST is the composition of the two FSTs.

**Whole Stream Reasoning:** The above composed FST is a functional FST. We can transform it into a whole-stream-based-to-whole-stream-based FST: for all final states, add a transition that accepts "\n" and outputs epsilon to the initial state.

#### No Operation-Related Flags

**Pattern:** `grep <pattern-related-flags> <pattern>`

The `<pattern>`'s alphabet does not contain "\n".

**Implementation Approaches:**

**Preprocessing:** Eliminate the pattern-related flags (`-w`, `-x`) and make sure each disjunct of the expression has at most one start anchor and one end anchor. For example, the pattern `(^|[^[:alnum:]_])((^a)|(b$))([^[:alnum:]_]|$)` should be transformed to `(^a([^[:alnum:]_]|$))|(^|[^[:alnum:]_])b$`. Then add `.*` as prefix to each disjunct which does not have a start anchor, and add `.*` as suffix to each disjunct which does not have an end anchor. Then remove all the start anchors and end anchors. Then eliminate `-E` and `-i` flags to get the NFA of the pattern.

**First Approach:** We can directly compute the intersection between the input and the NFA of the pattern.

**Second Approach:** A pure FST approach. We can construct an FST that represents the identity translation, and compute the product of this FST and the NFA of the pattern. This FST (FST1) is a single-valued FST (0 or 1 output). If we want a functional FST, we can construct another FST (FST2) that represents a constant empty output. We compute the product of this FST and the complement of the NFA of the pattern. Then we construct a new FST (FST3) by creating a new initial state and add empty transitions from it to the initial states of these two sub-FSTs (FST1 and FST2).

**Whole Stream Reasoning:** For the first approach, we cannot directly get the whole stream output. For the second approach, we can construct a new FST that represents the whole stream translation. For all final states in FST3, if it belongs to FST1, add a transition that accepts "\n" and outputs "\n". If it belongs to FST2, add a transition that accepts "\n" and outputs epsilon. Non-final states in FST3 have no transitions that accept "\n".

#### Flag `-v`

**Pattern:** `grep <pattern-related-flags> -v <pattern>`

Same preprocessing as the no operation-related flags. Then compute the complement of the NFA/DFA of the preprocessed pattern.

**Implementation Approaches:**
Same as the no operation-related flags.

#### Context Flags `-A`, `-B`, `-C`

Not implemented now.

TODO

#### Postprocessing Flag `-n`

**Pattern:** `grep <any-flags except -c> -n <pattern>`

**Line-based Type:** For all $a$: $a \rightarrow$ `[0-9]+:`process($a$)

**Whole Stream Reasoning:** We can construct a non-deterministic infinite-valued FST that represents line-based concatenation. For each final state, add a transition that accepts "\n" and outputs "\n" to the initial state.

### sed

#### Pattern-Related Flag `-E`

Use the extended regular expression parser to parse the pattern.

#### Replacement Mode 1

**Pattern:** `sed <pattern-related-flags> s/<pattern>/<replacement>/g?i?`

If `<replacement>` contains references: TODO

Now we assume `<replacement>` is a pure string.

**Note:** There is a different behavior between `sed` replacement and `grep -o` approach: the pattern that can match empty strings will be matched. And a zero-length match cannot start at the position of the end of the previous match. For example, `echo "abcd" | sed "s/x*/x/g"` outputs `xaxbxcxdx`. `echo "abcd" | sed "s/x*|b/x/g"` outputs `xaxcxdx`.

**Implementation Approaches:**

Similar to the `grep -o` approach.

**If global flag is used:**

Start-anchor and end-anchor will be shown on the NFA's transition edges. The end anchor will be added to the input alphabet of FST.

Then eliminate `i` flag to get the NFA of the pattern.

**Transition Function Definition:**

The transition function of the NFA is defined as follows:
- Given a state or a set of states, a character or "", and a flag, it returns a set of states: `δ :: (2^Q | Q) × (Σ ∪ {""}) × Bool -> 2^Q`
- If the flag is true, the start anchor will be treated as an epsilon transition; otherwise, the transition that accepts the start anchor will be ignored. We will omit this flag when it is false for simplicity.
- If the first given parameter is a state, the transition function will return the set of states that can be reached from the given state by the given character.
- If the first given parameter is a set of states, the transition function will return the set of states that can be reached from any state in the set by the given character.

`.` and character classes will not match the anchor characters.

The input can be line-based or whole-stream-based. The output is whole-stream-based.

**FST Construction (Line-based to Whole-stream-based):**

**First FST:** Used to add the end-anchor to the input.

It is a 2-state non-deterministic but functional FST:
- There is a transition from the initial state to the second state that accepts epsilon and outputs the end-anchor.
- There is a transition from the initial state to itself that accepts any character and outputs the character itself.
- The second state does not have any transition and is the final state.

**Second FST:** Suppose we have an NFA for the pattern. The state set of the NFA is $Q$. We construct a non-deterministic but functional FST which has $O(|Q|4^{|Q|})$ states. The states are represented as $(mode, q_i, s_1, s_2) \in \{\text{init}, \text{start}, \text{scan}, \text{match}\} \times Q \times 2^Q \times 2^Q$.

For any state $(mode, q_i, s_1, s_2)$, if $s_1$ contains any final states in the NFA, then $(mode, q_i, s_1, s_2)$ will not be a final state and have no transitions. For the rest of the states, they satisfy the following conditions:

**Init Mode:**
- The init state is $(\text{init}, q_0, \emptyset, \emptyset)$. This is the only state under init mode.
- If $\delta(q_0, "", \text{true})$ contains any final states in the NFA, there are transitions to $\{(\text{scan}, q_i, \emptyset, \delta(q_0, "", \text{true}) - q_i) \mid q_i \in \delta(q_0, "", \text{true})\}$ that accepts epsilon and outputs `<replacement>`.
- If $\delta(q_0, "", \text{true})$ does not contain any final states in the NFA: For any character $c$, $(\text{init}, q_0, \emptyset, \emptyset)$ has transitions to $\{(\text{scan}, q_i, \emptyset, \delta(q_0, c, \text{true}) - q_i) \mid q_i \in \delta(q_0, c, \text{true})\}$ that accepts $c$ and outputs `<replacement>`.
- If $\delta(q_0, "", \text{true})$ does not contain any final states in the NFA: For any character $c$, another transition that accepts $c$ from this state is to $(\text{start}, q_0, \delta(q_0, c, \text{true}), \emptyset)$. If $c$ is not the end anchor, this transition outputs the character $c$, otherwise, this transition outputs epsilon.

**Start Mode:**
- All states are in the form of $(\text{start}, q_0, s_1, \emptyset)$.
- If $\delta(q_0, "")$ contains any final states in the NFA, there are transitions from any states under start mode $(\text{start}, q_0, s_1, \emptyset)$ to $\{(\text{scan}, q_i, s_1, \delta(q_0, "") - q_i) \mid q_i \in \delta(q_0, "")\}$ that accepts epsilon and outputs `<replacement>`.
- If $\delta(q_0, "")$ does not contain any final states in the NFA, for any character $c$, $(\text{start}, q_0, s_1, \emptyset)$ has transitions to $\{(\text{scan}, q_i, \delta(s_1, c), \delta(q_0, c) - q_i) \mid q_i \in \delta(q_0, c)\}$. These transitions accept $c$ and output `<replacement>`.
- If $\delta(q_0, "")$ does not contain any final states in the NFA, for any character $c$, $(\text{start}, q_0, s_1, \emptyset)$ also has a transition to $(\text{start}, q_0, \delta(s_1, c) \cup \delta(q_0, c), \emptyset)$ that accepts $c$. If $c$ is not the end anchor, this transition outputs the character $c$, otherwise, this transition outputs epsilon.

**Scan Mode:**
- For any character $c$, $(\text{scan}, q_i, s_1, s_2)$ has transitions to $\{(\text{scan}, q_j, \delta(s_1, c), \delta(q_0, c) - q_j) \mid q_j \in \delta(q_0, c)\}$. These transitions accept $c$ and output epsilon.
- If $q_i$ is a final state in the original NFA, $(\text{scan}, q_i, s_1, s_2)$ has a transition to $(\text{match}, q_i, s_1, s_2)$ that accepts epsilon and outputs epsilon.

**Match Mode:**
- For any character $c$, $(\text{match}, q_i, s_1, s_2)$ has transitions that accept $c$ to $\{(\text{scan}, q_j, \delta(s_1, c) \cup \delta(s_2, c) \cup \delta(q_i, c), \delta(q_0, c) - q_j) \mid q_j \in \delta(q_0, c)\}$ with output `<replacement>`.
- For any character $c$, $(\text{match}, q_i, s_1, s_2)$ has a transition to $(\text{start}, q_0, \delta(s_1, c) \cup \delta(s_2, c) \cup \delta(q_i, c) \cup \delta(q_0, c), \emptyset)$ that accepts $c$. If $c$ is not an end anchor, this transition outputs the character $c$, otherwise, this transition outputs epsilon.

**Final States:**
- For any start mode states $(\text{start}, q_i, s_1, \emptyset)$, if $s_1$ does not contain any final states in the NFA, then it will be a final state.
- For any match mode states $(\text{match}, q_i, s_1, s_2)$, if $s_1$ does not contain any final states in the NFA, then it will be a final state.
- The initial state is a final state.

The final FST is the composition of the two FSTs. This is a functional FST.

**If the global flag is not used:** We keep the first FST, and modify the second FST: 

Suppose we have an NFA for the pattern. The state set of the NFA is $Q$. We construct a non-deterministic but functional FST which has $O(|Q|4^{|Q|})$ states. The states are represented as $(mode, q_i, s_1, s_2) \in \{\text{init}, \text{start}, \text{scan}, \text{match}, \text{pass}\} \times Q \times 2^Q \times 2^Q$.

Keep the transitions under init, start, scan mode, update the match mode:
- For any character $c$, $(\text{match}, q_i, s_1, s_2)$ has a transition to $(\text{pass}, q_0, \delta(s_1, c) \cup \delta(s_2, c) \cup \delta(q_i, c), \emptyset)$ that accepts $c$. If $c$ is not an end anchor, this transition outputs the character $c$, otherwise, this transition outputs epsilon.

**Pass mode:**
- The states under pass mode are in the form of $(\text{pass}, q_0, s_1, \emptyset)$.
- For any character $c$, $(\text{pass}, q_0, s_1, \emptyset)$ has a transition that accepts $c$ to $(\text{pass}, q_0, \delta(s_1, c), \emptyset)$. If $c$ is not an end anchor, this transition outputs the character $c$, otherwise, this transition outputs epsilon.

**Final States:**
- For any start mode states $(\text{start}, q_i, s_1, \emptyset)$, if $s_1$ does not contain any final states in the NFA, then it will be a final state.
- For any match mode states $(\text{match}, q_i, s_1, s_2)$, if $s_1$ does not contain any final states in the NFA, then it will be a final state.
- The initial state is a final state.
- For any pass mode states $(\text{pass}, q_0, s_1, \emptyset)$, if $s_1$ does not contain any final states in the NFA, then it will be a final state.

The final FST is the composition of the two FSTs. This is a functional FST.

**Whole Stream Reasoning:**
Because the above constructions are functional FSTs, we can construct a new FST that represents the whole stream translation.

#### Replacement Mode 2

**Pattern:** `sed <pattern-related-flags> (-n)? s/<pattern>/<replacement>/pg?`

For the line-based modeling, the flag `-n` is optional, we can simply modify the above constructions:

We compute the product of the above corresponding (composed) FST and the NFA of the pattern to obtain FST1. And we compute the product (FST2) of the complement of the NFA of the pattern and a FST that represents the constant empty output. Then we construct a new FST (FST3) by creating a new initial state and add empty transitions from it to the initial states of these two sub-FSTs (FST1 and FST2).

For the whole-stream-based output, `-n` flag is necessary here. Otherwise, the whole stream output may not be regular. We can construct a new FST that represents the whole stream translation based on the above constructions. For all final states in the final FST, if it belongs to the FST 1, add a transition that accepts "\n" and outputs "\n". If it belongs to the FST 2, add a transition that accepts "\n" and outputs epsilon. Non-final states in the final FST have no transitions that accept "\n".

#### Filter Mode

**Pattern:** `sed <pattern-related-flags> /<pattern>/d|(!d)` or `sed <pattern-related-flags> (-n)? /<pattern>/p|(!p)`

Same as `grep`.

Again, for the line-based modeling, when the flag is `p`, the flag `-n` is optional. But for the whole-stream-based modeling, `-n` flag is necessary, otherwise, the whole stream output may not be regular.

#### Delete Mode

**Pattern:** `sed (<number>,)?<number>d`

**Line-based reasoning:** For all $a$: $a \rightarrow a$ 

**Whole stream reasoning:** Simply modify the construction of cut, use the delimiter `\n` and require the whole stream input.





