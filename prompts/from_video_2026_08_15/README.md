# System Prompts derived from  
## “The Week In The Life Cycle Of Price” – 15 Aug 2026  
https://youtu.be/dmHSwlmS9iY

Each file is a **stage-specific system prompt** (or sub-prompt) that the agent can load when running a back-test of any prior week.

Purpose: reproduce ICT’s *thinking process* on a different week and compare the agent’s output to what the lecture demonstrated for the week of ~4–8 Aug 2026 (the week just closed when the video was recorded).

### How to use for back-testing

1. Choose a historical week (e.g. the week before the one shown in the video).
2. Load the continuous-contract data for that instrument.
3. Run the prompts in order:
   - 00 → weekend / pre-week preparation
   - 01 → mark weekly & monthly levels
   - 02 → decide draw on liquidity + weekly profile
   - 03 → drop to 15-minute bellwether and annotate pools
   - 04 → daily bias + session process (repeat for each day)
   - 05 → Friday TGIF check
4. Compare the agent’s structured artefacts with the narrative ICT gave in the lecture.

All prompts are written in ICT’s voice and force the structured outputs defined in the doctrine documents.
