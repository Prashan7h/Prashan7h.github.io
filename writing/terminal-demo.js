/* A repeating demonstration, paused off screen and when the reader asks. */
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
  let frame=0,elapsed=0,lastTime=null,inView=false,paused=false;
  const button=document.createElement('button');
  button.type='button';button.className='motion-toggle';button.textContent='Pause animation';
  button.setAttribute('aria-pressed','false');root.append(button);
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
  function tick(time){
    if(lastTime!==null)elapsed+=time-lastTime;
    lastTime=time;
    // Hold the completed square briefly, then clear and begin again.
    elapsed%=duration+1800;
    draw(Math.min(elapsed,duration));
    frame=requestAnimationFrame(tick);
  }
  function sync(){
    cancelAnimationFrame(frame);frame=0;lastTime=null;
    const playing=inView&&!paused&&!document.hidden&&!motion.matches;
    root.classList.toggle('is-playing',playing);
    if(motion.matches)draw(duration);
    else if(playing)frame=requestAnimationFrame(tick);
  }
  button.addEventListener('click',()=>{paused=!paused;button.textContent=paused?'Play animation':'Pause animation';button.setAttribute('aria-pressed',String(paused));sync();});
  draw(motion.matches?duration:0);
  if('IntersectionObserver' in window){
    new IntersectionObserver(entries=>{inView=entries[0].isIntersecting;sync();},{threshold:.1}).observe(root.querySelector('.terminal-art'));
  }else {inView=true;sync();}
  document.addEventListener('visibilitychange',sync);
  motion.addEventListener('change',sync);
})();
