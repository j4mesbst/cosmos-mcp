import { animateSequence } from '../../../skills/get-started/scripts/cosmos-stagger.mjs';

const input = document.querySelector('#guide');
const result = document.querySelector('#result');
input.addEventListener('input', () => {
  result.textContent = input.value.trim() || 'Guide sans titre';
});
document.querySelector('#replay').addEventListener('click', () => {
  replay?.cancel();
  replay = animateSequence(document.querySelectorAll('.features article .example'),
    () => [{opacity:0.35, transform:'translateY(12px)'}, {opacity:1, transform:'translateY(0)'}],
    {durationMs:800, staggerMs:1000, playbackRate:0.5});
  window.relayAnimations = replay.animations;
});
let replay;
