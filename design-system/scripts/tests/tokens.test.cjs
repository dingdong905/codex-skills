const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const {spawnSync}=require('node:child_process');
const {generateCSS}=require('../generate-tokens.cjs');
const tok=v=>({$value:v});
function config(){return {primitive:{color:{paper:tok('#ffffff'),ink:tok('#111111')}},semantic:{color:{background:tok('{primitive.color.paper}')}},component:{input:{bg:tok('{semantic.color.background}')}},dark:{semantic:{color:{background:tok('{primitive.color.ink}')}}}};}
test('component aliases follow dark themes including nested boundaries',()=>{
  const css=generateCSS(config());
  assert.match(css,/--input-bg: var\(--color-background\)/);
  const dark=css.split('.dark {')[1];
  assert.match(dark,/--color-background: var\(--primitive-color-ink\)/);
  assert.match(dark,/--input-bg: var\(--color-background\)/);
});
test('bundled starter resolves all aliases',()=>{
  const starter=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../templates/design-tokens-starter.json'),'utf8'));
  const css=generateCSS(starter); assert.match(css,/--button-bg: var\(--color-primary\)/);
  assert.doesNotMatch(css,/\{(?:primitive|semantic|component)\./);
});
test('references inside CSS shorthand are retained',()=>{
  const c=config(); c.component.input.border=tok('1px solid {primitive.color.ink}');
  assert.match(generateCSS(c),/--input-border: 1px solid var\(--primitive-color-ink\)/);
});
test('missing references fail',()=>{const c=config();c.component.input.bg=tok('{semantic.color.missing}');assert.throws(()=>generateCSS(c),/Missing reference/);});
test('cycles fail before emitting CSS',()=>{const c=config();c.semantic.color.background=tok('{component.input.bg}');assert.throws(()=>generateCSS(c),/cycle/);});
test('effective dark cycles fail',()=>{const c=config();c.dark.semantic.color.background=tok('{component.input.bg}');assert.throws(()=>generateCSS(c),/Dark theme reference cycle/);});
test('CSS variable collisions fail',()=>{const c=config();c.component.color={background:tok('#000')};assert.throws(()=>generateCSS(c),/collision/);});
test('zero is supported and composite values fail clearly',()=>{const c=config();c.primitive.spacing={zero:tok(0)};assert.match(generateCSS(c),/--primitive-spacing-zero: 0;/);c.primitive.spacing.zero=tok({value:0,unit:'px'});assert.throws(()=>generateCSS(c),/Unsupported composite/);});
test('unsafe CSS and invalid names fail',()=>{for(const value of ['red; color: blue','red/* hidden */','red}']){const c=config();c.primitive.color.ink=tok(value);assert.throws(()=>generateCSS(c),/Unsafe CSS/);}const c=config();c.primitive['bad name']=tok('red');assert.throws(()=>generateCSS(c),/Invalid token name/);});
test('invalid config leaves existing output untouched',t=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'codex-token-test-'));t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));
  const file=path.join(dir,'tokens.json'),out=path.join(dir,'tokens.css');fs.writeFileSync(file,JSON.stringify({semantic:{color:{x:tok('{missing}') }}}));fs.writeFileSync(out,'existing');
  const r=spawnSync(process.execPath,[path.resolve(__dirname,'../generate-tokens.cjs'),'--config',file,'-o',out],{encoding:'utf8'});
  assert.equal(r.status,1);assert.equal(fs.readFileSync(out,'utf8'),'existing');
});
test('hardcoding scanner detects a color beside a token and never fixes files',t=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'codex-scan-test-'));t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));
  const file=path.join(dir,'sample.css'),css='.btn { background: #FF6B6B; color: var(--color-primary); }\n';fs.writeFileSync(file,css);
  const r=spawnSync(process.execPath,[path.resolve(__dirname,'../validate-tokens.cjs'),'--dir',dir,'--fix'],{encoding:'utf8'});
  assert.equal(r.status,1);assert.match(r.stdout,/#FF6B6B/);assert.equal(fs.readFileSync(file,'utf8'),css);
  fs.writeFileSync(file,'.btn { background: var(--color-bg); }');
  assert.equal(spawnSync(process.execPath,[path.resolve(__dirname,'../validate-tokens.cjs'),'--dir',dir]).status,0);
});
