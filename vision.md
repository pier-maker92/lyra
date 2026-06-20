# 🌌 Lyro
### *"Lost for words? Say it with lyrics"* 🎶✨

***

### 🚀 The Vision
Music says what we cannot, but finding the right track for a video usually kills the momentum. You capture a great sunset or a fun party clip, and then you waste twenty minutes searching through audio libraries trying to match the feeling. 

**Lyro** turns regular music listening into **active storytelling**. The premise is dead simple: **you record a video and tell the app how you feel**, and the AI takes care of the rest. Instead of forcing you to type exact song titles, Lyro looks at your footage, listens to your emotion, and **understands the vibe**. By reading your image and pairing it with the right lyrics, it acts as your personal music director. It puts synced lyrics at the center of social video, turning everyday moments into **perfectly scored visual stories**. 📸🌍

***

### ✨ How It Works
The app is built to be fast, smooth, and very simple to use:

1. **Capture and Express:** You take a photo or record a quick video directly inside our interface built on Replit. Then **you tell the app how you feel** by choosing from a massive library of moods, spanning ❤️ *Love*, 🧗 *Adventure*, 🎉 *Party*, 🧘 *Relax*, 🌧️ *Melancholy*, and many of others.
2. **AI Vision:** In milliseconds, Lyro looks at the colors, the lighting, the subjects, and the movement in your video, blending **what it sees with the exact emotion you declared**.
3. **Sync and Share:** Lyro instantly pairs your media with the best lyric match. It generates a clean visual card with **timed lyrics and audio**, ready for immediate export to Instagram or TikTok. 📲🔥

***

### ⚡ Under the Hood
To build an app that genuinely gets visual vibes while respecting hackathon rules around data privacy, we engineered a completely anonymous vector search engine.

**1. Sourcing and Legal Compliance**  
We used the **Musixmatch Pro API** to pull a rich dataset of 8,000 top songs across our vast mood spectrum. To respect hackathon rules around copyright and data protection, **Lyro stores absolutely no plain text lyrics, song titles, or artist names in its database.** 

**2. The Anonymous Vector Space**  
Instead of saving text, we ran the lyrics through an advanced Multimodal LLM to pull their actual meaning and emotion. The model turned these lyrics into **long lists of numbers called vector embeddings**. Our database holds only these floating point numbers sorted by mood tags, meaning **zero raw data exists on our servers**.

**3. Live Querying and Matchmaking**  
When a user captures a video and selects their feeling, our Replit backend feeds that live visual frame and mood choice into the same LLM to create a live vector. We then run a **fast cosine similarity search** across our database:

$$s = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\| \|\mathbf{v}\|}$$

This math formula finds the saved song vector that sits **closest to the visual and emotional vector** of the user video.

**4. Live API Resolution**  
Once the system finds the winning vector ID, Lyro calls the **Musixmatch Pro API** to fetch the actual synced lyrics and audio directly to the user screen in real time. The user gets a fully synced preview, while our backend remains **totally anonymous, fast, and 100% legal**. 🧠🎯