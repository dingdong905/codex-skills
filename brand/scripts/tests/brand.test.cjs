const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const os=require('node:os');
const {spawnSync}=require('node:child_process');
const {extractColorsFromMarkdown,updateDesignTokens}=require('../sync-brand-to-tokens.cjs');
const script=path.resolve(__dirname,'../sync-brand-to-tokens.cjs');
const starter=path.resolve(__dirname,'../../templates/brand-guidelines-starter.md');
function fixture(t){const dir=fs.mkdtempSync(path.join(os.tmpdir(),'codex-brand-test-'));t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));fs.mkdirSync(path.join(dir,'docs'));fs.copyFileSync(starter,path.join(dir,'docs/brand-guidelines.md'));return dir;}
function run(dir,...args){return spawnSync(process.execPath,[script,'--project-root',dir,...args],{cwd:os.tmpdir(),encoding:'utf8'});}
test('starter swatches parse without inventing shades',()=>{
  const colors=extractColorsFromMarkdown(fs.readFileSync(starter,'utf8'));
  assert.equal(colors.primary.base,'#2563EB');assert.equal(colors.secondary.base,'#8B5CF6');assert.equal(colors.accent.base,'#10B981');
  const updated=updateDesignTokens({},colors);assert.equal(updated.primitive.color.primary['500'].$value,'#2563EB');assert.equal(updated.primitive.color.primary['700'],undefined);
});
test('brand name, status colors and existing primitives survive sync',()=>{
  const original={brand:'Example Company',primitive:{color:{coral:{$value:'#ABCDEF'}}},semantic:{color:{success:{$value:'#16A34A'},error:{$value:'#EF4444'},info:{$value:'#2563EB'}}},component:{button:{padding:{$value:'12px'}}}};
  const updated=updateDesignTokens(original,{primary:{base:'#333333'},secondary:{},accent:{}});
  assert.equal(updated.brand,original.brand);assert.deepEqual(updated.semantic.color.success,original.semantic.color.success);assert.deepEqual(updated.semantic.color.error,original.semantic.color.error);assert.deepEqual(updated.semantic.color.info,original.semantic.color.info);assert.deepEqual(updated.primitive.color.coral,original.primitive.color.coral);assert.deepEqual(updated.component,original.component);assert.equal(original.primitive.color.primary,undefined);
});
test('ambiguous guidelines fail instead of choosing a swatch',()=>{assert.throws(()=>extractColorsFromMarkdown('| Primary Color | #123456 |\n### Primary Colors\n| Main | #654321 |'),/Conflicting/);assert.throws(()=>extractColorsFromMarkdown('No colors supplied'),/No explicit/);});
test('empty project creates JSON and CSS from any cwd',t=>{
  const dir=fixture(t),r=run(dir);assert.equal(r.status,0,r.stderr);
  const data=JSON.parse(fs.readFileSync(path.join(dir,'assets/design-tokens.json'),'utf8'));
  assert.equal(data.primitive.color.accent['500'].$value,'#10B981');assert.match(fs.readFileSync(path.join(dir,'assets/design-tokens.css'),'utf8'),/--color-primary: var\(--primitive-color-primary-500\)/);
});
test('dry run creates no directories and does not overwrite JSON',t=>{
  const dir=fixture(t);assert.equal(run(dir,'--dry-run').status,0);assert.equal(fs.existsSync(path.join(dir,'assets')),false);
  fs.mkdirSync(path.join(dir,'assets'));const file=path.join(dir,'assets/design-tokens.json');fs.writeFileSync(file,'{}');assert.equal(run(dir,'--dry-run').status,0);assert.equal(fs.readFileSync(file,'utf8'),'{}');
});
test('custom project-relative output paths work',t=>{const dir=fixture(t),r=run(dir,'--tokens','theme/custom.json','--css','theme/custom.css');assert.equal(r.status,0,r.stderr);assert.ok(fs.existsSync(path.join(dir,'theme/custom.css')));assert.equal(fs.existsSync(path.join(dir,'assets')),false);});
test('missing generator fails without creating outputs',t=>{const dir=fixture(t),r=run(dir,'--generator',path.join(dir,'missing.cjs'));assert.equal(r.status,1);assert.match(r.stderr,/generator missing/);assert.equal(fs.existsSync(path.join(dir,'assets')),false);});
test('invalid existing references leave both outputs intact',t=>{
  const dir=fixture(t);fs.mkdirSync(path.join(dir,'assets'));const json=path.join(dir,'assets/design-tokens.json'),css=path.join(dir,'assets/design-tokens.css');
  const original=JSON.stringify({component:{button:{bg:{$value:'{semantic.color.no-such-color}'}}}});fs.writeFileSync(json,original);fs.writeFileSync(css,'existing css');
  const r=run(dir);assert.equal(r.status,1);assert.match(r.stderr,/Missing reference/);assert.equal(fs.readFileSync(json,'utf8'),original);assert.equal(fs.readFileSync(css,'utf8'),'existing css');
});
test('out-of-project and overlapping paths fail without output',t=>{
  const dir=fixture(t);assert.equal(run(dir,'--tokens','../outside.json').status,1);assert.equal(run(dir,'--tokens','docs/brand-guidelines.md').status,1);assert.equal(fs.existsSync(path.join(dir,'assets')),false);
});
test('context and palette tools parse the bundled template',()=>{
  const context=spawnSync(process.execPath,[path.resolve(__dirname,'../inject-brand-context.cjs'),'--json',starter],{cwd:os.tmpdir(),encoding:'utf8'});
  assert.equal(context.status,0,context.stderr);assert.ok(JSON.parse(context.stdout));
  const palette=spawnSync(process.execPath,[path.resolve(__dirname,'../extract-colors.cjs'),'--palette','--json','--brand-file',starter],{cwd:os.tmpdir(),encoding:'utf8'});
  assert.equal(palette.status,0,palette.stderr);assert.ok(JSON.parse(palette.stdout).all.includes('#2563EB'));
});
