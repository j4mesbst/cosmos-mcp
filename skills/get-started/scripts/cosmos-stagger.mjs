// Apply project-authored frames to an ordered group. No media or listener is added.
export function animateSequence(elements, frames, options = {}) {
  const {
    durationMs = 700,
    staggerMs = 120,
    playbackRate = 1,
    easing = 'cubic-bezier(0.22, 1, 0.36, 1)',
    reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches,
  } = options;

  if (typeof frames !== 'function' || !Number.isFinite(durationMs) || durationMs <= 0
      || !Number.isFinite(staggerMs) || staggerMs < 0
      || !Number.isFinite(playbackRate) || playbackRate <= 0) {
    throw new TypeError('Supply a frame factory, positive duration and speed, and non-negative stagger.');
  }

  const animations = [...elements].map((element, index) => {
    const keyframes = frames(element, index);
    if (!Array.isArray(keyframes) || keyframes.length < 2) {
      throw new TypeError('Each item needs at least two keyframes.');
    }
    const animation = element.animate(keyframes, {
      duration: reducedMotion ? 0 : durationMs,
      delay: reducedMotion ? 0 : staggerMs * index * playbackRate,
      easing,
      fill: 'both',
    });
    animation.playbackRate = playbackRate;
    if (reducedMotion) animation.finish();
    return animation;
  });

  return { animations, cancel: () => animations.forEach(animation => animation.cancel()) };
}
