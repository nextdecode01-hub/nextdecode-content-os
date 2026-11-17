import React from "react";
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from "remotion";
export const NextDecodeDemo = ({title, steps}) => {
  const frame=useCurrentFrame(); const {fps}=useVideoConfig();
  const opacity=interpolate(frame,[0,18,132,150],[0,1,1,0],{extrapolateLeft:"clamp",extrapolateRight:"clamp"});
  const y=interpolate(frame,[0,24],[80,0],{extrapolateRight:"clamp"});
  return <AbsoluteFill style={{backgroundColor:"#080E18",color:"#F3F6FC",fontFamily:"Arial",padding:76}}>
    <div style={{opacity,transform:`translateY(${y}px)`,fontSize:58,fontWeight:800,marginTop:170}}>{title}</div>
    <div style={{marginTop:100,display:"flex",flexDirection:"column",gap:38}}>
      {steps.map((step,i)=>{const start=i*Math.round(fps*.65);const reveal=interpolate(frame,[start,start+14],[0,1],{extrapolateLeft:"clamp",extrapolateRight:"clamp"});
        return <div key={step} style={{opacity:reveal,transform:`translateX(${interpolate(reveal,[0,1],[50,0])}px)`,padding:36,borderRadius:22,background:"#142235",border:"2px solid #56D6C8",fontSize:38}}>{String(i+1).padStart(2,"0")}　{step}</div>;
      })}
    </div>
  </AbsoluteFill>;
};
