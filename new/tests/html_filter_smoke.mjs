// Exercise the actual generated HTML filter logic in Node; this is not a browser/layout test.
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const html=fs.readFileSync(new URL('../reports/figures/fig01_stolen_fund_flow.html',import.meta.url),'utf8');
const start=html.lastIndexOf('<script>')+8;
const code=html.slice(start,html.indexOf('</script>',start));
const elements={};
for(const id of ['chain','token','start','end','minimum','unvalued','apply','plot','count','detail'])elements['#'+id]={value:'',checked:false,textContent:'',innerHTML:'',appendChild(){},removeAllListeners(){},on(event,listener){this.listener=listener;}};
elements['#chain'].value='ethereum';elements['#minimum'].value='1000000';
globalThis.document={querySelector:s=>elements[s],createElement:()=>({})};
globalThis.Plotly={react(id,traces,layout){elements['#plot'].traces=traces;}};
await vm.runInThisContext(code);
function count(){return Number(elements['#count'].textContent.match(/^([\d,]+)/)[1].replaceAll(',',''));}
const initial=count();assert.equal(initial,176);
elements['#chain'].value='bitcoin';elements['#minimum'].value='0';elements['#apply'].onclick();assert.equal(count(),3);
const btc=elements['#plot'].traces.filter(t=>t.mode==='lines');assert.equal(btc.length,3);
elements['#plot'].listener({points:[{customdata:btc[0].customdata[0]}]});assert.match(elements['#detail'].innerHTML,/blockstream.info/);assert.match(elements['#detail'].innerHTML,/vout:0/);
elements['#token'].value='native:eth';elements['#apply'].onclick();assert.equal(count(),0);
elements['#chain'].value='';elements['#token'].value='native:btc';elements['#apply'].onclick();assert.equal(count(),3);
elements['#end'].value='2026-10-30T07:03';elements['#apply'].onclick();assert.equal(count(),0);
console.log(JSON.stringify({test:'actual generated Figure1 filter logic',ethereum_min_1M:initial,bitcoin_outputs:3,incompatible_token_chain:0,October_excludes_November_BTC:true,browser_render_verified:false}));
