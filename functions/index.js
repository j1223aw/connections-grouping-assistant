const { onRequest } = require("firebase-functions/v2/https");
const { GoogleGenAI, Type } = require("@google/genai");

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

      console.log("Starting solver inference for words:", words.join(", "));
      const ai = new GoogleGenAI({ apiKey });

      const prompt = `You are an elite solver for the NYT Connections 16-word grouping puzzle.
Analyze these 16 words and partition them into exactly four disjoint groups of four:
Words: ${words.join(", ")}

Strict Rules:
1. Every word must appear exactly once across the four categories.
2. Watch out for red herrings (words that deliberately seem to fit multiple groups).
3. Identify lateral connections, prefixes/suffixes, homophones, and compound phrases for Purple and Blue tiers.
4. You MUST assign EXACTLY ONE group to each of the 4 difficulty tiers:
   - "Yellow (Straightforward)"
   - "Green (Moderate)"
   - "Blue (Trivia/Subset)"
   - "Purple (Wordplay/Abstract)"
No two groups may share the same difficulty tier.`;

      const response = await ai.models.generateContent({
        model: "gemini-2.5-flash",
        contents: prompt,
        config: {
          responseMimeType: "application/json",
          responseSchema: solveSchema,
          temperature: 0.1
        }
      });

      const rawText = typeof response.text === "function" ? response.text() : response.text;
      const cleanJson = (rawText || "").replace(/```json/g, "").replace(/```/g, "").trim();
      const parsed = JSON.parse(cleanJson);

      console.log("Solver inference successful.");
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