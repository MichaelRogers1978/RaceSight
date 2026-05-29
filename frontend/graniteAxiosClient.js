import axios from "axios";

export async function callGranite(prompt, systemPrompt = "") {
  const endpoint = process.env.GRANITE_ENDPOINT;
  const apiKey = process.env.GRANITE_API_KEY;
  const modelId = process.env.GRANITE_MODEL;
  const projectId = process.env.GRANITE_PROJECT_ID;

  if (!endpoint || !apiKey || !modelId || !projectId) {
    throw new Error(
      "Missing env vars. Required: GRANITE_ENDPOINT, GRANITE_API_KEY, GRANITE_MODEL, GRANITE_PROJECT_ID"
    );
  }

  const input = systemPrompt && systemPrompt.trim().length > 0
    ? `System: ${systemPrompt.trim()}\\n\\nUser: ${prompt}`
    : prompt;

  const payload = {
    model_id: modelId,
    project_id: projectId,
    input,
    parameters: {
      decoding_method: "greedy",
      max_new_tokens: 400,
      min_new_tokens: 1,
    },
  };

  const response = await axios.post(endpoint, payload, {
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    timeout: 60000,
  });

  const data = response.data;
  if (Array.isArray(data?.results) && data.results.length > 0) {
    return data.results[0]?.generated_text ?? JSON.stringify(data);
  }
  return data?.generated_text ?? JSON.stringify(data);
}
