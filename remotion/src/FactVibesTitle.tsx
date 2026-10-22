// Carte-titre ciné FactVibes — miroir web de artdir.title_card.
// Même grammaire : fond nocturne + faisceau + grain, titre révélé par masque
// montant, interlettrage large, mot-clé en jaune accent, letterbox qui s'ouvre.
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export type TitreProps = {
  /** Lignes du titre, ex. ["ELLE RÉPOND", "AVANT QUE", "TU AIES FINI"] */
  lignes: string[];
  /** Index de la ligne contenant le mot accentué (jaune) */
  ligneAccent: number;
  /** Mot accentué dans cette ligne */
  accent: string;
  /** Marque en haut */
  marque: string;
};

export const titreProps: TitreProps = {
  lignes: ["ELLE RÉPOND", "AVANT QUE", "TU AIES FINI"],
  ligneAccent: 2,
  accent: "FINI",
  marque: "FACTVIBES TOONS",
};

const FOND = "radial-gradient(120% 80% at 50% 30%, #2a2440 0%, #14121f 55%, #0a0912 100%)";

const Ligne: React.FC<{
  texte: string;
  accent: string;
  progress: number;
  taille: number;
}> = ({ texte, accent, progress, taille }) => {
  const mots = texte.split(" ");
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        gap: taille * 0.18,
        overflow: "hidden",
        clipPath: `inset(0 ${(1 - progress) * 100}% 0 0)`,
      }}
    >
      {mots.map((mot, i) => (
        <span
          key={i}
          style={{
            fontFamily: "Impact, 'Arial Black', sans-serif",
            fontWeight: 400,
            fontSize: taille,
            letterSpacing: taille * 0.08,
            color: mot === accent ? "#ffd34d" : "#ffffff",
            WebkitTextStroke: `${taille * 0.06}px #0a0912`,
            textShadow: `0 ${taille * 0.04}px 0 rgba(0,0,0,.45)`,
          }}
        >
          {mot}
        </span>
      ))}
    </div>
  );
};

export const FactVibesTitle: React.FC<TitreProps> = ({
  lignes,
  ligneAccent,
  accent,
  marque,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const t = frame / fps;

  // letterbox qui se ferme puis se rouvre (intro/outro)
  const bars = interpolate(
    frame,
    [0, 14, durationInFrames - 14, durationInFrames],
    [0, 0.055, 0.055, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  // entrée élastique du bloc titre
  const bloc = spring({ frame: frame - 6, fps, config: { damping: 16, mass: 0.9 } });

  return (
    <AbsoluteFill style={{ background: FOND }}>
      {/* faisceau de lumière */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(196deg, rgba(255,214,120,.20) 0%, rgba(255,214,120,0) 42%)",
        }}
      />
      {/* grain */}
      <AbsoluteFill
        style={{
          opacity: 0.05,
          backgroundImage:
            "repeating-conic-gradient(#fff 0% 25%, #000 0% 50%)",
          backgroundSize: "3px 3px",
          mixBlendMode: "overlay",
        }}
      />
      {/* marque */}
      <div
        style={{
          position: "absolute",
          top: 96,
          width: "100%",
          textAlign: "center",
          fontFamily: "Impact, 'Arial Black', sans-serif",
          fontSize: 38,
          letterSpacing: 8,
          color: "rgba(255,255,255,.75)",
          opacity: interpolate(t, [0.2, 0.6], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        {marque}
      </div>
      {/* titre */}
      <AbsoluteFill
        style={{
          justifyContent: "center",
          gap: 26,
          transform: `scale(${0.92 + bloc * 0.08})`,
        }}
      >
        {lignes.map((l, i) => (
          <Ligne
            key={i}
            texte={l}
            accent={i === ligneAccent ? accent : ""}
            progress={interpolate(frame, [6 + i * 5, 16 + i * 5], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            })}
            taille={104}
          />
        ))}
      </AbsoluteFill>
      {/* letterbox */}
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: `${bars * 100}%`, background: "#000" }} />
      <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: `${bars * 100}%`, background: "#000" }} />
    </AbsoluteFill>
  );
};
