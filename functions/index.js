const { onRequest } = require("firebase-functions/v2/https");
const { GoogleGenAI, Type } = require("@google/genai");

const SYSTEM_INSTRUCTION = `You are an elite linguistic partitioner for 16-word NYT Connections puzzles.
Partition exactly 16 words into four discrete groups of four: Yellow (Straightforward), Green (Moderate), Blue (Trivia/Subset), and Purple (Wordplay/Abstract).

<example>
<input>["LEAP", "JUMP", "BOUND", "SPRING", "CAPTAIN", "CREW", "SAILOR", "SKIPPER", "KEY", "DASH", "SNOW", "SURF", "BEAR", "HARE", "DEAR", "FAIR"]</input>
<output>
{
  "groups": [
    {
      "theme": "Direct Synonyms for Hopping/Jumping",
      "difficulty_tier": "Yellow (Straightforward)",
      "confidence": 1.0,
      "words": ["BOUND", "JUMP", "LEAP", "SPRING"]
    },
    {
      "theme": "Nautical Vessel Personnel",
      "difficulty_tier": "Green (Moderate)",
      "confidence": 1.0,
      "words": ["CAPTAIN", "CREW", "SAILOR", "SKIPPER"]
    },
    {
      "theme": "Prefixes for 'Board'",
      "difficulty_tier": "Blue (Trivia/Subset)",
      "confidence": 0.95,
      "words": ["DASH", "KEY", "SNOW", "SURF"]
    },
    {
      "theme": "Homophones of Animals/Conditions",
      "difficulty_tier": "Purple (Wordplay/Abstract)",
      "confidence": 0.95,
      "words": ["BEAR", "DEAR", "FAIR", "HARE"]
    }
  ]
}
</output>
</example>`;

const solveSchema = {
  type: Type.OBJECT,
  properties: {
    groups: {
      type: Type.ARRAY,
      description: "Exactly 4 groups of 4 words each partitioning the 16 words",
      items: {
        type: Type.OBJECT,
        properties: {
          theme: {
            type: Type.STRING,
            description: "The underlying category, rule, or lateral wordplay theme"
          },
          difficulty_tier: {
            type: Type.STRING,
            enum: [
              "Yellow (Straightforward)",
              "Green (Moderate)",
              "Blue (Trivia/Subset)",
              "Purple (Wordplay/Abstract)"
            ]
          },
          confidence: {
            type: Type.NUMBER,
            description: "Confidence score between 0.0 and 1.0"
          },
          words: {
            type: Type.ARRAY,
            items: { type: Type.STRING },
            description: "Exactly 4 distinct words matching this specific group"
          }
        },
        required: ["theme", "difficulty_tier", "confidence", "words"]
      }
    }
  },
  required: ["groups"]
};

exports.solve = onRequest(
  {
    cors: true,
    memory: "512MiB",
    timeoutSeconds: 120,
    secrets: ["GEMINI_API_KEY"]
  },
  async (req, res) => {
    if (req.method !== "POST") {
      return res.status(405).json({ error: "Method not allowed. Use POST." });
    }

    try {
      const { words } = req.body;
      if (!words || !Array.isArray(words) || words.length !== 16) {
        return res.status(400).json({ error: "Exactly 16 words are required." });
      }

      const apiKey = process.env.GEMINI_API_KEY;
      if (!apiKey) {
        console.error("FATAL: Missing GEMINI_API_KEY environment variable.");
        return res.status(500).json({ error: "API key not configured." });
      }

      const normalizedInputs = words.map(w => String(w).trim().toUpperCase());
      console.log("Starting solver inference for words:", normalizedInputs.join(", "));
      const ai = new GoogleGenAI({ apiKey });

      const prompt = `Analyze these 16 words and partition them into the 4 NYT Connections tiers:
Words: ${normalizedInputs.join(", ")}

Strict Rules:
1. Every word must appear exactly once across the four categories.
2. Isolate red herrings by checking alternative secondary meanings.
3. You MUST assign EXACTLY ONE group to each of the 4 difficulty tiers: Yellow, Green, Blue, Purple.`;

      const response = await ai.models.generateContent({
        model: "gemini-2.5-flash",
        contents: prompt,
        config: {
          systemInstruction: SYSTEM_INSTRUCTION,
          responseMimeType: "application/json",
          responseSchema: solveSchema,
          temperature: 0.1
        }
      });

      const rawText = typeof response.text === "function" ? response.text() : response.text;
      const cleanJson = (rawText || "").replace(/```json/g, "").replace(/```/g, "").trim();
      const parsed = JSON.parse(cleanJson);

      // --- DETERMINISTIC HARNESS² WATCHDOG VERIFICATION ---
      if (!parsed.groups || parsed.groups.length !== 4) {
        throw new Error(`Watchdog fail: Expected 4 groups, received ${parsed.groups ? parsed.groups.length : 0}`);
      }

      const seenWords = new Set();
      const seenTiers = new Set();

      for (const group of parsed.groups) {
        if (!group.words || group.words.length !== 4) {
          throw new Error(`Watchdog fail: Group "${group.theme}" has ${group.words ? group.words.length : 0} words instead of 4.`);
        }

        if (seenTiers.has(group.difficulty_tier)) {
          throw new Error(`Watchdog fail: Duplicate difficulty tier assigned: ${group.difficulty_tier}`);
        }
        seenTiers.add(group.difficulty_tier);

        for (const word of group.words) {
          const upperWord = String(word).trim().toUpperCase();
          if (seenWords.has(upperWord)) {
            throw new Error(`Watchdog fail: Word "${upperWord}" appears in multiple groups.`);
          }
          if (!normalizedInputs.includes(upperWord)) {
            throw new Error(`Watchdog fail: Word "${upperWord}" was not in the original 16-word input grid.`);
          }
          seenWords.add(upperWord);
        }
      }

      if (seenWords.size !== 16) {
        throw new Error(`Watchdog fail: Grid partition incomplete (${seenWords.size}/16 unique words accounted for).`);
      }

      console.log("Solver inference & deterministic watchdog verification successful.");
      return res.status(200).json(parsed);
    } catch (error) {
      console.error("Inference Error:", error);
      return res.status(500).json({
        error: "Failed to solve grouping grid.",
        details: error.message
      });
    }
  }
);