// Mirrors the old config.py / coords.py — but scoped to just the canvas
// element's own pixel box (0,0)-(BOX_W,BOX_H) rather than the whole window.

export const WORLD_WIDTH = 50;
export const WORLD_HEIGHT = 30;

export const BOX_W = 800;
export const BOX_H = 480;

const ppx = BOX_W / WORLD_WIDTH;
const ppy = BOX_H / WORLD_HEIGHT;

export function worldToScreen(wx, wy) {
  return [wx * ppx, BOX_H - wy * ppy];
}

export function screenToWorld(sx, sy) {
  return [sx / ppx, (BOX_H - sy) / ppy];
}

export function worldLenToPxX(len) {
  return len * ppx;
}

export function worldLenToPxY(len) {
  return len * ppy;
}

export function rgb([r, g, b]) {
  return `rgb(${r}, ${g}, ${b})`;
}
