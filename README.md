# WanderSync – Sync your journey with who you are

## Getting Started

### Setup Instructions
Follow these steps to set up the development environment:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python wsgi.py
```

Before running the application, please review the `.env.example` file and set up all required environment variables.

### Deployment Information
Our services are currently deployed at the following locations:
- Embedding Server: [fsq-emb-server-20555262314.us-central1.run.app](https://fsq-emb-server-20555262314.us-central1.run.app)
- AI Backend: [fsq-ai-server-20555262314.us-central1.run.app](https://fsq-ai-server-20555262314.us-central1.run.app)
- User Interface: [wandersync-brown.vercel.app](https://wandersync-brown.vercel.app/)

### Usage Guide
Follow these steps to get the most out of WanderSync:
1. Log in to your account using your credentials
2. Create your personal profile by sharing your preferences, old photos, and travel descriptions
3. Create a new trip with your desired destination and dates
4. Send invitations to friends or family members to join your trip
5. Begin collecting real-time data using the WearOS app by entering your trip ID and user ID
6. Visit the notifications tab to receive location-tailored alerts and recommendations
7. Explore the heatmap section to visualize and track your health data across different locations

---

## Problem Statement

### The Problem with Traditional Travel Apps

Most travel apps today are static and task-focused — they help users plan trips, book hotels or flights, and build itineraries. But once the trip starts, they stop adapting.

### What's Missing in Current Solutions?

* **No Real-Time Adaptability**: Itineraries remain rigid — no dynamic adjustment based on user's location, context, or mood.
* **Neglect of Health & Fatigue**: No awareness of physical exertion, altitude strain, or wellness needs — especially critical during treks and active travel.
* **Lack of Contextual Personalization**: Preferences (like comic stores, vegan cuisine, or budget constraints) are rarely surfaced in the moment.
* **Smartwatch Integration Overlooked**: Wearables generate rich health and mobility data — largely untapped in mainstream travel apps.
* **Not Spontaneous or Agentic**: Most platforms are reactive and on-demand, not proactive or empathetic to changing dynamics or emotional states.

---

## Our Solution

With the rise of location-aware intelligence, wearable tech, and LLMs, we can reimagine travel as personalized, real-time, and emotionally aware.

**WanderSync** is a travel companion that transforms your journey into a path of self-discovery, connecting your inner personality with the world around you through intelligent technology and meaningful experiences.

> *"Travel is not just about the places you visit, but who you become along the way." – WanderSync*

---

## Key Features

* **Personal Intelligence**
  Analyzes travel history, personality, and expense patterns for hyper-personalized recommendations.

* **Health Monitoring**
  Tracks physical vitals and mobility patterns for safety-driven suggestions (e.g., altitude fatigue, ORS alerts).

* **Smart Recommendations**
  Contextual suggestions based on interests, budget, and surroundings using real-time Foursquare queries.

* **WearOS Integration**
  Continuous location, vitals, and movement tracking for seamless on-the-go travel intelligence.

* **AI Personalization**
  Combines LLMs and embeddings to understand preferences, detect emotions, and offer tailored advice.

* **Memory-Based Suggestions**
  Learns from photo metadata and past experiences to identify golden-hour moments, social trends, and emotional hotspots.

* **Group Dynamics**
  Cloud-enabled info sharing between group members' smartwatches to coordinate playlists, events, and activities.

---

## System Stages

### Stage 1: User Registration and Intelligent Profile Building

* WanderSync collects and processes user data during onboarding.
* Inputs include favorite artists, past trips, expense patterns, health info, and photo metadata.
* Data is processed using LLMs and image embedding models to infer user traits and tastes (e.g., romantic, nature-loving).
* These traits feed into an adaptive travel profile integrated with Foursquare's user API for personalized place recommendations.

### Stage 2: Secure Trip Initialization & Group Syncing

* When a user starts a trip, a unique **Trip Secret** is generated for session-level privacy.
* Users can form groups, leading to a shared **Group Secret** for synchronized experience tracking.
* Mood, trip location, and time are logged, and monitoring begins.
* Enables collaborative and contextual recommendations during the trip.

### Stage 3: Real-Time Monitoring & Alert Generation

* Wearable data is sent for time-series analysis.
* An agentic LLM chain interprets context and pulls relevant content from APIs such as:

  * Foursquare Places & Geofences
  * Music APIs
  * Health metadata sources
* This enables instant, context-aware alerts like fatigue warnings or group playlist sync.

---

## Example Scenarios

### Scenario 1: Fatigue at Montmartre (Health-Aware Trek Alert)

* **Context**: A solo traveler begins climbing the Montmartre hill in Paris.
* **How WanderSync Helps**:

  * Detects elevated heart rate and irregular steps.
  * Recognizes fatigue using health history.
  * Generates an alert:
    *“Physically Straining? — You may need a break. ORS available 150m ahead at Pharmacie Vrai Santé.”*
  * Recommendation powered by the Foursquare Places API.

### Scenario 2: Group Roadtrip Vibe Sync (Social + Music Personalization)

* **Context**: Three friends on a countryside road trip in southern France.
* **How WanderSync Helps**:

  * Detects group presence via shared Trip Secret.
  * Recognizes shared music preferences.
  * Generates an alert:
    *“Shared Vibe Detected — Curating a group playlist blending each of your favorites.”*
  * Combines Foursquare Geofences and music APIs for rest-stop and playlist generation.


---

## **Who is the end user?**

* **Active travelers** (trekkers, backpackers, road-trippers) who want spontaneous, safe, and adaptive experiences.
* **Travel groups** who want coordinated recommendations and synced experiences.
* **Health-conscious explorers** who benefit from fatigue and wellness-aware alerts via wearables.

---

## **Why is it important to your users?**

* Traditional travel apps stop adapting once the trip begins.
* WanderSync provides:

  * **Safety** → fatigue detection, hydration/pharmacy alerts.
  * **Relevance** → real-time recommendations aligned with personal interests and context.
  * **Connection** → shared group dynamics and memory-driven experiences.
* This makes travel **smarter, safer, and more meaningful**.

---

## **If you had more time and resources, what would you add or improve?**

1. **Deeper personalization** using richer behavioral data.
2. **Offline mode** with cached recommendations for low-connectivity regions.
3. **Mood & emotional AI** using wearable patterns.
4. **Gamification & social features** (badges, streaks, community tips).
5. **Wider device ecosystem** (Apple Watch, Garmin, Fitbit).

---

## **What FSQ API/endpoints did you use & why?**

* We have used the **Foursquare Places API** to fetch **keyword-based searches** based on **location and categories**.
* This enabled **contextual, real-time recommendations** like pharmacies, cafes, comic stores, or vegan restaurants — directly aligned with the user’s personality traits and situational needs.

---

## **Infrastructure & Tech Stack**

* **Frontend** → Vercel for fast, serverless deployment and easy scalability.
* **Mobile App** → Kotlin (WearOS) app for continuous health + location tracking.
* **Backend (AI + Logic)** → Google Cloud Run (low RAM services for AI backend, high RAM services for embeddings).
* **Embedding Service** → Hugging Face CLIP model on Cloud Run for image/text embeddings.
* **AI Reasoning** → OpenAI GPT-4o-mini for personalization, contextual recommendations, and agentic responses.
* **Database** → MongoDB for storing user profiles, trips, and historical context.
* **Location Intelligence** → Foursquare Places API via EC2 proxy for keyword-based, category-aware location recommendations.
* **Hosting & Infra Flexibility** → Multi-cloud approach (AWS + GCP) to balance cost, scalability, and performance.


---

## Privacy & Security Practices

1. **User-Centric Consent Flow**

   * Transparent opt-in screens for Location Access, Health Data Usage, and Cloud Sync.

2. **Device-First Privacy Model**

   * All sensitive health data stays on-device by default.
   * Cloud synchronization is fully optional and only enabled upon explicit user consent.

3. **Secure Authentication & Communication**

   * OAuth 2.0 with PKCE for robust and secure mobile login.
   * Short-lived JWTs manage authentication between microservices securely.

4. **Regulatory Compliance**

   * Fully compliant with GDPR and CCPA guidelines.
   * `/user/delete` endpoint enables user-initiated, complete data deletion.

5. **Security Guidelines**

   * All components are verified against internal security standards before production deployment.
