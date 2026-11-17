import {Link} from '@tanstack/react-router';
import {ArrowLeft,Compass} from 'lucide-react';
import {Page,Panel} from '../components';
export function NotFound(){
 return <>
  <Page eyebrow="WORKSPACE / NOT FOUND" title="Page not found" description="This address does not match any dashboard route."/>
  <Panel>
   <div className="empty">
    <Compass size={24}/>
    <b>No dashboard view matches this address</b>
    <p>The link may be outdated or mistyped. No task, run or Studio state was changed.</p>
    <Link className="btn" to="/"><ArrowLeft size={14}/> Back to Home</Link>
   </div>
  </Panel>
 </>;
}
