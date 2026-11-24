// 참고 영상을 프레임마다 재는 스크립트 (haze-inari 6절-2).
//
// 쓰는 법 (Claude의 내장 브라우저):
//   1. 영상 주소로 직접 이동한다 (navigate). 페이지가 곧 영상이라 캔버스가 막히지 않는다.
//      다른 사이트에 끼워진 영상은 교차 출처라 getImageData가 막힌다: 영상 파일 주소를 찾아 직접 연다.
//   2. javascript_tool로 이 파일의 내용을 실행한다 (함수 정의).
//   3. `await hazeProbe.table()`      -> 프레임마다 [시각, 밝기, 흰색%, 붉은색%, 자홍%, 어두운%, 앞 프레임과의 차이]
//      `await hazeProbe.grid(0.1, 12)` -> 0.1초부터 12장을 한 화면에 늘어놓는다 (screenshot으로 본다)
//      `await hazeProbe.two([2.38, 2.53])` -> 두 장을 화면 너비로 크게 (자세히 볼 때)
//
// 읽는 법:
//   - 차이(diff)가 0인 프레임이 이어지면 화면 정지(히트스톱). 없으면 정지 없이 느려짐만 쓴 것이다.
//   - 밝기가 한 장만 튀면 '흰 주인공 프레임'. 그 앞뒤 장을 two()로 본다.
//   - 색 비율이 높은 장이 몇 장 이어지는지가 색 면의 수명.
//   - 어두운 비율이 서서히 오르면 큰 연출 전의 암전.
// 영상의 프레임은 파일로 저장하지 않는다 (타인의 저작물). 수치와 관찰만 문서에 적는다.

window.hazeProbe = (() => {
  const video = () => document.querySelector('video');
  // grid·two는 화면을 캔버스로 바꾼다. 영상 요소를 붙잡아 두어 그 뒤에도 table·grid를 계속 쓸 수 있게 한다.
  let keep = null;

  const seek = (v, t) => new Promise((resolve) => {
    const done = () => { v.removeEventListener('seeked', done); resolve(); };
    v.addEventListener('seeked', done);
    v.currentTime = t;
  });

  const canvasFor = (w, h) => {
    const c = document.createElement('canvas');
    c.width = w; c.height = h;
    return c;
  };

  // 한 프레임의 수치. 색 기준은 영상에 맞게 고친다 (여기서는 붉은색·자홍이 주인공 색).
  const measure = (data, prev) => {
    let luma = 0, white = 0, red = 0, magenta = 0, dark = 0, diff = 0;
    const n = data.length / 4;
    for (let i = 0; i < data.length; i += 4) {
      const r = data[i], g = data[i + 1], b = data[i + 2];
      const y = 0.299 * r + 0.587 * g + 0.114 * b;
      luma += y;
      if (y > 215) white++;
      if (y < 24) dark++;
      if (r > 150 && g < 90 && b < 110) red++;
      if (r > 150 && g < 100 && b > 110) magenta++;
      if (prev) diff += Math.abs(r - prev[i]) + Math.abs(g - prev[i + 1]) + Math.abs(b - prev[i + 2]);
    }
    const pct = (k) => Math.round(k / n * 1000) / 10;
    return [Math.round(luma / n * 10) / 10, pct(white), pct(red), pct(magenta), pct(dark), Math.round(diff / n * 10) / 10];
  };

  // 프레임마다 재서 표로 돌려준다. step은 영상의 프레임 간격(초): 30fps면 1/30, 잘 모르면 1/60으로 재고 차이가 0인 줄을 뺀다.
  async function table(step = 1 / 30, from = 0, to = null) {
    const v = keep || (keep = video());
    v.pause();
    const w = Math.min(320, v.videoWidth), h = Math.round(w * v.videoHeight / v.videoWidth);
    const c = canvasFor(w, h), g = c.getContext('2d', { willReadFrequently: true });
    const rows = [];
    let prev = null;
    for (let t = from; t <= (to ?? v.duration) - 0.001; t += step) {
      await seek(v, t);
      g.drawImage(v, 0, 0, w, h);
      const d = g.getImageData(0, 0, w, h).data;
      rows.push([Math.round(t * 1000) / 1000, ...measure(d, prev)]);
      prev = d.slice();
    }
    return { size: [v.videoWidth, v.videoHeight], duration: v.duration, columns: ['t', 'luma', 'white%', 'red%', 'magenta%', 'dark%', 'diff'], rows };
  }

  const show = (c) => {
    document.body.innerHTML = '';
    document.body.style.cssText = 'margin:0;background:#111';
    document.body.appendChild(c);
    c.style.width = window.innerWidth + 'px';
    c.style.imageRendering = 'pixelated';
  };

  // t0부터 count장을 cols칸으로 늘어놓는다. 시각을 왼쪽 위에 적는다.
  async function grid(t0, count = 12, cols = 4, step = 1 / 30) {
    const v = keep || (keep = video());
    v.pause();
    const w = v.videoWidth, h = v.videoHeight, rowsN = Math.ceil(count / cols);
    const c = canvasFor(w * cols, h * rowsN), g = c.getContext('2d');
    g.font = '20px monospace';
    for (let i = 0; i < count; i++) {
      const t = t0 + i * step;
      await seek(v, t);
      const x = (i % cols) * w, y = Math.floor(i / cols) * h;
      g.drawImage(v, x, y, w, h);
      g.fillStyle = '#000'; g.fillRect(x, y, 82, 24);
      g.fillStyle = '#fff'; g.fillText(t.toFixed(3), x + 4, y + 18);
    }
    show(c);
    return `${count} frames from ${t0}`;
  }

  // 고른 시각 두 장(또는 여러 장)을 위아래로 원래 크기 그대로.
  async function two(times) {
    const v = keep || (keep = video());
    v.pause();
    const w = v.videoWidth, h = v.videoHeight;
    const c = canvasFor(w, h * times.length), g = c.getContext('2d');
    g.font = '20px monospace';
    for (let i = 0; i < times.length; i++) {
      await seek(v, times[i]);
      g.drawImage(v, 0, i * h, w, h);
      g.fillStyle = '#000'; g.fillRect(0, i * h, 82, 24);
      g.fillStyle = '#fff'; g.fillText(times[i].toFixed(3), 4, i * h + 18);
    }
    show(c);
    return times.join(', ');
  }

  return { table, grid, two };
})();
