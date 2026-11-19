// Execute the real generated review-page script; no browser/layout claim.
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const html=fs.readFileSync(new URL('../reports/mev_expansion/真实收支核对入口.html',import.meta.url),'utf8');
const start=html.lastIndexOf('<script>')+8,code=html.slice(start,html.indexOf('</script>',start));
const elements={select:{value:'0',options:[],add(o){this.options.push(o)}},input:{value:''},'#meta':{},'#count':{},thead:{},tbody:{}};
const buttons=['moves','net'].map(mode=>({dataset:{mode},classList:{toggle(){}}}));
globalThis.document={querySelector:s=>elements[s],querySelectorAll:()=>buttons};
globalThis.Option=function(text,value){this.text=text;this.value=value};
vm.runInThisContext(code);assert.equal(elements.select.options.length,7);assert.match(elements['#meta'].innerHTML,/etherscan.io\/tx\/0x722001/);assert.match(elements.tbody.innerHTML,/gas_base_fee_burn/);
elements.select.value='3';elements.select.onchange();assert.match(elements.tbody.innerHTML,/ERC6909_claim_transfer_not_cash/);elements.input.value='0x82ccba35ad0c7a62230ef8ff337ac67f4cce0ea5';elements.input.oninput();assert.match(elements.tbody.innerHTML,/64521435779627872/);
buttons[1].onclick();assert.match(elements.thead.innerHTML,/原始净变化/);assert.match(elements.tbody.innerHTML,/64521435779627872/);elements.input.value='no_such_address';elements.input.oninput();assert.equal(elements.tbody.innerHTML,'');
console.log(JSON.stringify({cases:7,case_selection:true,address_filter:true,raw_claim_units_preserved:true,net_view:true,browser_layout_verified:false}));
