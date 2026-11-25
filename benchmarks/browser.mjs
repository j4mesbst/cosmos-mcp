import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {mkdir, writeFile} from 'node:fs/promises';
import {createRequire} from 'node:module';
import path from 'node:path';

const require = createRequire(path.resolve(process.env.COSMOS_BROWSER_PROJECT || '.', 'package.json'));
const {chromium} = require('playwright-core');
const port = 5469;
const out = 'benchmarks/results/relay';
const server = spawn('python3', ['-u', '-m', 'http.server', String(port), '--bind', '127.0.0.1'], {stdio:['ignore','pipe','inherit']});
let browser;
try {
  await Promise.race([once(server.stdout, 'data'), once(server, 'exit').then(([code]) => { throw new Error('Preview failed: ' + code); })]);
  browser = await chromium.launch({executablePath: process.env.COSMOS_CHROMIUM});
  await mkdir(out, {recursive:true});
  const checks = [];
  for (const width of [1440,768,390]) {
    const page = await browser.newPage({ viewport: {width, height: 900} });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => {if (message.type() === 'error') errors.push(message.text());});
    const url = 'http://127.0.0.1:' + port + '/benchmarks/fixtures/relay/index.html';
    await page.goto(url);
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({path: out + '/relay-' + width + '.png', fullPage:true});
    const viewport = await page.evaluate(() => ({
      overflow: Math.max(0, document.documentElement.scrollWidth - innerWidth),
      controls: [...document.querySelectorAll('a[href], input, button')].length,
      navigationMs: Math.round(performance.getEntriesByType('navigation')[0].duration)
    }));
    await page.keyboard.press('Tab');
    assert.equal(await page.locator(':focus').textContent(), 'Relais.');
    await page.getByRole('link', {name:'Essayer l’éditeur', exact:true}).press('Enter');
    assert.equal(new URL(page.url()).hash, '#conversion');
    await page.getByLabel('Titre du guide').fill('Publier en équipe');
    assert.equal(await page.locator('#result').textContent(), 'Publier en équipe');
    await page.locator('#replay').click();
    const motion = await page.evaluate(() => window.relayAnimations.map(animation => {
      animation.pause();
      return { delay: animation.effect.getTiming().delay / animation.playbackRate,
        duration: animation.effect.getTiming().duration / animation.playbackRate,
        rate: animation.playbackRate };
    }));
    assert.deepEqual(motion.map(row => row.delay), [0, 1000, 2000]);
    assert.ok(motion.every(row => row.duration === 1600 && row.rate === 0.5));
    if (width === 1440) {
      const motionVideo = process.env.COSMOS_SAMPLE_MOTION === '1';
      const times = motionVideo ? Array.from({length:45}, (_, i) => i * 1000 / 12) : [0,1200,2000,3600];
      if (motionVideo) await mkdir(out + '/frames', {recursive:true});
      for (const [i, ms] of times.entries()) {
        await page.evaluate(ms => window.relayAnimations.forEach(a => {a.currentTime = ms * a.playbackRate;}), ms);
        const name = motionVideo ? '/frames/frame-' + String(i).padStart(3,'0') : '/motion-' + ms;
        await page.locator('#features').screenshot({path: out + name + '.png'});
      }
    }
    await page.emulateMedia({reducedMotion:'reduce'});
    await page.locator('#replay').click();
    assert.ok(await page.evaluate(() => window.relayAnimations.every(a =>
      a.effect.getTiming().delay === 0 && a.effect.getTiming().duration === 0 && a.playState === 'finished')));
    assert.equal(viewport.overflow, 0);
    assert.deepEqual(errors, []);
    checks.push({width, ...viewport, keyboard: true, interaction: true, errors, motion, reducedMotion: true});
    await page.close();
  }
  await writeFile(out + '/browser.json', JSON.stringify({browser: browser.version(), checks}, null, 2) + '\n');
  console.log('PASS: three viewports, keyboard, live preview, motion offsets and reduced motion.');
} finally {
  await browser?.close();
  server.kill();
}
