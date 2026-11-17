import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const input = JSON.parse(readFileSync(0, "utf8"));
const jsEntry = process.env.KOKORO_JS_ENTRY;
const transformersEntry = process.env.KOKORO_TRANSFORMERS_ENTRY;
const cacheDir = process.env.KOKORO_MODEL_CACHE;
if (!jsEntry || !transformersEntry || !cacheDir) {
  throw new Error("Kokoro runtime paths are not configured");
}

const [{ KokoroTTS }, { env }] = await Promise.all([
  import(pathToFileURL(jsEntry).href),
  import(pathToFileURL(transformersEntry).href),
]);
env.cacheDir = cacheDir;
env.allowLocalModels = true;
env.allowRemoteModels = false;

const modelId = input.model_id || process.env.KOKORO_MODEL_ID || "onnx-community/Kokoro-82M-v1.0-ONNX";
const voice = input.voice || process.env.KOKORO_VOICE || "am_fenrir";
const tts = await KokoroTTS.from_pretrained(modelId, {
  dtype: "q4",
  device: "cpu",
});
const speed = Number(input.speed ?? process.env.KOKORO_SPEED ?? "1.45");
const chunks = Array.isArray(input.chunks) ? input.chunks : [input.text];
if (!chunks.length || chunks.some((chunk) => typeof chunk !== "string" || !chunk.trim())) {
  throw new Error("Kokoro requires one or more non-empty text chunks");
}
const outputDir = input.output_dir;
if (!outputDir) throw new Error("Kokoro output_dir is required");
const outputs = [];
let sampleRate = 0;
let totalSamples = 0;
for (let index = 0; index < chunks.length; index += 1) {
  const audio = await tts.generate(chunks[index], { voice, speed });
  if (!sampleRate) sampleRate = audio.sampling_rate;
  if (audio.sampling_rate !== sampleRate) throw new Error("Kokoro chunk sample rates differ");
  const outputPath = `${outputDir}/chunk_${String(index).padStart(3, "0")}.wav`;
  audio.save(outputPath);
  outputs.push(outputPath);
  totalSamples += audio.audio.length;
}
process.stdout.write(JSON.stringify({
  status: "ok",
  model: modelId,
  voice,
  chunks: outputs,
  sample_rate: sampleRate,
  samples: totalSamples,
}));
