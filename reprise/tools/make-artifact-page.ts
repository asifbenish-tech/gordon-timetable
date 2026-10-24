// tools/make-artifact-page.ts: turns dist/index.html into dist/artifact.html for hosts that wrap the page
// in their own document skeleton (a claude.ai Artifact): title, inline CSS, the app root and the bundle.
import { readFileSync, readdirSync, writeFileSync } from "node:fs";

const dist = new URL("../dist/", import.meta.url);
const html = readFileSync(new URL("index.html", dist), "utf8");
const script = html.match(/<script type="module"[^>]*src="([^"]+)"/)?.[1];
const css = html.match(/<link rel="stylesheet"[^>]*href="([^"]+)"/)?.[1];
const title = html.match(/<title>([^<]*)<\/title>/)?.[1] ?? "Reprise";
if (!script || !css) throw new Error("dist/index.html has no bundle; run vite build first");
const style = readFileSync(new URL(css.replace(/^\.\//, ""), dist), "utf8");
writeFileSync(
  new URL("artifact.html", dist),
  `<title>${title}</title>
<meta name="description" content="A free point-and-click adventure where every action is a melody.">
<style>${style}</style>
<div id="app"></div>
<noscript>This game needs JavaScript.</noscript>
<script type="module" src="${script}"></script>
`,
);
const files = readdirSync(new URL("assets/", dist)).filter((f) => !f.endsWith(".css"));
console.log(`dist/artifact.html written; ${files.length} supporting files in dist/assets`);
