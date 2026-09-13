/* A deliberately small local interpreter, not a shell or a full Logo implementation. */
(function () {
  'use strict';
  const aliases = {FD:'FORWARD',BK:'BACK',RT:'RIGHT',LT:'LEFT',PU:'PENUP',PD:'PENDOWN',CS:'CLEAR'};
  class LogoTerminal {
    constructor() { this.reset(); }
    reset() { this.x=200; this.y=120; this.heading=0; this.pen=true; this.lines=[]; }
    execute(source) {
      const tokens=String(source).trim().match(/\[|\]|[^\s\[\]]+/g)||[];
      if (!tokens.length) return {text:'',drawing:false};
      let cursor=0;
      const parse=(nested=false,depth=0)=>{
        if(depth>4) throw new Error('Keep REPEAT nesting to four levels.');
        const result=[];
        while(cursor<tokens.length){
          const token=tokens[cursor++].toUpperCase();
          if(token===']'){if(!nested)throw new Error('Unexpected ].');return result;}
          const cmd=aliases[token]||token;
          if(cmd==='REPEAT'){
            const count=Number(tokens[cursor++]);
            if(!Number.isInteger(count)||count<1||count>36)throw new Error('Use REPEAT 1–36 [commands].');
            if(tokens[cursor++]!=='[')throw new Error('Put repeated commands inside [brackets].');
            const body=parse(true,depth+1);
            if(!body.length)throw new Error('Add a command inside the brackets.');
            if(result.length+body.length*count>200)throw new Error('Try a shorter drawing (up to 200 steps).');
            for(let n=0;n<count;n++)result.push(...body);
          }else if(['FORWARD','BACK','RIGHT','LEFT'].includes(cmd)){
            const raw=tokens[cursor++];
            if(!raw||!/^[-+]?(?:\d+(?:\.\d*)?|\.\d+)$/.test(raw)||Math.abs(Number(raw))>1000)throw new Error('Add a number between −1000 and 1000, e.g. FORWARD 100.');
            result.push({cmd,value:Number(raw)});
          }else if(cmd==='PRINT'){
            let words=[];
            if(tokens[cursor]==='['){cursor++;while(cursor<tokens.length&&tokens[cursor]!==']')words.push(tokens[cursor++]);if(tokens[cursor++]!==']')throw new Error('Close PRINT text with ].');}
            else {if(nested)throw new Error('Use PRINT [your text] inside REPEAT.');words=tokens.slice(cursor);cursor=tokens.length;}
            result.push({cmd,value:words.join(' ')});
          }else if(cmd==='MUSIC'){
            const note=(tokens[cursor++]||'').toUpperCase();
            if(!/^[A-G]$/.test(note))throw new Error('Try MUSIC C (one note, A–G).');
            result.push({cmd,value:note});
          }else if(['HELP','CLEAR','RESET','HOME','PENUP','PENDOWN'].includes(cmd))result.push({cmd});
          else throw new Error('Unknown command. Type HELP for examples.');
          if(result.length>200)throw new Error('Try a shorter drawing (up to 200 steps).');
        }
        if(nested)throw new Error('Close REPEAT with ].');
        return result;
      };
      let instructions;
      try{instructions=parse();}catch(error){return {text:error.message,error:true};}
      const messages=[],notes=[];let drawing=false,reset=false;
      for(const instruction of instructions){
        const {cmd,value}=instruction;
        if(cmd==='FORWARD'||cmd==='BACK'){
          const distance=cmd==='BACK'?-value:value,rad=this.heading*Math.PI/180;
          const x=this.x+Math.sin(rad)*distance,y=this.y-Math.cos(rad)*distance;
          if(this.pen)this.lines.push({x1:this.x,y1:this.y,x2:x,y2:y});
          this.x=x;this.y=y;drawing=true;
        }else if(cmd==='RIGHT'||cmd==='LEFT'){this.heading=((this.heading+(cmd==='RIGHT'?value:-value))%360+360)%360;drawing=true;}
        else if(cmd==='HOME'){this.x=200;this.y=120;this.heading=0;drawing=true;}
        else if(cmd==='PENUP'||cmd==='PENDOWN'){this.pen=cmd==='PENDOWN';drawing=true;}
        else if(cmd==='CLEAR'){this.lines=[];drawing=true;}
        else if(cmd==='RESET'){this.reset();drawing=false;reset=true;}
        else if(cmd==='PRINT')messages.push(value||'(empty text)');
        else if(cmd==='MUSIC'){notes.push(value);messages.push('Playing '+value+'.');}
        else if(cmd==='HELP')messages.push('FORWARD 100 / RIGHT 90\nREPEAT 4 [FORWARD 80 RIGHT 90]\nBACK 40 / LEFT 90\nPENUP / PENDOWN / HOME\nPRINT [Hello, world!]\nMUSIC C (notes A–G)\nCLEAR drawing / RESET');
      }
      this.lines=this.lines.slice(-2000);
      const offscreen=this.x<0||this.x>400||this.y<0||this.y>240;
      return {drawing:messages.length?false:drawing,reset,notes:notes.slice(0,12),text:messages.join('\n'),status:offscreen?'Off screen. HOME brings the turtle back.':drawing?'Heading '+Math.round(this.heading)+'° · pen '+(this.pen?'down':'up'):''};
    }
  }
  if(typeof module!=='undefined'&&module.exports)module.exports={LogoTerminal};
  if(typeof document==='undefined')return;
  const root=document.getElementById('logo-terminal');
  if(!root)return;
  const engine=new LogoTerminal(),form=root.querySelector('form'),input=root.querySelector('input'),output=root.querySelector('.terminal-output'),drawing=root.querySelector('svg'),trails=root.querySelector('.terminal-trails'),turtle=root.querySelector('.terminal-turtle'),status=root.querySelector('.terminal-status');
  const history=[];let historyIndex=0,draft='',audio;
  const write=text=>{const line=document.createElement('div');line.textContent=text;output.appendChild(line);while(output.children.length>60)output.firstElementChild.remove();output.scrollTop=output.scrollHeight;};
  function welcome(){output.replaceChildren();write('READY.\nType HELP, or try FORWARD 100.');status.textContent='';drawing.hidden=true;output.hidden=false;}
  function render(){
    trails.replaceChildren();
    for(const l of engine.lines){const el=document.createElementNS('http://www.w3.org/2000/svg','line');for(const [key,value] of Object.entries(l))el.setAttribute(key,value.toFixed(3));trails.appendChild(el);}
    turtle.setAttribute('transform',`translate(${engine.x} ${engine.y}) rotate(${engine.heading})`);
    turtle.hidden=engine.x<0||engine.x>400||engine.y<0||engine.y>240;
    drawing.setAttribute('aria-label',`Logo drawing with ${engine.lines.length} line segments. Turtle heading ${Math.round(engine.heading)} degrees.`);
  }
  async function play(notes){
    if(!notes.length)return;
    try{
      const Audio=window.AudioContext||window.webkitAudioContext;
      if(!Audio)throw new Error('Audio unavailable');
      if(!audio)audio=new Audio();
      await audio.resume();
      const frequencies={C:261.63,D:293.66,E:329.63,F:349.23,G:392,A:440,B:493.88};
      notes.forEach((note,index)=>{const at=audio.currentTime+index*.25,osc=audio.createOscillator(),gain=audio.createGain();osc.type='sine';osc.frequency.value=frequencies[note];gain.gain.setValueAtTime(0,at);gain.gain.linearRampToValueAtTime(.07,at+.02);gain.gain.exponentialRampToValueAtTime(.001,at+.2);osc.connect(gain);gain.connect(audio.destination);osc.start(at);osc.stop(at+.23);});
    }catch(error){status.textContent='Sound is unavailable in this browser.';}
  }
  function run(command){
    if(!command.trim())return;
    history.push(command);if(history.length>50)history.shift();historyIndex=history.length;draft='';
    const result=engine.execute(command);
    if(result.reset)welcome();
    write('> '+command);if(result.text)write(result.text);
    render();drawing.hidden=!result.drawing;output.hidden=!!result.drawing;
    status.textContent=result.status||'';
    if(!result.drawing)output.scrollTop=output.scrollHeight;
    input.value='';play(result.notes||[]);
  }
  form.addEventListener('submit',event=>{event.preventDefault();run(input.value);});
  root.querySelectorAll('[data-command]').forEach(button=>button.addEventListener('click',()=>{run(button.dataset.command);}));
  input.addEventListener('keydown',event=>{
    if(event.key!=='ArrowUp'&&event.key!=='ArrowDown')return;
    if(!history.length)return;event.preventDefault();
    if(historyIndex===history.length)draft=input.value;
    historyIndex=Math.max(0,Math.min(history.length,historyIndex+(event.key==='ArrowUp'?-1:1)));
    input.value=historyIndex===history.length?draft:history[historyIndex];
  });
  welcome();render();
})();
