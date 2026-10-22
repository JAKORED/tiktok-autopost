// Pont Remotion FactVibes — composition racine.
//
// Deux compositions 9:16 (1080×1920, 24 i/s) alignées sur le pipeline cairo :
//   - FactVibesTitle    : carte-titre ciné (masque + interlettrage + fond nocturne)
//   - FactVibesDialogue : squelette de dialogue 2 personnages + sous-titres mot-à-mot
//
// Usage : npx remotion render src/index.ts FactVibesTitle out.mp4
import { registerRoot } from "remotion";
import { RemotionRoot } from "./Root";

registerRoot(RemotionRoot);
