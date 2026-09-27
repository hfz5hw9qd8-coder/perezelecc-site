/* PEREZELECC — SFX discrets, sans fichier audio externe */
(function(){
  "use strict";
  let ctx=null;
  let enabled=true;

  function audio(){
    if(!enabled) return null;
    const C=window.AudioContext||window.webkitAudioContext;
    if(!C) return null;
    if(!ctx) ctx=new C();
    if(ctx.state==="suspended") ctx.resume().catch(()=>{});
    return ctx;
  }

  function tone(freq,duration,type="sine",volume=.035,delay=0){
    const a=audio(); if(!a) return;
    const now=a.currentTime+delay;
    const o=a.createOscillator(), g=a.createGain();
    o.type=type; o.frequency.setValueAtTime(freq,now);
    g.gain.setValueAtTime(0.0001,now);
    g.gain.exponentialRampToValueAtTime(volume,now+.012);
    g.gain.exponentialRampToValueAtTime(0.0001,now+duration);
    o.connect(g); g.connect(a.destination);
    o.start(now); o.stop(now+duration+.02);
  }

  window.PEREZELECC_SFX={
    click(){ tone(520,.055,"sine",.025); },
    select(){ tone(620,.06,"sine",.028); tone(760,.075,"sine",.022,.045); },
    success(){ tone(523,.10,"sine",.035); tone(659,.12,"sine",.032,.09); tone(784,.18,"sine",.028,.20); },
    error(){ tone(190,.11,"triangle",.03); tone(145,.16,"triangle",.025,.09); }
  };

  document.addEventListener("click",function(e){
    const el=e.target.closest("button,a,select");
    if(!el) return;
    if(el.matches("#home-booking-confirm") || el.classList.contains("booking-home-slot")){
      PEREZELECC_SFX.select();
    } else if(el.matches("#mobile-menu-button")){
      PEREZELECC_SFX.click();
    } else if(el.matches("a[href^='tel:'],a[href^='mailto:']")){
      PEREZELECC_SFX.click();
    } else if(el.tagName==="BUTTON"){
      PEREZELECC_SFX.click();
    }
  },{passive:true});

  const message=document.getElementById("home-booking-message");
  if(message){
    let last="";
    const observer=new MutationObserver(function(){
      const text=message.textContent.trim();
      if(!text || text===last) return;
      last=text;
      if(/enregistr|confirm|rendez-vous/i.test(text)) PEREZELECC_SFX.success();
      else if(/erreur|impossible|indisponible|obligatoire/i.test(text)) PEREZELECC_SFX.error();
    });
    observer.observe(message,{childList:true,subtree:true,characterData:true});
  }
})();