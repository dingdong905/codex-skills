#!/usr/bin/env node
// Adapted from claudekit: explicit swatches only, preserve existing brand and status tokens.
const fs=require('node:fs');
const path=require('node:path');
function extractColorsFromMarkdown(content) {
  const colors={primary:{},secondary:{},accent:{}};
  function assign(role,kind,hex) {
    const normalized=hex.toUpperCase();
    if (colors[role][kind] && colors[role][kind] !== normalized) throw new Error(`Conflicting ${role} ${kind} color values`);
    colors[role][kind]=normalized;
  }
  for (const role of Object.keys(colors)) {
    const quick=new RegExp(`\\|\\s*\\*{0,2}${role} Color\\*{0,2}\\s*\\|\\s*(#[0-9a-f]{6})\\b`,'gi');
    for (const m of content.matchAll(quick)) assign(role,'base',m[1]);
    const heading=new RegExp(`^### ${role} Colors\\s*$([\\s\\S]*?)(?=^#{1,3} |$(?![\\s\\S]))`,'gim');
    for (const section of content.matchAll(heading)) {
      for (const row of section[1].matchAll(/\|\s*\*{0,2}([^*|]+?)\*{0,2}\s*\|\s*(#[a-f0-9]{6})\b/gi)) {
        const label=row[1].trim().toLowerCase();
        const target=label.includes('accent')?'accent':role;
        const kind=label.includes('dark')?'dark':label.includes('light')?'light':'base';
        assign(target,kind,row[2]);
      }
    }
  }
  if (!Object.values(colors).some(c=>Object.keys(c).length)) throw new Error('No explicit brand swatches found in guidelines');
  return colors;
}
function updateDesignTokens(tokens,colors) {
  const result=structuredClone(tokens);
  result.primitive ??={}; result.primitive.color ??={};
  result.semantic ??={}; result.semantic.color ??={};
  for (const [role,swatches] of Object.entries(colors)) {
    if (!Object.keys(swatches).length) continue;
    result.primitive.color[role] ??={};
    for (const [kind,hex] of Object.entries(swatches)) {
      const shade={base:'500',dark:'600',light:'100'}[kind];
      result.primitive.color[role][shade]={...(result.primitive.color[role][shade]||{}),$value:hex,$type:'color'};
      const semantic=kind==='base'?role:kind==='dark'?`${role}-hover`:`${role}-light`;
      result.semantic.color[semantic]={...(result.semantic.color[semantic]||{}),$value:`{primitive.color.${role}.${shade}}`,$type:'color'};
    }
  }
  return result;
}
function projectPath(root,value) {
  const resolved=path.resolve(root,value);
  const rel=path.relative(root,resolved);
  if (rel==='..' || rel.startsWith('..'+path.sep) || path.isAbsolute(rel)) throw new Error(`Path outside project: ${value}`);
  // Check existing parents for junctions/symlinks that resolve outside the root.
  let parent=resolved;
  while (!fs.existsSync(parent)) { const next=path.dirname(parent); if (next===parent) break; parent=next; }
  if (fs.existsSync(parent)) {
    const real=fs.realpathSync(parent), actualRoot=fs.realpathSync(root), realRel=path.relative(actualRoot,real);
    if (realRel==='..' || realRel.startsWith('..'+path.sep) || path.isAbsolute(realRel)) throw new Error(`Path resolves outside project: ${value}`);
  }
  return resolved;
}
function main() {
  const args=process.argv.slice(2), opt={};
  for(let i=0;i<args.length;i++) {
    if(args[i]==='--dry-run'){ opt.dryRun=true; continue; }
    if(['--help','-h'].includes(args[i])){ console.log('Usage: node sync-brand-to-tokens.cjs --project-root DIR [--guidelines FILE] [--tokens FILE] [--css FILE] [--generator FILE] [--dry-run]'); return; }
    const key={'--project-root':'root','--guidelines':'guidelines','--tokens':'tokens','--css':'css','--generator':'generator'}[args[i]];
    if(!key || !args[i+1] || args[i+1].startsWith('-')) throw new Error(`Invalid argument: ${args[i]}`);
    opt[key]=args[++i];
  }
  if(!opt.root) throw new Error('--project-root is required');
  const root=fs.realpathSync(path.resolve(opt.root));
  if(!fs.statSync(root).isDirectory()) throw new Error('Project root must be a directory');
  const guidelines=projectPath(root,opt.guidelines||'docs/brand-guidelines.md');
  const tokensPath=projectPath(root,opt.tokens||'assets/design-tokens.json');
  const cssPath=projectPath(root,opt.css||'assets/design-tokens.css');
  if(new Set([guidelines,tokensPath,cssPath].map(p=>p.toLowerCase())).size!==3) throw new Error('Input, JSON output and CSS output must be different paths');
  const generator=opt.generator?path.resolve(opt.generator):path.resolve(__dirname,'../../design-system/scripts/generate-tokens.cjs');
  if(!fs.existsSync(generator)) throw new Error('Token generator missing: install design-system alongside brand or pass --generator');
  const {generateCSS}=require(generator);
  const colors=extractColorsFromMarkdown(fs.readFileSync(guidelines,'utf8'));
  const old=fs.existsSync(tokensPath)?JSON.parse(fs.readFileSync(tokensPath,'utf8').replace(/^\uFEFF/,'')):{};
  const updated=updateDesignTokens(old,colors);
  const css=generateCSS(updated);
  if(opt.dryRun){ console.log(JSON.stringify({swatches:colors,tokens:updated,outputs:[tokensPath,cssPath]},null,2)); return; }
  fs.mkdirSync(path.dirname(tokensPath),{recursive:true}); fs.mkdirSync(path.dirname(cssPath),{recursive:true});
  fs.writeFileSync(tokensPath,JSON.stringify(updated,null,2)+'\n'); fs.writeFileSync(cssPath,css);
  console.log(`Updated: ${tokensPath}\nGenerated: ${cssPath}`);
}
module.exports={extractColorsFromMarkdown,updateDesignTokens,projectPath};
if(require.main===module){try{main();}catch(e){console.error(`Error: ${e.message}`);process.exitCode=1;}}
