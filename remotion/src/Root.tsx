// Racine des compositions FactVibes (Remotion 4.x).
import { Composition } from "remotion";
import { FactVibesTitle, titreProps } from "./FactVibesTitle";
import { FactVibesDialogue, dialogueProps } from "./FactVibesDialogue";

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="FactVibesTitle"
      component={FactVibesTitle}
      durationInFrames={72}
      fps={24}
      width={1080}
      height={1920}
      defaultProps={titreProps}
    />
    <Composition
      id="FactVibesDialogue"
      component={FactVibesDialogue}
      durationInFrames={240}
      fps={24}
      width={1080}
      height={1920}
      defaultProps={dialogueProps}
    />
  </>
);
