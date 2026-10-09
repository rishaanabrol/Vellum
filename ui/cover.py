import streamlit as st
import streamlit.components.v1 as components

# ─────────────────────────────────────────────────────────────────────────────
# EXACT reference HTML, verbatim, with one addition:
#   • the "Begin learning" button styled to match
#   • enterVellum() that postMessages to the parent Streamlit page
#   • self-resize JS that makes this iframe fill the viewport
# ─────────────────────────────────────────────────────────────────────────────
_LANDING_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Manrope:wght@400;500;600&display=swap" rel="stylesheet"/>
<style>
:root{
  --parchment:#E8E0D2; --ivory:#F5F1E8; --ink:#24231F;
  --sage:#7D8A72; --terra:#B97862; --dusk:#C8A39B;
}
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;overflow:hidden}
body{
  font-family:'Manrope','Helvetica Neue',sans-serif; color:var(--ink);
  background:
    radial-gradient(120% 90% at 16% 6%, rgba(248,244,236,.85), rgba(248,244,236,0) 55%),
    radial-gradient(110% 85% at 88% 104%, rgba(36,35,31,.07), rgba(36,35,31,0) 60%),
    var(--parchment);
  -webkit-font-smoothing:antialiased;
}
::selection{background:rgba(183,120,98,.28)}

.light{
  position:fixed; inset:-12%; z-index:0; pointer-events:none;
  background:radial-gradient(46% 38% at 30% 24%, rgba(252,249,242,.55), rgba(252,249,242,0) 70%);
  animation:morning 34s ease-in-out infinite alternate;
}
@keyframes morning{from{transform:translate(-2.2%,-1.4%)}to{transform:translate(2.8%,2%) scale(1.05)}}

.grain,.fiber{position:fixed; inset:0; pointer-events:none; mix-blend-mode:multiply}
.grain{z-index:60; opacity:.055;
  background:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='260' height='260'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix type='saturate' values='0'/></filter><rect width='260' height='260' filter='url(%23n)'/></svg>");
  background-size:260px 260px}
.fiber{z-index:59; opacity:.04;
  background:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='500' height='500'><filter id='f'><feTurbulence type='fractalNoise' baseFrequency='0.012 0.22' numOctaves='2' stitchTiles='stitch'/><feColorMatrix type='saturate' values='0'/></filter><rect width='500' height='500' filter='url(%23f)'/></svg>");
  background-size:500px 500px}

.stackWrap{position:fixed; left:50%; top:38.5%; z-index:1; perspective:1300px; pointer-events:none}
.stack{
  position:relative; pointer-events:auto;
  width:clamp(240px,26vw,372px); aspect-ratio:.76;
  transform:translate(-50%,-50%) rotateX(var(--tx,0deg)) rotateY(var(--ty,0deg));
  transform-style:preserve-3d;
  animation:stackIn 1.7s cubic-bezier(.22,.7,.25,1) .1s backwards;
}
@keyframes stackIn{from{opacity:0; transform:translate(-50%,-47%)}}

.leaf{
  position:absolute; inset:0; transform-style:preserve-3d;
  transform:translate3d(calc(var(--nx,0)*var(--px,0px)),calc(var(--ny,0)*var(--py,0px)),0);
  animation:fadeIn 1.3s ease backwards;
}
.leaf-b{--px:3px; --py:2px; z-index:1; animation-delay:.55s}
.leaf-a{--px:6px; --py:4.5px; z-index:2; animation-delay:.7s}
.leaf-front{--px:11px; --py:8px; z-index:3; animation-delay:.85s}
.leaf-inner{position:absolute; inset:0; transform-style:preserve-3d; will-change:transform}

.leaf-b .leaf-inner{
  background:rgba(206,190,175,.5); border:1px solid rgba(36,35,31,.08);
  box-shadow:0 16px 36px -20px rgba(36,35,31,.25);
  animation:driftB 14s ease-in-out -5s infinite alternate;
}
.leaf-a .leaf-inner{
  background:rgba(238,231,219,.62); border:1px solid rgba(36,35,31,.09);
  box-shadow:0 20px 44px -22px rgba(36,35,31,.28);
  animation:driftA 11.5s ease-in-out -2s infinite alternate;
}
.leaf-front .leaf-inner{
  background:rgba(247,244,237,.93); border:1px solid rgba(36,35,31,.1);
  box-shadow:0 30px 60px -28px rgba(36,35,31,.32), 0 6px 16px -10px rgba(36,35,31,.12);
  transition:box-shadow .6s ease;
  animation:driftF 9s ease-in-out -3s infinite alternate;
}
.leaf-front:hover .leaf-inner{
  box-shadow:0 44px 76px -30px rgba(36,35,31,.42), 0 10px 24px -12px rgba(36,35,31,.16);
}
@keyframes driftB{from{transform:translate(-8%,-6.6%) rotate(-2.9deg)}to{transform:translate(-7%,-5.4%) rotate(-2deg)}}
@keyframes driftA{from{transform:translate(7%,-4.6%) rotate(2.2deg)}to{transform:translate(8.2%,-5.8%) rotate(3deg)}}
@keyframes driftF{from{transform:rotate(-.35deg)}to{transform:rotate(-1deg) translateY(-4px)}}

.page{position:absolute; inset:0; padding:12% 13% 9%; overflow:hidden;
  display:flex; flex-direction:column;
  backface-visibility:hidden; -webkit-backface-visibility:hidden}
.mark{display:block; height:1px; background:rgba(36,35,31,.34); margin-top:10px;
  opacity:calc(.3 + var(--reveal,0)*.5)}
.mark.head{height:2px; margin-top:0; opacity:calc(.28 + var(--reveal,0)*.36)}
.mark.annot{background:var(--sage); height:2px; opacity:calc(.3 + var(--reveal,0)*.42)}
.mark.catch{margin-top:auto; align-self:flex-end; background:var(--terra); height:2px;
  opacity:calc(.42 + var(--reveal,0)*.3)}
.gap{display:block; height:15px}

.ribbon{position:absolute; top:-2.5%; right:15%; width:6px; height:63%; z-index:9;
  background:var(--terra); opacity:.95;
  clip-path:polygon(0 0,100% 0,100% 100%,50% calc(100% - 11px),0 100%);
  box-shadow:inset -1px 0 0 rgba(36,35,31,.14), 1px 3px 6px rgba(36,35,31,.2);
  transform-origin:50% 0;
  animation:ribbonIn 1s ease 1.25s backwards, sway 7.5s ease-in-out 2.25s infinite alternate}
@keyframes ribbonIn{from{opacity:0}}
@keyframes sway{from{transform:rotate(1.7deg)}to{transform:rotate(-1.9deg)}}

.cover{position:fixed; inset:0; z-index:2; display:flex; align-items:center;
  justify-content:center; pointer-events:none}
.titleBlock{display:flex; flex-direction:column; align-items:center; text-align:center;
  max-width:760px; padding:0 26px 5vh}

.wordmark{pointer-events:auto; display:flex; justify-content:center; gap:.16em;
  font-family:'Cormorant Garamond',Georgia,serif; font-weight:500;
  font-size:clamp(2.9rem,13vw,9.5rem); line-height:.95; color:var(--ink);
  animation:trackIn 2.2s cubic-bezier(.2,.65,.25,1) backwards}
@keyframes trackIn{from{gap:.34em}}
.lt{display:block}
.lt:nth-child(1){transform:rotate(-.8deg) translateY(1px)}
.lt:nth-child(2){transform:rotate(.5deg) translateY(-2px)}
.lt:nth-child(3){transform:rotate(-.4deg) translateY(1.5px)}
.lt:nth-child(4){transform:rotate(.6deg) translateY(-1px)}
.lt:nth-child(5){transform:rotate(-.5deg) translateY(2px)}
.lt:nth-child(6){transform:rotate(.7deg) translateY(-1.5px)}
.li{display:block; text-shadow:0 1px 0 rgba(255,255,255,.35);
  animation:inkIn 1.15s cubic-bezier(.22,.7,.25,1) backwards;
  animation-delay:calc(.55s + var(--i)*.09s);
  transition:transform .55s cubic-bezier(.2,.7,.2,1), color .55s}
.lt:hover .li{transform:translateY(-.05em); color:#463a30}
@keyframes inkIn{from{opacity:0; transform:translateY(.14em); filter:blur(7px)}}

.tagline{margin-top:clamp(12px,2.2vh,20px);
  font-family:'Cormorant Garamond',Georgia,serif; font-style:italic; font-weight:500;
  font-size:clamp(1.2rem,2.3vw,1.65rem); letter-spacing:.04em; color:rgba(36,35,31,.9);
  animation:fadeUp 1.1s ease 1.45s backwards}

.philosophy{max-width:600px; margin-top:clamp(28px,4.6vh,44px);
  font-size:clamp(13px,1.35vw,14.5px); font-weight:500; line-height:1.95;
  letter-spacing:.015em; color:rgba(36,35,31,.8);
  animation:fadeUp 1.1s ease 1.95s backwards}
.philosophy em{font-family:'Cormorant Garamond',Georgia,serif; font-style:italic;
  font-size:1.28em; letter-spacing:.02em; color:rgba(36,35,31,.9)}

.footnote{margin-top:clamp(32px,5.4vh,54px); font-size:10.5px; letter-spacing:.06em;
  color:rgba(36,35,31,.72); animation:fadeUp 1.1s ease 2.2s backwards}
.footnote i{font-family:'Cormorant Garamond',Georgia,serif; font-size:1.2em;
  color:rgba(36,35,31,.82)}
.asterisk{color:var(--terra); margin-right:2px}

/* Enter button — styled to match the design, added to reference */
.enter-wrap{
  pointer-events:auto;
  margin-top:clamp(32px,5.4vh,54px);
  animation:fadeUp 1.1s ease 2.35s backwards;
}
.enter-btn{
  background:transparent;
  border:1px solid rgba(36,35,31,.35);
  color:var(--ink);
  padding:11px 36px;
  font-family:'Manrope',sans-serif;
  font-size:11px; font-weight:700;
  letter-spacing:.18em; text-transform:uppercase;
  cursor:pointer;
  transition:border-color .45s cubic-bezier(.22,.7,.25,1),
             color .45s cubic-bezier(.22,.7,.25,1),
             letter-spacing .45s cubic-bezier(.22,.7,.25,1),
             box-shadow .45s cubic-bezier(.22,.7,.25,1);
}
.enter-btn:hover{
  border-color:var(--terra); color:var(--terra);
  letter-spacing:.22em;
  box-shadow:0 18px 30px -22px rgba(36,35,31,.28);
}

@keyframes fadeUp{from{opacity:0; transform:translateY(10px)}}
@keyframes fadeIn{from{opacity:0}}

@media (max-width:560px){.stack{width:clamp(200px,64vw,300px)}}
@media (max-height:600px){
  .philosophy{font-size:12.5px; line-height:1.7; margin-top:18px}
  .titleBlock{padding-bottom:2vh}
}
@media (max-height:520px){body{overflow:auto}}
@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{animation:none !important; transition:none !important}
}
</style>
</head>
<body>

<div class="light" aria-hidden="true"></div>

<div class="stackWrap">
  <div class="stack" id="stack" aria-hidden="true">
    <div class="leaf leaf-b"><div class="leaf-inner"></div></div>
    <div class="leaf leaf-a"><div class="leaf-inner"></div></div>
    <div class="leaf leaf-front"><div class="leaf-inner">
      <div class="page">
        <i class="mark head" style="width:44%"></i>
        <s class="gap" style="height:19px"></s>
        <i class="mark" style="width:91%"></i>
        <i class="mark" style="width:72%"></i>
        <i class="mark" style="width:63%"></i>
        <s class="gap"></s>
        <i class="mark annot" style="width:60%"></i>
        <i class="mark" style="width:79%"></i>
        <i class="mark" style="width:38%"></i>
        <s class="gap"></s>
        <i class="mark" style="width:86%"></i>
        <i class="mark" style="width:67%"></i>
        <i class="mark" style="width:31%"></i>
        <s class="gap"></s>
        <i class="mark" style="width:74%"></i>
        <i class="mark" style="width:58%"></i>
        <i class="mark catch" style="width:17%"></i>
      </div>
    </div></div>
    <div class="ribbon"></div>
  </div>
</div>

<main class="cover">
  <div class="titleBlock">
    <h1 class="wordmark" aria-label="Vellum">
      <span class="lt" aria-hidden="true"><span class="li" style="--i:0">V</span></span>
      <span class="lt" aria-hidden="true"><span class="li" style="--i:1">E</span></span>
      <span class="lt" aria-hidden="true"><span class="li" style="--i:2">L</span></span>
      <span class="lt" aria-hidden="true"><span class="li" style="--i:3">L</span></span>
      <span class="lt" aria-hidden="true"><span class="li" style="--i:4">U</span></span>
      <span class="lt" aria-hidden="true"><span class="li" style="--i:5">M</span></span>
    </h1>
    <p class="tagline">A new way of learning.</p>
    <p class="philosophy">Vellum is a smart document information retrieval system designed to help you learn from the knowledge you already have. Inspired by the pages that once preserved human wisdom, Vellum brings your documents into conversation — helping you <em>discover, understand, and connect</em> the ideas within them.</p>
    <p class="footnote"><span class="asterisk">*</span> Vellum — from the Old French <i>velin</i>: the fine calfskin on which knowledge was once preserved.</p>
    <div class="enter-wrap">
      <button class="enter-btn" onclick="enterVellum()">Begin learning</button>
    </div>
  </div>
</main>

<div class="fiber" aria-hidden="true"></div>
<div class="grain" aria-hidden="true"></div>

<script>
// ── 1. Make this iframe fill the entire parent viewport ──
(function(){
  try {
    var frames = window.parent.document.querySelectorAll('iframe');
    for (var i = 0; i < frames.length; i++) {
      if (frames[i].contentWindow === window) {
        var f = frames[i];
        f.style.cssText = [
          'position:fixed', 'top:0', 'left:0',
          'width:100vw', 'height:100vh',
          'border:none', 'z-index:9999',
          'display:block'
        ].join('!important;') + '!important';
        // Also lift the wrapper div
        if (f.parentElement) {
          f.parentElement.style.cssText = [
            'position:fixed','top:0','left:0',
            'width:100vw','height:100vh','z-index:9999'
          ].join('!important;') + '!important';
        }
        break;
      }
    }
  } catch(e) {}
})();

// ── 2. Enter Vellum: postMessage + direct DOM click ──
function enterVellum() {
  // postMessage route (caught by bridge script below)
  try { window.parent.postMessage({type:'vellum_enter'}, '*'); } catch(e) {}
  // Direct DOM route as immediate fallback
  try {
    var btns = window.parent.document.querySelectorAll('button');
    for (var i = 0; i < btns.length; i++) {
      var t = (btns[i].innerText || '').toLowerCase();
      if (t.indexOf('begin') !== -1 || t.indexOf('enter') !== -1) {
        btns[i].click(); return;
      }
    }
  } catch(e) {}
}

// ── 3. Exact reference pointer-tilt JS ──
(function(){
  var stack=document.getElementById('stack');
  var fine=matchMedia('(pointer:fine)').matches,
      still=matchMedia('(prefers-reduced-motion: reduce)').matches;
  if(!fine&&!still){stack.style.setProperty('--reveal','0.45')}
  if(fine&&!still){
    var tx=0,ty=0,cx=0,cy=0,rv=0,rvT=0;
    addEventListener('pointermove',function(e){
      tx=(e.clientX/innerWidth)*2-1; ty=(e.clientY/innerHeight)*2-1;
      var rc=stack.getBoundingClientRect();
      var d=Math.hypot(e.clientX-(rc.left+rc.width/2),e.clientY-(rc.top+rc.height/2));
      var a=Math.min(rc.width,rc.height)*.42, b=Math.max(rc.width,rc.height)*1.05;
      rvT=Math.max(0,Math.min(1,1-(d-a)/Math.max(1,b-a)));
    });
    document.addEventListener('mouseleave',function(){tx=0;ty=0;rvT=0});
    (function loop(){
      cx+=(tx-cx)*.055; cy+=(ty-cy)*.055; rv+=(rvT-rv)*.075;
      stack.style.setProperty('--ty',(cx*2.4).toFixed(3)+'deg');
      stack.style.setProperty('--tx',(-cy*2).toFixed(3)+'deg');
      stack.style.setProperty('--nx',cx.toFixed(4));
      stack.style.setProperty('--ny',cy.toFixed(4));
      stack.style.setProperty('--reveal',rv.toFixed(3));
      requestAnimationFrame(loop);
    })();
  }
})();
</script>
</body>
</html>"""


# Bridge: listens in the parent for the postMessage and clicks Streamlit's button.
# Uses textContent (not innerText) so it reads nested <p> tags even when off-screen.
_BRIDGE_JS = """
<script>
(function(){
  var p = window.parent;
  if (!p || !p.document) return;
  if (p._vellumBridgeV3) return;
  p._vellumBridgeV3 = true;
  p.addEventListener('message', function(e) {
    if (!e.data || e.data.type !== 'vellum_enter') return;
    var btns = p.document.querySelectorAll('button');
    for (var i = 0; i < btns.length; i++) {
      var t = (btns[i].textContent || '').toLowerCase();
      if (t.indexOf('begin') !== -1) { btns[i].click(); return; }
    }
  });
})();
</script>
"""


def render_cover() -> None:
    """Landing cover — rendered as a full-screen iframe matching the reference HTML exactly.

    Architecture:
      1. st.markdown hides all Streamlit chrome and moves the real button off-screen.
      2. components.html embeds the full reference landing HTML, self-resizes to
         fill the viewport, and sends postMessage on Enter click.
      3. A second tiny bridge iframe catches the postMessage and clicks the real
         Streamlit button, triggering the session-state transition.
    """
    # Hide Streamlit chrome; push real button out of sight
    st.markdown(
        """
<style>
header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stBottom"],
[data-testid="stSidebar"],
[data-testid="stStatusWidget"] { display: none !important; }

.block-container {
  padding: 0 !important;
  margin: 0 !important;
  max-width: 100% !important;
}
[data-testid="stMain"],
[data-testid="stApp"],
[data-testid="stAppViewContainer"] {
  background: transparent !important;
  overflow: hidden !important;
}
/* Push real Streamlit button completely out of view (it is clicked
   programmatically by the bridge, never by a human) */
.stButton,
[data-testid="stButton"],
[data-testid="stBaseButton"] {
  position: fixed !important;
  bottom: -500px !important;
  left: -500px !important;
  opacity: 0 !important;
  pointer-events: none !important;
  z-index: -1 !important;
}
</style>
""",
        unsafe_allow_html=True,
    )

    # Full-screen landing page (self-resizes via JS)
    components.html(_LANDING_HTML, height=800, scrolling=False)

    # Bridge: catches postMessage from the landing iframe, clicks Streamlit's button
    if hasattr(st, "iframe"):
        st.iframe(_BRIDGE_JS, height=1)
    else:
        components.html(_BRIDGE_JS, height=1)

    # Real Streamlit button (hidden off-screen, clicked programmatically by bridge)
    if st.button("Begin learning", key="enter_vellum"):
        st.session_state["entered_vellum"] = True
        st.rerun()
