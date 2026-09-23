"use strict";

const WEATHER_ICONS = {
  sun: {
    viewBox: "0 0 512 512",
    d: "M361.5 1.2c5 2.1 8.6 6.6 9.6 11.9L391 121l107.9 19.8c5.3 1 9.8 4.6 11.9 9.6s1.5 10.7-1.6 15.2L446.9 256l62.3 90.3c3.1 4.5 3.7 10.2 1.6 15.2s-6.6 8.6-11.9 9.6L391 391 371.1 498.9c-1 5.3-4.6 9.8-9.6 11.9s-10.7 1.5-15.2-1.6L256 446.9l-90.3 62.3c-4.5 3.1-10.2 3.7-15.2 1.6s-8.6-6.6-9.6-11.9L121 391 13.1 371.1c-5.3-1-9.8-4.6-11.9-9.6s-1.5-10.7 1.6-15.2L65.1 256 2.8 165.7c-3.1-4.5-3.7-10.2-1.6-15.2s6.6-8.6 11.9-9.6L121 121 140.9 13.1c1-5.3 4.6-9.8 9.6-11.9s10.7-1.5 15.2 1.6L256 65.1 346.3 2.8c4.5-3.1 10.2-3.7 15.2-1.6zM160 256a96 96 0 1 1 192 0 96 96 0 1 1 -192 0zm224 0a128 128 0 1 0 -256 0 128 128 0 1 0 256 0z",
  },
  moon: {
    viewBox: "0 0 384 512",
    d: "M223.5 32C100 32 0 132.3 0 256S100 480 223.5 480c60.6 0 115.5-24.2 155.8-63.4c5-4.9 6.3-12.5 3.1-18.7s-10.1-9.7-17-8.5c-9.8 1.7-19.8 2.6-30.1 2.6c-96.9 0-175.5-78.8-175.5-176c0-65.8 36-123.1 89.3-153.3c6.1-3.5 9.2-10.5 7.7-17.3s-7.3-11.9-14.3-12.5c-6.3-.5-12.6-.8-19-.8z",
  },
  cloud: {
    viewBox: "0 0 640 512",
    d: "M0 336c0 79.5 64.5 144 144 144l368 0c70.7 0 128-57.3 128-128c0-61.9-44-113.6-102.4-125.4c4.1-10.7 6.4-22.4 6.4-34.6c0-53-43-96-96-96c-19.7 0-38.1 6-53.3 16.2C367 64.2 315.3 32 256 32C167.6 32 96 103.6 96 192c0 2.7 .1 5.4 .2 8.1C40.2 219.8 0 273.2 0 336z",
  },
  partly: {
    viewBox: "0 0 640 512",
    d: "M294.2 1.2c5.1 2.1 8.7 6.7 9.6 12.1l14.1 84.7 84.7 14.1c5.4 .9 10 4.5 12.1 9.6s1.5 10.9-1.6 15.4l-38.5 55c-2.2-.1-4.4-.2-6.7-.2c-23.3 0-45.1 6.2-64 17.1l0-1.1c0-53-43-96-96-96s-96 43-96 96s43 96 96 96c8.1 0 15.9-1 23.4-2.9c-36.6 18.1-63.3 53.1-69.8 94.9l-24.4 17c-4.5 3.2-10.3 3.8-15.4 1.6s-8.7-6.7-9.6-12.1L98.1 317.9 13.4 303.8c-5.4-.9-10-4.5-12.1-9.6s-1.5-10.9 1.6-15.4L52.5 208 2.9 137.2c-3.2-4.5-3.8-10.3-1.6-15.4s6.7-8.7 12.1-9.6L98.1 98.1l14.1-84.7c.9-5.4 4.5-10 9.6-12.1s10.9-1.5 15.4 1.6L208 52.5 278.8 2.9c4.5-3.2 10.3-3.8 15.4-1.6zM144 208a64 64 0 1 1 128 0 64 64 0 1 1 -128 0zM639.9 431.9c0 44.2-35.8 80-80 80l-271.9 0c-53 0-96-43-96-96c0-47.6 34.6-87 80-94.6l0-1.3c0-53 43-96 96-96c34.9 0 65.4 18.6 82.2 46.4c13-9.1 28.8-14.4 45.8-14.4c44.2 0 80 35.8 80 80c0 5.9-.6 11.7-1.9 17.2c37.4 6.7 65.8 39.4 65.8 78.7z",
  },
  "partly-night": {
    viewBox: "0 0 640 512",
    d: "M495.8 0c5.5 0 10.9 .2 16.3 .7c7 .6 12.8 5.7 14.3 12.5s-1.6 13.9-7.7 17.3c-44.4 25.2-74.4 73-74.4 127.8c0 81 65.5 146.6 146.2 146.6c8.6 0 17-.7 25.1-2.1c6.9-1.2 13.8 2.2 17 8.5s1.9 13.8-3.1 18.7c-34.5 33.6-81.7 54.4-133.6 54.4c-9.3 0-18.4-.7-27.4-1.9c-11.2-22.6-29.8-40.9-52.6-51.7c-2.7-58.5-50.3-105.3-109.2-106.7c-1.7-10.4-2.6-21-2.6-31.8C304 86.1 389.8 0 495.8 0zM447.9 431.9c0 44.2-35.8 80-80 80L96 511.9c-53 0-96-43-96-96c0-47.6 34.6-87 80-94.6l0-1.3c0-53 43-96 96-96c34.9 0 65.4 18.6 82.2 46.4c13-9.1 28.8-14.4 45.8-14.4c44.2 0 80 35.8 80 80c0 5.9-.6 11.7-1.9 17.2c37.4 6.7 65.8 39.4 65.8 78.7z",
  },
  rain: {
    viewBox: "0 0 512 512",
    d: "M96 320c-53 0-96-43-96-96c0-42.5 27.6-78.6 65.9-91.2C64.7 126.1 64 119.1 64 112C64 50.1 114.1 0 176 0c43.1 0 80.5 24.3 99.2 60c14.7-17.1 36.5-28 60.8-28c44.2 0 80 35.8 80 80c0 5.5-.6 10.8-1.6 16c.5 0 1.1 0 1.6 0c53 0 96 43 96 96s-43 96-96 96L96 320zm-6.8 52c1.3-2.5 3.9-4 6.8-4s5.4 1.5 6.8 4l35.1 64.6c4.1 7.5 6.2 15.8 6.2 24.3l0 3c0 26.5-21.5 48-48 48s-48-21.5-48-48l0-3c0-8.5 2.1-16.9 6.2-24.3L89.2 372zm160 0c1.3-2.5 3.9-4 6.8-4s5.4 1.5 6.8 4l35.1 64.6c4.1 7.5 6.2 15.8 6.2 24.3l0 3c0 26.5-21.5 48-48 48s-48-21.5-48-48l0-3c0-8.5 2.1-16.9 6.2-24.3L249.2 372zm124.9 64.6L409.2 372c1.3-2.5 3.9-4 6.8-4s5.4 1.5 6.8 4l35.1 64.6c4.1 7.5 6.2 15.8 6.2 24.3l0 3c0 26.5-21.5 48-48 48s-48-21.5-48-48l0-3c0-8.5 2.1-16.9 6.2-24.3z",
  },
  storm: {
    viewBox: "0 0 512 512",
    d: "M0 224c0 53 43 96 96 96l47.2 0L290 202.5c17.6-14.1 42.6-14 60.2 .2s22.8 38.6 12.8 58.8L333.7 320l18.3 0 64 0c53 0 96-43 96-96s-43-96-96-96c-.5 0-1.1 0-1.6 0c1.1-5.2 1.6-10.5 1.6-16c0-44.2-35.8-80-80-80c-24.3 0-46.1 10.9-60.8 28C256.5 24.3 219.1 0 176 0C114.1 0 64 50.1 64 112c0 7.1 .7 14.1 1.9 20.8C27.6 145.4 0 181.5 0 224zm330.1 3.6c-5.8-4.7-14.2-4.7-20.1-.1l-160 128c-5.3 4.2-7.4 11.4-5.1 17.8s8.3 10.7 15.1 10.7l70.1 0L177.7 488.8c-3.4 6.7-1.6 14.9 4.3 19.6s14.2 4.7 20.1 .1l160-128c5.3-4.2 7.4-11.4 5.1-17.8s-8.3-10.7-15.1-10.7l-70.1 0 52.4-104.8c3.4-6.7 1.6-14.9-4.2-19.6z",
  },
  snow: {
    viewBox: "0 0 448 512",
    d: "M224 0c17.7 0 32 14.3 32 32l0 30.1 15-15c9.4-9.4 24.6-9.4 33.9 0s9.4 24.6 0 33.9l-49 49 0 70.3 61.4-35.8 17.7-66.1c3.4-12.8 16.6-20.4 29.4-17s20.4 16.6 17 29.4l-5.2 19.3 23.6-13.8c15.3-8.9 34.9-3.7 43.8 11.5s3.8 34.9-11.5 43.8l-25.3 14.8 21.7 5.8c12.8 3.4 20.4 16.6 17 29.4s-16.6 20.4-29.4 17l-67.7-18.1L287.5 256l60.9 35.5 67.7-18.1c12.8-3.4 26 4.2 29.4 17s-4.2 26-17 29.4l-21.7 5.8 25.3 14.8c15.3 8.9 20.4 28.5 11.5 43.8s-28.5 20.4-43.8 11.5l-23.6-13.8 5.2 19.3c3.4 12.8-4.2 26-17 29.4s-26-4.2-29.4-17l-17.7-66.1L256 311.7l0 70.3 49 49c9.4 9.4 9.4 24.6 0 33.9s-24.6 9.4-33.9 0l-15-15 0 30.1c0 17.7-14.3 32-32 32s-32-14.3-32-32l0-30.1-15 15c-9.4 9.4-24.6 9.4-33.9 0s-9.4-24.6 0-33.9l49-49 0-70.3-61.4 35.8-17.7 66.1c-3.4 12.8-16.6 20.4-29.4 17s-20.4-16.6-17-29.4l5.2-19.3L48.1 395.6c-15.3 8.9-34.9 3.7-43.8-11.5s-3.7-34.9 11.5-43.8l25.3-14.8-21.7-5.8c-12.8-3.4-20.4-16.6-17-29.4s16.6-20.4 29.4-17l67.7 18.1L160.5 256 99.6 220.5 31.9 238.6c-12.8 3.4-26-4.2-29.4-17s4.2-26 17-29.4l21.7-5.8L15.9 171.6C.6 162.7-4.5 143.1 4.4 127.9s28.5-20.4 43.8-11.5l23.6 13.8-5.2-19.3c-3.4-12.8 4.2-26 17-29.4s26 4.2 29.4 17l17.7 66.1L192 200.3l0-70.3L143 81c-9.4-9.4-9.4-24.6 0-33.9s24.6-9.4 33.9 0l15 15L192 32c0-17.7 14.3-32 32-32z",
  },
  fog: {
    viewBox: "0 0 640 512",
    d: "M32 144c0 79.5 64.5 144 144 144l123.3 0c22.6 19.9 52.2 32 84.7 32s62.1-12.1 84.7-32l27.3 0c61.9 0 112-50.1 112-112s-50.1-112-112-112c-10.7 0-21 1.5-30.8 4.3C443.8 27.7 401.1 0 352 0c-32.6 0-62.4 12.2-85.1 32.3C242.1 12.1 210.5 0 176 0C96.5 0 32 64.5 32 144zM616 368l-336 0c-13.3 0-24 10.7-24 24s10.7 24 24 24l336 0c13.3 0 24-10.7 24-24s-10.7-24-24-24zm-64 96l-112 0c-13.3 0-24 10.7-24 24s10.7 24 24 24l112 0c13.3 0 24-10.7 24-24s-10.7-24-24-24zm-192 0L24 464c-13.3 0-24 10.7-24 24s10.7 24 24 24l336 0c13.3 0 24-10.7 24-24s-10.7-24-24-24zM224 392c0-13.3-10.7-24-24-24L96 368c-13.3 0-24 10.7-24 24s10.7 24 24 24l104 0c13.3 0 24-10.7 24-24z",
  },
};

const STATE_ICONS = {
  play: {
    viewBox: "0 0 384 512",
    d: "M73 39c-14.8-9.1-33.4-9.4-48.5-.9S0 62.6 0 80V432c0 17.4 9.4 33.4 24.5 41.9s33.7 8.1 48.5-.9L361 297c14.3-8.7 23-24.2 23-41s-8.7-32.2-23-41L73 39z",
  },
  pause: {
    viewBox: "0 0 320 512",
    d: "M48 64C21.5 64 0 85.5 0 112V400c0 26.5 21.5 48 48 48H80c26.5 0 48-21.5 48-48V112c0-26.5-21.5-48-48-48H48zm192 0c-26.5 0-48 21.5-48 48V400c0 26.5 21.5 48 48 48h32c26.5 0 48-21.5 48-48V112c0-26.5-21.5-48-48-48H240z",
  },
  spinner: {
    viewBox: "0 0 512 512",
    d: "M222.7 32.1c5 16.9-4.6 34.8-21.5 39.8C121.8 95.6 64 169.1 64 256c0 106 86 192 192 192s192-86 192-192c0-86.9-57.8-160.4-137.1-184.1c-16.9-5-26.6-22.9-21.5-39.8s22.9-26.6 39.8-21.5C434.9 42.1 512 140 512 256c0 141.4-114.6 256-256 256S0 397.4 0 256C0 140 77.1 42.1 182.9 10.6c16.9-5 34.8 4.6 39.8 21.5z",
  },
};

const state = {
  spotifyVisible: false,
  playing: false,
  buffering: false,
  positionMs: 0,
  durationMs: 0,
  lastSyncMs: Date.now(),
  artUrl: "",
  artFront: "a",
  wallpaperUrl: "",
  wallpaperFront: "a",
  sunrise: "",
  sunset: "",
  emptyStreak: 0,
  stateIcon: "",
  titleScrollGeneration: 0,
  titleTrackKey: "",
  lastProgressSec: -1,
  lastProgressPct: -1,
  night: null,
  clockKey: "",
};

const els = {};
const $ = (id) => els[id] || (els[id] = document.getElementById(id));

let sampleCanvas = null;
let sampleCtx = null;
let spotifyInflight = false;
let snapshotInflight = false;

const sigs = {};

function changed(key, value) {
  const next = JSON.stringify(value);
  if (sigs[key] === next) return false;
  sigs[key] = next;
  return true;
}

function setText(el, value) {
  const next = value == null ? "" : String(value);
  if (el.textContent !== next) el.textContent = next;
}

function setScrollingTitle(value, trackKey) {
  const el = $("spotify-title");
  const next = value || "Unknown track";
  const nextKey = trackKey || next;
  if (state.titleTrackKey === nextKey && el.textContent === next && el.dataset.scrollReady === "1") return;
  const generation = ++state.titleScrollGeneration;
  state.titleTrackKey = nextKey;
  el.textContent = next;
  el.dataset.scrollReady = "0";
  el.classList.remove("is-scrolling");
  el.style.removeProperty("--title-shift");
  el.style.removeProperty("--title-duration");
  el.style.transform = "";
  const start = () => {
    if (generation !== state.titleScrollGeneration || el.textContent !== next) return;
    el.dataset.scrollReady = "1";
    const viewport = el.parentElement ? el.parentElement.clientWidth : 0;
    const overflow = Math.ceil(el.scrollWidth - viewport);
    if (overflow <= 4) return;
    const travel = Math.max(7, Math.min(16, overflow / 28));
    el.style.setProperty("--title-shift", `-${overflow}px`);
    el.style.setProperty("--title-duration", `${((travel + 1.9) * 2).toFixed(2)}s`);
    el.classList.add("is-scrolling");
  };
  requestAnimationFrame(() => requestAnimationFrame(start));
}

function sampleContext() {
  if (!sampleCanvas) {
    sampleCanvas = document.createElement("canvas");
    sampleCtx = sampleCanvas.getContext("2d", { willReadFrequently: true });
  }
  return sampleCtx;
}

function applyArtworkAccent(image) {
  try {
    const context = sampleContext();
    sampleCanvas.width = 8;
    sampleCanvas.height = 8;
    context.drawImage(image, 0, 0, 8, 8);
    const pixels = context.getImageData(0, 0, 8, 8).data;
    let r = 0;
    let g = 0;
    let b = 0;
    let n = 0;
    for (let i = 0; i < pixels.length; i += 4) {
      const lum = pixels[i] * 0.3 + pixels[i + 1] * 0.59 + pixels[i + 2] * 0.11;
      if (lum < 28 || lum > 230) continue;
      r += pixels[i];
      g += pixels[i + 1];
      b += pixels[i + 2];
      n += 1;
    }
    if (!n) return;
    r /= n;
    g /= n;
    b /= n;
    const max = Math.max(r, g, b) / 255;
    const min = Math.min(r, g, b) / 255;
    const delta = max - min;
    let hue = 150;
    if (delta) {
      if (max === r / 255) hue = 60 * (((g - b) / 255 / delta) % 6);
      else if (max === g / 255) hue = 60 * ((b - r) / 255 / delta + 2);
      else hue = 60 * ((r - g) / 255 / delta + 4);
    }
    if (hue < 0) hue += 360;
    document.body.style.setProperty("--dynamic-accent-dark", `hsl(${Math.round(hue)} 62% 64%)`);
    document.body.style.setProperty("--dynamic-accent-light", `hsl(${Math.round(hue)} 58% 38%)`);
  } catch (_) {}
}

function scheduleClock() {
  updateClock();
  const delay = 60000 - (Date.now() % 60000) + 80;
  setTimeout(scheduleClock, delay);
}

function updateClock() {
  const now = new Date();
  const key = `${now.getHours()}:${now.getMinutes()}`;
  if (key === state.clockKey) {
    applyTheme();
    return;
  }
  state.clockKey = key;
  const hours = now.getHours();
  setText($("clock-time"), `${hours % 12 || 12}:${String(now.getMinutes()).padStart(2, "0")}`);
  setText($("clock-ampm"), hours < 12 ? "AM" : "PM");
  setText($("date"), now.toLocaleDateString([], { weekday: "long", month: "long", day: "numeric" }));
  const hour = now.getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
  setText($("greeting"), greeting);
  applyTheme();
}

function parseSunMinutes(value) {
  const text = String(value || "").trim();
  if (!text) return null;
  const match = text.match(/^(\d{1,2}):(\d{2})\s*(AM|PM)?$/i);
  if (!match) return null;
  let hours = Number(match[1]);
  const minutes = Number(match[2]);
  const ampm = (match[3] || "").toUpperCase();
  if (ampm === "PM" && hours < 12) hours += 12;
  if (ampm === "AM" && hours === 12) hours = 0;
  return hours * 60 + minutes;
}

function isNight() {
  const now = new Date();
  const nowM = now.getHours() * 60 + now.getMinutes();
  const rise = parseSunMinutes(state.sunrise);
  const sett = parseSunMinutes(state.sunset);
  if (rise == null || sett == null) return now.getHours() < 7 || now.getHours() >= 20;
  return nowM < rise || nowM >= sett;
}

function applyTheme() {
  const night = isNight();
  if (state.night === night) return;
  state.night = night;
  document.body.classList.toggle("theme-light", !night);
  document.body.classList.toggle("theme-dark", night);
}

function formatTime(ms) {
  const seconds = Math.max(0, Math.floor(Number(ms || 0) / 1000));
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}

function currentPositionMs() {
  let value = state.positionMs;
  if (state.playing && !state.buffering) value += Date.now() - state.lastSyncMs;
  return state.durationMs ? Math.min(value, state.durationMs) : value;
}

function renderProgress() {
  if (!state.spotifyVisible) return;
  const pos = currentPositionMs();
  const sec = Math.floor(pos / 1000);
  if (sec !== state.lastProgressSec) {
    state.lastProgressSec = sec;
    setText($("spotify-position"), formatTime(pos));
    setText($("spotify-duration"), formatTime(state.durationMs));
  }
  const pct = state.durationMs > 0 ? Math.min(100, (pos / state.durationMs) * 100) : 0;
  const rounded = Math.round(pct * 2) / 2;
  if (rounded === state.lastProgressPct) return;
  state.lastProgressPct = rounded;
  $("spotify-progress").style.transform = `scaleX(${rounded / 100})`;
}

function setStateIcon(kind, spinning = false) {
  const key = `${kind}:${spinning ? 1 : 0}`;
  if (state.stateIcon === key) return;
  state.stateIcon = key;
  const svg = $("spotify-state-icon");
  const eq = $("spotify-eq");
  const playing = kind === "play" && !spinning;
  if (eq) eq.classList.toggle("is-on", playing);
  if (playing) {
    svg.classList.add("is-idle");
    return;
  }
  svg.classList.remove("is-idle");
  const icon = STATE_ICONS[kind];
  svg.setAttribute("viewBox", icon.viewBox);
  svg.innerHTML = `<path fill="currentColor" d="${icon.d}"></path>`;
  svg.classList.toggle("spin", spinning);
}

function showIdle() {
  if (!state.spotifyVisible) return;
  state.spotifyVisible = false;
  state.titleScrollGeneration += 1;
  state.titleTrackKey = "";
  state.lastProgressSec = -1;
  state.lastProgressPct = -1;
  document.body.classList.remove("is-paused");
  const title = $("spotify-title");
  title.classList.remove("is-scrolling");
  title.style.removeProperty("--title-shift");
  title.style.removeProperty("--title-duration");
  title.style.transform = "";
  title.dataset.scrollReady = "0";
  $("spotify-widget").classList.add("hidden");
  const eq = $("spotify-eq");
  if (eq) eq.classList.remove("is-on");
  clearSpotifyArt();
}

function showSpotify() {
  if (state.spotifyVisible) return;
  state.spotifyVisible = true;
  $("spotify-widget").classList.remove("hidden");
}

function clearSpotifyArt() {
  ["a", "b"].forEach((key) => {
    const image = $(`spotify-image-${key}`);
    image.classList.remove("active");
    image.removeAttribute("src");
    image.alt = "";
  });
  $("spotify-placeholder").classList.remove("is-faded");
  document.body.style.removeProperty("--dynamic-accent-dark");
  document.body.style.removeProperty("--dynamic-accent-light");
  state.artUrl = "";
}

function setSpotifyArt(url) {
  if (!url) {
    clearSpotifyArt();
    return;
  }
  if (url === state.artUrl) return;

  const preload = new Image();
  preload.crossOrigin = "anonymous";
  preload.onload = () => {
    const nextKey = state.artFront === "a" ? "b" : "a";
    const prevKey = state.artFront;
    const nextImg = $(`spotify-image-${nextKey}`);
    nextImg.src = url;
    nextImg.alt = "Album artwork";
    nextImg.classList.add("active");
    const prevImg = $(`spotify-image-${prevKey}`);
    prevImg.classList.remove("active");
    $("spotify-placeholder").classList.add("is-faded");
    state.artFront = nextKey;
    state.artUrl = url;
    applyArtworkAccent(preload);
    setTimeout(() => {
      if (state.artFront !== nextKey) return;
      prevImg.removeAttribute("src");
      prevImg.alt = "";
    }, 500);
  };
  preload.src = url;
}

function applySpotify(data) {
  const track = data && data.track;
  if (!data || !track) {
    state.emptyStreak += 1;
    state.playing = false;
    state.buffering = false;
    if (state.spotifyVisible && state.emptyStreak < 3) {
      setText($("spotify-state-label"), "Paused");
      setStateIcon("pause");
      return;
    }
    showIdle();
    return;
  }

  state.emptyStreak = 0;
  const paused = Boolean(data.paused) || Boolean(data.stopped);
  const buffering = Boolean(data.buffering);
  const serverPos = Number(track.position || 0);
  const duration = Number(track.duration || 0);
  const estimated = currentPositionMs();

  state.buffering = buffering;
  state.durationMs = duration;

  if (paused || buffering) {
    state.playing = false;
    state.positionMs = serverPos || estimated;
    state.lastSyncMs = Date.now();
  } else {
    state.playing = true;
    if (Math.abs(serverPos - estimated) > 2000) {
      state.positionMs = serverPos;
      state.lastSyncMs = Date.now();
    }
  }

  showSpotify();
  document.body.classList.toggle("is-paused", paused && !buffering);
  const trackKey = track.uri || "";
  if (trackKey !== state.titleTrackKey) {
    state.lastProgressSec = -1;
    state.lastProgressPct = -1;
  }
  setScrollingTitle(track.name || "Unknown track", trackKey);
  setText($("spotify-artist"), (track.artist_names || []).join(", ") || "Unknown artist");
  setSpotifyArt(track.album_cover_url || "");

  if (buffering) {
    setText($("spotify-state-label"), data.source === "cd" ? "Reading disc" : "Buffering");
    setStateIcon("spinner", true);
  } else if (paused) {
    setText($("spotify-state-label"), "Paused");
    setStateIcon("pause");
  } else {
    setText($("spotify-state-label"), data.source === "cd" ? "Compact Disc" : "Now Playing");
    setStateIcon("play");
  }
  renderProgress();
}

function applyNetwork(data) {
  if (!data || !changed("network", data)) return;
  setText($("network-ssid"), data.ssid || "Offline");
  setText($("network-ip"), data.ip || "No IP");
}

function applyServices(data) {
  if (!data || !changed("services", data)) return;
  Object.entries(data).forEach(([name, ready]) => {
    const el = document.querySelector(`[data-service="${name}"]`);
    if (!el) return;
    const optionalIdle = name === "disc" && !ready;
    el.classList.toggle("is-ready", Boolean(ready));
    el.classList.toggle("is-down", !ready && !optionalIdle);
    el.classList.toggle("is-idle", optionalIdle);
  });
}

function escapeHtml(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function weatherIconMarkup(kind, className) {
  const icon = WEATHER_ICONS[kind] || WEATHER_ICONS.sun;
  const cls = className ? ` class="${className}"` : ' class="icon"';
  return `<svg${cls} viewBox="${icon.viewBox}" aria-hidden="true"><path fill="currentColor" d="${icon.d}"></path></svg>`;
}

function setWeatherIcon(svg, kind) {
  if (!svg) return;
  const key = WEATHER_ICONS[kind] ? kind : "sun";
  if (svg.dataset.icon === key) return;
  const icon = WEATHER_ICONS[key];
  svg.dataset.icon = key;
  svg.setAttribute("viewBox", icon.viewBox);
  svg.innerHTML = `<path fill="currentColor" d="${icon.d}"></path>`;
}

function applyHourly(hours) {
  const root = $("hourly");
  if (!root) return;
  const items = Array.isArray(hours) ? hours.slice(0, 5) : [];
  root.classList.toggle("has-items", items.length > 0);
  root.innerHTML = items.map((hour) => {
    const chance = Number(hour.rain || 0);
    const rainClass = chance >= 50 ? "hourly-rain is-likely" : "hourly-rain";
    const rain = `<span class="${rainClass}">${chance}%</span>`;
    return `<div class="hourly-slot">${escapeHtml(hour.label || "")}${weatherIconMarkup(hour.icon)}<span class="hourly-temp">${hour.temp != null ? `${hour.temp}°` : ""}</span>${rain}</div>`;
  }).join("");
}

function applyForecast(days) {
  const root = $("forecast");
  if (!root) return;
  const items = Array.isArray(days) ? days.slice(0, 3) : [];
  root.classList.toggle("has-items", items.length > 0);
  root.innerHTML = items.map((day) => {
    const chance = Number(day.rain || 0);
    const rainClass = chance >= 50 ? "forecast-rain is-likely" : "forecast-rain";
    const rain = `<span class="${rainClass}">${chance}%</span>`;
    const temps = [day.high != null ? `${day.high}°` : "", day.low != null ? `${day.low}°` : ""].filter(Boolean).join(" / ");
    return `<div class="forecast-day"><span class="forecast-label">${escapeHtml(day.label || "")}</span>${weatherIconMarkup(day.icon)}<span class="forecast-temps">${temps}</span>${rain}</div>`;
  }).join("");
}

function applyWeather(data) {
  if (!data) return;
  const weatherKey = {
    temp: data.temp, desc: data.desc, icon: data.icon, high: data.high, low: data.low,
    feels: data.feels, humidity: data.humidity, wind: data.wind, wind_dir: data.wind_dir,
    uv: data.uv, aqi: data.aqi, is_night: data.is_night, alert: data.alert,
    sunrise: data.sunrise, sunset: data.sunset, hourly: data.hourly, days: data.days,
    location: data.location, region: data.region,
  };
  if (!changed("weather", weatherKey)) {
    state.sunrise = data.sunrise || "";
    state.sunset = data.sunset || "";
    applyTheme();
    return;
  }
  setText($("weather-temp"), data.temp != null ? data.temp : "--");
  setText($("weather-desc"), data.desc || "");
  const place = [data.location, data.region].filter(Boolean).join(", ");
  setText($("weather-place"), place || "Newberry");
  const high = data.high != null ? `H ${data.high}°` : "";
  const low = data.low != null ? `L ${data.low}°` : "";
  const range = [high, low].filter(Boolean).join("  ");
  setText($("weather-range"), range);
  const feels = data.feels != null && data.feels !== data.temp ? `Feels ${data.feels}°` : "";
  setText($("weather-feels"), feels);
  setText($("weather-alert"), data.alert || "");
  const humidity = data.humidity != null ? `${data.humidity}%` : "";
  const windParts = [];
  if (data.wind != null) windParts.push(`${data.wind} mph`);
  if (data.wind_dir) windParts.push(data.wind_dir);
  const wind = windParts.join(" ");
  setText($("weather-humidity"), humidity);
  setText($("weather-wind"), wind);
  const showUv = !data.is_night && data.uv != null && Number(data.uv) > 0;
  const showAqi = data.aqi != null;
  setText($("weather-uv"), showUv ? String(data.uv) : "");
  setText($("weather-aqi"), showAqi ? String(data.aqi) : "");
  $("weather-uv-stat")?.classList.toggle("hidden", !showUv);
  $("weather-aqi-stat")?.classList.toggle("hidden", !showAqi);
  const stats = $("weather-stats");
  if (stats) stats.classList.toggle("has-items", Boolean(humidity || wind || showUv || showAqi));
  const extras = [];
  if (data.sunrise) extras.push(`↑ ${data.sunrise}`);
  if (data.sunset) extras.push(`↓ ${data.sunset}`);
  setText($("weather-extras"), extras.join(" · "));
  setWeatherIcon($("weather-icon"), data.icon || "sun");
  applyHourly(data.hourly);
  applyForecast(data.days);
  state.sunrise = data.sunrise || "";
  state.sunset = data.sunset || "";
  applyTheme();
}

function applyBluetooth(data) {
  if (!changed("bluetooth", data || {})) return;
  const chip = document.querySelector('[data-service="bluetooth"]');
  const connected = Boolean(data && data.connected && data.name);
  setText($("bluetooth-label"), connected ? data.name : "Bluetooth");
  if (chip) chip.classList.toggle("is-connected", connected);
}

function applyAlerts(data) {
  if (!changed("alerts", data || {})) return;
  const el = $("hazard");
  if (!el) return;
  const primary = data && data.primary;
  if (!primary || !primary.event) {
    el.classList.add("hidden");
    el.classList.remove("is-on", "is-warning", "is-watch", "is-urgent");
    document.body.classList.remove("has-hazard");
    setText($("hazard-event"), "");
    setText($("hazard-copy"), "");
    return;
  }
  setText($("hazard-event"), primary.event);
  let copy = primary.detail || "";
  if (data.count > 1) copy = copy ? `${copy} · +${data.count - 1} more` : `+${data.count - 1} more`;
  setText($("hazard-copy"), copy);
  el.classList.toggle("is-warning", primary.level === "warning");
  el.classList.toggle("is-watch", primary.level !== "warning");
  el.classList.toggle("is-urgent", Boolean(primary.urgent));
  el.classList.add("is-on");
  el.classList.remove("hidden");
  document.body.classList.add("has-hazard");
}

function applyAgenda(calendar, ntfy) {
  const card = $("agenda");
  const list = $("agenda-items");
  if (!card || !list) return;
  const events = calendar && Array.isArray(calendar.events) ? calendar.events.slice(0, 2) : [];
  const notes = ntfy && Array.isArray(ntfy.items) ? ntfy.items.slice(0, 2) : [];
  if (!changed("agenda", { events, notes })) return;
  if (!events.length && !notes.length) {
    card.classList.add("hidden");
    list.innerHTML = "";
    return;
  }
  const rows = [];
  events.forEach((event) => {
    rows.push(`<div class="agenda-item is-event"><div class="agenda-label">${escapeHtml(event.when || "")}</div><div class="agenda-copy">${escapeHtml(event.title || "Busy")}</div><div class="agenda-when"></div></div>`);
  });
  notes.forEach((item) => {
    const kind = item.kind === "missed" ? " is-missed" : "";
    const extra = item.body ? ` <span>${escapeHtml(item.body)}</span>` : "";
    rows.push(`<div class="agenda-item is-notify${kind}"><div class="agenda-label">${escapeHtml(item.app || "Notification")}</div><div class="agenda-copy">${escapeHtml(item.title || "Notification")}${extra}</div><div class="agenda-when">${escapeHtml(item.when || "")}</div></div>`);
  });
  list.innerHTML = rows.join("");
  card.classList.remove("hidden");
}

function wallpaperLayer(key) {
  return $(`wallpaper-${key}`);
}

function hiddenWallpaperKey() {
  return state.wallpaperFront === "a" ? "b" : "a";
}

function setWallpaperLayer(key, url) {
  const el = wallpaperLayer(key);
  if (!el || el.dataset.url === url) return el;
  el.src = url;
  el.dataset.url = url;
  return el;
}

function wallpaperReady(el, url) {
  return el && el.dataset.url === url && el.complete && el.naturalWidth > 0;
}

function showWallpaper(url, immediate = false) {
  if (!url || url === state.wallpaperUrl) return;
  const nextKey = hiddenWallpaperKey();
  const prevKey = state.wallpaperFront;
  const nextEl = setWallpaperLayer(nextKey, url);
  const apply = () => {
    if (immediate) nextEl.style.transition = "none";
    nextEl.classList.add("active");
    const prevEl = wallpaperLayer(prevKey);
    prevEl.classList.remove("active");
    if (immediate) {
      void nextEl.offsetHeight;
      nextEl.style.transition = "";
    }
    state.wallpaperFront = nextKey;
    state.wallpaperUrl = url;
    setTimeout(() => {
      if (state.wallpaperFront !== nextKey) return;
      prevEl.removeAttribute("src");
      delete prevEl.dataset.url;
    }, immediate ? 0 : 500);
  };
  if (wallpaperReady(nextEl, url)) {
    apply();
    return;
  }
  const onReady = () => {
    nextEl.removeEventListener("load", onReady);
    if (nextEl.dataset.url === url) apply();
  };
  nextEl.addEventListener("load", onReady);
}

function applyBackground(data) {
  if (!data) return;
  const query = data.query ? String(data.query).replace(/\b\w/g, (char) => char.toUpperCase()) : "";
  setText($("wallpaper-credit"), ["Wallhaven", query, data.id].filter(Boolean).join(" · "));
  if (data.local) showWallpaper(data.local, !state.wallpaperUrl);
}

async function refreshSnapshot() {
  if (snapshotInflight) return;
  snapshotInflight = true;
  try {
    const res = await fetch("/api/snapshot", { cache: "no-store" });
    if (!res.ok) return;
    const data = await res.json();
    applyNetwork(data.network);
    applyServices(data.services);
    applyBluetooth(data.bluetooth);
    applyWeather(data.weather);
    applyAgenda(data.calendar, data.ntfy);
    applyAlerts(data.alerts);
    applyBackground(data.background);
  } catch (_) {}
  finally {
    snapshotInflight = false;
  }
}

async function refreshSpotify() {
  if (spotifyInflight) return;
  spotifyInflight = true;
  try {
    const res = await fetch("/api/spotify", { cache: "no-store" });
    if (res.status === 204) {
      applySpotify(null);
      return;
    }
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    applySpotify(await res.json());
  } catch (_) {}
  finally {
    spotifyInflight = false;
  }
}

async function refreshWallpaper() {
  try {
    const res = await fetch("/api/background", { cache: "no-store" });
    if (!res.ok) return;
    const data = await res.json();
    applyBackground(data);
  } catch (_) {}
}

function loopProgress() {
  if (state.spotifyVisible && state.playing) renderProgress();
  setTimeout(loopProgress, 1000);
}

function loopSpotify() {
  refreshSpotify().finally(() => {
    setTimeout(loopSpotify, state.spotifyVisible ? 2000 : 4500);
  });
}

function loopSnapshot() {
  refreshSnapshot().finally(() => {
    setTimeout(loopSnapshot, 20000);
  });
}

scheduleClock();
loopSnapshot();
loopSpotify();
loopProgress();
