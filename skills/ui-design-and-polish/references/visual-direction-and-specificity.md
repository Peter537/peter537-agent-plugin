# Visual Direction and Product Specificity

Use this reference for `create` and `redesign`, a consequential visual-language change, an explicit concern that a product interface looks generic, templated, homogenized, or insufficiently specific to its work, or a material specificity candidate discovered during review. Do not load it for every narrow UI edit.

Specificity is not visual novelty. A product-specific interface makes its actual tasks, information, states, and priorities easier to recognize and operate. A neutral or conventional treatment may be the strongest choice when it serves those needs.

## Establish a Visual Direction Contract

Before consequential visual work, record a compact contract:

| Field | Evidence to capture |
| --- | --- |
| User job | The decision, action, or repeated workflow the surface must support |
| Product evidence | Routes, domain objects, data shape, content, screenshots, tests, research, or user direction that constrains the design |
| Incumbent system | Established layout, tokens, components, typography, iconography, density, and interaction conventions |
| Differentiating choices | A few consequential choices that make the workflow clearer or more recognizable for this product |
| Familiar conventions to retain | Platform or domain patterns whose familiarity reduces learning and error |
| Inappropriate patterns | Treatments that conflict with the task, evidence, information density, risk, accessibility, or established system |

Keep the contract short enough to guide implementation. Do not turn adjectives such as "modern," "clean," or "premium" into unsupported product facts. If the evidence is incomplete, identify what is provisional.

## Separate quality from specificity

Ordinary quality defects include broken hierarchy, inconsistent spacing, inaccessible contrast, unclear actions, missing states, clipped content, and behavior regressions. Address them whether or not the interface is distinctive.

A specificity concern exists only when a treatment weakens the relationship between the interface and its product context. Examples include:

- a dashboard whose visual emphasis contradicts the decision users actually make;
- a data comparison converted into decorative cards that obscure aligned values;
- generic introductory copy replacing source, scope, freshness, or consequence information;
- repeated ornamental containers that flatten meaningful structural differences;
- a visual motif repeated without a role in hierarchy, state, brand, or interaction;
- a new surface that ignores an established domain convention without a demonstrated benefit.

Do not label an interface insufficiently specific merely because it uses cards, pills, gradients, a sidebar, a neutral palette, a standard component library, or a familiar layout. Those patterns may be justified by the product and platform.

## Use layered evidence

Evaluate a specificity concern from the strongest available layers:

1. **Product evidence:** user goals, domain concepts, risk, frequency, data relationships, and actual content.
2. **Repository evidence:** design tokens, component contracts, routes, state models, tests, analytics hooks, and prior decisions.
3. **Rendered evidence:** hierarchy, density, repetition, responsive behavior, interaction, and real states observed in the application.
4. **Heuristic evidence:** general design experience used to form a candidate, never to override stronger product evidence by itself.

Record which layers support or contradict the concern. A screenshot without product context can show repetition or weak hierarchy, but it cannot by itself establish that a familiar pattern is inappropriate.

## Classify concerns

Use one qualitative status:

- `confirmed`: multiple relevant evidence layers establish a material mismatch with the product or direction contract.
- `probable`: strong evidence indicates a mismatch, but one material context or rendered check remains unavailable.
- `candidate`: a heuristic signal deserves inspection but lacks enough evidence for a change recommendation.
- `exempted`: the pattern is justified by product, platform, accessibility, framework, compatibility, or incumbent-system evidence.

Only `confirmed` and well-supported `probable` concerns normally justify implementation. Preserve `candidate` observations as questions or gaps, not defects. Record why an `exempted` pattern is appropriate so later reviews do not repeatedly remove justified conventions.

## Choose differentiating decisions proportionately

Favor a small number of decisions that affect actual use:

- task-aligned information order and density;
- domain-appropriate comparison, grouping, and status representation;
- a stable action hierarchy for frequent or consequential work;
- meaningful use of established type, color, icon, and motion tokens;
- responsive behavior based on task priority rather than simple shrinking;
- state treatments that make source, freshness, permissions, failure, and recovery legible.

Avoid distinction for its own sake. Do not add decorative motion, custom controls, unusual navigation, novel icons, arbitrary tokens, or an extra styling system merely to appear unique. Familiar patterns are valuable when they reduce cognitive load and preserve platform expectations.

## Verify the direction

After implementation, compare the rendered result with the contract:

- Can the primary job and current state be identified without explanatory filler?
- Do hierarchy and density reflect the importance and frequency of the work?
- Do differentiating choices have evidence-backed roles rather than decorative novelty?
- Do retained conventions remain familiar, operable, and consistent with the system?
- Are the identified inappropriate patterns absent without removing information or capability?
- Do responsive, keyboard, zoom, theme, loading, error, empty, and permission states preserve the direction where applicable?
- Did the change preserve routes, semantics, data relationships, tests, and interaction behavior?

Use blind before-and-after review when an independent reviewer is available, but give the reviewer the user job and preservation constraints. Do not use a numerical taste score or declare one aesthetic universally superior.
