(() => {
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  document.querySelectorAll('.animated-illustration').forEach(art => {
    let visible = false, paused = false;
    const button = document.createElement('button');
    button.type = 'button'; button.className = 'motion-toggle';
    button.textContent = 'Pause animation'; button.setAttribute('aria-pressed', 'false');
    art.closest('figure').append(button);
    const sync = () => art.classList.toggle('motion-paused', paused || !visible || document.hidden || motion.matches);
    button.addEventListener('click', () => { paused = !paused; button.textContent = paused ? 'Play animation' : 'Pause animation'; button.setAttribute('aria-pressed', String(paused)); sync(); });
    if ('IntersectionObserver' in window) new IntersectionObserver(entries => {visible = entries[0].isIntersecting; sync();}, {threshold: .1}).observe(art);
    else visible = true;
    document.addEventListener('visibilitychange', sync); motion.addEventListener('change', sync); sync();
  });
})();
