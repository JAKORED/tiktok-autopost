// Squelette de dialogue FactVibes — 2 personnages + sous-titres mot-à-mot.
// Sert de pont web optionnel : même format 9:16, même synchronisation que
// cinema.subtitle_block. Les personnages sont des vecteurs simplifiés (tête +
// corps) — le pipeline cairo reste la source de vérité pour le rendu final.
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export type Repart = { qui: "gauche" | "droite"; t0: number; t1: number; texte: string };

export type DialogueProps = {
  fond: string;
  gauche: string;
  droite: string;
  repliques: Repart[];
};

export const dialogueProps: DialogueProps = {
  fond: "radial-gradient(130% 90% at 45% 25%, #3b3350 0%, #1a1726 60%, #0c0b14 100%)",
  gauche: "KEVIN",
  droite: "FOURNIER",
  repliques: [
    { qui: "gauche", t0: 0.4, t1: 2.6, texte: "Assistante, quelle heure il est ?" },
    { qui: "droite", t0: 2.9, t1: 5.2, texte: "Elle a répondu avant la fin de ta question." },
    { qui: "gauche", t0: 5.5, t1: 7.0, texte: "Je n'ai pas fini de la poser." },
  ],
};

const TAILLE = 62;
const CAR = TAILLE * 0.62;

const Tete: React.FC<{ x: number; y: number; couleur: string; parle: boolean }> = ({
  x,
  y,
  couleur,
  parle,
}) => (
  <div style={{ position: "absolute", left: x - 150, top: y, width: 300, textAlign: "center" }}>
    {/* corps */}
    <div
      style={{
        width: 260,
        height: 340,
        margin: "120px auto 0",
        borderRadius: "130px 130px 40px 40px",
        background: couleur,
        border: "10px solid rgba(0,0,0,.45)",
      }}
    />
    {/* tête */}
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 25,
        width: 250,
        height: 250,
        borderRadius: "50%",
        background: "#f6d3ac",
        border: "10px solid rgba(0,0,0,.45)",
      }}
    >
      {/* yeux */}
      <div style={{ position: "absolute", top: 92, left: 62, width: 34, height: 34, borderRadius: "50%", background: "#1c150e" }} />
      <div style={{ position: "absolute", top: 92, right: 62, width: 34, height: 34, borderRadius: "50%", background: "#1c150e" }} />
      {/* bouche */}
      <div
        style={{
          position: "absolute",
          bottom: 48,
          left: "50%",
          transform: "translateX(-50%)",
          width: parle ? 46 : 70,
          height: parle ? 34 : 14,
          borderRadius: parle ? "50%" : "0 0 40px 40px",
          background: "#5a3320",
        }}
      />
    </div>
  </div>
);

export const FactVibesDialogue: React.FC<DialogueProps> = ({
  fond,
  gauche,
  droite,
  repliques,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const enCours = repliques.find((r) => t >= r.t0 && t <= r.t1);
  const locuteur = enCours?.qui ?? null;
  // bouche animée sur le rythme du débit (~4 syllabes/s simulées)
  const parle = enCours ? Math.sin(t * Math.PI * 8) > 0 : false;

  // découpage mot-à-mot synchronisé
  let sousTitre: React.ReactNode = null;
  if (enCours) {
    const mots = enCours.texte.split(" ");
    const pas = (enCours.t1 - enCours.t0) / Math.max(mots.length, 1);
    const idx = Math.min(Math.floor((t - enCours.t0) / pas), mots.length - 1);
    const debut = Math.max(mots.length - 4, 0); // 4 mots max par ligne
    sousTitre = (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          gap: 14,
          maxWidth: 940,
          flexWrap: "wrap",
        }}
      >
        {mots.slice(debut).map((mot, i) => {
          const reel = debut + i;
          return (
            <span
              key={i}
              style={{
                fontFamily: "Impact, 'Arial Black', sans-serif",
                fontSize: TAILLE,
                letterSpacing: 5,
                color: reel === idx ? "#ffd34d" : reel <= idx ? "#ffffff" : "rgba(255,255,255,.35)",
                WebkitTextStroke: `${CAR * 0.28}px #0a0912`,
              }}
            >
              {mot}
            </span>
          );
        })}
      </div>
    );
  }

  return (
    <AbsoluteFill style={{ background: fond }}>
      {/* lueur de fenêtre */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(200deg, rgba(255,208,120,.16) 0%, rgba(255,208,120,0) 40%)",
        }}
      />
      <Tete x={340} y={520} couleur="#3f9c8f" parle={locuteur === "gauche" && parle} />
      <Tete x={760} y={560} couleur="#e07b39" parle={locuteur === "droite" && parle} />
      {/* noms discrets */}
      <div style={{ position: "absolute", top: 300, left: 0, right: 0, display: "flex", justifyContent: "space-around", fontFamily: "Impact, sans-serif", fontSize: 40, letterSpacing: 6, color: "rgba(255,255,255,.5)" }}>
        <span>{gauche}</span>
        <span>{droite}</span>
      </div>
      {/* sous-titres */}
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 300, display: "flex", justifyContent: "center" }}>
        {sousTitre ?? (
          <div style={{ fontFamily: "Impact, sans-serif", fontSize: 48, letterSpacing: 10, color: "rgba(255,255,255,.55)", WebkitTextStroke: "12px #0a0912" }}>
            SUIS POUR LA SUITE
          </div>
        )}
      </div>
      {/* vignettage */}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 340px 90px rgba(0,0,0,.55)", pointerEvents: "none" }} />
      <div style={{ position: "absolute", top: 90, width: "100%", textAlign: "center", fontFamily: "Impact, sans-serif", fontSize: 34, letterSpacing: 8, color: "rgba(255,255,255,.6)" }}>
        FACTVIBES TOONS
      </div>
      <div style={{ opacity: interpolate(frame, [0, 8], [1, 1]) }} />
    </AbsoluteFill>
  );
};
