import React from "react";
import {Composition, registerRoot} from "remotion";
import {NextDecodeDemo} from "./scenes/NextDecodeDemo.jsx";
const Root = () => <Composition id="NextDecodeDemo" component={NextDecodeDemo} durationInFrames={150} fps={30} width={1080} height={1920} defaultProps={{title:"How AI systems work",steps:["Input","Reasoning","Output"]}} />;
registerRoot(Root);
