# MNEXA Vision Document — Section 2: The Cognitive Architecture

## 2.1 The central idea

MNEXA does not treat memory as a single store.

An intelligent system needs several fundamentally different kinds of memory because **remembering an event, knowing a fact, recognizing a pattern, knowing how to perform a task, and understanding why something happened are different cognitive operations**.

MNEXA therefore models intelligence as a set of interacting memory systems built over a common substrate.

```text
                         MNEXA

                   EXPERIENCE LAYER
                         │
                         ▼
              ┌─────────────────────┐
              │ EXPERIENCE LEDGER   │
              │ what actually       │
              │ happened            │
              └──────────┬──────────┘
                         │
          ┌──────────────┼───────────────┐
          │              │               │
          ▼              ▼               ▼
      EPISODIC        ENTITY          DECISION
       MEMORY         MEMORY           MEMORY
          │              │               │
          └───────┬──────┴──────┬────────┘
                  │             │
                  ▼             ▼
              TEMPORAL        CAUSAL
               MEMORY          MODEL
                  │             │
                  └──────┬──────┘
                         ▼
                   CONSOLIDATION
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      SEMANTIC       PROCEDURAL      PATTERN
       MEMORY          MEMORY         MEMORY
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                    PRINCIPLES
                         │
                         ▼
                    META-MEMORY
                         │
                         ▼
                  ACTIVE COGNITION
```

These are not isolated databases.

They are different **cognitive views over the same lived history**.

---

# 2.2 The canonical experience

Everything begins with experience.

MNEXA's atomic historical unit is not a text chunk.

It is an **Experience Record**.

Conceptually:

```text
EXPERIENCE
│
├── identity
├── timestamp
├── actor
├── environment
├── entities involved
├── observation
├── world state
├── goal
├── reasoning
├── decision
├── action
├── expected outcome
├── actual outcome
├── evidence
├── uncertainty
├── provenance
└── relationships to other experiences
```

An experience might represent:

* a conversation,
* a software deployment,
* a failed hypothesis,
* an API response,
* an agent decision,
* a customer interaction,
* a robot movement,
* an experiment,
* a correction from a human,
* a production incident.

The Experience Ledger answers:

> **What actually happened?**

Everything else MNEXA believes must ultimately remain traceable back to this layer.

This gives us an important invariant:

> **Knowledge may evolve. History must not.**

---

# 2.3 Episodic memory — the Scrub Jay layer

Episodic memory remembers events as situated experiences.

Every episode captures:

```text
WHAT
WHO
WHERE
WHEN
STATE
WHY
OUTCOME
```

For example:

```text
Episode E-9182

Agent:
Backend-17

Goal:
Reduce checkout latency

Context:
Production v172

Action:
Changed Redis expiry strategy

Outcome:
P99 improved initially

Later outcome:
Database load increased 42%

Final outcome:
Change rolled back
```

MNEXA can therefore reconstruct experiences rather than retrieve isolated fragments.

This is the agent's autobiographical memory.

---

# 2.4 Entity memory — the Dolphin layer

Everything important acquires a durable identity.

```text
ENTITY: customer.acme
ENTITY: service.checkout
ENTITY: person.alice
ENTITY: machine.robot-742
ENTITY: project.foundry
ENTITY: concept.cache-stampede
```

Names can change.

Descriptions can change.

Properties can change.

The identity persists.

Thus:

```text
"checkout API"
"payment checkout service"
"svc-checkout"
"Service #7812"
```

may all resolve to:

```text
ENTITY-7812
```

An entity accumulates its entire history:

```text
ENTITY
│
├── current state
├── previous states
├── relationships
├── interactions
├── relevant episodes
├── decisions involving it
├── learned properties
└── uncertainty
```

This prevents one of the most common failures in current AI memory:

**losing continuity because language changed.**

---

# 2.5 Relational memory — the Elephant layer

Individual entities are insufficient.

Intelligence depends heavily on relationships.

MNEXA maintains a living relational model:

```text
Service A
   │
depends_on
   ▼
Service B
   │
reads_from
   ▼
Database C

Decision D
   │
modified
   ▼
Service A

Incident I
   │
followed
   ▼
Decision D
```

Relationships themselves have memory:

```text
relationship:
Service A → depends_on → Service B

valid_from:
2026-02-14

valid_until:
present

confidence:
0.99

source:
deployment configuration

history:
previously depended on Service C
```

MNEXA therefore remembers not merely objects but **the structure of its world**.

---

# 2.6 Temporal memory

Time is a first-class dimension.

MNEXA must distinguish:

```text
true now

true previously

expected to become true

unknown whether still true
```

For example:

```text
January:
Service A uses PostgreSQL 17.

March:
Migration begins.

April:
Service A uses PostgreSQL 18.
```

A conventional knowledge base might simply overwrite 17 with 18.

MNEXA preserves:

```text
STATE(t)
```

This enables questions such as:

> What did we know at the time?

> When did this belief change?

> Which decision was rational given the information available then?

That prevents hindsight from corrupting historical reasoning.

---

# 2.7 Decision memory

This should be one of MNEXA's defining memory species.

Agents must remember not merely **what they did** but **why**.

```text
DECISION D-8821

Goal:
Choose persistence layer.

Context:
Financial ledger.

Constraints:
Strong consistency.
Auditability.
Moderate throughput.

Options considered:
PostgreSQL
DynamoDB
MongoDB

Chosen:
PostgreSQL

Reason:
Transactional invariants dominate scaling requirement.

Confidence at decision:
0.81

Expected outcome:
Reliable ledger semantics.

Actual outcome:
Pending.
```

Later MNEXA attaches reality:

```text
Actual outcome:
Successful.

Incidents attributable to decision:
0

Unexpected consequences:
Operational complexity higher than expected.

Updated assessment:
Decision remains correct.

Confidence:
0.94
```

Now decisions become **learning objects**.

---

# 2.8 Causal memory

MNEXA should distinguish:

```text
A happened before B
```

from:

```text
A contributed to B
```

and:

```text
A caused B under conditions C.
```

Causal knowledge must therefore accumulate evidence rather than appear magically.

Example:

```text
Hypothesis H-41

Synchronized cache expiry
        ↓
correlated cache misses
        ↓
database load spike
        ↓
request latency
```

Initially:

```text
confidence: 0.31
```

After repeated independent incidents:

```text
confidence: 0.87
```

With counterexamples:

```text
works primarily when:
traffic > threshold X
and cache-key concentration > threshold Y
```

This converts simplistic rules into **conditional causal understanding**.

---

# 2.9 Semantic memory — what MNEXA believes

Episodic memory says:

> This happened.

Semantic memory says:

> This is what I currently believe about the world.

For example:

```text
BELIEF

Correlated expiration of high-volume
cache keys can produce database load spikes.

confidence:
0.93

supported_by:
E12
E98
E177
E221

counterevidence:
E291

applicability:
high-throughput cached services

exceptions:
low traffic systems
```

Semantic memory is therefore not static truth.

It is **versioned belief backed by evidence**.

---

# 2.10 Procedural memory — how to do things

Knowledge must eventually become capability.

A repeatedly successful sequence can evolve into a procedure:

```text
Goal:
Diagnose sudden API latency

Procedure:
1. Compare deployment delta.
2. Partition latency by endpoint.
3. Inspect dependency traces.
4. Compare cache hit rate.
5. Inspect DB saturation.
6. Correlate timing.
7. test leading hypothesis.
```

Procedural memory stores:

```text
procedure
conditions
success rate
failure rate
known exceptions
required tools
evidence
version
```

Eventually an agent does not need to rediscover the procedure.

It **knows how**.

---

# 2.11 Pattern memory — the Immune System layer

Sometimes the important memory is not an exact event.

It is a structural resemblance.

MNEXA should discover:

```text
Episode A ─┐
Episode B ─┤
Episode C ─┼─► shared structural pattern
Episode D ─┤
Episode E ─┘
```

Example:

```text
PATTERN P-72

Symptoms:
recent deployment
cache-hit collapse
rapid DB connection increase
P99 increase

Common mechanism:
cache invalidation failure

Historical cases:
184

precision:
0.91
```

A new event can activate that pattern **before anyone explicitly searches for it**.

This becomes the basis of machine intuition.

---

# 2.12 Principle memory — abstraction beyond individual experiences

Repeated patterns can become broader principles.

```text
experiences
    ↓
patterns
    ↓
mechanisms
    ↓
principles
```

For example:

```text
PRINCIPLE

Systems that synchronize expiration
across highly correlated cached resources
should introduce expiry variance where
strict synchronization is unnecessary.
```

A principle is more general than the incidents that produced it.

This is where MNEXA begins compressing thousands of experiences into a small amount of powerful intelligence.

---

# 2.13 Predictive memory

Memory should not wait for a query.

The current situation itself should activate relevant knowledge.

Suppose an agent proposes:

```text
Set every cache entry to expire exactly
at midnight.
```

MNEXA may recognize:

```text
current intent
   +
architecture
   +
historical patterns
   +
causal model
```

and surface:

```text
Relevant risk:

This proposed configuration resembles
Pattern P-72.

17 previous incidents involved correlated
expiry boundaries.

Recommend evaluating expiry jitter.
```

This is:

> **Memory becoming anticipation.**

---

# 2.14 Counterfactual memory

MNEXA should preserve rejected alternatives.

Suppose:

```text
Chosen:
Architecture A

Rejected:
Architecture B
Architecture C
```

Six months later the consequences of A are known.

MNEXA can ask:

> Given everything we now know, was A still the best decision?

Counterfactual analysis can update future policy without rewriting history.

```text
At the time:
A was rational.

With later information:
B would likely have performed better.

Lesson:
Constraint X was underestimated.
```

This is far more valuable than simply labeling the original decision a failure.

---

# 2.15 Meta-memory — knowing what it knows

MNEXA must maintain a model of its own knowledge.

It should understand:

```text
high-confidence domains
low-confidence domains
stale knowledge
contradictory knowledge
poorly understood entities
unresolved hypotheses
missing evidence
historically unreliable sources
knowledge gaps
```

An agent should be able to know:

> I have extensive evidence about PostgreSQL migrations.

while simultaneously knowing:

> I have almost no reliable experience operating this particular distributed database.

That makes uncertainty structural rather than merely something an LLM claims verbally.

---

# 2.16 Forgetting is a cognitive operation

MNEXA should not make every memory equally accessible forever.

That would eventually destroy retrieval quality.

Instead:

```text
memory
  │
  ├── strengthened
  ├── consolidated
  ├── superseded
  ├── compressed
  ├── archived
  └── forgotten from active cognition
```

Forgetting does **not necessarily mean deletion**.

The immutable experience can remain.

What changes is its cognitive weight.

A useful memory grows stronger.

A stale observation becomes harder to activate.

A superseded belief stops influencing decisions.

A disproven hypothesis remains historically inspectable but no longer behaves as knowledge.

---

# 2.17 Personal Super-Memory

Every agent gets an independent cognitive history.

```text
               AGENT A

        ┌─────────────────┐
        │ Working Memory  │
        ├─────────────────┤
        │ Episodic        │
        │ Entity          │
        │ Decision        │
        │ Semantic        │
        │ Procedural      │
        │ Pattern         │
        │ Meta-memory     │
        └─────────────────┘
```

This memory contains things that should **never automatically become global knowledge**:

* tentative hypotheses,
* private interactions,
* experimental strategies,
* mistakes,
* unfinished reasoning,
* domain-specific experience,
* temporary preferences,
* low-confidence observations.

This gives each agent a genuine **individual cognitive history**.

---

# 2.18 Collective Intelligence

Agents contribute selected learnings upward.

But there is a hard rule:

> **Agents publish claims. They do not publish truth.**

The flow is:

```text
PERSONAL EXPERIENCE

        ↓

LOCAL LEARNING

        ↓

CANDIDATE KNOWLEDGE

        ↓

EVIDENCE PACKAGE

        ↓

CORROBORATION

        ↓

VERIFICATION

        ↓

DOMAIN KNOWLEDGE

        ↓

BROADER VALIDATION

        ↓

COLLECTIVE INTELLIGENCE
```

The shared substrate therefore consists primarily of:

```text
validated beliefs
validated patterns
causal models
proven procedures
reusable skills
principles
failure modes
known uncertainty
```

rather than raw agent thoughts.

---

# 2.19 The promotion ladder

MNEXA should explicitly model epistemic maturity.

```text
L0  EXPERIENCE
        │
        ▼
L1  OBSERVATION
        │
        ▼
L2  HYPOTHESIS
        │
        ▼
L3  CANDIDATE
        │
        ▼
L4  CORROBORATED
        │
        ▼
L5  VALIDATED
        │
        ▼
L6  ESTABLISHED
```

Knowledge can also move downward.

```text
ESTABLISHED
     ↓
new contradictory evidence
     ↓
VALIDATED
     ↓
major contradiction
     ↓
CANDIDATE
```

Nothing is permanently protected from reality.

---

# 2.20 Intelligence scopes

The hierarchy from Section 1 becomes architectural:

```text
                    L4
             CIVILIZATION MEMORY
                     ▲
                     │
                    L3
            ORGANIZATION MEMORY
                     ▲
                     │
                    L2
               DOMAIN MEMORY
                     ▲
                     │
                    L1
               AGENT MEMORY
                     ▲
                     │
                    L0
              WORKING MEMORY
```

An experience normally originates at the bottom.

Knowledge earns its way upward.

Relevant intelligence flows downward.

---

# 2.21 Knowledge activation

The collective system could eventually contain trillions of memories.

Putting all of them into an agent's context would be catastrophic.

MNEXA therefore distinguishes:

```text
AVAILABLE INTELLIGENCE
```

from:

```text
ACTIVE INTELLIGENCE
```

At any moment, activation depends on:

```text
current goal
+
active entities
+
current environment
+
semantic similarity
+
causal relevance
+
temporal relevance
+
historical usefulness
+
agent specialization
+
permissions
+
uncertainty
```

The principle is:

> **Every authorized agent can access the civilization's intelligence. Only the intelligence relevant to the present situation enters cognition.**

---

# 2.22 Consolidation — the heart of MNEXA

This is likely the most important subsystem in the entire project.

Agents create enormous quantities of experience.

MNEXA must continuously metabolize it.

```text
10,000 experiences
        ↓
1,300 meaningful episodes
        ↓
240 recurring patterns
        ↓
51 candidate mechanisms
        ↓
18 validated principles
        ↓
7 reusable procedures
        ↓
3 durable capabilities
```

Consolidation performs functions analogous to biological sleep:

```text
deduplicate
connect
cluster
compare
find contradictions
detect recurrence
identify exceptions
infer candidate causality
abstract
compress
strengthen
weaken
proceduralize
```

This is how MNEXA prevents memory from becoming an infinitely growing landfill.

---

# 2.23 Memory evolution

A memory object is never just written and forgotten.

It has a lifecycle.

```text
BIRTH
  ↓
USE
  ↓
EVIDENCE
  ↓
REINFORCEMENT
  ↓
CONTRADICTION
  ↓
REVISION
  ↓
ABSTRACTION
  ↓
CONSOLIDATION
  ↓
POSSIBLE PROMOTION
  ↓
POSSIBLE DECAY
```

That gives us an important concept:

> **MNEXA memory is evolutionary rather than archival.**

---

# 2.24 The two loops

At the heart of MNEXA are really **two coupled learning loops**.

### Individual loop

```text
Agent acts
   ↓
experiences outcome
   ↓
personal memory changes
   ↓
agent behaves better
   ↺
```

### Civilization loop

```text
Many agents act
      ↓
candidate discoveries emerge
      ↓
evidence accumulates
      ↓
knowledge is verified
      ↓
collective substrate changes
      ↓
all relevant agents improve
      ↺
```

The first creates **individual intelligence**.

The second creates **collective intelligence**.

MNEXA connects them.

---

# 2.25 The defining architecture

The resulting system looks like this:

```text
 ┌──────────┐   ┌──────────┐   ┌──────────┐
 │ Agent A  │   │ Agent B  │   │ Agent C  │
 │          │   │          │   │          │
 │ PERSONAL │   │ PERSONAL │   │ PERSONAL │
 │  MNEXA   │   │  MNEXA   │   │  MNEXA   │
 └────┬─────┘   └────┬─────┘   └────┬─────┘
      │              │              │
      │ candidate    │ learning     │
      │              │              │
      └──────────────┼──────────────┘
                     │
                     ▼
        ╔══════════════════════════╗
        ║                          ║
        ║     MNEXA COLLECTIVE     ║
        ║                          ║
        ║ Entity Model             ║
        ║ Experience Graph         ║
        ║ Temporal Model           ║
        ║ Decision Memory          ║
        ║ Causal Models            ║
        ║ Semantic Knowledge       ║
        ║ Pattern Library          ║
        ║ Procedures / Skills      ║
        ║ Principles               ║
        ║ Meta-Memory              ║
        ║                          ║
        ║ ──────────────────────── ║
        ║ Consolidation            ║
        ║ Verification             ║
        ║ Knowledge Evolution      ║
        ║ Relevance Activation     ║
        ║                          ║
        ╚════════════╤═════════════╝
                     │
              relevant intelligence
                     │
        ┌────────────┼─────────────┐
        ▼            ▼             ▼
      Agent A      Agent B       Agent C
```

---

# 2.26 The architectural law

I would lock one law above everything in this section:

> **Experience is local by default. Knowledge is shared only when earned. Intelligence becomes active only when relevant.**

That protects the system simultaneously from:

* memory pollution,
* collective hallucination,
* information overload,
* premature generalization,
* one-agent epistemic contamination.

And it gives us the architecture necessary for the original ambition:

> **Every agent possesses a super-memory of its own, while every agent can benefit from the verified intelligence accumulated by the whole population.**

---

## Section 2 principle

> **MNEXA does not remember everything equally. It transforms experience into progressively more useful forms of intelligence.**