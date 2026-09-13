/* One quiet demonstration, triggered when the illustration comes into view. */
(function () {
  'use strict';
  const root=document.getElementById('logo-terminal');
  if(!root)return;
  const typed=root.querySelector('.terminal-typed');
  const trail=root.querySelector('.terminal-trail');
  const turtle=root.querySelector('.terminal-turtle');
  const motion=window.matchMedia('(prefers-reduced-motion: reduce)');
  // Each command is typed, considered, then executed before the next begins.
  const commands=['RIGHT 90','FORWARD 100','LEFT 90','FORWARD 100','LEFT 90','FORWARD 100','LEFT 90','FORWARD 100'];
  let duration=0;
  const sequence=commands.map((command,index)=>{
    const start=duration;
    let time=start+650;
    const letters=Array.from(command,(letter,i)=>{
      time+=letter===' '?340:[170,240,150,210,190][(i+index)%5];
      return time;
    });
    const actionStart=time+550;
    const actionEnd=actionStart+(command.startsWith('FORWARD')?1600:850);
    duration=actionEnd+700;
    return {command,start,letters,actionStart,actionEnd};
  });
  let frame=0,started=false,elapsed=0,lastTime=null,observer,inView=false;
  function draw(time){
    let x=150,y=155,heading=0,path='M 150 155';
    typed.textContent='';
    for(const step of sequence){
      if(time<step.start)break;
      typed.textContent=step.command.slice(0,step.letters.filter(at=>at<=time).length);
      const progress=Math.max(0,Math.min(1,(time-step.actionStart)/(step.actionEnd-step.actionStart)));
      const eased=progress*progress*(3-2*progress);
      if(step.command.startsWith('FORWARD')){
        const radians=heading*Math.PI/180;
        x+=Math.sin(radians)*100*eased;
        y-=Math.cos(radians)*100*eased;
        if(progress>0)path+=` L ${Number(x.toFixed(3))} ${Number(y.toFixed(3))}`;
      }else heading+=(step.command.startsWith('RIGHT')?90:-90)*eased;
      if(time<step.actionEnd)break;
    }
    trail.setAttribute('d',path);
    turtle.setAttribute('transform',`translate(${Number(x.toFixed(3))} ${Number(y.toFixed(3))}) rotate(${heading})`);
  }
  function finish(){
    cancelAnimationFrame(frame);frame=0;
    draw(duration);
    root.classList.remove('is-playing');
    if(observer)observer.disconnect();
  }
  function tick(time){
    if(lastTime!==null)elapsed+=time-lastTime;
    lastTime=time;
    draw(elapsed);
    if(elapsed>=duration){finish();return;}
    frame=requestAnimationFrame(tick);
  }
  function start(){
    if(started||document.hidden)return;
    started=true;
    if(motion.matches){finish();return;}
    root.classList.add('is-playing');
    frame=requestAnimationFrame(tick);
  }
  if(motion.matches){finish();return;}
  // Without scripts or with reduced motion, the markup shows the final result.
  typed.textContent='';draw(0);
  if('IntersectionObserver' in window){
    observer=new IntersectionObserver(entries=>{
      inView=entries.some(entry=>entry.isIntersecting);
      if(inView)start();
    },{threshold:.35});
    observer.observe(root.querySelector('.terminal-art'));
  }else start();
  document.addEventListener('visibilitychange',()=>{
    if(document.hidden){cancelAnimationFrame(frame);frame=0;lastTime=null;}
    else if(started&&elapsed<duration&&!motion.matches){frame=requestAnimationFrame(tick);}
    else if(!started&&(!observer||inView))start();
  });
  motion.addEventListener('change',event=>{if(event.matches){started=true;elapsed=duration;finish();}});
})();
