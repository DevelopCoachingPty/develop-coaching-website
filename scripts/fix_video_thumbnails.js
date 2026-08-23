#!/usr/bin/env node

const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const WWW = path.join(ROOT, "www");
const ORIGIN = "https://develop-coaching.com";
const WRITE = process.argv.includes("--write");
const SCRIPT_RE = /(<script[^>]*type=["']application\/ld\+json["'][^>]*>)([\s\S]*?)(<\/script>)/gi;

const SPECIAL_THUMBNAILS = new Map([
  [
    "/wp-content/uploads/2022/12/MONTAGE-181022.mp4",
    `${ORIGIN}/wp-content/uploads/2022/12/MONTAGE-181022-thumbnail.jpg`,
  ],
  [
    "/wp-content/uploads/2023/01/Promo-Website-Video_Subtitles-1.mp4",
    `${ORIGIN}/wp-content/uploads/2023/01/Promo-Website-Video_Subtitles-1-thumbnail.jpg`,
  ],
  [
    "/wp-content/uploads/2022/12/LUKAS-TESTIMONIAL.mp4",
    `${ORIGIN}/wp-content/uploads/2022/12/Lukas-Thumbnail-2.png`,
  ],
]);

function filesUnder(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const fullPath = path.join(directory, entry.name);
    return entry.isDirectory() ? filesUnder(fullPath) : [fullPath];
  });
}

function urlPath(value) {
  try {
    return new URL(value, ORIGIN).pathname;
  } catch {
    return null;
  }
}

function absoluteUrl(value) {
  return new URL(value, ORIGIN).href;
}

function posterMap(html) {
  const posters = new Map();
  for (const match of html.matchAll(/<video\b[^>]*>/gi)) {
    const tag = match[0];
    const source = tag.match(/\bsrc=["']([^"']+)["']/i)?.[1];
    const poster = tag.match(/\bposter=["']([^"']+)["']/i)?.[1];
    const sourcePath = source && urlPath(source);
    if (sourcePath && poster && !posters.has(sourcePath)) {
      posters.set(sourcePath, absoluteUrl(poster));
    }
  }
  return posters;
}

function objectSpans(raw) {
  const spans = [];
  const stack = [];
  let inString = false;
  let escaped = false;

  for (let index = 0; index < raw.length; index += 1) {
    const character = raw[index];
    if (inString) {
      if (escaped) escaped = false;
      else if (character === "\\") escaped = true;
      else if (character === '"') inString = false;
      continue;
    }
    if (character === '"') inString = true;
    else if (character === "{") stack.push(index);
    else if (character === "}") spans.push([stack.pop(), index + 1]);
  }
  return spans;
}

function hasVideoType(value) {
  const types = Array.isArray(value["@type"]) ? value["@type"] : [value["@type"]];
  return types.includes("VideoObject");
}

function desiredThumbnail(video, posters) {
  if (video.contentUrl) {
    const contentPath = urlPath(video.contentUrl);
    return posters.get(contentPath) || SPECIAL_THUMBNAILS.get(contentPath) || null;
  }
  if (video.embedUrl) {
    const videoId = urlPath(video.embedUrl)?.match(/^\/embed\/([A-Za-z0-9_-]{11})$/)?.[1];
    return videoId ? `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg` : null;
  }
  return null;
}

function deletionRange(raw, start, end) {
  let next = end;
  while (/\s/.test(raw[next] || "")) next += 1;
  if (raw[next] === ",") return [start, next + 1];

  let previous = start - 1;
  while (/\s/.test(raw[previous] || "")) previous -= 1;
  return raw[previous] === "," ? [previous, end] : [start, end];
}

function transformJson(raw, posters, counters) {
  const replacements = [];

  for (const [start, end] of objectSpans(raw)) {
    let value;
    try {
      value = JSON.parse(raw.slice(start, end));
    } catch {
      continue;
    }
    if (!hasVideoType(value)) continue;

    if (value.embedUrl && urlPath(value.embedUrl) === "/embed/videoseries") {
      const [deleteStart, deleteEnd] = deletionRange(raw, start, end);
      replacements.push([deleteStart, deleteEnd, ""]);
      counters.removed += 1;
      continue;
    }

    const desired = desiredThumbnail(value, posters);
    if (!desired) {
      if (!value.thumbnailUrl) counters.unresolved.push(value["@id"] || "VideoObject");
      continue;
    }

    const objectText = raw.slice(start, end);
    if (!value.thumbnailUrl) {
      replacements.push([start + 1, start + 1, `"thumbnailUrl":${JSON.stringify(desired)},`]);
      counters.added += 1;
    } else if (
      value.contentUrl &&
      urlPath(value.contentUrl) === "/wp-content/uploads/2022/12/MONTAGE-181022.mp4" &&
      value.thumbnailUrl !== desired
    ) {
      const oldProperty = `"thumbnailUrl":${JSON.stringify(value.thumbnailUrl)}`;
      const offset = objectText.indexOf(oldProperty);
      if (offset >= 0) {
        replacements.push([
          start + offset,
          start + offset + oldProperty.length,
          `"thumbnailUrl":${JSON.stringify(desired)}`,
        ]);
        counters.updated += 1;
      }
    }
  }

  return replacements
    .sort((left, right) => right[0] - left[0])
    .reduce(
      (text, [start, end, replacement]) => text.slice(0, start) + replacement + text.slice(end),
      raw,
    );
}

const counters = { added: 0, updated: 0, removed: 0, files: 0, unresolved: [] };

for (const filePath of filesUnder(WWW).filter((file) => file.endsWith(".html"))) {
  const original = fs.readFileSync(filePath, "utf8");
  const posters = posterMap(original);
  const transformed = original.replace(
    SCRIPT_RE,
    (whole, opening, raw, closing) => opening + transformJson(raw, posters, counters) + closing,
  );
  if (transformed !== original) {
    counters.files += 1;
    if (WRITE) fs.writeFileSync(filePath, transformed);
  }
}

console.log(JSON.stringify({ mode: WRITE ? "write" : "check", ...counters }, null, 2));
if (counters.unresolved.length) process.exitCode = 1;
