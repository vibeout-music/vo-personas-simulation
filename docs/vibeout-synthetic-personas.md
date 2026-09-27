# Designing Persistent Synthetic Personas for Vibeout

## Objective

Design an initial population of up to **20,000 persistent synthetic users** to simulate plausible long-term behaviour in Vibeout, a platform centred on music and emotions.

A JSON representation of a user profile is useful as a contract and example, but static profiles alone do not simulate behaviour. It is important to distinguish between:

> **Persona = relatively stable traits and preferences**  
> **Synthetic user = persistent persona + current state + behavioural rules + queryable history**

The complete simulation should represent who each user is, their current state and context, how they decide to act in response to what the application shows them, and how those actions and states evolve across multiple execution batches.

`SocialEdge` and persona affinity remain useful domain concepts, but they belong to an independent affinity and matching pipeline. They are not inputs to the listening simulation described in this document.

## 1. Define What the Simulation Must Test

The purpose of the simulation determines which information the model must contain:

- **Recommendation quality:** musical tastes, emotions, track exposure and feedback.
- **Retention:** sessions, habits, satisfaction, fatigue, return behaviour and churn.
- **Affinity and matching research:** relationships, interaction evidence and compatibility, evaluated outside the listening pipeline.
- **Product analytics:** onboarding, funnels, feature adoption and conversion.
- **Load testing:** arrival rates, concurrency and sequences of API calls.

A population designed to evaluate recommendations is not equivalent to 20,000 virtual users created to stress the infrastructure. Even when both use the same personas, they require different rules and events.

## 2. Layers of the Model

Each simulated user should be composed of four layers:

1. **Stable profile:** traits, preferences, constraints and general habits.
2. **Dynamic state:** current emotion, fatigue, satisfaction, lifecycle stage and bounded recent-history features.
3. **Context:** time of day, activity, device, social setting and available time.
4. **Behavioural policy:** probabilistic rules that turn a situation into actions.

## 3. Persona Dimensions

| Area | Useful features |
| --- | --- |
| Basic context | Age band, country, language, time zone and usual schedule |
| Musical taste | Affinity for genres, artists, eras and languages |
| Audio preferences | Energy, valence, tempo, danceability, acousticness and instrumentalness |
| Discovery style | Familiarity preference, novelty seeking, repetition tolerance and trend sensitivity |
| Emotional profile | Baseline emotion, volatility, inertia and intensity |
| Emotional regulation | Maintain, match, improve, calm, amplify or escape the current state |
| Product behaviour | Search versus feed usage, patience, skip threshold and feedback propensity |
| Social and affinity profile | Sociability, reciprocity, privacy and interaction style, reserved for separate affinity analysis |
| Lifecycle | New, activated, retained, dormant or at risk of churning |
| Commercial relationship | Free or premium plan, ad tolerance and propensity to subscribe |
| Constraints | Explicit-content settings, accessibility and regional availability |

Generating every field independently is not recommended. It would create numerically diverse users who are psychologically and behaviourally incoherent.

### Latent Traits

A stronger approach is to generate a set of latent traits first and derive other variables from them:

- Novelty seeking
- Emotional sensitivity
- Sociability
- Habit strength
- Patience
- Need for privacy
- Mainstream versus alternative preference
- Propensity to provide explicit feedback
- Interpersonal openness and affinity-related traits
- Emotional receptiveness to music

For example, someone with high novelty seeking might display greater genre diversity, use discovery features more frequently, tolerate repetition less and be more likely to listen to unfamiliar artists. These relationships should be statistically correlated rather than deterministic.

## 4. Modelling Emotions

For simulation purposes, emotions can be represented flexibly through continuous dimensions:

- **Valence:** negative ↔ positive
- **Arousal:** calm ↔ activated
- **Dominance, optional:** feeling powerless ↔ feeling in control

These coordinates can later be mapped to product-friendly labels such as calm, happy, melancholic, sad, angry or excited.

### Current and Desired Emotional States

For each relevant time or session, distinguish between:

- `latent_emotion`: the simulator's internal current emotion
- `desired_emotion`: the emotion they want to reach or maintain
- `emotion_regulation_strategy`: their regulation strategy
- `emotion_intensity`: the intensity of the emotion
- `reported_emotion`: an optional mood explicitly disclosed through the application
- `inferred_emotion`: an optional downstream product-model estimate with its own confidence

`latent_emotion` is stored in `PersonaStateCurrent` and projected into `EmotionalStateObservation`. `reported_emotion` is emitted as observable mood-check-in telemetry. `inferred_emotion` belongs to the product or evaluation system and must not be silently substituted for either value.

This distinction is essential. A sad user might want to:

- Listen to sad music to feel understood.
- Listen to upbeat or energetic music to change their state.
- Listen to calm music to reduce arousal.
- Distract themselves with familiar music that does not match their emotion.

Therefore, the rule “current mood = recommended music mood” would be too simplistic.

### Emotional Evolution

The emotional state should evolve over time:

```text
next_emotion =
    previous_emotion × emotional_inertia
    + music_effect × user_receptiveness
    + contextual_events
    + random_variation
```

Emotional labels should not be used to infer mental-health diagnoses. The model should also avoid stereotypical assumptions linking gender, age, location, musical taste and psychological state.

## 5. Modelling Session Context

The same person may behave very differently depending on the situation. Dynamic context can include:

- Morning, afternoon or night
- Weekday or weekend
- Commuting, working, studying, exercising, relaxing or socialising
- Device and connection quality
- Available time
- Recent listening history
- Organic entry or response to a notification
- Listening alone or with other people
- Interruptions and attention level

These values should generally be generated per session or evolve during the simulation instead of being stored as permanent user properties.

## 6. Modelling the Recommendation Feedback Loop

A user can only respond to content that the application exposes to them. For this reason, the simulation must model **exposure**, not just abstract preferences.

For every recommendation, an approximate utility can be calculated:

```text
utility =
    musical_taste_match
    + emotional_goal_match
    + familiarity_preference
    + popularity_bias
    - repetition_fatigue
    - contextual_mismatch
    + individual_variation
```

This utility should not determine an action directly. It should instead be converted into probabilities for actions such as:

- Play
- Skip after a few seconds
- Complete the track
- Replay it
- Like or dislike it
- Save it
- Add it to a playlist
- Share it
- Follow the artist or another user
- Continue or end the session

The simulation should also model **position bias**: the first items in a feed receive more interactions even when they are not necessarily the best recommendations.

## 7. Behavioural Cycle of a Synthetic User

A simulated session could follow this cycle:

1. The user enters because of habit, personal intent or a notification.
2. Their current emotion, desired emotion and context are resolved from persistent state.
3. They decide whether to search, browse music surfaces, start listening or leave.
4. The application selects and ranks the available content.
5. The user responds probabilistically to each exposure.
6. Their actions modify satisfaction, fatigue, emotional state and history.
7. The user decides whether to continue, change activity or end the session.
8. The outcome affects the probability and context of their next visit.

## 8. Initial Archetypes

Archetypes can provide a foundation for coherent correlations:

- Emotion regulator
- Mood matcher
- Music explorer
- Loyal fan
- Routine or background listener
- Socially expressive listener, retained as an affinity-analysis trait rather than a listening-pipeline dependency
- Trend follower
- Playlist curator
- Passive listener
- Privacy-conscious listener

Each persona should be a probabilistic variation or mixture of archetypes. There should not be hundreds of clones with merely cosmetic differences.

For numeric traits, beta, log-normal and Poisson distributions will usually be more realistic than uniform distributions. Generation should use a fixed random seed so that a population can be reproduced exactly and different experiments can be compared.

## 9. Separating Static and Dynamic Data

The entire simulation should not be stored in one deeply nested JSON document or as a directory of JSON files per persona.

JSON has two documentation roles:

- `schemas/entity-contracts.schema.json` describes the formal structure of every logical entity.
- `examples/entity-examples.json` provides one representative object per entity.

Runtime instances live in shared PostgreSQL tables:

- `PersonaProfile`: versioned stable characteristics and behavioural parameters.
- `PersonaStateCurrent`: one mutable, versioned current-state row per simulation and persona.
- `StateTransition`: append-only meaningful changes used for audit and replay.
- `EmotionalStateObservation`: compact time-series points used to query emotional history.
- `ObservableEvent` and `ListeningSession`: application-compatible usage history.
- `PersonTrackState` and `PersonArtistState`: sparse memory created only after meaningful contact.
- `SocialEdge`, `AffinityCalculation` and `AffinityScore`: separate affinity-context tables.

Closed historical partitions may later be exported to compressed Parquet for analytical scans and archival retention. JSONL remains useful for small fixtures and debugging, not as the primary runtime store.

### Emotional History

The simulator retains the current emotional state needed for the next decision and also creates a queryable history. Emotional observations are emitted at relevant session or life-event boundaries, after meaningful changes, and through a configurable heartbeat.

Recent trajectory features such as trend, volatility and time in state are maintained incrementally in `PersonaStateCurrent`; the behavioural pipeline does not scan the full history on every decision.

A mood explicitly reported through the application is observable telemetry. The simulator's latent emotional state is internal ground truth. These values may differ and must remain distinguishable.

### Conceptual Persona Example

```json
{
  "persona_id": "user_000001",
  "archetype": "private_emotion_regulator",
  "traits": {
    "novelty_seeking": 0.72,
    "sociability": 0.28,
    "habit_strength": 0.61,
    "privacy": 0.89
  },
  "music_profile": {
    "genre_affinities": {
      "indie": 0.84,
      "electronic": 0.63
    },
    "preferred_energy": 0.58,
    "preferred_valence": 0.42,
    "repeat_tolerance": 0.25
  },
  "emotion_profile": {
    "baseline_valence": 0.10,
    "baseline_arousal": -0.20,
    "volatility": 0.35,
    "inertia": 0.76,
    "regulation_strategy": "shift_toward_desired"
  },
  "behaviour": {
    "weekly_sessions": 5.4,
    "exploration_probability": 0.67,
    "feedback_probability": 0.18,
    "notification_response_probability": 0.09
  }
}
```

The current emotion, active session, recent-history features and interactions live outside this stable object.

## 10. Recommended Simulation Engine

For 20,000 persistent users, it is neither necessary nor advisable to use an LLM to decide every action. An approach based on probabilistic rules, state machines or statistical models will be:

- Faster
- Cheaper
- Reproducible
- Easier to calibrate
- Easier to debug
- Better suited to running many comparable simulations

LLMs can be reserved for actions that genuinely require natural language, such as generating posts, comments, messages or narrative descriptions for selected profiles.

## 11. Validating the Population

Without real Vibeout telemetry, these personas represent **product hypotheses**, not a proven replica of real users. Before using their output to make decisions, validate:

- Trait distributions
- Correlations between variables
- Session duration and frequency
- Action funnels
- Retention and churn
- Coverage of uncommon behaviours
- Consistency of constraints
- Reproducibility through random seeds
- Sensitivity of results to changing assumptions

It is also preferable to run multiple populations or scenarios, for example:

- Emotion-driven population
- Highly exploratory population
- Conservative, habit-driven population
- Highly social population
- Cold-start scenario
- Scenario with poorly matched recommendations
- Growth or viral-effect scenario

This makes it possible to determine whether a conclusion remains valid under different assumptions instead of presenting a single synthetic population as ground truth.

## 12. Resolved Architecture and Remaining Product Decisions

The architecture now assumes:

1. A continuous `SimulationInstance` advanced through periodic `ExecutionBatch` records.
2. PostgreSQL as the initial operational and historical source of truth.
3. Application-compatible telemetry with explicit synthetic provenance.
4. A dedicated emotional-history projection in addition to current state and transitions.
5. JSON Schema and representative examples as contracts, not per-person storage.
6. An independent affinity pipeline that retains `SocialEdge` but does not influence listening behaviour.

The remaining decisions are product and model-calibration inputs rather than storage-architecture blockers:

1. Which exact actions and surfaces exist in the first Vibeout MVP?
2. Whether Vibeout asks for current mood, desired mood, both, or neither.
3. Which track and artist features are available from the catalogue.
4. Which behavioural relationships are evidence-backed and which are explicit simulation hypotheses.
5. Whether synthetic users emit events directly through Vibeout APIs or through a compatible offline producer.
6. Which real telemetry, user research, or public datasets can calibrate distributions.

## Conclusion

The main artefact should not simply be a list of 20,000 biographies. The solution should combine:

- Coherent stable profiles
- Dynamic emotional and contextual states
- Real content exposure
- Probabilistic decisions
- Sparse music memory and application-compatible interaction history
- Evolution of emotion and satisfaction
- User lifecycles and churn
- Reproducible and verifiable scenarios

The next implementation step is to translate the architecture-level contracts into Pydantic models and PostgreSQL mappings, then define the exact Vibeout event catalogue and calibration assumptions before generating the 20,000-person population.
