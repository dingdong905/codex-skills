#!/usr/bin/env node
// Adapted from claudekit's design-system generator; retain aliases for theme overrides.
const fs = require('node:fs');
const path = require('node:path');
const REF = /\{([^{}]+)\}/g;
function cssName(parts) {
  const prefix = parts[0] === 'dark' ? parts.slice(2) : parts[0] === 'primitive' ? parts : parts.slice(1);
  if (prefix.some(p => !/^[a-zA-Z0-9_-]+$/.test(p))) throw new Error(`Invalid token name: ${parts.join('.')}`);
  return '--' + prefix.join('-');
}
function collectTokens(tokens) {
  if (!tokens || typeof tokens !== 'object' || Array.isArray(tokens)) throw new Error('Token config must be an object');
  const entries = new Map();
  function walk(obj, parts) {
    if (!obj || typeof obj !== 'object' || Array.isArray(obj)) throw new Error(`Expected token group: ${parts.join('.')}`);
    for (const [key,value] of Object.entries(obj)) {
      if (key.startsWith('$')) continue;
      const next = [...parts,key];
      if (value && typeof value === 'object' && !Array.isArray(value) && Object.hasOwn(value,'$value')) {
        if (!(typeof value.$value === 'string' || (typeof value.$value === 'number' && Number.isFinite(value.$value)))) {
          throw new Error(`Unsupported composite value at ${next.join('.')}: convert to a CSS string`);
        }
        const text = String(value.$value);
        const stripped = text.replace(REF, '');
        if (/[;{}]/.test(stripped) || /\/\*|\*\//.test(stripped)) throw new Error(`Unsafe CSS value at ${next.join('.')}`);
        entries.set(next.join('.'), {parts:next,name:cssName(next),value:text,dark:next[0]==='dark'});
      } else walk(value,next);
    }
  }
  for (const group of ['primitive','semantic','component']) if (tokens[group] !== undefined) walk(tokens[group],[group]);
  if (tokens.dark !== undefined) {
    if (Object.keys(tokens.dark).some(k => k !== 'semantic' && !k.startsWith('$'))) throw new Error('Only dark.semantic overrides are supported');
    if (tokens.dark.semantic !== undefined) walk(tokens.dark.semantic,['dark','semantic']);
  }
  if (!entries.size) throw new Error('No tokens found');
  const names = new Map();
  for (const [id,e] of entries) {
    const scoped = `${e.dark?'dark':'root'}:${e.name}`;
    if (names.has(scoped)) throw new Error(`CSS variable collision: ${id} and ${names.get(scoped)}`);
    names.set(scoped,id);
    for (const match of e.value.matchAll(REF)) {
      const target = entries.get(match[1]);
      if (!target) throw new Error(`Missing reference ${match[1]} in ${id}`);
      if (!e.dark && target.dark) throw new Error(`Light token ${id} cannot reference dark-only token ${match[1]}`);
    }
  }
  const visited=new Set(), active=new Set();
  function visit(id) {
    if (active.has(id)) throw new Error(`Token reference cycle at ${id}`);
    if (visited.has(id)) return;
    active.add(id);
    for (const m of entries.get(id).value.matchAll(REF)) visit(m[1]);
    active.delete(id); visited.add(id);
  }
  for (const id of entries.keys()) visit(id);
  // Check effective dark aliases too: references to a semantic variable may be overridden.
  const darkByName = new Map([...entries].filter(([,e])=>e.dark).map(([id,e])=>[e.name,id]));
  visited.clear(); active.clear();
  function visitDark(id) {
    if (active.has(id)) throw new Error(`Dark theme reference cycle at ${id}`);
    if (visited.has(id)) return;
    active.add(id);
    for (const m of entries.get(id).value.matchAll(REF)) {
      const target=entries.get(m[1]);
      visitDark(darkByName.get(target.name) || m[1]);
    }
    active.delete(id); visited.add(id);
  }
  for (const [id,e] of entries) if (e.dark || !darkByName.has(e.name)) visitDark(id);
  return entries;
}
function generateCSS(tokens) {
  const entries=collectTokens(tokens), root=[], dark=[];
  for (const e of entries.values()) {
    const value=e.value.replace(REF,(_,id)=>`var(${entries.get(id).name})`);
    (e.dark?dark:root).push(`  ${e.name}: ${value};`);
  }
  // Rebind inherited aliases at a nested dark boundary; CSS resolves var() where declared.
  if (dark.length) {
    const overridden=new Set([...entries.values()].filter(e=>e.dark).map(e=>e.name));
    for (const e of entries.values()) {
      if (!e.dark && !overridden.has(e.name) && /\{[^{}]+\}/.test(e.value)) {
        dark.push(`  ${e.name}: ${e.value.replace(REF,(_,id)=>`var(${entries.get(id).name})`)};`);
      }
    }
  }
  return '/* Design Tokens - generated from JSON; edit the source */\n:root {\n'+root.join('\n')+'\n}\n'+(dark.length?'\n.dark {\n'+dark.join('\n')+'\n}\n':'');
}
function main() {
  const args=process.argv.slice(2), options={};
  for (let i=0;i<args.length;i++) {
    const key={'--config':'config','-c':'config','--output':'output','-o':'output','--format':'format','-f':'format'}[args[i]];
    if (['--help','-h'].includes(args[i])) { console.log('Usage: node generate-tokens.cjs --config tokens.json [-o tokens.css] [--format css]'); return; }
    if (!key || !args[i+1] || args[i+1].startsWith('-')) throw new Error(`Invalid argument: ${args[i]}`);
    options[key]=args[++i];
  }
  if (!options.config) throw new Error('--config is required');
  if (options.format && options.format !== 'css') throw new Error('Only CSS output is supported; map semantic variables into the existing Tailwind configuration');
  const output=generateCSS(JSON.parse(fs.readFileSync(path.resolve(options.config),'utf8').replace(/^\uFEFF/,'')));
  if (options.output) { const dest=path.resolve(options.output); fs.mkdirSync(path.dirname(dest),{recursive:true}); fs.writeFileSync(dest,output); console.log(`Generated: ${dest}`); }
  else process.stdout.write(output);
}
module.exports={collectTokens,generateCSS};
if (require.main===module) { try { main(); } catch(e) { console.error(`Error: ${e.message}`); process.exitCode=1; } }
