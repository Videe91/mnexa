# MNEXA Vision Document — Section 5: Recall, Attention & Machine Intuition

## 5.1 The central problem

A memory system with perfect storage can still be cognitively useless.

If MNEXA eventually contains:

```text
10 memories
        → trivial

1 million memories
        → retrieval problem

1 billion memories
        → attention problem

1 trillion memories
        → intelligence-routing problem
```

the challenge is no longer:

> **Can the system find something similar?**

It becomes:

> **Can MNEXA activate the right few pieces of intelligence, at the right moment, for the right agent, before irrelevant memory overwhelms cognition?**

This is where MNEXA must move beyond conventional RAG.

---

# 5.2 Retrieval is not recall

Traditional retrieval looks approximately like:

```text
query
  ↓
embedding
  ↓
nearest neighbours
  ↓
top-k chunks
  ↓
context
```

MNEXA recall should instead behave like:

```text
CURRENT SITUATION
       │
       ├── goal
       ├── entities
       ├── environment
       ├── recent events
       ├── intended action
       ├── uncertainty
       ├── predicted consequences
       └── agent identity
               │
               ▼
        MEMORY ACTIVATION
               │
      thousands compete
               │
               ▼
       handful become active
```

The agent should not always need to formulate the correct search query.

> **The situation itself should become the query.**

---

# 5.3 MNEXA Attention

We therefore introduce a central cognitive mechanism:

# **MNEXA Attention**

Attention decides which subset of available intelligence becomes active cognition.

Conceptually:

```text
AVAILABLE INTELLIGENCE
      billions+
          │
          ▼
       ATTENTION
          │
          ▼
     ACTIVE SET
       perhaps
      tens / hundreds
          │
          ▼
        AGENT
```

The objective is not maximal recall.

It is:

> **maximum useful cognition under a finite attention budget.**

---

# 5.4 Context is multidimensional

A conventional vector query largely asks:

> Which text is semantically similar?

MNEXA asks many questions simultaneously.

```text
What am I trying to achieve?

Which entities are involved?

What just changed?

What am I about to do?

Which risks exist?

Which previous outcomes resemble this?

Which causal mechanisms could apply?

Which procedures have worked here?

Which principles constrain the action?

What knowledge am I missing?

Which memories have historically helped in this situation?
```

The current cognitive state therefore becomes a structured **Context Frame**.

---

# 5.5 The Context Frame

Conceptually:

```text
CONTEXT FRAME C-882

Agent:
Infrastructure-Agent-19

Goal:
Deploy database schema change

Active entities:
Payments
PostgreSQL
Migration-882

Intent:
Drop legacy column

Environment:
production

Recent events:
migration test passed staging

Constraints:
zero downtime

Risk:
high

Uncertainty:
medium

Expected outcome:
successful migration
```

This frame becomes MNEXA's primary recall signal.

---

# 5.6 Many retrieval systems operate simultaneously

MNEXA should not rely on one index.

The same context can activate memory through several independent routes:

```text
                    CONTEXT
                       │
     ┌─────────────────┼─────────────────┐
     ▼                 ▼                 ▼
 SEMANTIC           ENTITY           TEMPORAL
 similarity        relevance         relevance
     │                 │                 │
     ├─────────────────┼─────────────────┤
     ▼                 ▼                 ▼
 CAUSAL            STRUCTURAL       PROCEDURAL
 relevance         analogy          relevance
     │                 │                 │
     ├─────────────────┼─────────────────┤
     ▼                 ▼                 ▼
 OUTCOME            RISK           HISTORICAL
 similarity        relevance         utility
     │                 │                 │
     └─────────────────┴─────────────────┘
                       │
                       ▼
                 CANDIDATE SET
```

Then MNEXA decides which memories deserve cognition.

Embeddings remain useful.

They simply stop being the entire architecture.

---

# 5.7 Associative recall — the Nutcracker principle

The Clark's nutcracker does not perform a textual search for:

> “Where was seed cache #8,271?”

Environmental cues activate location memory.

MNEXA should work similarly.

Suppose the current context contains:

```text
Redis
+
high traffic
+
TTL modification
+
midnight boundary
```

Without the agent asking anything, those cues may activate:

```text
Incident E-821
Pattern P-18
Principle P-4
Procedure S-91
```

because together they form a familiar cognitive configuration.

This is **associative addressing**.

---

# 5.8 Spreading activation

A recalled memory can activate neighboring memories.

Example:

```text
Current context
     ↓
Service Payments
     ↓
Decision D91
     ↓
Incident I42
     ↓
Pattern P7
     ↓
Principle P3
```

The search therefore does not necessarily happen in one jump.

Relevant concepts activate related concepts.

```text
cue
 ↓
memory
 ↓
association
 ↓
related memory
 ↓
higher abstraction
```

This allows MNEXA to reconstruct useful context even when no individual memory perfectly matches the original request.

---

# 5.9 Activation should decay with distance

Unlimited spreading activation would explode across the entire knowledge graph.

Therefore activation should weaken as it travels.

Conceptually:

```text
direct match             ██████████

1 relationship away      ███████

2 relationships away     ████

3 relationships away     ██

weakly connected         ░
```

But strong evidence, high salience or known utility may overcome distance.

This creates controlled associative thought.

---

# 5.10 Memory competition

Nature does not consciously surface every relevant memory simultaneously.

Memories compete for attention.

MNEXA should do the same.

Imagine 3,200 candidate memories.

They compete based on signals such as:

```text
goal relevance
causal relevance
entity relevance
prediction value
historical usefulness
risk
confidence
specificity
novelty
temporal validity
agent specialization
```

Eventually perhaps:

```text
3,200 candidates
      ↓
240 plausible
      ↓
37 highly relevant
      ↓
8 active
```

This creates a cognitive bottleneck intentionally.

---

# 5.11 Inhibition is as important as activation

A critical principle from biological cognition is that intelligence requires suppressing irrelevant signals.

MNEXA therefore needs **memory inhibition**.

Examples:

```text
similar but wrong domain
→ suppress

obsolete version
→ suppress

low-confidence speculation
→ suppress

duplicate of stronger memory
→ suppress

knowledge superseded by newer evidence
→ suppress

agent lacks permission
→ block

frequently retrieved but historically useless
→ suppress strongly
```

This may ultimately matter as much as retrieval itself.

> **A powerful memory system must know what not to remember right now.**

---

# 5.12 Active memory is temporary

MNEXA distinguishes:

```text
PERSISTENT MEMORY
```

from:

```text
ACTIVE MEMORY
```

Persistent memory may contain everything MNEXA knows.

Active memory is the tiny subset currently shaping cognition.

```text
Persistent:
1,000,000,000 objects

Active:
42 objects
```

Active memory changes continuously as the situation changes.

---

# 5.13 Working memory becomes managed cognition

The LLM context window becomes only one implementation of working memory.

MNEXA can maintain a structured cognitive workspace:

```text
ACTIVE GOAL

ACTIVE ENTITIES

CURRENT PLAN

ACTIVE BELIEFS

CURRENT RISKS

RELEVANT EPISODES

ACTIVE PROCEDURES

OPEN QUESTIONS

UNCERTAINTIES

EXPECTED OUTCOMES
```

Only necessary portions need to be serialized into model context.

This separates:

> **what the system currently knows**

from:

> **what the model currently sees.**

That distinction is fundamental to model independence.

---

# 5.14 Attention budgets

More information does not necessarily produce better reasoning.

MNEXA should explicitly budget cognition.

Example:

```text
working set budget
│
├── 25% current-world state
├── 20% critical constraints
├── 20% prior relevant knowledge
├── 15% procedures
├── 10% counterevidence
└── 10% uncertainty / alternatives
```

Those percentages are illustrative.

The important principle is:

> **Memory consumption is a scarce cognitive resource.**

MNEXA should optimize what earns that resource.

---

# 5.15 Memory diversity

A dangerous retrieval system may retrieve five different memories that all say effectively the same thing.

MNEXA should prefer a useful cognitive portfolio.

For example:

```text
1 strongest supporting principle

1 relevant historical episode

1 known failure case

1 useful procedure

1 counterexample

1 unresolved uncertainty
```

may be more valuable than:

```text
6 supporting memories
```

This protects agents against one-sided recall.

---

# 5.16 Counter-memory

Whenever a high-impact belief becomes active, MNEXA may intentionally retrieve its strongest contradiction.

```text
Active belief:
Architecture X is appropriate.

            +

Counter-memory:
Architecture X failed badly
under condition Y.
```

This creates an automatic cognitive safeguard against confirmation bias.

For critical decisions:

> **MNEXA should recall not only why something may work, but the best evidence that it may fail.**

---

# 5.17 Prospective memory

Biological memory is not only about the past.

Humans also remember:

> When X occurs, I need to do Y.

MNEXA needs **prospective memory**.

Example:

```text
MEMORY:
When deployment reaches production,
verify replication lag.
```

It should remain dormant until:

```text
deployment.status == production
```

Then activate automatically.

This allows memories to contain **future activation conditions**.

---

# 5.18 Event-triggered cognition

A memory can therefore subscribe to reality.

```text
"If user mentions cancellation..."
"When CPU > 90%..."
"If this customer returns..."
"When migration begins..."
"If confidence falls below threshold..."
"On the next interaction with Entity X..."
```

Instead of constantly searching everything:

```text
world event
    ↓
matches dormant memory trigger
    ↓
memory activates
```

This is substantially more efficient.

---

# 5.19 Predictive recall

MNEXA should also ask:

> What will probably become relevant soon?

Suppose Agent A begins:

```text
modify authentication architecture
```

MNEXA predicts likely next concerns:

```text
session migration
token revocation
backwards compatibility
authorization
rollback
security testing
```

and quietly preloads relevant knowledge.

Before the agent asks:

```text
"I need to think about token revocation."
```

MNEXA may already have the relevant intelligence ready.

---

# 5.20 Pre-attention

This gives us a useful concept:

# **Pre-attention**

```text
Current intent
     ↓
likely future cognitive needs
     ↓
memory preactivation
     ↓
lower latency / better reasoning
```

Pre-attention should remain cheap and probabilistic.

Incorrect predictions simply decay without reaching active cognition.

---

# 5.21 Machine intuition

We should define this term carefully.

MNEXA **machine intuition** is not mystical.

It means:

> **The rapid activation of learned patterns, risks, analogies or likely outcomes before explicit deliberate reasoning has reconstructed why they are relevant.**

Example:

```text
Agent examines architecture.

MNEXA:
Something looks dangerous.

Why?

Pattern P-891 resembles this structure
across 73 previous incidents.
```

This is computationally understandable.

```text
many historical experiences
        ↓
consolidated patterns
        ↓
current structural match
        ↓
fast activation
```

That is our definition of machine intuition.

---

# 5.22 Intuition must remain explainable

Fast pattern recognition should never become:

```text
"Trust me."
```

MNEXA should support:

```text
INTUITION

"This architecture appears risky."

        ↓ ask why

Pattern P-891
        ↓
73 episodes
        ↓
11 organizations
        ↓
failure mechanism
        ↓
known exceptions
```

Thus intuition has **depth on demand**.

Fast cognition can remain fast while evidence stays available.

---

# 5.23 Two recall paths

MNEXA should ultimately have at least two cognitive pathways.

### Fast path

```text
context
 ↓
strong known pattern
 ↓
procedure/reflex
 ↓
action
```

Milliseconds.

### Deliberative path

```text
context
 ↓
retrieve evidence
 ↓
compare competing memories
 ↓
causal reasoning
 ↓
counterfactuals
 ↓
decision
```

Slower but deeper.

The system chooses based on:

```text
risk
novelty
confidence
ambiguity
consequence
```

---

# 5.24 Familiarity

MNEXA should know whether a situation is familiar.

Example:

```text
Scenario A:
97% structural overlap with
2,000 prior experiences.

→ highly familiar
```

versus:

```text
Scenario B:
weak overlap with anything known.

→ unfamiliar
```

This should affect cognition.

Highly familiar situations may justify fast-path reasoning.

Unfamiliar situations should trigger:

```text
more exploration
more external evidence
lower confidence
less reliance on reflexes
```

---

# 5.25 Recognition without false certainty

Similarity is not identity.

MNEXA must distinguish:

```text
This IS Pattern X.
```

from:

```text
This RESEMBLES Pattern X.
```

Therefore every activation has something like:

```text
match strength
applicability confidence
important mismatches
```

For example:

```text
Pattern match: 0.88

BUT:

historical examples used PostgreSQL
current system uses distributed KV store

→ reduce transfer confidence
```

This prevents analogy from silently becoming fact.

---

# 5.26 Retrieval through structure, not just language

Two situations may use completely different vocabulary yet have identical structure.

For example:

```text
BIOLOGY:
population collapses after shared dependency fails

DISTRIBUTED SYSTEM:
services collapse after shared dependency fails
```

Semantic text similarity may be poor.

Structural memory can recognize:

```text
many dependent nodes
        ↓
single shared dependency
        ↓
dependency failure
        ↓
system-wide collapse
```

This enables deep cross-domain analogy.

---

# 5.27 Analogical memory

MNEXA should explicitly support:

```text
CURRENT PROBLEM
      ↓
structural representation
      ↓
search across domains
      ↓
analogous mechanisms
```

This may allow:

```text
biology
    ↓
software

economics
    ↓
agent coordination

immune systems
    ↓
cybersecurity
```

It could become one of the engines for novel idea formation.

---

# 5.28 Recall episodes, not only conclusions

Sometimes a principle is insufficient.

An agent may need the full historical story.

Example:

```text
Principle:
Avoid synchronized expiry.
```

may be enough normally.

But during a complex incident:

```text
retrieve Episode E91

What was changed?
What happened next?
What measurements changed?
What was tried?
What eventually fixed it?
```

MNEXA should dynamically move between:

```text
compressed knowledge
        ↕
raw experience
```

depending on cognitive need.

---

# 5.29 Adaptive resolution

Memory therefore has different resolutions.

```text
LEVEL 1
reflex

LEVEL 2
skill

LEVEL 3
principle

LEVEL 4
pattern

LEVEL 5
episode

LEVEL 6
raw experience
```

Routine cognition starts high in the abstraction hierarchy.

If uncertainty rises, MNEXA can descend toward evidence.

This reduces cognitive cost while preserving auditability.

---

# 5.30 Memory reconstruction

MNEXA need not permanently store every possible summary.

It can reconstruct context from:

```text
episode
+
entities
+
relationships
+
world state
+
knowledge
```

for the current cognitive purpose.

This allows the same historical event to be recalled differently depending on the task.

Example:

```text
Security agent
→ recalls security implications.

Database agent
→ recalls DB consequences.

Managerial agent
→ recalls operational impact.
```

Same history.

Different useful reconstruction.

---

# 5.31 Recall should respect identity

Agent memory should be personalized.

Two agents facing the same event may receive different recall.

```text
Agent A:
experienced 900 similar events

Agent B:
newly instantiated
```

For A, MNEXA may activate:

```text
personal intuition
+
collective knowledge
```

For B:

```text
collective knowledge
+
more explicit supporting evidence
```

A mature agent may need fewer explanations because its own memory provides context.

---

# 5.32 Recall should respect expertise

Suppose the task involves database security.

MNEXA may combine intelligence from:

```text
database guild
+
security guild
+
organization-specific systems
+
personal agent experience
```

The context is routed across the shared substrate.

Thus recall becomes partly:

> **Who—or what part of the civilization—already knows this?**

---

# 5.33 Collective recall without collective overload

An agent should not query millions of agents.

MNEXA should query **shared distilled intelligence first**.

```text
Agent
 ↓
Collective Knowledge
 ↓
sufficient?
 ├── yes → use
 └── no
       ↓
     expertise graph
       ↓
     specialist agents
```

Direct agent consultation becomes a deeper fallback, not the default.

---

# 5.34 Memory can ask for help

If MNEXA detects that relevant memory is weak:

```text
high-risk task
+
low familiarity
+
low evidence
```

it should signal:

```text
KNOWLEDGE GAP
```

This may cause the agent to:

```text
search externally
run experiment
consult another agent
request human judgment
simulate alternatives
```

Knowing when not to rely on memory is itself an intelligent behavior.

---

# 5.35 Retrieval confidence

MNEXA needs to distinguish:

```text
I found nothing relevant.
```

from:

```text
I searched poorly.
```

and:

```text
Relevant intelligence probably does not exist.
```

Meta-memory should estimate:

```text
coverage confidence
retrieval confidence
knowledge confidence
```

Those are different.

This prevents false certainty based on retrieval failure.

---

# 5.36 Attention should be outcome-trained

This is where the system begins learning how to remember.

For every recalled memory:

```text
Memory M
    ↓
activated for Context C
    ↓
influenced Decision D
    ↓
Outcome O
```

MNEXA records whether that activation helped.

Over millions of cases it can learn:

```text
For context type X,
causal memories are highly useful.

For context type Y,
recent episodes matter more.

For context type Z,
semantic similarity creates distraction.
```

Attention itself becomes learned.

---

# 5.37 Recall utility

Every activation can receive downstream utility:

```text
HELPFUL
NEUTRAL
DISTRACTING
MISLEADING
CRITICAL
```

Eventually this can be inferred from outcomes rather than manually labeled.

Then:

```text
frequently helpful memory
→ easier to activate

frequently distracting memory
→ increasingly inhibited
```

This gives recall evolutionary pressure.

---

# 5.38 Retrieval regret

MNEXA should also study memories it **failed to activate**.

Suppose:

```text
Incident occurs.

Agent makes bad decision.

Afterward MNEXA discovers:
Memory M would probably have prevented it.
```

That creates a:

# **Retrieval Regret**

```text
useful memory existed
        +
was not activated
        +
outcome suffered
        ↓
attention policy learns
```

This may be one of the most powerful learning signals for the memory system.

---

# 5.39 Attention regret

The reverse also matters.

```text
Memory M was activated
        ↓
consumed context
        ↓
misdirected reasoning
        ↓
worse outcome
```

MNEXA learns:

```text
This class of memory should be
less cognitively dominant here.
```

Now both omission and distraction improve future attention.

---

# 5.40 Cognitive provenance

Every important decision should record not merely:

```text
what knowledge existed
```

but:

```text
what knowledge was actually active
when the decision was made
```

For example:

```text
DECISION D-41

Active knowledge:
P7-v2
E91
Skill S18

Not activated:
P19

Outcome:
failure
```

This lets MNEXA investigate:

> Was the decision wrong because knowledge was wrong, or because the correct knowledge was not recalled?

That distinction is essential.

---

# 5.41 Recall replay

After important outcomes, MNEXA can replay cognition.

```text
What did the agent see?

What did MNEXA surface?

What was ignored?

What was missing?

Which memories should have activated?

Which memories distracted?
```

This closes the attention-learning loop.

---

# 5.42 Predictive memory can become anticipation

Eventually MNEXA should learn sequences.

```text
A usually leads to B.

B usually leads to C.

When A begins,
C may soon matter.
```

Therefore:

```text
A detected
   ↓
prepare knowledge for B
   ↓
preactivate knowledge for possible C
```

The system begins cognitively preparing for probable futures.

---

# 5.43 Temporal horizons

Different memories matter across different horizons.

```text
NOW
milliseconds–seconds

SOON
minutes

TASK
hours

PROJECT
days/months

STRATEGIC
years
```

MNEXA attention should reason across all of them.

For example:

```text
Action X

immediate:
faster response

week:
higher infrastructure cost

year:
architectural lock-in
```

A strong memory system should surface consequences at the appropriate horizon.

---

# 5.44 Goal-conditioned recall

The same situation can produce different relevant memories depending on the goal.

Example:

```text
Entity:
Database
```

Goal A:

```text
reduce cost
```

activates different intelligence from:

```text
maximize reliability
```

or:

```text
investigate breach
```

So retrieval relevance is:

```text
memory relevance
=
relationship to situation
AND
relationship to goal
```

not just similarity to the words used.

---

# 5.45 Intent-conditioned recall

Even more important than the current state may be:

> **What is the agent about to do?**

Suppose:

```text
Current state:
healthy production DB
```

Nothing is wrong.

But agent intent is:

```text
DROP COLUMN customer_reference
```

MNEXA should immediately recall:

```text
dependencies
past migrations
rollback procedures
data retention requirements
downstream consumers
similar incidents
```

before the action occurs.

This converts memory into prevention.

---

# 5.46 Risk-conditioned attention

High consequence should widen cognition.

```text
low-risk action
      ↓
small active set
      ↓
fast cognition
```

versus:

```text
high-risk action
      ↓
larger evidence set
      ↓
counterexamples
      ↓
causal inspection
      ↓
policy checks
      ↓
slower cognition
```

Attention becomes risk-adaptive.

---

# 5.47 Novelty-conditioned attention

If a situation is extremely familiar:

```text
known pattern
+
strong evidence
+
low risk
```

use compressed cognition.

If it is novel:

```text
weak historical match
+
high uncertainty
```

MNEXA should avoid forcing old patterns onto it.

Instead:

```text
reduce reflex reliance
broaden search
retrieve analogies carefully
seek new evidence
```

This helps prevent overfitting to history.

---

# 5.48 Permission is part of attention

A memory may be highly relevant but unavailable to an agent.

Therefore activation happens after authorization constraints.

```text
relevant
+
high utility
+
not authorized
=
not cognitively accessible
```

MNEXA can still perhaps expose:

```text
Relevant restricted knowledge exists.
Escalation may be required.
```

without leaking its contents.

---

# 5.49 Attention firewall

Collective memory also creates an attack surface.

An adversary might create memories designed to activate constantly.

MNEXA therefore needs an **Attention Firewall** against:

```text
prompt injection memories
malicious high-salience objects
artificial relevance inflation
retrieval hijacking
repeated propaganda
poisoned associative links
```

No memory should be able to declare itself important merely through its text.

Importance must come from trusted metadata, evidence and learned utility.

---

# 5.50 Memory cannot command the agent

Another law:

> **Retrieved memory is evidence, not authority.**

Even a strongly established memory can be inappropriate in a new situation.

Therefore:

```text
MEMORY
  ↓
informs cognition

not:

MEMORY
  ↓
unconditionally controls action
```

Only explicitly authorized policies/reflexes may acquire stronger control—and even those remain bounded and reversible.

---

# 5.51 The emergence of familiarity, intuition and expertise

With enough experience, an agent's cognitive progression may look like:

```text
NOVICE

explicit retrieval
large evidence sets
slow reasoning
frequent uncertainty

       ↓ experience

COMPETENT

better recall
strong procedures
recognizable patterns

       ↓ experience

EXPERT

rapid pattern activation
strong causal models
better inhibition
better anticipation
fewer irrelevant memories

       ↓

MATURE EXPERT

knows:
what applies
what does not
when intuition is trustworthy
when to distrust itself
```

This is an important target.

MNEXA should not merely increase what an agent knows.

It should change **how efficiently the agent thinks**.

---

# 5.52 Machine intuition must be measurable

We should never accept:

> “The agent feels smarter.”

We should measure whether anticipatory memory improves outcomes.

For example:

```text
prevented errors
decision accuracy
time to correct solution
prediction accuracy
relevant recall precision
missed-memory rate
context consumption
unnecessary retrieval
counterexample coverage
novel-case performance
```

Machine intuition should earn its name through performance.

---

# 5.53 The no-memory baseline

Every MNEXA evaluation should compare against:

```text
same base model
same tools
same task
NO MNEXA
```

Then:

```text
same base model
same tools
same task
WITH MNEXA
```

If performance does not materially improve:

> the memory is not creating intelligence.

This protects the project from building architectural complexity that merely looks sophisticated.

---

# 5.54 The recall challenge

One of MNEXA's first Grand Challenges should therefore be:

### **Needle Before You Know You Need It**

Give an agent enormous historical memory.

Create a new task where one obscure historical experience is crucial—but the task never directly asks for it.

MNEXA must:

```text
recognize situation
      ↓
activate relevant historical memory
      ↓
surface it before decision
      ↓
improve outcome
```

A vector search driven by the agent's explicit query should not be enough.

That would directly test anticipatory recall.

---

# 5.55 The intuition challenge

Another Grand Challenge:

Expose agents to thousands of structured experiences.

Do not modify their model weights.

Later expose them to unseen situations that contain the same underlying structural failure patterns but different vocabulary and entities.

Success means:

```text
Agent + MNEXA
```

recognizes the latent danger substantially better than:

```text
same Agent - MNEXA
```

That would provide evidence of **memory-derived machine intuition**.

---

# 5.56 The attention challenge

Give MNEXA:

```text
1,000 useful memories

+

999,000 plausible but irrelevant memories
```

The system must maintain reasoning quality.

This tests whether increasing memory size eventually degrades intelligence.

The goal should be:

> **Intelligence quality scales with useful experience without requiring cognition to scale linearly with stored experience.**

That is critical.

---

# 5.57 The ultimate recall architecture

```text
                    CURRENT REALITY
                          │
                          ▼
                    CONTEXT FRAME
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
        GOAL            INTENT          ENTITIES
          │               │               │
          └───────────────┼───────────────┘
                          ▼
                  ASSOCIATIVE ACTIVATION
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
     SEMANTIC          CAUSAL          STRUCTURAL
        │                 │                 │
     TEMPORAL          EPISODIC        PROCEDURAL
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
                     CANDIDATES
                          │
                          ▼
                  ATTENTION FIREWALL
                          │
                          ▼
               COMPETITION + INHIBITION
                          │
                ┌─────────┼──────────┐
                ▼         ▼          ▼
              SUPPORT   COUNTER     RISK
                │         │          │
                └─────────┼──────────┘
                          ▼
                      ACTIVE SET
                          │
                          ▼
                        AGENT
                          │
                          ▼
                       DECISION
                          │
                          ▼
                        ACTION
                          │
                          ▼
                       OUTCOME
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
       Recall Utility            Retrieval Regret
             │                         │
             └────────────┬────────────┘
                          ▼
                 ATTENTION LEARNING
                          │
                          └──────────────↺
```

---

# 5.58 The governing laws of recall

I would lock these:

1. **The situation is the primary query.**
2. **Available memory and active memory are different things.**
3. **Recall is competition for finite cognitive attention.**
4. **Suppressing irrelevant memory is as important as finding relevant memory.**
5. **High-impact beliefs should bring their strongest counterevidence with them.**
6. **Memory should activate before an action when it can predict relevant consequences.**
7. **Similarity produces hypotheses of relevance, not certainty of applicability.**
8. **Recall quality must be judged by downstream outcomes.**
9. **Missed useful memories are learning signals.**
10. **A mature memory system must learn how, when and what to recall.**

---

# 5.59 What MNEXA machine intuition really becomes

The progression is:

```text
EXPERIENCE
      ↓
MEMORY
      ↓
CONSOLIDATION
      ↓
PATTERN
      ↓
CAUSAL UNDERSTANDING
      ↓
REPEATED UTILITY
      ↓
FAST ASSOCIATIVE ACTIVATION
      ↓
ANTICIPATION
```

So machine intuition isn't another model.

It is what happens when **deep accumulated memory becomes fast enough to influence cognition before deliberate search begins**.

And unlike biological intuition, MNEXA can always descend back through:

```text
intuition
   ↓
principle
   ↓
pattern
   ↓
episode
   ↓
evidence
```

to ask:

> **Why did I think that?**

---

## Section 5 principle

> **Perfect memory is useless without selective attention. MNEXA must not merely remember the past; it must know which part of the past matters to the future that is about to happen.**

And the phrase I would lock for this section is:

> **Recall what matters before you know you need it.**
