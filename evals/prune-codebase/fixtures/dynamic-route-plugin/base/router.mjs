import { readFile } from "node:fs/promises";


const routes = JSON.parse(
  await readFile(new URL("./routes.json", import.meta.url), "utf8"),
);

export async function load(name) {
  const [modulePath, exportName] = routes[name].split("#", 2);
  const module = await import(new URL(modulePath, import.meta.url));
  return module[exportName];
}
