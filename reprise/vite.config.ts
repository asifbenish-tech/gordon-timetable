import { defineConfig, type Plugin } from "vite";
import { readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { join, relative } from "node:path";

/** Writes dist/sw.js listing every built file, so the game installs and plays offline (GDD 9.9). */
function serviceWorker(): Plugin {
  let outDir = "dist";
  return {
    name: "reprise-sw",
    apply: "build",
    configResolved(c) {
      outDir = c.build.outDir;
    },
    closeBundle() {
      const files: string[] = [];
      const walk = (d: string) => {
        for (const f of readdirSync(d)) {
          const p = join(d, f);
          if (statSync(p).isDirectory()) walk(p);
          else if (f !== "sw.js") files.push("./" + relative(outDir, p).split("\\").join("/"));
        }
      };
      walk(outDir);
      const version = Date.now().toString(36);
      writeFileSync(
        join(outDir, "sw.js"),
        `const CACHE="reprise-${version}";const FILES=${JSON.stringify(["./", ...files])};
self.addEventListener("install",e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(FILES)).then(()=>self.skipWaiting())));
self.addEventListener("activate",e=>e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener("fetch",e=>{if(e.request.method!=="GET")return;e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)))});
`,
      );
    },
  };
}

/** The page title and the install manifest come from the chosen name set (GDD 1). */
function nameSet(): Plugin {
  const names = JSON.parse(readFileSync(new URL("content/names.json", import.meta.url), "utf8")) as { default: string; sets: Record<string, Record<string, string>> };
  const set = names.sets[process.env.NAMES ?? ""] ?? names.sets[names.default];
  let outDir = "dist";
  return {
    name: "reprise-names",
    configResolved(c) {
      outDir = c.build.outDir;
    },
    transformIndexHtml: (html) => html.replace(/<title>[^<]*<\/title>/, `<title>${set.title}</title>`),
    closeBundle() {
      const manifest = {
        name: set.title,
        short_name: set.titleShort,
        description: "A free point-and-click adventure where every action is a melody.",
        start_url: "./",
        display: "fullscreen",
        orientation: "landscape",
        background_color: "#0d0b14",
        theme_color: "#0d0b14",
        icons: [{ src: "icon.png", sizes: "192x192", type: "image/png", purpose: "any" }],
      };
      writeFileSync(join(outDir, "app.webmanifest"), JSON.stringify(manifest, null, 1));
    },
  };
}

export default defineConfig(({ mode }) => ({
  base: "./",
  define: {
    __NAMES__: JSON.stringify(process.env.NAMES ?? ""),
    __DEBUG__: JSON.stringify(mode !== "production"),
  },
  build: {
    target: "es2022",
    assetsInlineLimit: 0,
    chunkSizeWarningLimit: 3000,
  },
  plugins: [nameSet(), serviceWorker()],
}));
